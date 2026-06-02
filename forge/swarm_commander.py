"""
GhostPrime — Swarm Commander
Orchestrates the ghost swarm. Deploys N ghosts concurrently across all faucet targets.
Reports cycle results to Telegram.
"""

import asyncio
import os
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import aiohttp
from ghost import run_ghost
from proxy_pool import get_pool, get_random_proxy

# ─── Targets ─────────────────────────────────────────────────────────────────

TARGETS = [
    "https://maticdrop-1.onrender.com",
    "https://maticdrop-2.onrender.com",
    "https://maticdrop-3.onrender.com",
    "https://maticdrop-4.onrender.com",
    "https://maticdrop-5.onrender.com",
]

# ─── Config ───────────────────────────────────────────────────────────────────

SWARM_SIZE = int(os.getenv("SWARM_SIZE", "25"))
CYCLE_INTERVAL = int(os.getenv("CYCLE_INTERVAL", "1800"))
CONCURRENCY = int(os.getenv("CONCURRENCY", "10"))
TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")
USE_PROXIES = os.getenv("USE_PROXIES", "true").lower() == "true"
PORT = int(os.getenv("PORT", "10000"))

# ─── Health Server (keeps Render web_service alive) ──────────────────────────

_status = {"cycle": 0, "last_run": "not started", "total_hits": 0}


class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        body = (
            f"🔱 GhostPrime LIVE\n"
            f"Cycle: {_status['cycle']} | Hits: {_status['total_hits']}\n"
            f"Last: {_status['last_run']}"
        ).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format, *args):
        pass  # Suppress access logs


def start_health_server():
    server = HTTPServer(("0.0.0.0", PORT), HealthHandler)
    t = threading.Thread(target=server.serve_forever, daemon=True)
    t.start()
    print(f"[HEALTH] Server listening on port {PORT}")


# ─── Telegram ─────────────────────────────────────────────────────────────────

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


# ─── Swarm Cycle ──────────────────────────────────────────────────────────────

async def run_cycle(cycle_num: int, proxy_pool: list):
    print(f"\n[SWARM] Cycle {cycle_num} — deploying {SWARM_SIZE} ghosts...")
    start = time.time()

    tasks = []
    for i in range(SWARM_SIZE):
        target = TARGETS[i % len(TARGETS)]
        proxy = get_random_proxy(proxy_pool) if USE_PROXIES and proxy_pool else None
        tasks.append(run_ghost(target_url=target, proxy=proxy, ghost_id=i + 1))

    semaphore = asyncio.Semaphore(CONCURRENCY)

    async def bounded(coro):
        async with semaphore:
            return await coro

    results = await asyncio.gather(*[bounded(t) for t in tasks])

    elapsed = round(time.time() - start, 1)
    successes = [r for r in results if r["success"]]
    failures = [r for r in results if not r["success"]]
    avg_dwell = round(sum(r["dwell"] for r in successes) / max(len(successes), 1), 1)

    site_hits = {}
    for r in successes:
        key = r["url"].split("//")[1].split(".")[0]
        site_hits[key] = site_hits.get(key, 0) + 1

    breakdown = " | ".join([f"{k}: {v}" for k, v in sorted(site_hits.items())])

    report = (
        f"🔱 <b>GhostPrime — Cycle {cycle_num}</b>\n"
        f"👻 Ghosts: {len(successes)}/{SWARM_SIZE} success\n"
        f"⏱ Avg dwell: {avg_dwell}s | Total: {elapsed}s\n"
        f"🎯 {breakdown}\n"
        f"❌ Failures: {len(failures)}"
    )

    print(report)
    await telegram(report)

    if failures:
        errs = set(r["error"] for r in failures if r["error"])
        for e in list(errs)[:3]:
            print(f"  ↳ {e}")

    _status["cycle"] = cycle_num
    _status["last_run"] = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    _status["total_hits"] = _status["total_hits"] + len(successes)

    return len(successes)


# ─── Main Loop ────────────────────────────────────────────────────────────────

async def main():
    # Start health server first so Render sees a bound port immediately
    start_health_server()

    print("🔱 GhostPrime Swarm Commander — ONLINE")
    print(f"   Targets: {len(TARGETS)} sites")
    print(f"   Swarm size: {SWARM_SIZE} ghosts/cycle")
    print(f"   Concurrency: {CONCURRENCY}")
    print(f"   Cycle interval: {CYCLE_INTERVAL}s")
    print(f"   Proxies: {'ON' if USE_PROXIES else 'OFF'}")

    await telegram(
        f"🔱 <b>GhostPrime ONLINE</b>\n"
        f"Swarm: {SWARM_SIZE} ghosts | Concurrency: {CONCURRENCY}\n"
        f"Targets: {len(TARGETS)} sites | Interval: {CYCLE_INTERVAL}s\n"
        f"Proxies: {'ON' if USE_PROXIES else 'OFF'}"
    )

    proxy_pool = []
    if USE_PROXIES:
        print("[PROXY] Fetching pool...")
        proxy_pool = await get_pool()
        print(f"[PROXY] {len(proxy_pool)} proxies loaded")

    cycle = 1
    while True:
        hits = await run_cycle(cycle, proxy_pool)
        cycle += 1

        if USE_PROXIES and cycle % 10 == 0:
            proxy_pool = await get_pool(refresh=True)
            print(f"[PROXY] Pool refreshed — {len(proxy_pool)} proxies")

        print(f"[SWARM] Sleeping {CYCLE_INTERVAL}s until next cycle...")
        await asyncio.sleep(CYCLE_INTERVAL)


if __name__ == "__main__":
    asyncio.run(main())
