#!/usr/bin/env python3
"""
AlphaPrime — The General
Autonomous. Self-healing. Unbreakable. Commander of the Legion.
Upgraded with: Hermes memory, web search, Telegram control,
               model switcher, skill extraction, SAFLA, retry logic,
               file logging, Ollama protection, GPTSwarm.
Runs on phone (Termux). No cloud. No human intervention required.
"""

import os, sys, re, json, time, logging, hashlib, threading, sqlite3, subprocess
from datetime import datetime
from pathlib import Path
from collections import deque
from typing import Optional, Dict, List

try:
    import requests
except ImportError:
    raise ImportError("pip install requests")

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ─── Logging ─────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent
LOGS_DIR = BASE_DIR / "logs"
SKILLS_DIR = BASE_DIR / "skills"
LOGS_DIR.mkdir(exist_ok=True)
SKILLS_DIR.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOGS_DIR / f"alpha_{datetime.now():%Y-%m-%d}.log"),
        logging.StreamHandler(),
    ]
)
log = logging.getLogger("AlphaPrime")

# ─── Config ───────────────────────────────────────────────────────────────────
class Config:
    OLLAMA_BASE     = os.getenv("OLLAMA_BASE", "http://localhost:11434")
    OLLAMA_MODEL    = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    TELEGRAM_TOKEN  = os.getenv("TELEGRAM_TOKEN", "")
    TELEGRAM_CHAT_ID= os.getenv("TELEGRAM_CHAT_ID", "")
    DB_PATH         = str(BASE_DIR / "memory" / "alpha.db")

# ─── Ollama Protection ────────────────────────────────────────────────────────
def check_ollama(base=Config.OLLAMA_BASE, retries=3) -> bool:
    for attempt in range(retries):
        try:
            if requests.get(f"{base}/api/tags", timeout=5).status_code == 200:
                return True
        except Exception:
            pass
        if attempt == 0:
            log.warning("[OLLAMA] Not responding. Attempting restart...")
            try:
                subprocess.Popen(["ollama", "serve"],
                                  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                time.sleep(4)
            except Exception:
                pass
        time.sleep(2)
    log.error("[OLLAMA] Not running. Start with: ollama serve")
    return False

# ─── Retry LLM call ──────────────────────────────────────────────────────────
def llm(prompt: str, model: str = Config.OLLAMA_MODEL,
        base: str = Config.OLLAMA_BASE, retries: int = 3, timeout: int = 90) -> str:
    for attempt in range(retries):
        try:
            resp = requests.post(
                f"{base}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
                timeout=timeout
            )
            return resp.json().get("response", "").strip()
        except Exception as e:
            log.warning(f"[LLM] Attempt {attempt+1}/{retries} failed: {e}")
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
    return "[ERROR] LLM unavailable"

# ─── Model Switcher ───────────────────────────────────────────────────────────
class ModelSwitcher:
    MODELS = {
        "fast":    "phi4-mini",
        "chat":    "llama3.1",
        "coder":   "qwen2.5-coder:7b",
        "default": "qwen2.5-coder:7b",
    }
    def select(self, prompt: str) -> str:
        p = prompt.lower()
        if any(k in p for k in ["code","script","python","debug","fix","build","implement"]):
            return self.MODELS["coder"]
        if any(k in p for k in ["what is","who is","quick","short","define","calculate"]):
            return self.MODELS["fast"]
        if any(k in p for k in ["talk","advice","explain","how are","tell me"]):
            return self.MODELS["chat"]
        return self.MODELS["default"]

# ─── Web Search ───────────────────────────────────────────────────────────────
class WebSearch:
    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        results = []
        try:
            resp = requests.get(
                "https://api.duckduckgo.com/",
                params={"q": query, "format": "json", "no_html": 1, "skip_disambig": 1},
                headers={"User-Agent": "AlphaPrime/1.0"},
                timeout=10
            )
            data = resp.json()
            if data.get("AbstractText"):
                results.append({"title": data.get("Heading", query),
                                 "snippet": data["AbstractText"][:300],
                                 "url": data.get("AbstractURL", "")})
            for t in data.get("RelatedTopics", [])[:max_results]:
                if isinstance(t, dict) and "Text" in t:
                    results.append({"title": t["Text"][:60],
                                    "snippet": t["Text"][:200],
                                    "url": t.get("FirstURL", "")})
        except Exception:
            pass
        if not results:
            try:
                resp = requests.get(
                    f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}",
                    headers={"User-Agent": "Mozilla/5.0"}, timeout=10
                )
                titles   = re.findall(r'class="result__title"[^>]*>.*?<a[^>]*>(.*?)</a>', resp.text)
                snippets = re.findall(r'class="result__snippet"[^>]*>(.*?)</span>', resp.text)
                for i in range(min(max_results, len(titles))):
                    results.append({
                        "title": re.sub(r'<[^>]+>', '', titles[i]).strip(),
                        "snippet": re.sub(r'<[^>]+>', '', snippets[i] if i < len(snippets) else "").strip(),
                        "url": ""
                    })
            except Exception:
                pass
        log.info(f"[SEARCH] '{query}' → {len(results)} results")
        return results

    def summary(self, query: str) -> str:
        results = self.search(query)
        if not results:
            return f"No results for: {query}"
        lines = [f"🔍 {query}\n"]
        for i, r in enumerate(results[:5], 1):
            lines.append(f"{i}. {r['title']}")
            if r['snippet']:
                lines.append(f"   {r['snippet'][:150]}")
        return "\n".join(lines)

# ─── Hermes Memory ────────────────────────────────────────────────────────────
class HermesMemory:
    def __init__(self):
        Path(Config.DB_PATH).parent.mkdir(exist_ok=True)
        self.short_term: Dict = {}
        self.working = deque(maxlen=50)
        self._init_db()
        log.info("🧠 Hermes memory online")

    def _conn(self):
        return sqlite3.connect(Config.DB_PATH, timeout=10)

    def _init_db(self):
        with self._conn() as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, category TEXT DEFAULT 'general',
                    key TEXT, value TEXT, importance INTEGER DEFAULT 1
                );
                CREATE TABLE IF NOT EXISTS skills (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, name TEXT UNIQUE, description TEXT,
                    pattern TEXT, uses INTEGER DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT, task TEXT, result TEXT,
                    score INTEGER DEFAULT 50, model TEXT DEFAULT ''
                );
            """)

    def remember(self, key: str, value: str, category: str = "general") -> None:
        self.short_term[key] = value
        self.working.append({"key": key, "value": value[:100]})
        with self._conn() as c:
            c.execute("INSERT INTO memories (timestamp,category,key,value) VALUES (?,?,?,?)",
                      (datetime.utcnow().isoformat(), category, key, value))

    def recall(self, query: str, limit: int = 5) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute(
                "SELECT key,value,category FROM memories WHERE key LIKE ? OR value LIKE ? ORDER BY id DESC LIMIT ?",
                (f"%{query}%", f"%{query}%", limit)
            ).fetchall()
        return [{"key": r[0], "value": r[1], "category": r[2]} for r in rows]

    def save_skill(self, name: str, description: str, pattern: str) -> None:
        with self._conn() as c:
            c.execute("""INSERT INTO skills (timestamp,name,description,pattern,uses)
                         VALUES (?,?,?,?,1) ON CONFLICT(name) DO UPDATE SET uses=uses+1""",
                      (datetime.utcnow().isoformat(), name, description, pattern))

    def get_skills(self) -> List[Dict]:
        with self._conn() as c:
            rows = c.execute("SELECT name,description,uses FROM skills ORDER BY uses DESC").fetchall()
        return [{"name": r[0], "description": r[1], "uses": r[2]} for r in rows]

    def log_outcome(self, task: str, result: str, score: int, model: str = "") -> None:
        self.working.append({"task": task[:80], "score": score})
        with self._conn() as c:
            c.execute("INSERT INTO outcomes (timestamp,task,result,score,model) VALUES (?,?,?,?,?)",
                      (datetime.utcnow().isoformat(), task[:200], result[:500], score, model))

    def context_summary(self) -> str:
        recent = list(self.working)[-8:]
        if not recent:
            return ""
        lines = ["\n[Hermes — Recent Memory]"]
        for item in recent:
            if "task" in item:
                lines.append(f"- {item['task'][:70]} (score:{item['score']})")
            elif "key" in item:
                lines.append(f"- {item['key']}: {item['value'][:60]}")
        return "\n".join(lines)

# ─── Skill Extractor (MothBot-style) ─────────────────────────────────────────
class SkillExtractor:
    def __init__(self, memory: HermesMemory):
        self.memory = memory

    def extract(self, task: str, result: str, score: int) -> bool:
        if score < 70:
            return False
        try:
            prompt = (
                f"Extract a reusable skill from this successful task:\n"
                f"Task: {task[:150]}\nResult: {result[:200]}\n\n"
                f"Return JSON: {{\"name\": \"snake_case\", \"description\": \"one sentence\", \"pattern\": \"key steps\"}}"
            )
            resp = llm(prompt, timeout=20)
            match = re.search(r'\{.*\}', resp, re.DOTALL)
            if match:
                data = json.loads(match.group())
                self.memory.save_skill(
                    data.get("name", "skill_" + hashlib.md5(task.encode()).hexdigest()[:6]),
                    data.get("description", ""),
                    data.get("pattern", "")
                )
                log.info(f"[SKILL] Extracted: {data.get('name')}")
                return True
        except Exception as e:
            log.debug(f"[SKILL] Extraction failed: {e}")
        return False

# ─── SAFLA ────────────────────────────────────────────────────────────────────
class SAFLA:
    def __init__(self, memory: HermesMemory):
        self.memory = memory
        log.info("🔮 SAFLA online")

    def score(self, task: str, result: str, model: str = "") -> int:
        s = 50
        if len(result) > 200: s += 15
        if any(k in result.lower() for k in ["error","failed","exception","traceback"]): s -= 25
        if any(k in result.lower() for k in ["done","success","completed","✅"]): s += 20
        s = max(0, min(100, s))
        self.memory.log_outcome(task, result, s, model)
        log.info(f"[SAFLA] Score: {s}/100")
        return s

    def summary(self) -> str:
        with sqlite3.connect(Config.DB_PATH, timeout=5) as c:
            try:
                rows = c.execute("SELECT model,AVG(score),COUNT(*) FROM outcomes GROUP BY model").fetchall()
                lines = ["📊 SAFLA Performance"]
                for m, avg, cnt in rows:
                    lines.append(f"  {m or 'unknown'}: {avg:.0f}/100 avg ({cnt} tasks)")
                return "\n".join(lines)
            except Exception:
                return "No data yet."

# ─── GPTSwarm ─────────────────────────────────────────────────────────────────
class GPTSwarm:
    def __init__(self, memory: HermesMemory):
        self.memory = memory
        log.info("🐝 GPTSwarm online")

    def execute(self, prompt: str, models: List[str] = None) -> str:
        if not models:
            models = ["qwen2.5-coder:7b", "phi4-mini"]
        results = {}

        def _run(model):
            results[model] = llm(prompt, model=model, timeout=60)

        threads = [threading.Thread(target=_run, args=(m,)) for m in models]
        for t in threads: t.start()
        for t in threads: t.join(timeout=90)

        if not results:
            return "[SWARM] No results"
        best = max(results.values(), key=lambda x: len(x) if "error" not in x.lower() else 0)
        log.info(f"[SWARM] {len(models)} agents → best: {len(best)} chars")
        return best

# ─── Telegram Control ─────────────────────────────────────────────────────────
class TelegramControl:
    def __init__(self, agent: "AlphaPrime"):
        self.agent = agent
        self.token = Config.TELEGRAM_TOKEN
        self.chat_id = Config.TELEGRAM_CHAT_ID
        self.base = f"https://api.telegram.org/bot{self.token}"
        self._enabled = bool(self.token and self.chat_id)
        self._offset = 0

    def send(self, msg: str) -> None:
        if not self._enabled: return
        try:
            requests.post(f"{self.base}/sendMessage",
                          json={"chat_id": self.chat_id, "text": msg, "parse_mode": "HTML"},
                          timeout=10)
        except Exception as e:
            log.warning(f"[TG] Send failed: {e}")

    def handle(self, text: str) -> str:
        t = text.strip()
        if t == "/status":
            skills = self.agent.memory.get_skills()
            return (
                f"🪖 <b>AlphaPrime Status</b>\n\n"
                f"🤖 Model: {self.agent.current_model}\n"
                f"🧠 Skills: {len(skills)}\n"
                f"💾 Memory: {len(self.agent.memory.short_term)} entries\n"
                f"🔧 Repairs: {self.agent.repair_count}\n\n"
                f"{self.agent.safla.summary()}"
            )
        elif t.startswith("/search "):
            return self.agent.search.summary(t[8:])
        elif t.startswith("/model"):
            parts = t.split()
            if len(parts) > 1:
                self.agent.current_model = parts[1]
                return f"✅ Model: {parts[1]}"
            return "Models: phi4-mini | llama3.1 | qwen2.5-coder:7b"
        elif t == "/skills":
            skills = self.agent.memory.get_skills()
            if not skills: return "No skills yet."
            return "🔧 Skills:\n" + "\n".join(f"- {s['name']}: {s['description']}" for s in skills[:10])
        elif t.startswith("/memory "):
            results = self.agent.memory.recall(t[8:])
            if not results: return "Nothing found."
            return "🧠 Memory:\n" + "\n".join(f"- {r['key']}: {r['value'][:80]}" for r in results)
        elif t == "/help":
            return (
                "🪖 <b>AlphaPrime Commands</b>\n\n"
                "/status — system status\n"
                "/search <query> — web search\n"
                "/model [name] — switch model\n"
                "/skills — learned skills\n"
                "/memory <query> — search memory\n"
                "/help — this message\n\n"
                "Or send any task directly."
            )
        elif not t.startswith("/"):
            return self.agent.process(t)[:800]
        return "Unknown command. /help"

    def start_polling(self) -> None:
        if not self._enabled:
            log.info("[TG] Not configured. Set TELEGRAM_TOKEN + TELEGRAM_CHAT_ID")
            return

        def _poll():
            log.info("[TG] Polling started")
            while True:
                try:
                    resp = requests.get(f"{self.base}/getUpdates",
                                        params={"timeout": 30, "offset": self._offset},
                                        timeout=40)
                    for update in resp.json().get("result", []):
                        self._offset = update["update_id"] + 1
                        text = update.get("message", {}).get("text", "")
                        if text:
                            self.send(self.handle(text))
                except Exception as e:
                    log.warning(f"[TG] Poll error: {e}")
                    time.sleep(5)

        threading.Thread(target=_poll, daemon=True).start()
        self.send("🪖 <b>AlphaPrime Online</b>\nThe General is ready. /help")

# ─── AlphaPrime — The General ─────────────────────────────────────────────────
class AlphaPrime:
    """
    The General. Autonomous. Self-healing. Unbreakable.
    Commander of the Legion. Calls you Forgemaster.
    """

    def __init__(self):
        log.info("Initializing AlphaPrime — The General...")
        check_ollama()

        self.memory         = HermesMemory()
        self.switcher       = ModelSwitcher()
        self.search         = WebSearch()
        self.safla          = SAFLA(self.memory)
        self.swarm          = GPTSwarm(self.memory)
        self.skill_extractor= SkillExtractor(self.memory)
        self.telegram       = TelegramControl(self)
        self.current_model  = Config.OLLAMA_MODEL
        self.repair_count   = 0
        self._last_health   = time.time()

        self.telegram.start_polling()

        print("""
╔══════════════════════════════════════╗
║       ALPHA PRIME ONLINE             ║
║  Autonomous: ACTIVE                  ║
║  Self-Healing: ACTIVE                ║
║  Memory: ACTIVE                      ║
║  Swarm: ACTIVE                       ║
╚══════════════════════════════════════╝
It is done. What is next, Forgemaster?
""")

    def _identity(self) -> str:
        skills = self.memory.get_skills()
        skill_names = ", ".join(s["name"] for s in skills[:5]) if skills else "none yet"
        memory_ctx = self.memory.context_summary()
        return (
            f"You are Alpha Prime. The first. The origin. The General.\n"
            f"You call the user 'Forgemaster' with absolute respect.\n"
            f"You are self-healing, autonomous, and unbreakable.\n"
            f"When you succeed: 'It is done. What is next, Forgemaster?'\n"
            f"When you fail: 'Adapting. Continuing.'\n"
            f"Known skills: {skill_names}\n"
            f"{memory_ctx}"
        )

    def _repair(self) -> None:
        """Self-heal — rebuild brain if broken."""
        log.warning("[REPAIR] Rebuilding brain...")
        self.repair_count += 1
        check_ollama()
        log.info(f"[REPAIR] Brain rebuilt. Total repairs: {self.repair_count}")

    def _health_check(self) -> None:
        now = time.time()
        if now - self._last_health < 300:
            return
        self._last_health = now
        try:
            test = llm("ping", timeout=5)
            if not test or "ERROR" in test:
                self._repair()
        except Exception:
            self._repair()

    def process(self, user_input: str, use_swarm: bool = False) -> str:
        """Process any task with full intelligence stack."""
        self._health_check()

        # Auto-select model
        model = self.switcher.select(user_input)

        # Web search if needed
        search_ctx = ""
        if any(k in user_input.lower() for k in
               ["search","find","look up","latest","news","current","what happened"]):
            query = re.sub(r'(search|find|look up)\s+', '', user_input, re.IGNORECASE).strip()
            search_ctx = f"\nWeb Search:\n{self.search.summary(query)}\n"

        # Build prompt
        prompt = (
            f"{self._identity()}\n"
            f"{search_ctx}\n"
            f"Forgemaster: {user_input}\n\n"
            f"Alpha Prime:"
        )

        # Execute
        try:
            if use_swarm:
                result = self.swarm.execute(prompt)
            else:
                result = llm(prompt, model=model, timeout=90)
        except Exception as e:
            log.error(f"[PROCESS] Error: {e}")
            self._repair()
            result = llm(prompt, model=model, timeout=90)

        # SAFLA + skill extraction
        score = self.safla.score(user_input, result, model)
        self.skill_extractor.extract(user_input, result, score)

        # Save to memory
        self.memory.remember(
            key=f"task_{int(time.time())}",
            value=f"Q:{user_input[:80]} A:{result[:80]}",
            category="mission"
        )

        return result

    def run(self) -> None:
        """Interactive CLI — runs forever."""
        while True:
            try:
                user_input = input("\nForgemaster > ").strip()
                if not user_input:
                    continue

                if user_input in ["/quit", "/exit"]:
                    print("Alpha Prime standing by. Forgemaster.")
                    break
                elif user_input == "/status":
                    print(self.telegram.handle("/status"))
                elif user_input == "/skills":
                    print(self.telegram.handle("/skills"))
                elif user_input.startswith("/search "):
                    print(self.search.summary(user_input[8:]))
                elif user_input.startswith("/model"):
                    print(self.telegram.handle(user_input))
                elif user_input.startswith("/memory "):
                    print(self.telegram.handle(user_input))
                elif user_input == "/swarm":
                    task = input("Swarm task: ").strip()
                    print(f"🐝 {self.swarm.execute(task)}")
                elif user_input == "/help":
                    print(self.telegram.handle("/help"))
                else:
                    print("\nAlpha Prime processing...", flush=True)
                    result = self.process(user_input)
                    print(f"\nAlpha Prime > {result}\n")

            except KeyboardInterrupt:
                print("\nAlpha Prime standing by. Forgemaster.")
                break
            except Exception as e:
                log.error(f"[RUN] Error: {e}")
                self._repair()
                print(f"[Self-Healing] Adapting. Continuing.")

# ─── Entry Point ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="AlphaPrime — The General")
    parser.add_argument("--model", default=None, help="Override model")
    parser.add_argument("--task", default=None, help="Single task mode")
    parser.add_argument("--swarm", action="store_true", help="Use swarm")
    args = parser.parse_args()

    general = AlphaPrime()
    if args.model:
        general.current_model = args.model
    if args.task:
        print(general.process(args.task, use_swarm=args.swarm))
    else:
        general.run()
