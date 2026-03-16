import subprocess
import time
import logging

log = logging.getLogger(__name__)

CONNECT_TIMEOUT = 30  # seconds to wait for association
SCAN_TIMEOUT = 20     # seconds to wait for SSID to appear in scan results


def _find_wifi_interface() -> str:
    from .ap_manager import _find_wifi_interface as _find
    return _find()


def _scan_for_ssid(iface: str, ssid: str) -> bool:
    """Trigger a rescan and poll until the target SSID appears or timeout."""
    subprocess.run(
        ["nmcli", "device", "wifi", "rescan", "ifname", iface],
        capture_output=True,
    )
    for _ in range(SCAN_TIMEOUT):
        time.sleep(1)
        out = subprocess.run(
            ["nmcli", "-t", "-f", "DEVICE,SSID", "device", "wifi", "list", "ifname", iface],
            capture_output=True, text=True,
        ).stdout
        for line in out.splitlines():
            if line.startswith(f"{iface}:") and line.split(":", 1)[1].strip() == ssid:
                log.info("SSID '%s' found in scan", ssid)
                return True
    log.warning("SSID '%s' not seen after %ds — attempting connect anyway", ssid, SCAN_TIMEOUT)
    return False


def connect(ssid: str, psk: str) -> bool:
    """
    Connect to the given SSID using NetworkManager (nmcli).
    Rescans first so NM knows the network exists before trying to connect.
    Returns True on success, False if the connection fails or times out.
    """
    conn_name = f"byteorder-{ssid}"

    # Delete any stale connection profile with this name
    subprocess.run(
        ["nmcli", "connection", "delete", conn_name],
        capture_output=True,
    )

    try:
        iface = _find_wifi_interface()
    except RuntimeError:
        iface = "wlan0"

    # Scan first — on boot NM may not have seen the network yet
    _scan_for_ssid(iface, ssid)

    # Add and activate the connection
    result = subprocess.run(
        [
            "nmcli", "device", "wifi", "connect", ssid,
            "password", psk,
            "name", conn_name,
            "ifname", iface,
        ],
        capture_output=True,
        text=True,
        timeout=CONNECT_TIMEOUT + 5,
    )

    if result.returncode != 0:
        log.error("nmcli connect failed: %s", result.stderr.strip())
        return False

    # Wait for actual IP
    for _ in range(CONNECT_TIMEOUT):
        time.sleep(1)
        out = subprocess.run(
            ["nmcli", "-t", "-f", "GENERAL.STATE", "device", "show", iface],
            capture_output=True, text=True,
        ).stdout
        if "100 (connected)" in out:
            return True

    log.error("Timed out waiting for WiFi connection")
    return False


def current_ssid() -> str | None:
    """Return the SSID wlan0 is currently connected to, or None."""
    out = subprocess.run(
        ["nmcli", "-t", "-f", "active,ssid", "dev", "wifi"],
        capture_output=True, text=True,
    ).stdout
    for line in out.splitlines():
        if line.startswith("yes:"):
            return line.split(":", 1)[1] or None
    return None
