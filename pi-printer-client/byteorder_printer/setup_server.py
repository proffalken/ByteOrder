"""
Captive-portal web server shown when the Pi is in AP/setup mode.

Intercepts iOS / Android captive-portal probe URLs and serves a simple
WiFi + API-base configuration form.  On submission it saves the config,
stops the AP, connects to the chosen network, and registers with the backend.
"""
import logging
import threading
from flask import Flask, request, redirect, render_template_string

log = logging.getLogger(__name__)

_PORTAL_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ByteOrder Printer Setup</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5;
           display: flex; justify-content: center; padding: 2rem 1rem; }
    .card { background: white; border-radius: 12px; padding: 2rem;
            max-width: 400px; width: 100%; box-shadow: 0 2px 12px rgba(0,0,0,.1); }
    h1 { font-size: 1.4rem; margin-bottom: .25rem; }
    p  { color: #666; font-size: .9rem; margin-bottom: 1.5rem; }
    label { display: block; font-size: .85rem; font-weight: 600;
            color: #333; margin-bottom: .25rem; margin-top: 1rem; }
    input { width: 100%; border: 1px solid #ddd; border-radius: 8px;
            padding: .6rem .8rem; font-size: 1rem; }
    .claim { background: #f0f4ff; border-radius: 8px; padding: 1rem;
             margin-bottom: 1.5rem; text-align: center; }
    .claim .code { font-size: 2rem; font-weight: 700; letter-spacing: .2em;
                   color: #2563eb; font-family: monospace; }
    .claim small { display: block; color: #666; font-size: .8rem; margin-top: .25rem; }
    button { width: 100%; margin-top: 1.5rem; background: #2563eb; color: white;
             border: none; border-radius: 8px; padding: .75rem; font-size: 1rem;
             font-weight: 600; cursor: pointer; }
    button:hover { background: #1d4ed8; }
    .error { background: #fef2f2; color: #dc2626; border-radius: 8px;
             padding: .75rem; margin-bottom: 1rem; font-size: .9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>ByteOrder Printer Setup</h1>
    <p>Connect this printer to your WiFi network and link it to your kitchen.</p>

    <div class="claim">
      <div class="code">{{ claim_code }}</div>
      <small>Enter this code in the Admin → Printers page after setup</small>
    </div>

    {% if error %}
    <div class="error">{{ error }}</div>
    {% endif %}

    <form method="POST" action="/setup">
      <label>WiFi Network (SSID)</label>
      <input type="text" name="ssid" placeholder="My Kitchen WiFi" required
             value="{{ ssid or '' }}">

      <label>WiFi Password</label>
      <input type="password" name="psk" placeholder="password">

      <label>ByteOrder API Base URL</label>
      <input type="url" name="api_base" required
             value="{{ api_base }}" placeholder="https://byteorder.example.com">

      <button type="submit">Connect &amp; Save</button>
    </form>
  </div>
</body>
</html>
"""

_CONNECTING_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Connecting…</title>
  <meta http-equiv="refresh" content="20;url=/">
  <style>
    body { font-family: system-ui, sans-serif; text-align: center;
           padding: 4rem 1rem; background: #f5f5f5; }
    h1 { font-size: 1.4rem; }
    p  { color: #666; margin-top: 1rem; }
  </style>
</head>
<body>
  <h1>Connecting to WiFi…</h1>
  <p>The printer is joining your network. This page will reload in 20 seconds.<br>
     You can now reconnect to your normal WiFi.</p>
</body>
</html>
"""

# Captive-portal detection URLs used by iOS and Android
_CAPTIVE_PROBES = {
    # Apple
    "/hotspot-detect.html",
    "/library/test/success.html",
    # Android / Google
    "/generate_204",
    "/gen_204",
    "/connecttest.txt",
    "/ncsi.txt",
    "/redirect",
    "/canonical.html",
    "/success.txt",
}


def create_app(claim_code: str, api_base: str, on_submit) -> Flask:
    app = Flask(__name__)
    app.secret_key = claim_code  # good enough for a single-session setup server

    @app.before_request
    def intercept_captive():
        """Redirect all captive-portal probes to the setup page."""
        if request.path in _CAPTIVE_PROBES:
            return redirect("/", 302)

    @app.route("/", methods=["GET"])
    def index():
        return render_template_string(
            _PORTAL_HTML,
            claim_code=claim_code,
            api_base=api_base,
            ssid=None,
            error=None,
        )

    @app.route("/setup", methods=["POST"])
    def setup():
        ssid = request.form.get("ssid", "").strip()
        psk = request.form.get("psk", "")
        new_api_base = request.form.get("api_base", "").rstrip("/")

        if not ssid or not new_api_base:
            return render_template_string(
                _PORTAL_HTML,
                claim_code=claim_code,
                api_base=new_api_base or api_base,
                ssid=ssid,
                error="SSID and API base URL are required.",
            )

        # Kick off the connect + register flow in a background thread so the
        # browser gets the "Connecting…" page before the AP disappears.
        threading.Thread(
            target=on_submit,
            args=(ssid, psk, new_api_base),
            daemon=True,
        ).start()

        return render_template_string(_CONNECTING_HTML)

    return app


def run(claim_code: str, api_base: str, on_submit, host: str = "0.0.0.0", port: int = 80):
    app = create_app(claim_code, api_base, on_submit)
    log.info("Starting setup server on %s:%d", host, port)
    # use_reloader=False is essential inside a thread
    app.run(host=host, port=port, use_reloader=False, threaded=True)
