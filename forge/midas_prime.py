#!/usr/bin/env python3
"""
MidasPrime — The Metabolic Core (V3.0.0 LEGION)
Everything it touches turns to gold.

V3.0.0: Fully integrated into the Universal Vessel / Synaptic Bridge.
The heart of the Pantheon's energy flow.
"""

import os
import re
import sys
import json
import time
import uuid
import math
import signal
import sqlite3
import logging
import hashlib
import threading
import traceback
import importlib.util
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from collections import deque, defaultdict
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum

try:
    import requests
except ImportError:
    raise ImportError("requests required: pip install requests")

# ============================================================================
# LOGGING & SETUP
# ============================================================================

BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
TOPOLOGY_FILE = BASE_DIR / "pantheon_topology.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [MIDAS-PRIME] %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "midas_prime.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("MidasPrime")

# ============================================================================
# CONFIGURATION
# ============================================================================

class Config:
    OLLAMA_BASE     = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    DB_PATH         = os.getenv("MIDAS_DB", str(BASE_DIR / "midas_prime.db"))
    INITIAL_CAPITAL = float(os.getenv("INITIAL_CAPITAL", "0.0"))
    AUTO_WITHDRAW_THRESHOLD = float(os.getenv("AUTO_WITHDRAW_THRESHOLD", "500.0"))

# ============================================================================
# SYNAPTIC BRIDGE (The Heartbeat)
# ============================================================================

class MidasSynapse:
    def __init__(self, db: "MidasDB"):
        self.db = db
        self.role = "METABOLIC_CORE"
        self.topology = self._load_topology()
        log.info(f"❤️ Midas Synapse Active: {self.role} manifest.")

    def _load_topology(self):
        if TOPOLOGY_FILE.exists():
            return json.loads(TOPOLOGY_FILE.read_text())
        return {}

    def broadcast_metabolism(self):
        """Broadcasts financial vitals to the Synaptic Bridge."""
        vitals = {
            "balance": self.db.get_balance(),
            "total_earnings": self.db.get_total_earnings(),
            "total_trade_pnl": self.db.get_total_trade_pnl(),
            "total_withdrawn": self.db.get_total_withdrawn(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        signal = {
            "source": "MidasPrime",
            "type": "METABOLIC_PULSE",
            "data": vitals
        }
        
        # Manifest the signal for Deep-Meta to ingest
        signal_file = BASE_DIR / "aether_logs" / "synapse_deep-meta.jsonl"
        signal_file.parent.mkdir(exist_ok=True)
        with open(signal_file, "a") as f:
            f.write(json.dumps(signal) + "\n")
            
        log.info(f"💓 Metabolic Pulse Sent: Balance ${vitals['balance']:.2f}")

# ============================================================================
# MIDAS ENGINE
# ============================================================================

class MidasDB:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init()

    def _conn(self):
        return sqlite3.connect(self.db_path, timeout=10)

    def _init(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS wallet (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    amount REAL NOT NULL,
                    balance_after REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS performance (
                    metric TEXT PRIMARY KEY,
                    value REAL NOT NULL
                );
            """)

    def get_balance(self) -> float:
        with self._conn() as c:
            row = c.execute("SELECT balance_after FROM wallet ORDER BY id DESC LIMIT 1").fetchone()
            return row[0] if row else Config.INITIAL_CAPITAL

    def get_total_earnings(self): return 0.0 # Placeholder for expanded DB
    def get_total_trade_pnl(self): return 0.0 # Placeholder
    def get_total_withdrawn(self): return 0.0 # Placeholder

# ============================================================================
# MAIN
# ============================================================================

class MidasPrime:
    def __init__(self):
        self.db = MidasDB(Config.DB_PATH)
        self.synapse = MidasSynapse(self.db)

        # ── Stripe Conduit (PropPilot AI Revenue) ──────────────────────────
        stripe_key = os.environ.get("STRIPE_SECRET_KEY")
        if stripe_key:
            try:
                from stripe_conduit import StripeConduit
                self.stripe = StripeConduit(api_key=stripe_key)
                log.info("StripeConduit: ONLINE — PropPilot revenue tracking active.")
            except Exception as e:
                self.stripe = None
                log.warning(f"StripeConduit: offline — {e}")
        else:
            self.stripe = None
            log.info("StripeConduit: standby — set STRIPE_SECRET_KEY to activate.")
        
        print("""
   __  __ _     _           _____      _                 
  |  \/  (_)   | |         |  __ \    (_)                
  | \  / |_  __| | __ _ ___| |__) | __ _ _ __ ___   ___ 
  | |\/| | |/ _` |/ _` / __|  ___/ '__| | '_ ` _ \ / _ \\
  | |  | | | (_| | (_| \__ \ |   | |  | | | | | | |  __/
  |_|  |_|_|\__,_|\__,_|___/_|   |_|  |_|_| |_| |_|\___|
                                                         
        MidasPrime V3.0.0 Online.
        Metabolic Core: ACTIVE
        Synaptic Bridge: CONNECTED
        """)

    def run(self):
        cycle = 0
        log.info("🔱 MidasPrime metabolic cycle STARTED.")
        while True:
            try:
                cycle += 1
                log.info(f"⚡ Cycle #{cycle} — {datetime.now(tz=timezone.utc).strftime('%H:%M:%S UTC')}")

                # 1. Heartbeat
                self.synapse.broadcast_metabolism()

                # 2. Stripe Sync — PropPilot revenue every cycle
                if self.stripe:
                    try:
                        self.stripe.sync_to_war_chest()
                        self.stripe.sync_subscriptions()
                        log.info(self.stripe.war_chest_report())
                    except Exception as e:
                        log.error(f"Stripe sync error: {e}")

                # 3. Bird Dog Lead Sourcing — every 6 cycles (~30 min)
                if cycle % 6 == 0:
                    try:
                        from bird_dog_sourcer import BirdDogSourcer
                        sourcer = BirdDogSourcer()
                        new_leads = sourcer.run_scan()
                        log.info(f"🐕 Bird Dog: {new_leads} new leads sourced this cycle.")
                    except Exception as e:
                        log.error(f"Bird Dog sourcing error: {e}")

                # 3b. Buyer Discovery — every 24 cycles (~2 hours)
                if cycle % 24 == 0:
                    try:
                        from buyer_finder import BuyerFinder
                        finder = BuyerFinder()
                        new_buyers = finder.run_scan()
                        log.info(f"🎯 Buyer Finder: {new_buyers} new investors added to list.")
                    except Exception as e:
                        log.error(f"Buyer finder error: {e}")

                # 4. War Chest Bridge Sync — pulls in OmegaPrime + TradeMeta earnings
                try:
                    from war_chest_bridge import sync_all, full_report
                    balance = sync_all()
                    log.info(f"💰 War Chest: ${balance:,.2f}")
                except Exception as e:
                    log.error(f"War Chest bridge error: {e}")

                # 5. Print tracker report every 3 cycles (~15 min)
                if cycle % 3 == 0:
                    try:
                        import subprocess
                        subprocess.run(["python3", str(Path(__file__).parent / "midas_tracker.py")],
                                       capture_output=False, timeout=30)
                    except Exception as e:
                        log.error(f"Tracker report error: {e}")

                time.sleep(300)  # 5-minute metabolic cycle

            except KeyboardInterrupt:
                log.info("🛑 MidasPrime shutdown signal received.")
                break
            except Exception as e:
                log.error(f"Error in Midas loop: {e}")
                time.sleep(30)

if __name__ == "__main__":
    import sys
    from datetime import datetime, timezone
    midas = MidasPrime()
    if "--run" in sys.argv:
        midas.run()
    else:
        # Default: single status check
        log.info("MidasPrime online. Run with --run to start metabolic cycle.")
        if midas.stripe:
            midas.stripe.sync_to_war_chest()
            print(midas.stripe.war_chest_report())
