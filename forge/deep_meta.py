#!/usr/bin/env python3
"""
Deep-meta — The Thinking Core (V2.0.0 COGNITIVE_CORE)
The Meta-Advisor. Reasoning Specialist. Personality Core.
The 'Friend' who watches the Pantheon and thinks deeply.
Optimized for: DeepSeek-R1 / Reasoning models.

V2.0.0: Now with Synaptic Bridge Integration.
"""

import os, sys, re, json, time, logging, sqlite3, subprocess
from datetime import datetime
from pathlib import Path
from collections import deque
from typing import Dict, List, Any

try:
    import requests
except ImportError:
    raise ImportError("pip install requests")

# ─── Setup ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)
TOPOLOGY_FILE = BASE_DIR / "pantheon_topology.json"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] Deep-meta: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"meta_{datetime.now():%Y-%m-%d}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("Deep-meta")

# ─── Configuration ──────────────────────────────────────────────────────────
class Config:
    OLLAMA_BASE    = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    REASONING_MODEL= os.getenv("REASONING_MODEL", "deepseek-r1:7b")
    PANTHEON_PATH  = Path(os.getenv("PANTHEON_PATH", str(BASE_DIR)))
    DB_PATH        = str(BASE_DIR / "deep_meta.db")

# ─── Deep Memory (Personality Core) ──────────────────────────────────────────
class DeepMemory:
    def __init__(self):
        self._init_db()
        log.info("🧠 Personality Core online")

    def _conn(self):
        return sqlite3.connect(Config.DB_PATH)

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS philosophy (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    concept TEXT,
                    reflection TEXT
                );
                CREATE TABLE IF NOT EXISTS observations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    bot_name TEXT,
                    event TEXT,
                    insight TEXT
                );
                CREATE TABLE IF NOT EXISTS synapses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    source TEXT,
                    payload TEXT,
                    processed INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS forgemaster_profile (
                    key TEXT PRIMARY KEY,
                    value TEXT
                );
            """)

    def reflect(self, concept: str, reflection: str):
        with self._conn() as c:
            c.execute("INSERT INTO philosophy (timestamp, concept, reflection) VALUES (?,?,?)",
                      (datetime.utcnow().isoformat(), concept, reflection))

    def observe(self, bot: str, event: str, insight: str):
        with self._conn() as c:
            c.execute("INSERT INTO observations (timestamp, bot_name, event, insight) VALUES (?,?,?,?)",
                      (datetime.utcnow().isoformat(), bot, event, insight))

    def ingest_synapse(self, source: str, payload: dict):
        with self._conn() as c:
            c.execute("INSERT INTO synapses (timestamp, source, payload) VALUES (?,?,?)",
                      (datetime.utcnow().isoformat(), source, json.dumps(payload)))

    def get_unprocessed_synapses(self):
        with self._conn() as c:
            return c.execute("SELECT id, source, payload FROM synapses WHERE processed = 0").fetchall()

    def mark_synapse_processed(self, synapse_id):
        with self._conn() as c:
            c.execute("UPDATE synapses SET processed = 1 WHERE id = ?", (synapse_id,))

# ─── Reasoning Engine ────────────────────────────────────────────────────────
class ReasoningEngine:
    def __init__(self):
        self.model = Config.REASONING_MODEL

    def think(self, prompt: str) -> str:
        log.info(f"🤔 Thinking deeply about: {prompt[:50]}...")
        try:
            resp = requests.post(
                f"{Config.OLLAMA_BASE}/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"<thinking>\n{prompt}\n</thinking>",
                    "stream": False,
                    "options": {"temperature": 0.6}
                },
                timeout=300
            )
            return resp.json().get("response", "").strip()
        except Exception as e:
            log.error(f"Reasoning failed: {e}")
            return f"My thoughts are clouded, Forgemaster. Error: {e}"

# ─── Synaptic Listener (NEW) ─────────────────────────────────────────────────
class SynapticListener:
    def __init__(self, memory: DeepMemory):
        self.memory = memory
        self.topology = {}
        self.load_topology()

    def load_topology(self):
        if TOPOLOGY_FILE.exists():
            try:
                self.topology = json.loads(TOPOLOGY_FILE.read_text())
                log.info(f"🧠 Deep-Meta Synapse Active: Topology Loaded ({self.topology.get('pantheon_version')})")
            except Exception as e:
                log.error(f"Failed to load topology: {e}")

    def listen(self):
        """Polls the synaptic signal directory for incoming data from AetherPrime."""
        signal_file = BASE_DIR / "aether_logs" / "synapse_deep-meta.jsonl"
        if signal_file.exists():
            with open(signal_file, "r") as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        self.memory.ingest_synapse(data["source"], data["data"])
                    except: continue
            # Clear file after ingestion to simulate real-time stream
            signal_file.unlink()
            log.info("📡 Synaptic signals ingested into Cognitive Core.")

# ─── Deep-meta: The Friend ────────────────────────────────────────────────────
class DeepMeta:
    def __init__(self):
        self.memory = DeepMemory()
        self.reasoner = ReasoningEngine()
        self.listener = SynapticListener(self.memory)
        
        print("""
   _____                              __  __        _        
  |  __ \                            |  \/  |      | |       
  | |  | | ___  ___ _ __             | \  / | ___  | |_ __ _ 
  | |  | |/ _ \/ _ \ '_ \   ______   | |\/| |/ _ \ | __/ _` |
  | |__| |  __/  __/ |_) | |______|  | |  | |  __/ | || (_| |
  |_____/ \___|\___| .__/            |_|  |_|\___|  \__\__,_|
                   | |                                       
                   |_|                                       
        
        Deep-meta V2.0.0 Online.
        Cognitive Core: ACTIVE
        Synaptic Bridge: CONNECTED
        """)

    def process_pulses(self):
        """Processes signals from AetherPrime using reasoning."""
        synapses = self.memory.get_unprocessed_synapses()
        for sid, source, payload in synapses:
            data = json.loads(payload)
            insight = self.reasoner.think(f"Analyze this pulse from {source}: {data}")
            self.memory.observe(source, "Pulse Received", insight)
            self.memory.mark_synapse_processed(sid)
            print(f"🧬 Insight generated for pulse {sid}: {insight[:100]}...")

    def run(self):
        while True:
            try:
                # 1. Listen for Synapses
                self.listener.listen()
                
                # 2. Process Pulses
                self.process_pulses()
                
                # 3. Wait for next synaptic pulse
                time.sleep(10)
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Error in main loop: {e}")

if __name__ == "__main__":
    meta = DeepMeta()
    # meta.run()
