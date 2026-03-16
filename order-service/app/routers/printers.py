import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app import models, schemas
from app.auth import get_kitchen_id
from app.database import get_db, SessionLocal
from app.redis_client import get_redis

router = APIRouter(prefix="/orders/printers", tags=["printers"])


def _claim_code_from_mac(mac: str) -> str:
    """Last 6 hex characters of the MAC address, uppercase, no colons."""
    return mac.replace(":", "").upper()[-6:]


def _get_printer_by_mac(mac: str, db: Session) -> models.PrinterDevice | None:
    return db.query(models.PrinterDevice).filter(
        models.PrinterDevice.mac_address == mac.upper()
    ).first()


# ── Public endpoint — called by the Pi on every boot ──────────────────────────

@router.post("/register", response_model=schemas.PrinterRegisterResponse)
def register_printer(data: schemas.PrinterRegistration, db: Session = Depends(get_db)):
    """Idempotent registration called by the Pi on boot.
    No auth required — only announces the device's existence.
    """
    mac = data.mac_address.upper()
    claim_code = _claim_code_from_mac(mac)

    device = _get_printer_by_mac(mac, db)
    if device:
        device.last_seen_at = datetime.utcnow()
        if data.ip_address:
            device.ip_address = data.ip_address
    else:
        device = models.PrinterDevice(
            mac_address=mac,
            claim_code=claim_code,
            ip_address=data.ip_address,
        )
        db.add(device)

    db.commit()
    db.refresh(device)

    return schemas.PrinterRegisterResponse(
        claim_code=device.claim_code,
        claimed=device.kitchen_id is not None,
        kitchen_id=device.kitchen_id,
    )


# ── Admin endpoints — authenticated via Clerk (X-Kitchen-ID from proxy) ───────

@router.get("/", response_model=list[schemas.PrinterDeviceOut])
def list_printers(db: Session = Depends(get_db), kitchen_id: str = Depends(get_kitchen_id)):
    return db.query(models.PrinterDevice).filter(
        models.PrinterDevice.kitchen_id == kitchen_id
    ).order_by(models.PrinterDevice.registered_at).all()


@router.post("/claim", response_model=schemas.PrinterDeviceOut)
def claim_printer(
    data: schemas.PrinterClaim,
    db: Session = Depends(get_db),
    kitchen_id: str = Depends(get_kitchen_id),
):
    device = db.query(models.PrinterDevice).filter(
        models.PrinterDevice.claim_code == data.claim_code.upper()
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="No printer found with that claim code")
    if device.kitchen_id and device.kitchen_id != kitchen_id:
        raise HTTPException(status_code=409, detail="Printer is already claimed by another kitchen")

    device.kitchen_id = kitchen_id
    device.name = data.name
    device.claimed_at = datetime.utcnow()
    db.commit()
    db.refresh(device)
    return device


@router.put("/{printer_id}", response_model=schemas.PrinterDeviceOut)
def rename_printer(
    printer_id: int,
    data: schemas.PrinterRename,
    db: Session = Depends(get_db),
    kitchen_id: str = Depends(get_kitchen_id),
):
    device = db.query(models.PrinterDevice).filter(
        models.PrinterDevice.id == printer_id,
        models.PrinterDevice.kitchen_id == kitchen_id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Printer not found")
    device.name = data.name
    db.commit()
    db.refresh(device)
    return device


@router.delete("/{printer_id}", status_code=204)
def unclaim_printer(
    printer_id: int,
    db: Session = Depends(get_db),
    kitchen_id: str = Depends(get_kitchen_id),
):
    device = db.query(models.PrinterDevice).filter(
        models.PrinterDevice.id == printer_id,
        models.PrinterDevice.kitchen_id == kitchen_id,
    ).first()
    if not device:
        raise HTTPException(status_code=404, detail="Printer not found")
    device.kitchen_id = None
    device.name = None
    device.claimed_at = None
    db.commit()


# ── Printer SSE stream — authenticated with MAC as Bearer token ───────────────

@router.get("/stream")
async def printer_stream(
    authorization: str = Header(default=""),
    db: Session = Depends(get_db),
):
    """SSE stream of new orders for the printer's kitchen.
    Auth: Authorization: Bearer <mac_address>
    """
    if not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Bearer MAC token required")

    mac = authorization[7:].strip().upper()
    device = _get_printer_by_mac(mac, db)
    if not device:
        raise HTTPException(status_code=401, detail="Unknown printer — register first")
    if not device.kitchen_id:
        raise HTTPException(status_code=403, detail="Printer not yet claimed by a kitchen")

    # Update last_seen
    device.last_seen_at = datetime.utcnow()
    db.commit()

    kitchen_id = device.kitchen_id

    async def event_generator():
        redis = get_redis()
        pubsub = redis.pubsub()
        pubsub.subscribe(f"new_orders:{kitchen_id}")
        try:
            while True:
                message = pubsub.get_message(ignore_subscribe_messages=True, timeout=0)
                if message:
                    yield f"data: {message['data'].decode()}\n\n"
                else:
                    yield ": keepalive\n\n"
                await asyncio.sleep(0.5)
        finally:
            pubsub.unsubscribe()
            pubsub.close()

    return StreamingResponse(event_generator(), media_type="text/event-stream")
