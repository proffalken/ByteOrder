import json
import os
from dataclasses import dataclass, asdict
from typing import Optional

CONFIG_PATH = os.environ.get("BYTEORDER_CONFIG", "/etc/byteorder-printer/config.json")


@dataclass
class Config:
    api_base: str = "https://byteorder.example.com"
    mac_address: str = ""
    kitchen_id: Optional[str] = None
    wifi_ssid: Optional[str] = None
    wifi_psk: Optional[str] = None


def load() -> Config:
    try:
        with open(CONFIG_PATH) as f:
            data = json.load(f)
        return Config(**{k: v for k, v in data.items() if k in Config.__dataclass_fields__})
    except (FileNotFoundError, json.JSONDecodeError, TypeError):
        return Config()


def save(cfg: Config) -> None:
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(asdict(cfg), f, indent=2)
