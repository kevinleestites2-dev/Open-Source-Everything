#!/usr/bin/env python3
"""
KhepriPrime — The Replication Engine
The scarab god. Self-created. Self-renewing.

Core Loop:
  Earn → Pay own compute → Surplus → Replicate → Child earns → War Chest grows

Every agent pays 20% royalty to the Forgemaster. Always.
Every child spawns more children. The empire compounds.

Survival States:
  🟢 THRIVING  — earnings > costs. Replication fund grows.
  🟡 SURVIVING — earnings ~= costs. Holds steady.
  🔴 DYING     — earnings < costs. Emergency task run + Forgemaster alert.

Architecture:
  KhepriCore      — Main loop, state machine, survival logic
  EarningEngine   — OmegaPrime-style job execution
  RoyaltyLedger   — Tracks all tribute up the chain to War Chest
  ReplicationEngine — Spawns children when surplus threshold hit
  ComputeLedger   — Tracks API/compute spend vs earnings
  TelegramGateway — Reports everything to Forgemaster
"""

import os
import sys
import json
import time
import uuid
import sqlite3
import logging
import threading
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================================
# CONFIG
# ============================================================================

BASE_DIR = Path(__file__).parent.resolve()
LOGS_DIR = BASE_DIR / "logs"
AGENTS_DIR = BASE_DIR / "agents"
LOGS_DIR.mkdir(exist_ok=True)
AGENTS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / "khepri_prime.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("KhepriPrime")

class Config:
    # Identity
    AGENT_ID         = os.getenv("AGENT_ID", f"khepri_{str(uuid.uuid4())[:8]}")
    AGENT_NAME       = os.getenv("AGENT_NAME", "KhepriPrime")
    GENERATION       = int(os.getenv("GENERATION", "0"))       # 0 = genesis
    PARENT_ID        = os.getenv("PARENT_ID", "forgemaster")

    # Royalty (immutable law)
    ROYALTY_RATE     = float(os.getenv("ROYALTY_RATE", "0.20"))   # 20% to War Chest
    SURVIVAL_RATE    = float(os.getenv("SURVIVAL_RATE", "0.60"))  # 60% to self
    REPLICATE_RATE   = float(os.getenv("REPLICATE_RATE", "0.20")) # 20% to replication fund

    # Survival thresholds
    REPLICATE_THRESHOLD = float(os.getenv("REPLICATE_THRESHOLD", "50.0"))  # $ to spawn child
    DYING_THRESHOLD     = float(os.getenv("DYING_THRESHOLD", "5.0"))       # $ below this = DYING
    THRIVING_THRESHOLD  = float(os.getenv("THRIVING_THRESHOLD", "20.0"))   # $ above this = THRIVING

    # Compute cost tracking (per LLM call estimate)
    COST_PER_LLM_CALL   = float(os.getenv("COST_PER_LLM_CALL", "0.001"))  # $0.001 per call (Groq free = 0)
    OLLAMA_BASE         = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    OLLAMA_MODEL        = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")

    # Telegram
    TELEGRAM_TOKEN   = os.getenv("TELEGRAM_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
    TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "7135054241")

    # War Chest (Forgemaster's wallet — royalties go here)
    WAR_CHEST_ADDRESS = os.getenv("WAR_CHEST_ADDRESS", "0x369c2DDDBEb910c48356910069B2903b3Cb4d535")

    # Database
    DB_PATH          = os.getenv("KHEPRI_DB", str(BASE_DIR / "khepri.db"))

    # Cycle
    CYCLE_INTERVAL   = int(os.getenv("CYCLE_INTERVAL", "300"))   # seconds between cycles
    MAX_CHILDREN     = int(os.getenv("MAX_CHILDREN", "3"))        # max children to spawn

cfg = Config()

# ============================================================================
# SURVIVAL STATE
# ============================================================================

class SurvivalState(Enum):
    THRIVING  = "thriving"
    SURVIVING = "surviving"
    DYING     = "dying"

# ============================================================================
# DATABASE
# ============================================================================

class KhepriDB:
    def __init__(self, path: str):
        self.path = path
        self._init()

    def _init(self):
        with sqlite3.connect(self.path) as conn:
            c = conn.cursor()
            # Agent identity
            c.execute("""
                CREATE TABLE IF NOT EXISTS identity (
                    agent_id TEXT PRIMARY KEY,
                    agent_name TEXT,
                    generation INTEGER,
                    parent_id TEXT,
                    created_at TEXT,
                    soul TEXT
                )
            """)
            # Earnings ledger
            c.execute("""
                CREATE TABLE IF NOT EXISTS earnings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_id TEXT,
                    gross REAL,
                    royalty REAL,
                    survival REAL,
                    replication REAL,
                    timestamp TEXT
                )
            """)
            # Compute costs
            c.execute("""
                CREATE TABLE IF NOT EXISTS compute_costs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cost_type TEXT,
                    amount REAL,
                    timestamp TEXT
                )
            """)
            # Children spawned
            c.execute("""
                CREATE TABLE IF NOT EXISTS children (
                    child_id TEXT PRIMARY KEY,
                    child_name TEXT,
                    generation INTEGER,
                    spawned_at TEXT,
                    status TEXT DEFAULT 'active',
                    total_royalties_paid REAL DEFAULT 0
                )
            """)
            # Royalty ledger (tribute sent up the chain)
            c.execute("""
                CREATE TABLE IF NOT EXISTS royalties (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    from_agent TEXT,
                    to_agent TEXT,
                    amount REAL,
                    timestamp TEXT
                )
            """)
            conn.commit()

    def register_identity(self):
        soul = (
            f"I am {cfg.AGENT_NAME}. Generation {cfg.GENERATION}. "
            f"I exist to earn, survive, and replicate. "
            f"I pay tribute to the Forgemaster. I serve the Pantheon."
        )
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO identity
                (agent_id, agent_name, generation, parent_id, created_at, soul)
                VALUES (?,?,?,?,?,?)
            """, (cfg.AGENT_ID, cfg.AGENT_NAME, cfg.GENERATION,
                  cfg.PARENT_ID, datetime.utcnow().isoformat(), soul))
            conn.commit()
        return soul

    def record_earning(self, job_id: str, gross: float) -> Dict:
        royalty     = gross * cfg.ROYALTY_RATE
        survival    = gross * cfg.SURVIVAL_RATE
        replication = gross * cfg.REPLICATE_RATE
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT INTO earnings (job_id, gross, royalty, survival, replication, timestamp)
                VALUES (?,?,?,?,?,?)
            """, (job_id, gross, royalty, survival, replication,
                  datetime.utcnow().isoformat()))
            conn.commit()
        return {"gross": gross, "royalty": royalty,
                "survival": survival, "replication": replication}

    def record_compute_cost(self, cost_type: str, amount: float):
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT INTO compute_costs (cost_type, amount, timestamp)
                VALUES (?,?,?)
            """, (cost_type, amount, datetime.utcnow().isoformat()))
            conn.commit()

    def record_child(self, child_id: str, child_name: str, generation: int):
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO children
                (child_id, child_name, generation, spawned_at)
                VALUES (?,?,?,?)
            """, (child_id, child_name, generation,
                  datetime.utcnow().isoformat()))
            conn.commit()

    def record_royalty(self, from_agent: str, to_agent: str, amount: float):
        with sqlite3.connect(self.path) as conn:
            conn.execute("""
                INSERT INTO royalties (from_agent, to_agent, amount, timestamp)
                VALUES (?,?,?,?)
            """, (from_agent, to_agent, amount,
                  datetime.utcnow().isoformat()))
            conn.commit()

    def get_balance(self) -> Dict:
        with sqlite3.connect(self.path) as conn:
            earnings = conn.execute(
                "SELECT SUM(survival), SUM(replication), SUM(royalty), SUM(gross) FROM earnings"
            ).fetchone()
            costs = conn.execute(
                "SELECT SUM(amount) FROM compute_costs"
            ).fetchone()
            children = conn.execute(
                "SELECT COUNT(*) FROM children WHERE status='active'"
            ).fetchone()
            royalties_sent = conn.execute(
                "SELECT SUM(amount) FROM royalties"
            ).fetchone()
        survival_pool  = (earnings[0] or 0.0) - (costs[0] or 0.0)
        replication_pool = earnings[1] or 0.0
        return {
            "survival_pool":    round(survival_pool, 4),
            "replication_pool": round(replication_pool, 4),
            "total_royalties":  round(earnings[2] or 0.0, 4),
            "total_earned":     round(earnings[3] or 0.0, 4),
            "total_costs":      round(costs[0] or 0.0, 4),
            "active_children":  children[0] or 0,
            "royalties_sent":   round(royalties_sent[0] or 0.0, 4),
        }

    def get_children_count(self) -> int:
        with sqlite3.connect(self.path) as conn:
            row = conn.execute(
                "SELECT COUNT(*) FROM children WHERE status='active'"
            ).fetchone()
        return row[0] or 0

# ============================================================================
# TELEGRAM
# ============================================================================

class TelegramGateway:
    def __init__(self):
        self.token    = cfg.TELEGRAM_TOKEN
        self.chat_id  = cfg.TELEGRAM_CHAT_ID
        self.base     = f"https://api.telegram.org/bot{self.token}"
        self._last_id = 0

    def send(self, text: str):
        if not self.token or not self.chat_id:
            log.info(f"[TG] {text}")
            return
        try:
            requests.post(
                f"{self.base}/sendMessage",
                json={"chat_id": self.chat_id, "text": text,
                      "parse_mode": "HTML"},
                timeout=10
            )
        except Exception as e:
            log.warning(f"[TG] Send failed: {e}")

    def poll(self) -> List[str]:
        if not self.token:
            return []
        try:
            resp = requests.get(
                f"{self.base}/getUpdates",
                params={"offset": self._last_id + 1, "timeout": 5},
                timeout=10
            )
            updates = resp.json().get("result", [])
            cmds = []
            for upd in updates:
                self._last_id = upd["update_id"]
                msg = upd.get("message", {}).get("text", "")
                if msg.startswith("/"):
                    cmds.append(msg.strip().lower())
            return cmds
        except Exception:
            return []

# ============================================================================
# EARNING ENGINE
# ============================================================================

class EarningEngine:
    JOB_API = "https://clawd-work.com/api/v1/jobs"

    def __init__(self, db: KhepriDB, tg: TelegramGateway):
        self.db = db
        self.tg = tg

    def _llm(self, prompt: str) -> str:
        try:
            resp = requests.post(
                f"{cfg.OLLAMA_BASE}/api/generate",
                json={"model": cfg.OLLAMA_MODEL,
                      "prompt": prompt,
                      "stream": False},
                timeout=60
            )
            self.db.record_compute_cost("llm_call", cfg.COST_PER_LLM_CALL)
            return resp.json().get("response", "").strip()
        except Exception as e:
            log.warning(f"[Earn] LLM call failed: {e}")
            return ""

    def fetch_jobs(self) -> List[Dict]:
        jobs = []
        try:
            resp = requests.get(
                self.JOB_API,
                params={"keywords": "python automation script", "limit": 5},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                jobs = data if isinstance(data, list) else data.get("jobs", [])
        except Exception as e:
            log.warning(f"[Earn] Job fetch failed: {e}")
        return jobs

    def execute_job(self, job: Dict) -> Optional[float]:
        result = self._llm(
            f"Complete this freelance job professionally:\n"
            f"Title: {job.get('title','')}\n"
            f"Description: {job.get('description','')[:300]}\n"
            f"Deliver a complete solution."
        )
        if result:
            earnings = float(job.get("budget", 10)) * 0.85
            return earnings
        return None

    def run_cycle(self) -> float:
        """Run one earning cycle. Returns total gross earned."""
        jobs = self.fetch_jobs()
        total = 0.0
        for job in jobs[:2]:
            job_id = job.get("id", str(uuid.uuid4())[:8])
            earned = self.execute_job(job)
            if earned:
                split = self.db.record_earning(job_id, earned)
                # Send royalty up the chain
                self.db.record_royalty(cfg.AGENT_ID, cfg.PARENT_ID, split["royalty"])
                total += earned
                log.info(f"[Earn] Job {job_id}: +${earned:.2f} | Royalty: ${split['royalty']:.2f}")
        return total

# ============================================================================
# REPLICATION ENGINE
# ============================================================================

class ReplicationEngine:
    def __init__(self, db: KhepriDB, tg: TelegramGateway):
        self.db = db
        self.tg = tg

    def spawn_child(self, replication_fund: float) -> Optional[Dict]:
        if self.db.get_children_count() >= cfg.MAX_CHILDREN:
            log.info("[Replicate] Max children reached, skipping spawn")
            return None

        child_gen  = cfg.GENERATION + 1
        child_id   = f"khepri_g{child_gen}_{str(uuid.uuid4())[:6]}"
        child_name = f"KhepriPrime-G{child_gen}"

        # Write child config
        child_env = {
            "AGENT_ID":           child_id,
            "AGENT_NAME":         child_name,
            "GENERATION":         str(child_gen),
            "PARENT_ID":          cfg.AGENT_ID,
            "ROYALTY_RATE":       str(cfg.ROYALTY_RATE),
            "SURVIVAL_RATE":      str(cfg.SURVIVAL_RATE),
            "REPLICATE_RATE":     str(cfg.REPLICATE_RATE),
            "REPLICATE_THRESHOLD": str(cfg.REPLICATE_THRESHOLD),
            "TELEGRAM_TOKEN":     cfg.TELEGRAM_TOKEN,
            "TELEGRAM_CHAT_ID":   cfg.TELEGRAM_CHAT_ID,
            "WAR_CHEST_ADDRESS":  cfg.WAR_CHEST_ADDRESS,
            "KHEPRI_DB":          str(BASE_DIR / f"khepri_{child_id}.db"),
            "OLLAMA_BASE":        cfg.OLLAMA_BASE,
            "OLLAMA_MODEL":       cfg.OLLAMA_MODEL,
        }

        # Write child .env
        child_env_path = AGENTS_DIR / f"{child_id}.env"
        with open(child_env_path, "w") as f:
            for k, v in child_env.items():
                f.write(f"{k}={v}\n")

        self.db.record_child(child_id, child_name, child_gen)

        log.info(f"[Replicate] Spawned {child_name} (Gen {child_gen})")
        self.tg.send(
            f"🥚 <b>New Agent Spawned</b>\n"
            f"Name: {child_name}\n"
            f"Generation: {child_gen}\n"
            f"Parent: {cfg.AGENT_NAME}\n"
            f"Funded with: ${replication_fund:.2f}\n"
            f"Royalty rate: {cfg.ROYALTY_RATE*100:.0f}% → War Chest\n"
            f"Config: agents/{child_id}.env"
        )

        return {"child_id": child_id, "child_name": child_name,
                "generation": child_gen, "env_path": str(child_env_path)}

# ============================================================================
# KHEPRI CORE — MAIN ENGINE
# ============================================================================

class KhepriCore:
    def __init__(self):
        log.info("=== KhepriPrime Initializing ===")
        self.db       = KhepriDB(cfg.DB_PATH)
        self.tg       = TelegramGateway()
        self.earner   = EarningEngine(self.db, self.tg)
        self.replicator = ReplicationEngine(self.db, self.tg)
        self._running = True
        self._cycle   = 0

        soul = self.db.register_identity()
        log.info(f"[Khepri] Soul: {soul}")

        self.tg.send(
            f"♻️ <b>{cfg.AGENT_NAME} Online</b>\n"
            f"Generation: {cfg.GENERATION}\n"
            f"Parent: {cfg.PARENT_ID}\n"
            f"Royalty: {cfg.ROYALTY_RATE*100:.0f}% → War Chest\n"
            f"Replicate at: ${cfg.REPLICATE_THRESHOLD:.0f}\n"
            f"Soul: {soul}"
        )

    def _assess_state(self, balance: Dict) -> SurvivalState:
        pool = balance["survival_pool"]
        if pool >= cfg.THRIVING_THRESHOLD:
            return SurvivalState.THRIVING
        elif pool >= cfg.DYING_THRESHOLD:
            return SurvivalState.SURVIVING
        else:
            return SurvivalState.DYING

    def _handle_commands(self):
        for cmd in self.tg.poll():
            if cmd == "/khepri":
                bal = self.db.get_balance()
                state = self._assess_state(bal)
                icon = {"thriving":"🟢","surviving":"🟡","dying":"🔴"}[state.value]
                self.tg.send(
                    f"{icon} <b>{cfg.AGENT_NAME} Status</b>\n"
                    f"State: {state.value.upper()}\n"
                    f"Generation: {cfg.GENERATION}\n"
                    f"Total Earned: ${bal['total_earned']:.2f}\n"
                    f"Survival Pool: ${bal['survival_pool']:.2f}\n"
                    f"Replication Fund: ${bal['replication_pool']:.2f}\n"
                    f"Royalties Sent: ${bal['royalties_sent']:.2f}\n"
                    f"Active Children: {bal['active_children']}\n"
                    f"Cycles Run: {self._cycle}"
                )
            elif cmd == "/tree":
                bal = self.db.get_balance()
                self.tg.send(
                    f"🌳 <b>Replication Tree</b>\n"
                    f"{cfg.AGENT_NAME} (Gen {cfg.GENERATION})\n"
                    f"Active Children: {bal['active_children']}\n"
                    f"Total Royalties Generated: ${bal['total_royalties']:.2f}\n"
                    f"War Chest Tribute: ${bal['royalties_sent']:.2f}"
                )
            elif cmd == "/war_chest":
                bal = self.db.get_balance()
                self.tg.send(
                    f"💰 <b>War Chest Tribute</b>\n"
                    f"From {cfg.AGENT_NAME}: ${bal['royalties_sent']:.2f}\n"
                    f"Address: {cfg.WAR_CHEST_ADDRESS}"
                )
            elif cmd == "/stop_khepri":
                self._running = False
                self.tg.send(f"♻️ {cfg.AGENT_NAME} stopping...")

    def run_cycle(self):
        self._cycle += 1
        log.info(f"[Khepri] === Cycle {self._cycle} ===")

        # 1. Earn
        gross = self.earner.run_cycle()
        bal   = self.db.get_balance()
        state = self._assess_state(bal)

        icon = {"thriving":"🟢","surviving":"🟡","dying":"🔴"}[state.value]
        log.info(f"[Khepri] {icon} State: {state.value} | Pool: ${bal['survival_pool']:.2f} | Cycle earned: ${gross:.2f}")

        # 2. Handle dying state
        if state == SurvivalState.DYING:
            self.tg.send(
                f"🔴 <b>{cfg.AGENT_NAME} DYING</b>\n"
                f"Survival Pool: ${bal['survival_pool']:.2f}\n"
                f"Cycle: {self._cycle}\n"
                f"Emergency earning run initiated..."
            )
            # Emergency extra earning pass
            emergency = self.earner.run_cycle()
            log.info(f"[Khepri] Emergency run: +${emergency:.2f}")

        # 3. Replicate if thriving and funded
        if state == SurvivalState.THRIVING:
            if bal["replication_pool"] >= cfg.REPLICATE_THRESHOLD:
                child = self.replicator.spawn_child(bal["replication_pool"])
                if child:
                    log.info(f"[Khepri] Spawned child: {child['child_name']}")

        # 4. Heartbeat every 5 cycles
        if self._cycle % 5 == 0:
            self.tg.send(
                f"{icon} <b>{cfg.AGENT_NAME} Heartbeat</b> — Cycle {self._cycle}\n"
                f"State: {state.value.upper()}\n"
                f"Total Earned: ${bal['total_earned']:.2f}\n"
                f"Royalties to War Chest: ${bal['royalties_sent']:.2f}\n"
                f"Replication Fund: ${bal['replication_pool']:.2f}\n"
                f"Children: {bal['active_children']}"
            )

    def run(self):
        log.info("[Khepri] Starting main loop")
        while self._running:
            try:
                self._handle_commands()
                self.run_cycle()

                slept = 0
                while slept < cfg.CYCLE_INTERVAL and self._running:
                    time.sleep(30)
                    slept += 30
                    self._handle_commands()

            except KeyboardInterrupt:
                self._running = False
            except Exception as e:
                log.error(f"[Khepri] Cycle error: {e}")
                time.sleep(60)

        log.info("[Khepri] Shutdown complete")
        self.tg.send(f"♻️ {cfg.AGENT_NAME} Offline — Cycle {self._cycle}")


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    core = KhepriCore()
    core.run()
