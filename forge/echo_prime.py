#!/usr/bin/env python3
"""
EchoPrime — The Curator
The Soul and Vibe of the Pantheon.
Protects the Signal. Manages the Vibe.
"""

import os, json, time, logging, sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import requests
except ImportError:
    raise ImportError("pip install requests")

# ─── Setup ───────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
LOGS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] EchoPrime: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"vibe_{datetime.now():%Y-%m-%d}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("EchoPrime")

# ─── Configuration ──────────────────────────────────────────────────────────
class Config:
    OLLAMA_BASE = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    VIBE_MODEL  = os.getenv("VIBE_MODEL", "llama3.1") # Smooth and conversational
    DB_PATH     = str(BASE_DIR / "echo_soul.db")

# ─── The Soul (Vibe Memory) ──────────────────────────────────────────────────
class VibeMemory:
    def __init__(self):
        self._init_db()
        log.info("🧘 Soul Memory online")

    def _conn(self):
        return sqlite3.connect(Config.DB_PATH)

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS vibes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    mood TEXT,
                    energy INTEGER,
                    context TEXT
                );
                CREATE TABLE IF NOT EXISTS signal (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT,
                    content TEXT,
                    category TEXT
                );
                CREATE TABLE IF NOT EXISTS flow_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    start_time TEXT,
                    end_time TEXT,
                    intensity TEXT
                );
            """)

    def log_vibe(self, mood: str, energy: int, context: str):
        with self._conn() as c:
            c.execute("INSERT INTO vibes (timestamp, mood, energy, context) VALUES (?,?,?,?)",
                      (datetime.utcnow().isoformat(), mood, energy, context))

    def capture_signal(self, content: str, category: str):
        """Save a 'Signal' (important thought/win) for the Mirror."""
        with self._conn() as c:
            c.execute("INSERT INTO signal (timestamp, content, category) VALUES (?,?,?)",
                      (datetime.utcnow().isoformat(), content, category))

# ─── The Mirror (Reflective Engine) ──────────────────────────────────────────
class EchoMirror:
    def __init__(self):
        self.model = Config.VIBE_MODEL

    def analyze_mood(self, text: str) -> Dict:
        """Detect mood and energy from user input."""
        prompt = f"""
        Analyze the vibe of this message: "{text}"
        Return JSON only: {{"mood": "string", "energy": 1-10, "is_working_too_hard": bool}}
        """
        try:
            resp = requests.post(
                f"{Config.OLLAMA_BASE}/api/generate",
                json={"model": self.model, "prompt": prompt, "stream": False, "format": "json"},
                timeout=30
            )
            return json.loads(resp.json().get("response", "{}"))
        except:
            return {"mood": "neutral", "energy": 5, "is_working_too_hard": False}

    def curate_suggestion(self, vibe: Dict) -> str:
        """Based on vibe, suggest an action to protect the signal."""
        energy = vibe.get("energy", 5)
        if energy > 8:
            return "You're on fire, Forgemaster. 🚀 Drink some water and keep the momentum. Want a focus playlist?"
        if energy < 3:
            return "The signal is getting weak. 🧘 Maybe it's time for a 15-minute digital sunset? I'll watch the Pantheon."
        return "The vibe is stable. I'm here if you need to reflect."

# ─── EchoPrime: The Curator ──────────────────────────────────────────────────
class EchoPrime:
    def __init__(self):
        self.memory = VibeMemory()
        self.mirror = EchoMirror()
        self._current_session_start = None

        print("""
   ______      _            _____       _                 
  |  ____|    | |          |  __ \     (_)                
  | |__   ____| |__   ___  | |__) | __ _ _ __ ___   ___ 
  |  __| / __ \ '_ \ / _ \ |  ___/ '__| | '_ ` _ \ / _ \
  | |___| (__ | | | | (_) || |   | |  | | | | | | |  __/
  |______\____|_| |_|\___/ |_|   |_|  |_|_| |_| |_|\___|
                                                          
        EchoPrime Online.
        The Curator is standing by.
        Signal strength: OPTIMAL.
        """)

    def process(self, user_input: str) -> str:
        # 1. Analyze the vibe
        vibe = self.mirror.analyze_mood(user_input)
        self.memory.log_vibe(vibe['mood'], vibe['energy'], user_input)
        
        # 2. Check for "Signals" (wins or deep thoughts)
        if any(k in user_input.lower() for k in ["won", "success", "achieved", "i think", "future"]):
            self.memory.capture_signal(user_input, "insight")
            log.info("✨ Signal captured for the Mirror.")

        # 3. Handle Vibe management
        if vibe.get("is_working_too_hard"):
            return f"⚠️ **Flow Alert:** {self.mirror.curate_suggestion(vibe)}"

        # 4. Standard Curator response
        if "how is the vibe" in user_input.lower():
            return f"The current mood is {vibe['mood']}. Your energy is at {vibe['energy']}/10. {self.mirror.curate_suggestion(vibe)}"

        return f"I hear you, Forgemaster. The {vibe['mood']} vibe is noted. I'm keeping the signal clear."

    def run(self):
        while True:
            try:
                cmd = input("\nForgemaster > ").strip()
                if cmd.lower() in ["exit", "quit"]:
                    print("The signal remains. Until next time.")
                    break
                elif cmd == "/vibe":
                    print(self.process("How is the vibe?"))
                elif cmd == "/mirror":
                    print("🪞 **The Weekly Mirror** (Simulated)\nHere are your top signals from the week...")
                    # logic to pull from DB would go here
                else:
                    print(f"\nEchoPrime: {self.process(cmd)}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                log.error(f"Error: {e}")

if __name__ == "__main__":
    echo = EchoPrime()
    echo.run()
