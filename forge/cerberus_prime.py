#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║          C E R B E R U S   P R I M E                      ║
║          One Bot. Three Heads. No Mercy.                  ║
╠═══════════════════════════════════════════════════════════╣
║  HEAD 1 — FLUX   : The Ocean  (Adaptive Strategy)        ║
║  HEAD 2 — AEON   : The Gale   (High-Velocity Signal)     ║
║  HEAD 3 — IGNIS  : The Flame  (Strike Execution)         ║
╠═══════════════════════════════════════════════════════════╣
║  Each head runs its own Agent Zero.                       ║
║  All three share one body, one mission, one War Chest.   ║
╚═══════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import time
import logging
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

# ── Path setup ────────────────────────────────────────────────────────────────
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))  # workspace root

from heads.flux_head  import FluxHead
from heads.aeon_head  import AeonHead
from heads.ignis_head import IgnisHead

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("CerberusPrime")


class CerberusPrime:
    """
    The Three-Headed God.
    
    Orchestrates FLUX, AEON, and IGNIS as parallel autonomous agents
    running on a shared body (HydraPrime / Red Magic device).
    
    Inter-head coordination:
    - FLUX → AEON: strategy signals (what to hunt)
    - AEON → IGNIS: validated targets (what to strike)
    - IGNIS → FLUX: strike results (what worked)
    - All heads → Telegram: live reporting
    """

    VERSION = "1.0.0"

    def __init__(self):
        # Load config
        self._load_config()

        # Telegram
        self.tg_token   = os.getenv("TELEGRAM_BOT_TOKEN", "8616341142:AAGv9M_buIvZtzzDGUE5ikE4K9GTlZ9E5ik")
        self.tg_chat_id = os.getenv("TELEGRAM_CHAT_ID",   "7135054241")

        # Shared state — all three heads write here
        self.shared_state = {
            "cerberus_cycle":  0,
            "total_pnl":       0.0,
            "flux_cycles":     0,
            "aeon_cycles":     0,
            "ignis_cycles":    0,
            "started_at":      datetime.utcnow().isoformat(),
            "mission":         None,
        }
        self.state_lock = threading.Lock()

        # Boot the three heads
        logger.info("🐕 Cerberus Prime initializing...")
        self.tg("🐕‍🦺 *CERBERUS PRIME AWAKENING*\nThree heads. One body. No mercy.\n\nBooting FLUX... AEON... IGNIS...")

        self.flux  = FluxHead(telegram_fn=self.tg,  cycle_interval=int(os.getenv("FLUX_INTERVAL",  "60")))
        self.aeon  = AeonHead(telegram_fn=self.tg,  cycle_interval=int(os.getenv("AEON_INTERVAL",  "45")))
        self.ignis = IgnisHead(telegram_fn=self.tg, cycle_interval=int(os.getenv("IGNIS_INTERVAL", "90")))

        self.heads = {
            "FLUX":  self.flux,
            "AEON":  self.aeon,
            "IGNIS": self.ignis,
        }

        self.running = False
        logger.info("🐕 Cerberus Prime initialized — all three heads online")

    # ── Config ────────────────────────────────────────────────────────────────

    def _load_config(self):
        """Load .env / cerberus.env"""
        from dotenv import load_dotenv
        env_paths = [
            ROOT / "config" / "cerberus.env",
            Path.home() / "CerberusPrime" / "config" / "cerberus.env",
            ROOT.parent / ".env",
        ]
        for p in env_paths:
            if p.exists():
                load_dotenv(p)
                logger.info(f"🐕 Config loaded from {p}")
                break

    # ── Telegram ─────────────────────────────────────────────────────────────

    def tg(self, msg: str):
        """Send Telegram message to Forgemaster."""
        if not self.tg_token or not self.tg_chat_id:
            return
        try:
            requests.post(
                f"https://api.telegram.org/bot{self.tg_token}/sendMessage",
                json={
                    "chat_id":    self.tg_chat_id,
                    "text":       f"🐕 CerberusPrime\n{msg}",
                    "parse_mode": "Markdown",
                },
                timeout=5,
            )
        except Exception:
            pass

    # ── Mission ───────────────────────────────────────────────────────────────

    def set_mission(self, mission: str):
        """Set the global mission. All three heads receive it."""
        with self.state_lock:
            self.shared_state["mission"] = mission

        self.flux.agent.set_mission(f"[FLUX] {mission}")
        self.aeon.agent.set_mission(f"[AEON] {mission}")
        self.ignis.agent.set_mission(f"[IGNIS] {mission}")

        self.tg(f"🎯 *Mission Set*\n{mission}\n\nAll three heads locked on target.")
        logger.info(f"🐕 Mission set: {mission}")

    # ── Inter-Head Coordination ───────────────────────────────────────────────

    def _coordination_loop(self):
        """
        The nervous system.
        FLUX outputs → AEON ingests → IGNIS fires.
        Runs as a background thread.
        """
        logger.info("🐕 Coordination loop started")
        while self.running:
            try:
                # FLUX → AEON: pass signals from FLUX memory to AEON queue
                if self.flux.agent.memory:
                    latest = self.flux.agent.memory[-1]
                    if latest.get("success") and latest.get("pnl", 0) > 50:
                        self.aeon.ingest_signal({
                            "type":   "flux_opportunity",
                            "pnl":    latest["pnl"],
                            "cycle":  latest["cycle"],
                            "source": "FLUX",
                        })

                # AEON → IGNIS: when AEON finds a high-conviction signal, queue strike
                if self.aeon.agent.memory:
                    latest = self.aeon.agent.memory[-1]
                    if latest.get("success") and latest.get("pnl", 0) > 100:
                        self.ignis.queue_strike(
                            target="https://lee.realtaxdeed.com",
                            strike_type="cloud"
                        )

                # IGNIS → FLUX: feed strike results back for learning
                if self.ignis.agent.memory:
                    latest = self.ignis.agent.memory[-1]
                    # Update shared PnL
                    with self.state_lock:
                        self.shared_state["total_pnl"] += latest.get("pnl", 0.0)
                        self.shared_state["cerberus_cycle"] += 1

                time.sleep(10)  # Coordination tick: every 10 seconds

            except Exception as e:
                logger.error(f"🐕 Coordination error: {e}")
                time.sleep(5)

    # ── Heartbeat ─────────────────────────────────────────────────────────────

    def _heartbeat_loop(self):
        """Every 30 min — full status report to Forgemaster."""
        while self.running:
            time.sleep(1800)
            self._report_status()

    def _report_status(self):
        with self.state_lock:
            state = dict(self.shared_state)

        flux_s  = self.flux.status()
        aeon_s  = self.aeon.status()
        ignis_s = self.ignis.status()

        msg = (
            f"💓 *Cerberus Heartbeat*\n"
            f"Time: {datetime.now().strftime('%H:%M:%S')}\n\n"
            f"🌊 FLUX  — Cycle {flux_s['cycle']} | "
            f"Conviction: {flux_s['weights']['conviction']:.2f}\n"
            f"🌬️ AEON  — Cycle {aeon_s['cycle']} | "
            f"Queue: {aeon_s['queue_depth']}\n"
            f"🔥 IGNIS — Cycle {ignis_s['cycle']} | "
            f"Strikes: {ignis_s['strike_queued']} queued\n\n"
            f"💰 Total PnL: ${state['total_pnl']:.2f}\n"
            f"🎯 Mission: {state['mission'] or 'None set'}"
        )
        self.tg(msg)
        logger.info(f"🐕 Status: PnL=${state['total_pnl']:.2f} | "
                    f"FLUX={flux_s['cycle']} AEON={aeon_s['cycle']} IGNIS={ignis_s['cycle']}")

    # ── Start / Stop ──────────────────────────────────────────────────────────

    def start(self, mission: Optional[str] = None):
        """Unleash Cerberus. All three heads go live simultaneously."""
        self.running = True

        if mission:
            self.set_mission(mission)

        # Start all three heads in parallel
        self.flux.start()
        self.aeon.start()
        self.ignis.start()

        # Start coordination nervous system
        coord_thread = threading.Thread(
            target=self._coordination_loop, daemon=True, name="CerberusCoord"
        )
        coord_thread.start()

        # Start heartbeat
        hb_thread = threading.Thread(
            target=self._heartbeat_loop, daemon=True, name="CerberusHeartbeat"
        )
        hb_thread.start()

        self.tg(
            f"🐕‍🦺 *CERBERUS IS LIVE*\n"
            f"Version: {self.VERSION}\n\n"
            f"🌊 FLUX  — Active\n"
            f"🌬️ AEON  — Active\n"
            f"🔥 IGNIS — Active\n\n"
            f"Three heads. One mission. Unleashed."
        )
        logger.info("🐕 CERBERUS PRIME — ALL HEADS LIVE")

        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()

    def stop(self):
        """Kill all three heads."""
        self.running = False
        self.flux.stop()
        self.aeon.stop()
        self.ignis.stop()
        self.tg("🐕 Cerberus Prime: ALL HEADS OFFLINE. Standing down.")
        logger.info("🐕 Cerberus Prime stopped")

    def status(self) -> Dict[str, Any]:
        with self.state_lock:
            state = dict(self.shared_state)
        state["heads"] = {
            "FLUX":  self.flux.status(),
            "AEON":  self.aeon.status(),
            "IGNIS": self.ignis.status(),
        }
        return state


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CerberusPrime — Three-Headed God")
    parser.add_argument("--mission", type=str, default=None, help="Mission directive")
    args = parser.parse_args()

    cerberus = CerberusPrime()
    cerberus.start(mission=args.mission or "Grow the War Chest. No limits.")

