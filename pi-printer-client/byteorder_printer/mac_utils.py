import subprocess
import re


def get_mac(interface: str = "wlan0") -> str:
    """Return the MAC address of the given interface (colon-separated, uppercase)."""
    try:
        with open(f"/sys/class/net/{interface}/address") as f:
            return f.read().strip().upper()
    except FileNotFoundError:
        # Fall back to ip command
        out = subprocess.check_output(["ip", "link", "show", interface], text=True)
        m = re.search(r"link/ether\s+([0-9a-f:]+)", out, re.I)
        if m:
            return m.group(1).upper()
        raise RuntimeError(f"Cannot determine MAC for {interface}")


def derive_claim_code(mac: str) -> str:
    """Return last 6 hex chars of MAC (no colons), uppercased — e.g. 'A1B2C3'."""
    return mac.replace(":", "")[-6:].upper()


def get_ip(interface: str = "wlan0") -> str | None:
    """Return the IPv4 address of the given interface, or None if not available."""
    try:
        with open(f"/sys/class/net/{interface}/operstate") as f:
            if f.read().strip() != "up":
                return None
        out = subprocess.check_output(["ip", "-4", "addr", "show", interface], text=True)
        m = re.search(r"inet\s+(\d+\.\d+\.\d+\.\d+)", out)
        return m.group(1) if m else None
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
