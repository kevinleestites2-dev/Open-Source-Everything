"""
GhostPrime — Swarm Commander v2.0
Upgraded to invisible_playwright stealth layer.
Each ghost = C++-patched Firefox, unique fingerprint, Bezier mouse motion.
reCAPTCHA v3 score: 0.90 | FingerprintJS: not detected | CreepJS: 0 lies
"""

import asyncio
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import aiohttp

# ─── Stealth Mode Toggle ─────────────────────────────────────────────────────
# STEALTH_MODE=true  → invisible_playwright (full browser, C++ fingerprint)
# STEALTH_MODE=false → legacy aiohttp (lightweight, header spoofing only)

STEALTH_MODE = os.getenv("STEALTH_MODE", "true").lower() == "true"

if STEALTH_MODE:
    from ghost_invisible import run_ghost_invisible as run_ghost_unit
else:
    from ghost import run_ghost as _legacy_ghost
    async def run_ghost_unit(target_url, proxy=None, ghost_id=0):
        r = await _legacy_ghost(target_url=target_url, proxy=proxy, ghost_id=ghost_id)
        # normalize to v2 result shape
        return {
            "ghost_id": ghost_id, "target": target_url, "proxy": proxy,
            "status": "success" if r.get("success") else "error",
            "duration": r.get("dwell", 0), "fingerprint_seed": None,
        }

from proxy_pool import get_pool, get_random_proxy

# ─── Targets ─────────────────────────────────────────────────────────────────

TARGETS = [
    "https://maticdrop-1.onrender.com",
    "https://maticdrop-2.onrender.com",
    "https://maticdrop-3.onrender.com",
    "https://maticdrop-4.onrender.com",
    "https://maticdrop-5.onrender.com",
]

# ─── Config ──────────────────────────────────────────────────────────────────

SWARM_SIZE      = int(os.getenv("SWARM_SIZE", "25"))
CYCLE_INTERVAL  = int(os.getenv("CYCLE_INTERVAL", "1800"))
CONCURRENCY     = int(os.getenv("CONCURRENCY", "10"))
TELEGRAM_TOKEN  = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
USE_PROXIES     = os.getenv("USE_PROXIES", "true").lower() == "true"
PORT            = int(os.getenv("PORT", "10000"))

# ─── Health Server ────────────────────────────────────────────────────────────

_status = {"cycle": 0, "last_run": "not started", "total_hits": 0, "mode": "STEALTH" if STEALTH_MODE else "LEGACY"}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (
            f"🔱 GhostPrime v2.0 LIVE [{_status['mode']} MODE]\n"
            f"Cycle: {_status['cycle']} | Hits: {_status['total_hits']}\n"
            f"Last: {_status['last_run']}"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[HEALTH] Server on port {PORT}")


# ─── Telegram ────────────────────────────────────────────────────────────────

async def telegram(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print(f"[TELEGRAM] {msg}")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"}
    try:
        async with aiohttp.ClientSession() as session:
            await session.post(url, json=payload, timeout=aiohttp.ClientTimeout(total=10))
    except Exception as e:
        print(f"[TELEGRAM ERROR] {e}")


# ─── Swarm Cycle ─────────────────────────────────────────────────────────────

async def run_cycle(cycle_num: int, proxy_pool: list):
    print(f"\n[SWARM] Cycle {cycle_num} — deploying {SWARM_SIZE} ghosts [{_status['mode']} MODE]...")
    start = time.time()

    tasks = []
    for i in range(SWARM_SIZE):
        target = TARGETS[i % len(TARGETS)]
        proxy  = get_random_proxy(proxy_pool) if USE_PROXIES and proxy_pool else None
        tasks.append(run_ghost_unit(target_url=target, proxy=proxy, ghost_id=i + 1))

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def bounded(coro):
        async with semaphore:
            return await coro

    results  = await asyncio.gather(*[bounded(t) for t in tasks])
    elapsed  = round(time.time() - start, 1)

    successes = [r for r in results if r["status"] == "success"]
    failures  = [r for r in results if r["status"] != "success"]
    avg_dur   = round(sum(r["duration"] for r in successes) / max(len(successes), 1), 1)

    site_hits = {}
    for r in successes:
        key = r["target"].split("//")[1].split(".")[0]
        site_hits[key] = site_hits.get(key, 0) + 1

    breakdown = " | ".join([f"{k}: {v}" for k, v in sorted(site_hits.items())])

    mode_icon = "🧠" if STEALTH_MODE else "👻"
    report = (
        f"🔱 <b>GhostPrime v2 — Cycle {cycle_num}</b>\n"
        f"{mode_icon} Mode: {'STEALTH (invisible_playwright)' if STEALTH_MODE else 'LEGACY (aiohttp)'}\n"
        f"👻 Ghosts: {len(successes)}/{SWARM_SIZE} success\n"
        f"⏱ Avg session: {avg_dur}s | Total: {elapsed}s\n"
        f"🎯 {breakdown}\n"
        f"❌ Failures: {len(failures)}"
    )

    print(report)
    await telegram(report)

    if failures:
        errs = set(r["status"] for r in failures if r["status"] != "success")
        for e in list(errs)[:3]:
            print(f"  ↳ {e}")

    _status["cycle"]      = cycle_num
    _status["last_run"]   = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    _status["total_hits"] += len(successes)

    return len(successes)


# ─── Main Loop ────────────────────────────────────────────────────────────────

async def main():
    start_health_server()

    print(f"🔱 GhostPrime Swarm Commander v2.0 — ONLINE")
    print(f"   Mode: {'STEALTH (invisible_playwright)' if STEALTH_MODE else 'LEGACY (aiohttp)'}")
    print(f"   Swarm: {SWARM_SIZE} | Concurrency: {CONCURRENCY} | Interval: {CYCLE_INTERVAL}s")

    await telegram(
        f"🔱 <b>GhostPrime v2.0 ONLINE</b>\n"
        f"{'🧠 STEALTH MODE — invisible_playwright active' if STEALTH_MODE else '👻 LEGACY MODE — aiohttp'}\n"
        f"Swarm: {SWARM_SIZE} | Concurrency: {CONCURRENCY} | Interval: {CYCLE_INTERVAL}s\n"
        f"Targets: {len(TARGETS)} sites | Proxies: {'ON' if USE_PROXIES else 'OFF'}"
    )

    proxy_pool = []
    if USE_PROXIES:
        print("[PROXY] Fetching pool...")
        proxy_pool = await get_pool()
        print(f"[PROXY] {len(proxy_pool)} proxies loaded")

    cycle = 1
    while True:
        await run_cycle(cycle, proxy_pool)
        cycle += 1

        if USE_PROXIES and cycle % 10 == 0:
            proxy_pool = await get_pool(refresh=True)
            print(f"[PROXY] Refreshed — {len(proxy_pool)} proxies")

        print(f"[SWARM] Sleeping {CYCLE_INTERVAL}s...")
        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
