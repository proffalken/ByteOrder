from unittest.mock import mock_open, patch
from byteorder_printer.mac_utils import get_ip, derive_claim_code


def test_derive_claim_code():
    assert derive_claim_code("AA:BB:CC:DD:EE:FF") == "DDEEFF"
    assert derive_claim_code("aa:bb:cc:11:22:33") == "112233"


def test_get_ip_returns_address_when_interface_up():
    ip_output = "2: wlan0: <BROADCAST> ...\n    inet 192.168.1.42/24 brd 192.168.1.255\n"
    with patch("builtins.open", mock_open(read_data="up\n")), \
         patch("subprocess.check_output", return_value=ip_output):
        assert get_ip("wlan0") == "192.168.1.42"


def test_get_ip_returns_none_when_interface_down():
    with patch("builtins.open", mock_open(read_data="down\n")):
        assert get_ip("wlan0") is None


def test_get_ip_returns_none_when_interface_missing():
    with patch("builtins.open", side_effect=FileNotFoundError):
        assert get_ip("wlan0") is None
