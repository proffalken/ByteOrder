from unittest.mock import call, patch, MagicMock
from byteorder_printer import wifi_manager


def _make_run(returncode=0, stdout="", stderr=""):
    m = MagicMock()
    m.returncode = returncode
    m.stdout = stdout
    m.stderr = stderr
    return m


def test_connect_rescans_before_connecting():
    """Ensures a wifi rescan is triggered before attempting to connect."""
    connected_state = _make_run(stdout="GENERAL.STATE:100 (connected)\n")

    with patch("byteorder_printer.wifi_manager._find_wifi_interface", return_value="wlan0"), \
         patch("subprocess.run") as mock_run:

        mock_run.side_effect = [
            _make_run(),                      # nmcli connection delete
            _make_run(),                      # nmcli device wifi rescan
            _make_run(stdout="wlan0:MyNet\n"),# scan poll — SSID found
            _make_run(),                      # nmcli device wifi connect
            connected_state,                  # state poll
        ]

        result = wifi_manager.connect("MyNet", "pass")

    assert result is True
    calls = [c.args[0] for c in mock_run.call_args_list]
    assert any("rescan" in c for c in calls)


def test_connect_waits_for_ssid_to_appear_in_scan():
    """Retries scan poll until SSID appears, then connects."""
    connected_state = _make_run(stdout="GENERAL.STATE:100 (connected)\n")

    with patch("byteorder_printer.wifi_manager._find_wifi_interface", return_value="wlan0"), \
         patch("byteorder_printer.wifi_manager.time") as mock_time, \
         patch("subprocess.run") as mock_run:

        mock_run.side_effect = [
            _make_run(),                          # delete
            _make_run(),                          # rescan
            _make_run(stdout="wlan0:Other\n"),    # scan poll 1 — not found
            _make_run(stdout="wlan0:Other\n"),    # scan poll 2 — not found
            _make_run(stdout="wlan0:MyNet\n"),    # scan poll 3 — found
            _make_run(),                          # connect
            connected_state,                      # state poll
        ]

        result = wifi_manager.connect("MyNet", "pass")

    assert result is True


def test_connect_falls_back_if_ssid_never_appears():
    """If SSID never shows up in scan, attempts connect anyway (AP may be hidden)."""
    connected_state = _make_run(stdout="GENERAL.STATE:100 (connected)\n")
    scan_timeout = 3

    with patch("byteorder_printer.wifi_manager._find_wifi_interface", return_value="wlan0"), \
         patch("byteorder_printer.wifi_manager.SCAN_TIMEOUT", scan_timeout), \
         patch("byteorder_printer.wifi_manager.time"), \
         patch("subprocess.run") as mock_run:

        scan_empty = _make_run(stdout="wlan0:Other\n")
        mock_run.side_effect = (
            [_make_run(), _make_run()]              # delete + rescan
            + [scan_empty] * scan_timeout           # all scan polls miss
            + [_make_run(), connected_state]        # connect + state
        )

        result = wifi_manager.connect("MyNet", "pass")

    assert result is True


def test_connect_returns_false_on_nmcli_error():
    with patch("byteorder_printer.wifi_manager._find_wifi_interface", return_value="wlan0"), \
         patch("byteorder_printer.wifi_manager.time"), \
         patch("subprocess.run") as mock_run:

        mock_run.side_effect = (
            [_make_run(), _make_run()]
            + [_make_run(stdout="wlan0:MyNet\n")]
            + [_make_run(returncode=1, stderr="Error: No network found")]
        )

        result = wifi_manager.connect("MyNet", "pass")

    assert result is False
