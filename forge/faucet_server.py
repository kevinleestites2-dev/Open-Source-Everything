"""
FaucetCloak Server — Render Web Service Wrapper
Keeps the service alive (HTTP on port 10000) while running
the cloak engine in a background thread loop.
"""

import threading
import asyncio
import time
import logging
from http.server import HTTPServer, BaseHTTPRequestHandler
from faucet_cloak import main as cloak_main, FAUCET_SITES, VISITS_PER_SITE

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("FaucetServer")

# ── STATUS TRACKING ──────────────────────────────────────────────────────────
state = {
    "cycles": 0,
    "running": False,
    "last_run": "never",
}

# ── HTTP KEEP-ALIVE SERVER ────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = f"""🔱 FaucetCloak Engine
Status: {'🟢 Running' if state['running'] else '⚪ Idle'}
Cycles completed: {state['cycles']}
Last run: {state['last_run']}
Sites: {len(FAUCET_SITES)}
Visits/site: {VISITS_PER_SITE}
Total visits/cycle: {len(FAUCET_SITES) * VISITS_PER_SITE}
""".encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # suppress HTTP logs

def run_http():
    server = HTTPServer(("0.0.0.0", 10000), Handler)
    log.info("HTTP keep-alive server on port 10000")
    server.serve_forever()

# ── CLOAK ENGINE LOOP ─────────────────────────────────────────────────────────
def run_cloak_loop():
    while True:
        state["running"] = True
        state["last_run"] = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
        log.info(f"🔱 Starting cloak cycle #{state['cycles'] + 1}")
        try:
            asyncio.run(cloak_main())
            state["cycles"] += 1
            log.info(f"✅ Cycle {state['cycles']} complete. Sleeping 30 min...")
        except Exception as e:
            log.error(f"Cycle error: {e}")
        finally:
            state["running"] = False
        time.sleep(1800)  # 30 min between cycles

# ── MAIN ──────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Start cloak engine in background thread
    t = threading.Thread(target=run_cloak_loop, daemon=True)
    t.start()

    # HTTP server on main thread (keeps Render alive)
    run_http()
