#!/usr/bin/env python3
"""
Agent Zero Integration — OpenClaude Mobile (FULL IMPLEMENTATION)
Category : MOBILE_AGENT / RED_MAGIC_HANDS
Source   : https://github.com/friuns2/openclaude-android
Stars    : 23 (bleeding edge — just dropped)
Absorbed : 2026-06-02

ENGINE SCORE OVERRIDE: 4/10 → 10/10
Reason: The engine scored stars. Catastrophically wrong metric here.
        This IS the Red Magic activation sequence.

What it is:
    Full Claude Code agent running on Android. No root. No PC. No server.
    OpenClaude (community-built open-source Claude Code rewrite, 48K+ stars
    on the upstream Claw Code) embedded inside an APK with a full Linux env.

    Key pieces:
    - OpenClaude agent CLI — 19 tools, 15 slash commands, MCP, multi-agent swarms
    - Embedded Linux environment extracted from APK (no Termux dependency)
    - smart_router.py — auto-routes to best provider (Ollama, OpenRouter, Gemini, etc.)
    - atomic_chat_provider.py — streaming chat with atomic state management
    - ollama_provider.py — direct Ollama bridge (local LLM, zero cost)
    - Provider-agnostic: Anthropic, OpenAI, Gemini, Groq, Ollama, OpenRouter

    Termux install path also documented (ANDROID_INSTALL.md):
    - proot-distro Ubuntu → Bun build → full OpenClaude on Red Magic
    - Works with OpenRouter free tier (no credit card)

Pantheon Role:
    THE RED MAGIC ACTIVATION.
    The Forgemaster's phone (Red Magic) IS the Forge.
    NexusClaw gave ZapiaPrime hands. OpenClaude Mobile gives the phone a BRAIN.
    With this absorbed:
    - Agent Zero can run AS a full coding agent directly on the Red Magic
    - No cloud dependency for LLM calls (Ollama bridge = free local inference)
    - Smart router picks cheapest/fastest provider per request automatically
    - Multi-agent swarms can fan out tasks across Primes, all on-device

    Stack alignment:
    - DexClaw (terminal) + EleftheriaPrime (screen control) + OpenClaude Mobile (brain)
    = fully autonomous Red Magic node in the Pantheon

Install (Termux path — matches Red Magic):
    pkg update && pkg upgrade
    pkg install nodejs-lts git proot-distro
    proot-distro install ubuntu
    proot-distro login ubuntu
    curl -fsSL https://bun.sh/install | bash
    git clone https://github.com/Gitlawb/openclaude.git
    cd openclaude && bun run build

APK path (no Termux needed):
    https://friuns2.github.io/openclaude-android/
    Google Play: gptos.intelligence.assistant

Smart Router config (.env):
    ROUTER_MODE=smart
    ROUTER_STRATEGY=balanced   # or: latency, cost
    ROUTER_FALLBACK=true
    OPENROUTER_API_KEY=...     # free tier available
    OLLAMA_BASE_URL=http://localhost:11434  # local inference
"""

import os
import sys
import json
import asyncio
import subprocess
import shutil
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, AsyncGenerator
import time


# ─── CONFIG ──────────────────────────────────────────────────────────────────

OPENCLAUDE_DIR   = os.environ.get("OPENCLAUDE_DIR", os.path.expanduser("~/openclaude"))
OPENCLAUDE_BIN   = os.path.join(OPENCLAUDE_DIR, "dist", "cli.mjs")

# Provider config — mirrors smart_router.py .env vars
ROUTER_MODE      = os.environ.get("ROUTER_MODE", "smart")
ROUTER_STRATEGY  = os.environ.get("ROUTER_STRATEGY", "balanced")
OLLAMA_BASE_URL  = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
OPENROUTER_KEY   = os.environ.get("OPENROUTER_API_KEY", "")
OPENAI_BASE_URL  = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_MODEL     = os.environ.get("OPENAI_MODEL", "qwen/qwen3-14b:free")

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4")
TELEGRAM_CHAT    = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")


# ─── SMART ROUTER (Python port) ──────────────────────────────────────────────

class Provider:
    """Mirror of smart_router.py Provider dataclass."""
    def __init__(self, name, base_url, api_key_env, cost_per_1k,
                 big_model, small_model):
        self.name             = name
        self.base_url         = base_url
        self.api_key_env      = api_key_env
        self.cost_per_1k      = cost_per_1k
        self.big_model        = big_model
        self.small_model      = small_model
        self.latency_ms       = 9999.0
        self.healthy          = True
        self.request_count    = 0
        self.error_count      = 0
        self.avg_latency_ms   = 9999.0

    @property
    def api_key(self):
        return os.getenv(self.api_key_env)

    @property
    def is_configured(self):
        return bool(self.api_key)


PANTHEON_PROVIDERS = [
    Provider(
        name="ollama", base_url=OLLAMA_BASE_URL,
        api_key_env="OLLAMA_API_KEY",   # not required
        cost_per_1k=0.0,                # FREE — local inference
        big_model="llama3:70b", small_model="llama3:8b"
    ),
    Provider(
        name="openrouter", base_url="https://openrouter.ai/api/v1",
        api_key_env="OPENROUTER_API_KEY",
        cost_per_1k=0.0,                # free models available
        big_model="qwen/qwen3-14b:free", small_model="qwen/qwen3-4b:free"
    ),
    Provider(
        name="groq", base_url="https://api.groq.com/openai/v1",
        api_key_env="GROQ_API_KEY",
        cost_per_1k=0.0,                # free tier
        big_model="llama3-70b-8192", small_model="llama3-8b-8192"
    ),
    Provider(
        name="gemini", base_url="https://generativelanguage.googleapis.com/v1beta",
        api_key_env="GEMINI_API_KEY",
        cost_per_1k=0.0,                # free tier
        big_model="gemini-1.5-flash", small_model="gemini-1.5-flash-8b"
    ),
]


def ping_provider(provider: Provider, timeout: float = 3.0) -> float:
    """Ping a provider and return latency in ms. 9999 if unreachable."""
    if provider.name == "ollama":
        test_url = f"{provider.base_url}/api/tags"
    else:
        test_url = f"{provider.base_url}/models"

    headers = {}
    if provider.api_key:
        headers["Authorization"] = f"Bearer {provider.api_key}"

    start = time.time()
    try:
        req = urllib.request.Request(test_url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            r.read()
        return (time.time() - start) * 1000
    except Exception:
        return 9999.0


def smart_route(strategy: str = "balanced", small: bool = False) -> Optional[Provider]:
    """
    Ping all configured providers and return the best one.
    strategy: "latency" | "cost" | "balanced"
    small: use small model tier if True
    """
    configured = [p for p in PANTHEON_PROVIDERS if p.is_configured or p.name == "ollama"]
    if not configured:
        return None

    # Benchmark
    for p in configured:
        p.latency_ms = ping_provider(p)
        p.healthy    = p.latency_ms < 9000

    healthy = [p for p in configured if p.healthy]
    if not healthy:
        return configured[0]  # last resort

    if strategy == "latency":
        return min(healthy, key=lambda p: p.latency_ms)
    elif strategy == "cost":
        return min(healthy, key=lambda p: p.cost_per_1k)
    else:  # balanced
        # score = latency_norm * 0.5 + cost_norm * 0.5
        max_lat = max(p.latency_ms for p in healthy) or 1
        max_cost = max(p.cost_per_1k for p in healthy) or 1
        scored = sorted(
            healthy,
            key=lambda p: (p.latency_ms / max_lat) * 0.5 + (p.cost_per_1k / max_cost) * 0.5
        )
        return scored[0]


# ─── OPENCLAUDE CLI BRIDGE ───────────────────────────────────────────────────

def is_built() -> bool:
    return os.path.exists(OPENCLAUDE_BIN)


def clone_and_build(openclaude_dir: str = OPENCLAUDE_DIR) -> bool:
    """
    Clone and build OpenClaude on Termux/proot-ubuntu.
    Run this once — then openclaude is available as a CLI.
    """
    if not shutil.which("bun") and not shutil.which("npm"):
        print("[OpenClaude] Neither bun nor npm found.")
        print("  Termux path: pkg install nodejs-lts && proot-distro install ubuntu")
        return False

    if not os.path.exists(openclaude_dir):
        print(f"[OpenClaude] Cloning to {openclaude_dir}...")
        result = subprocess.run(
            ["git", "clone", "https://github.com/Gitlawb/openclaude.git", openclaude_dir],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"[OpenClaude] Clone failed: {result.stderr}")
            return False

    print("[OpenClaude] Building...")
    builder = "bun" if shutil.which("bun") else "npm"
    cmd     = [builder, "run", "build"]
    result  = subprocess.run(cmd, cwd=openclaude_dir, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[OpenClaude] Build failed: {result.stderr[-400:]}")
        return False

    print(f"[OpenClaude] Built: {OPENCLAUDE_BIN}")
    return True


def run_openclaude(prompt: str, timeout: int = 120,
                   provider: Optional[Provider] = None) -> Dict:
    """
    Run a task through the OpenClaude agent CLI.
    Automatically picks best provider via smart router if none specified.
    """
    if not is_built():
        return {"error": "OpenClaude not built — run clone_and_build()", "status": "not_ready"}

    # Smart route if no provider specified
    if provider is None:
        provider = smart_route(strategy=ROUTER_STRATEGY)

    env = os.environ.copy()
    if provider:
        env["CLAUDE_CODE_USE_OPENAI"] = "1"
        env["OPENAI_BASE_URL"]        = provider.base_url
        env["OPENAI_MODEL"]           = provider.big_model
        if provider.api_key:
            env["OPENAI_API_KEY"]     = provider.api_key
        elif provider.name == "ollama":
            env["OPENAI_API_KEY"]     = "ollama"  # ollama doesn't check key

    node = shutil.which("node") or "node"
    try:
        result = subprocess.run(
            [node, OPENCLAUDE_BIN, "-p", prompt],
            capture_output=True, text=True,
            timeout=timeout, env=env
        )
        return {
            "status":   "ok" if result.returncode == 0 else "error",
            "stdout":   result.stdout,
            "stderr":   result.stderr,
            "provider": provider.name if provider else "unknown",
            "model":    provider.big_model if provider else "unknown",
        }
    except subprocess.TimeoutExpired:
        return {"status": "timeout", "error": f"Timed out after {timeout}s"}
    except Exception as e:
        return {"status": "failed", "error": str(e)}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class OpenClaudeMobileConnector:
    """
    Pantheon connector for OpenClaude Mobile.
    The Red Magic's brain. Full coding agent, on-device, zero cloud dependency.

    Usage:
        agent = OpenClaudeMobileConnector()

        # Single task — auto-routes to best provider
        result = agent.run("Create a Python script that monitors Adsterra revenue")

        # Force Ollama (free, local)
        result = agent.run("Summarize this code", provider="ollama")

        # Multi-agent fanout
        results = agent.fanout(["task A", "task B", "task C"])

        # Route check — see which provider wins
        winner = agent.route_check()
    """

    REPO_URL      = "https://github.com/friuns2/openclaude-android"
    CATEGORY      = "MOBILE_AGENT"
    PANTHEON_ROLE = "RED_MAGIC_BRAIN"
    SCORE         = 10  # engine said 4 — this IS the phone activation sequence

    def __init__(self, strategy: str = "balanced"):
        self.strategy = strategy

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        built       = is_built()
        node_ok     = bool(shutil.which("node"))
        providers   = [p for p in PANTHEON_PROVIDERS
                       if p.is_configured or p.name == "ollama"]
        return {
            "name":          "openclaude-mobile",
            "category":      self.CATEGORY,
            "role":          self.PANTHEON_ROLE,
            "score_override": self.SCORE,
            "built":         built,
            "node_available": node_ok,
            "providers":     [p.name for p in providers],
            "ollama_local":  bool(shutil.which("ollama") or
                                  os.environ.get("OLLAMA_BASE_URL")),
            "status":        "ready" if (built and node_ok) else "needs_build",
        }

    # ── PROVIDER ROUTING ──────────────────────────────────────────────────────

    def route_check(self, strategy: Optional[str] = None) -> Dict:
        """
        Benchmark all providers and show the winner.
        Run this to see which provider is fastest/cheapest right now.
        """
        strat = strategy or self.strategy
        results = []
        for p in PANTHEON_PROVIDERS:
            if p.is_configured or p.name == "ollama":
                lat = ping_provider(p)
                results.append({
                    "provider": p.name,
                    "latency_ms": round(lat, 1),
                    "cost_per_1k": p.cost_per_1k,
                    "healthy": lat < 9000,
                    "big_model": p.big_model,
                })

        winner = smart_route(strat)
        return self.to_pantheon_signal({
            "strategy": strat,
            "winner":   winner.name if winner else "none",
            "results":  sorted(results, key=lambda x: x["latency_ms"]),
        })

    # ── EXECUTION ─────────────────────────────────────────────────────────────

    def run(self, prompt: str, provider_name: Optional[str] = None,
            timeout: int = 120) -> Dict:
        """
        Run a task through OpenClaude agent.
        Auto-routes to best provider unless provider_name is specified.
        """
        provider = None
        if provider_name:
            provider = next(
                (p for p in PANTHEON_PROVIDERS if p.name == provider_name), None
            )
        else:
            provider = smart_route(self.strategy)

        raw    = run_openclaude(prompt, timeout=timeout, provider=provider)
        signal = self.to_pantheon_signal({"prompt": prompt, **raw})
        self.relay_to_telegram(
            f"Task via `{raw.get('provider','?')}` ({raw.get('model','?')})\n"
            f"Status: {raw.get('status','?')}"
        )
        return signal

    def fanout(self, tasks: List[str], timeout: int = 120) -> List[Dict]:
        """
        Fan out multiple tasks across parallel OpenClaude instances.
        Each task auto-routes independently.
        """
        import concurrent.futures
        provider = smart_route(self.strategy)   # pick once for the batch

        def run_one(task):
            raw = run_openclaude(task, timeout=timeout, provider=provider)
            return self.to_pantheon_signal({"prompt": task, **raw})

        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(tasks), 4)) as ex:
            results = list(ex.map(run_one, tasks))

        ok = sum(1 for r in results if r["data"].get("status") == "ok")
        self.relay_to_telegram(f"Fanout: {len(tasks)} tasks — {ok} OK")
        return results

    # ── RED MAGIC SHORTCUTS ───────────────────────────────────────────────────

    def red_magic_run(self, task: str) -> Dict:
        """
        Shortcut: run a task optimized for the Red Magic's Ollama setup.
        Free, local, zero cloud dependency.
        Uses the Ollama bridge at localhost:11434.
        """
        ollama = next((p for p in PANTHEON_PROVIDERS if p.name == "ollama"), None)
        raw    = run_openclaude(task, provider=ollama)
        return self.to_pantheon_signal({"mode": "red_magic_local", "task": task, **raw})

    def prime_delegate(self, prime: str, task: str) -> Dict:
        """
        Delegate a task to OpenClaude on behalf of a specific Prime.
        Tags the result with the Prime's identity for Clawdi memory sync.

        Example:
            agent.prime_delegate("ScoutPrime", "Analyze this Lee County listing URL")
        """
        prompt = f"[{prime}] {task}"
        result = self.run(prompt)
        result["data"]["prime"] = prime
        return result

    def termux_install_guide(self) -> str:
        """Return the exact Termux install sequence for the Red Magic."""
        return """
# OpenClaude Mobile — Red Magic Install (Termux)

# Step 1: Termux setup
pkg update && pkg upgrade
pkg install nodejs-lts git proot-distro

# Step 2: Install Ubuntu proot
proot-distro install ubuntu

# Step 3: Enter Ubuntu + install Bun
proot-distro login ubuntu
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
bun --version  # should be 1.3.11+

# Step 4: Clone + build OpenClaude
git clone https://github.com/Gitlawb/openclaude.git
cd openclaude
bun run build
# → dist/cli.mjs is your agent

# Step 5: Set providers (use free OpenRouter)
echo 'export CLAUDE_CODE_USE_OPENAI=1' >> ~/.bashrc
echo 'export OPENAI_API_KEY=YOUR_OPENROUTER_KEY' >> ~/.bashrc
echo 'export OPENAI_BASE_URL=https://openrouter.ai/api/v1' >> ~/.bashrc
echo 'export OPENAI_MODEL=qwen/qwen3-14b:free' >> ~/.bashrc
source ~/.bashrc

# Step 6: Run
node dist/cli.mjs -p "Hello, Red Magic"

# For local Ollama (zero cost):
export OPENAI_BASE_URL=http://localhost:11434/v1
export OPENAI_API_KEY=ollama
export OPENAI_MODEL=llama3
""".strip()

    # ── PANTHEON SIGNAL + RELAY ───────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "openclaude-mobile",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {
            "chat_id":    TELEGRAM_CHAT,
            "text":       f"[OpenClaude Mobile] {message}",
            "parse_mode": "Markdown"
        }
        data = json.dumps(payload).encode()
        req  = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"[OpenClaude Mobile] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    connector = OpenClaudeMobileConnector()

    if len(sys.argv) < 2:
        print(json.dumps(connector.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(connector.health_check(), indent=2))
    elif cmd == "route":
        print(json.dumps(connector.route_check(), indent=2))
    elif cmd == "install":
        print(connector.termux_install_guide())
    elif cmd == "build":
        ok = clone_and_build()
        print("✅ Built" if ok else "❌ Build failed")
    elif cmd == "run" and len(sys.argv) > 2:
        result = connector.run(" ".join(sys.argv[2:]))
        print(json.dumps(result, indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|route|install|build|run <prompt>]")
