from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app import models, schemas
from app.database import get_db

router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("/", response_model=list[schemas.CategoryOut])
def list_categories(active_only: bool = True, db: Session = Depends(get_db)):
    q = db.query(models.Category)
    if active_only:
        q = q.filter(models.Category.active == True)
    return q.order_by(models.Category.sort_order).all()


@router.get("/{category_id}", response_model=schemas.CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    return cat


@router.post("/", response_model=schemas.CategoryOut, status_code=201)
def create_category(data: schemas.CategoryIn, db: Session = Depends(get_db)):
    cat = models.Category(**data.model_dump())
    db.add(cat)
    db.commit()
    db.refresh(cat)
    return cat


@router.put("/{category_id}", response_model=schemas.CategoryOut)
def update_category(category_id: int, data: schemas.CategoryIn, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    for k, v in data.model_dump().items():
        setattr(cat, k, v)
    db.commit()
    db.refresh(cat)
    return cat


@router.delete("/{category_id}", status_code=204)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    cat = db.query(models.Category).filter(models.Category.id == category_id).first()
    if not cat:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(cat)
    db.commit()
