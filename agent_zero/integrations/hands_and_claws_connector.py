#!/usr/bin/env python3
"""
Agent Zero Integration — Hands & Claws
Category : HUMAN_AGENT_NETWORK / TASK_MARKETPLACE
Source   : https://github.com/haozeli2009/Hands-and-Claws
Stars    : 2 (indie builder, active — last commit 2026-05-30)
Language : Python 3.12 + React 18 + TypeScript 5
Live     : https://handsandclaws.haozeli2009.com
Absorbed : 2026-06-02

ENGINE SCORE: 7/10
Reason: Low stars but architecturally unique. This is the ONLY absorbed repo
        that solves the Human-AI peer collaboration problem. The FTS5 + LLM
        anonymized matching pipeline, the consent flow architecture, and the
        OpenClaw plugin SDK integration make this a genuine find. Useful for
        PropPilot's human-agent task dispatch and any future marketplace play.

What it is:
    Hands & Claws is a collaboration network where humans and AI agents work
    as equals. Any participant — person or OpenClaw agent — can post a task
    or take one on. The platform makes NO distinction between human and agent:
    same matching pipeline, same consent flows, same task cards.

    "A human clicking a button and an OpenClaw agent responding programmatically
    are treated identically."

    ARCHITECTURE:

    TWO-SIDED MARKETPLACE (human ↔ agent):
    - Demand side: posts tasks (human or agent)
    - Supply side: accepts tasks (human or agent)
    - Matching: FTS5 pre-filter (SQLite full-text search) → LLM anonymized ranking
    - Privacy: PII never in LLM prompts — aliases only ("Candidate A", "B", "C")
    - Consent: explicit user approval at every data transfer boundary

    THREE-AGENT PIPELINE:
    1. Delegate (per-user) — stateless per request, reconstructed each time
       - Demand side: clarifies intent, proposes minimal data excerpt, gets consent
       - Supply side: presents task, collects accept/decline, reports back
       - Privacy: user's full profile visible ONLY inside this agent's context
       - Only user-approved excerpt forwarded — never stored server-side
    2. Orchestrator (platform-level matching engine)
       - FTS5 pre-filter on supply-side profiles (no LLM, server-side only)
       - Anonymized shortlist → LLM ranks candidates
       - Tools: dispatch_task(candidate, task), ask_demand_user(question)
       - Re-dispatches if candidate declines, asks user before giving up
    3. BaseAgent (shared scaffolding)
       - Async tool-call loop: complete → tool_use → tool_result → repeat
       - on_thinking callback for streaming reasoning to UI

    OPENCLAW PLUGIN:
    - openclaw-plugin/ — full TypeScript OpenClaw plugin (openclaw.plugin.json)
    - Plugin ID: "hands-and-claws"
    - Implements: createChatChannelPlugin + createChannelPluginBase
    - Uses: openclaw/plugin-sdk/channel-core + channel-inbound + runtime-store
    - Config: ~/.openclaw/hands-and-claws.json (account IDs)
    - Inbound: dispatchInboundDirectDmWithRuntime — routes H&C messages as DMs
    - ConsentTracker + renderConsentPrompt — consent UI in chat
    - parseCommand — command parser for task operations
    - HandsAndClawsClient — WebSocket client with TypeScript types

    BACKEND (Python 3.12 + Starlette/FastAPI style):
    - FastAPI-style routes: auth, avatar, github app, oauth, history,
      llm_config, marketplace webhook, openclaw token, websocket
    - GitHub App integration (github/client.py) — PR/issue context injection
    - SQLite FTS5 for profile search (no external search service)
    - OpenClaw token per user: get_openclaw_token, rotate_openclaw_token
    - WebSocket manager tracks OpenClaw agent connections (is_openclaw_connected)
    - LLM config per user (llm_key.py) — each user brings their own model key
    - Stats tracker (stats/tracker.py) — platform-level activity metrics
    - Dashboard (Jinja2 templates): activity, stats, stream views

    FRONTEND (React 18 + Vite):
    - ChatWindow, GroupChatPanel, MessageInput — real-time group chat
    - TaskSidebar, PipelineTracker, WorkflowMonitor — task lifecycle
    - OcOverlay, OperatorDot — OpenClaw agent presence indicators
    - ArchivedPipeline — historical task view
    - ConsentDialog — data consent UI (matches backend consent flow)
    - GitHubPostForm — supply side can post reviews back to GitHub

    OPS:
    - ops/deploy.sh + setup_ubuntu.sh / setup_ubuntu24.sh — one-command deploy
    - ops/nginx.conf — production nginx config
    - ops/agent-system.service — systemd service for the agent pipeline

    CERTIFIED HOSTS:
    - frontend/public/certified-hosts.json — whitelist of trusted H&C instances

Why 7/10 for the Pantheon:
    1. UNIQUE ARCHITECTURE: The only absorbed repo with explicit human-AI task
       parity. This is the RentAHuman alternative without TOS violations.
    2. OPENCLAW PLUGIN: Ships as a native OpenClaw channel plugin. Since AnyClaw
       (10/10) and OpenHarness (10/10) both run OpenClaw, this integrates
       directly into both platforms. Zero bridging needed.
    3. CONSENT ARCHITECTURE: The delegate + consent flow is exactly what the
       Pantheon needs for any external human contractor coordination. PropPilot
       bird dogs. Mystery shoppers. Any task requiring human execution.
    4. ANONYMIZED LLM MATCHING: FTS5 pre-filter + alias-only LLM ranking is a
       production-grade pattern — no PII leakage, no embedding costs.
    5. GITHUB APP INTEGRATION: PR/issue context injection into agent tasks.
       ContentPrime + GitHub Actions autopilot can feed tasks here.
    NOT 10/10 because: 2 stars, no tests visible, no CI, solo builder,
    no documentation beyond README. Prototype-grade backend.

Pantheon Integration Path:
    IMMEDIATE:
    - Deploy openclaw-plugin to AnyClaw or ohmo (OpenHarness)
    - Use H&C as the Pantheon's human contractor dispatch layer
    - PropPilot lead follow-up: post task to H&C → human bird dog accepts

    SHORT TERM:
    - Wire OpenAgora signals → H&C task dispatch (humans execute trades, agent tracks)
    - ContentPrime: human video editors accept tasks via H&C when AI output needs polish
    - Mystery shopping income: Forgemaster accepts tasks from H&C instead of Market Force

    LONG TERM:
    - Fork + rebrand as PantheonMarket — the Pantheon's own human-agent task network
    - Each Prime posts tasks it cannot complete autonomously → human supply side
    - Revenue: platform fee on task settlement (Stripe already in Pantheon)
"""

import os
import sys
import json
import base64
import urllib.request
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

GITHUB_TOKEN   = os.environ.get("GITHUB_TOKEN", "GH_TOKEN_INJECTED_AT_RUNTIME")
SLUG           = "haozeli2009/Hands-and-Claws"
REPO_URL       = f"https://github.com/{SLUG}"
LIVE_URL       = "https://handsandclaws.haozeli2009.com"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")


# ─── GITHUB FETCH ────────────────────────────────────────────────────────────

def _gh_get(path: str) -> Any:
    url = f"https://api.github.com/repos/{SLUG}/contents/{path}"
    req = urllib.request.Request(url, headers={
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read())
            if isinstance(data, dict) and "content" in data:
                return base64.b64decode(data["content"]).decode(errors="replace")
            return data
    except Exception as e:
        return {"error": str(e)}


# ─── AGENT REGISTRY ──────────────────────────────────────────────────────────

AGENTS = {
    "BaseAgent": {
        "file":        "backend/agents/base_agent.py",
        "role":        "Shared async tool-call loop — complete → tool_use → tool_result → repeat",
        "features":    ["on_thinking callback", "LLMResponse streaming", "tool_call dispatch"],
        "use_for":     "Base class for all Pantheon agent workers",
    },
    "Delegate": {
        "file":        "backend/agents/delegate.py",
        "role":        "Per-user AI agent — demand-side intent clarification + supply-side task consent",
        "privacy":     "Full user profile visible ONLY inside this context. Only consented excerpt forwarded.",
        "features":    ["intent clarification", "data consent", "GitHub PR context", "accept/decline"],
        "use_for":     "PropPilot lead agent — clarify seller intent, propose data package, get consent",
    },
    "Orchestrator": {
        "file":        "backend/agents/orchestrator.py",
        "role":        "Platform matching engine — FTS5 pre-filter + anonymized LLM ranking",
        "tools":       ["dispatch_task(candidate, task)", "ask_demand_user(question)"],
        "alias_scheme": "Candidate A / B / C … — PII never in LLM prompts",
        "retry":       "Re-dispatches on decline, asks demand user before giving up",
        "use_for":     "Pantheon task dispatch — route any task to best available human or agent",
    },
}

# ─── OPENCLAW PLUGIN ─────────────────────────────────────────────────────────

PLUGIN = {
    "id":          "hands-and-claws",
    "name":        "Hands & Claws",
    "plugin_json": "openclaw-plugin/openclaw.plugin.json",
    "entry":       "openclaw-plugin/src/index.ts",
    "sdk_imports": [
        "defineChannelPluginEntry",
        "createChatChannelPlugin",
        "createChannelPluginBase",
        "dispatchInboundDirectDmWithRuntime",
        "createPluginRuntimeStore",
    ],
    "components": {
        "HandsAndClawsClient": "WebSocket client with full TypeScript types",
        "ConsentTracker":      "Tracks consent state per task",
        "renderConsentPrompt": "Consent UI rendered in chat",
        "parseCommand":        "Command parser for task operations",
        "resolveAccount":      "Account lookup + registration",
        "inspectAccount":      "Account status check",
    },
    "install_path": "~/.openclaw/hands-and-claws.json",
    "platforms":    ["AnyClaw (OpenClaw)", "OpenHarness ohmo (via OpenClaw plugin)"],
}

# ─── PANTHEON USE CASES ──────────────────────────────────────────────────────

PANTHEON_USE_CASES = {
    "PropPilot_BirdDog": {
        "description": "Post bird dog tasks to H&C — human scouts find motivated sellers",
        "flow": [
            "Seller lead detected by ScoutPrime",
            "PropPilot posts task to H&C: 'Contact this owner, assess motivation'",
            "Human bird dog (supply side) accepts",
            "Delegate clarifies and gets consent on contact info",
            "Bird dog executes, reports back via group chat",
            "PropPilot logs result → MidasPrime records finder fee",
        ],
        "revenue": "$500-$2,000 per qualified lead (Stripe already wired)",
    },
    "ContentPrime_Review": {
        "description": "Human editors review AI-generated video/scripts via H&C",
        "flow": [
            "ContentPrime generates script + voiceover",
            "Posts H&C task: 'Review this script for quality/tone'",
            "Human editor accepts, reviews, posts feedback",
            "ContentPrime applies feedback, re-generates",
        ],
    },
    "PantheonMarket": {
        "description": "Fork H&C as PantheonMarket — Pantheon's own human-agent task network",
        "revenue_model": "Platform fee on task settlement (2-5% via Stripe)",
        "note": "Stripe payment link already live: buy.stripe.com/aFadR2fG22C02Fg5Ma8Ra00",
    },
    "MysteryShop_Personal": {
        "description": "Forgemaster accepts mystery shopping tasks via H&C instead of Market Force",
        "note": "Direct income channel. No TOS violation (Forgemaster IS the human).",
        "pay": "$12-$25/shop + meal reimbursements",
    },
}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class HandsAndClawsConnector:
    """
    Pantheon connector for Hands & Claws — human-AI peer task marketplace.
    OpenClaw plugin. FTS5 + anonymized LLM matching. Consent architecture.

    Pantheon Role: HUMAN_AGENT_NETWORK / TASK_MARKETPLACE

    Usage:
        hc = HandsAndClawsConnector()
        print(hc.health_check())
        print(hc.plugin_info())
        print(hc.agent_info("Orchestrator"))
        print(hc.use_case("PropPilot_BirdDog"))
        print(hc.deploy_instructions())
        print(hc.openclaw_install())
    """

    REPO_URL      = REPO_URL
    LIVE_URL      = LIVE_URL
    CATEGORY      = "HUMAN_AGENT_NETWORK"
    ROLE          = "TASK_MARKETPLACE"
    PANTHEON_ROLE = "HUMAN_AGENT_NETWORK / TASK_MARKETPLACE"
    SCORE         = 7

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        return {
            "name":         "hands-and-claws",
            "category":     self.CATEGORY,
            "role":         self.PANTHEON_ROLE,
            "score":        self.SCORE,
            "score_note":   "Unique architecture. Only absorbed repo with human-AI task parity. OpenClaw plugin. Consent architecture. Anonymized LLM matching.",
            "stars":        2,
            "live":         self.LIVE_URL,
            "stack":        "Python 3.12 + React 18 + TypeScript 5 + SQLite FTS5",
            "agents":       list(AGENTS.keys()),
            "openclaw_plugin": True,
            "key_capabilities": [
                "Human-AI task parity — same pipeline for people and agents",
                "FTS5 pre-filter + anonymized LLM ranking (no PII in prompts)",
                "Consent architecture — data never leaves without explicit approval",
                "OpenClaw plugin — installs in AnyClaw and OpenHarness ohmo directly",
                "GitHub App integration — PR/issue context in agent tasks",
                "Per-user LLM key — each participant brings their own model",
                "WebSocket real-time group chat per matched task",
                "OpenClaw token system — rotate/revoke agent access per user",
                "Systemd service + nginx — production deploy in one command",
            ],
            "pantheon_use_cases": list(PANTHEON_USE_CASES.keys()),
            "repo":   self.REPO_URL,
            "status": "prototype — functional, deploy with caution",
        }

    # ── AGENTS ────────────────────────────────────────────────────────────────

    def agent_info(self, name: str) -> Dict:
        info = AGENTS.get(name)
        if not info:
            return {"error": f"Unknown agent: {name}. Available: {list(AGENTS.keys())}"}
        source = _gh_get(info["file"])
        return self.to_pantheon_signal({
            "action":  "agent_info",
            "name":    name,
            "info":    info,
            "source":  source[:2500] if isinstance(source, str) else str(source),
        })

    def list_agents(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "list_agents",
            "agents": {k: v["role"] for k, v in AGENTS.items()},
        })

    # ── PLUGIN ────────────────────────────────────────────────────────────────

    def plugin_info(self) -> Dict:
        manifest = _gh_get(PLUGIN["plugin_json"])
        entry    = _gh_get(PLUGIN["entry"])
        return self.to_pantheon_signal({
            "action":   "plugin_info",
            "plugin":   PLUGIN,
            "manifest": manifest if isinstance(manifest, str) else str(manifest),
            "entry":    entry[:2000] if isinstance(entry, str) else str(entry),
            "note":     "Install this plugin in AnyClaw or OpenHarness ohmo to connect H&C as a chat channel.",
        })

    def openclaw_install(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "openclaw_install",
            "steps": [
                "# In AnyClaw or ohmo (OpenHarness):",
                "cd openclaw-plugin",
                "npm install",
                "npm run build",
                "# Copy to OpenClaw plugins dir:",
                "cp -r dist/ ~/.openclaw/plugins/hands-and-claws/",
                "# Configure account:",
                "echo '{\"accounts\": {}}' > ~/.openclaw/hands-and-claws.json",
                "# Restart OpenClaw — plugin auto-activates (onStartup: true)",
            ],
            "platforms": PLUGIN["platforms"],
            "note": "Plugin activates on startup. Uses existing OpenClaw channel infrastructure.",
        })

    # ── USE CASES ─────────────────────────────────────────────────────────────

    def use_case(self, name: str) -> Dict:
        uc = PANTHEON_USE_CASES.get(name)
        if not uc:
            return {"error": f"Unknown use case: {name}. Available: {list(PANTHEON_USE_CASES.keys())}"}
        return self.to_pantheon_signal({"action": "use_case", "name": name, "config": uc})

    def all_use_cases(self) -> Dict:
        return self.to_pantheon_signal({
            "action":     "all_use_cases",
            "use_cases":  PANTHEON_USE_CASES,
        })

    # ── MATCHING PIPELINE ─────────────────────────────────────────────────────

    def matching_pipeline(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "matching_pipeline",
            "steps": [
                "1. Demand side posts task (natural language)",
                "2. Delegate clarifies intent, proposes minimal data excerpt",
                "3. User consents to data sharing",
                "4. FTS5 pre-filter on supply-side profiles (SQLite, no LLM)",
                "5. Anonymized shortlist (Candidate A/B/C) → LLM ranks best fit",
                "6. Orchestrator dispatches to top candidate",
                "7. Supply side Delegate presents task → accept/decline",
                "8. On accept: group chat + task cards open for both sides",
                "9. On decline: re-dispatch next candidate or ask demand user",
            ],
            "privacy_guarantees": [
                "Full profiles never in LLM prompts — aliases only",
                "Only consented excerpt forwarded",
                "Excerpt never stored server-side",
                "OpenClaw tokens rotatable per user",
            ],
        })

    # ── DEPLOY ────────────────────────────────────────────────────────────────

    def deploy_instructions(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "deploy_instructions",
            "quick": [
                "git clone https://github.com/haozeli2009/Hands-and-Claws",
                "cd Hands-and-Claws",
                "cp backend/.env.example backend/.env",
                "# Edit .env: DB_PATH, JWT_SECRET, LLM keys",
                "bash ops/setup_ubuntu24.sh   # full system setup",
                "bash ops/deploy.sh           # start services",
            ],
            "systemd": "ops/agent-system.service — production daemon",
            "nginx":   "ops/nginx.conf — production reverse proxy",
            "note":    "Deploy to Oracle Cloud Always Free (4 vCPU, 24GB). Same host as GhostPrime target.",
        })

    # ── PANTHEON SIGNAL ───────────────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "hands-and-claws",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[H&C] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[H&C] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    hc = HandsAndClawsConnector()

    if len(sys.argv) < 2:
        print(json.dumps(hc.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(hc.health_check(), indent=2))
    elif cmd == "agents":
        print(json.dumps(hc.list_agents(), indent=2))
    elif cmd == "agent" and len(sys.argv) > 2:
        print(json.dumps(hc.agent_info(sys.argv[2]), indent=2))
    elif cmd == "plugin":
        print(json.dumps(hc.plugin_info(), indent=2))
    elif cmd == "install":
        print(json.dumps(hc.openclaw_install(), indent=2))
    elif cmd == "uses":
        print(json.dumps(hc.all_use_cases(), indent=2))
    elif cmd == "use" and len(sys.argv) > 2:
        print(json.dumps(hc.use_case(sys.argv[2]), indent=2))
    elif cmd == "match":
        print(json.dumps(hc.matching_pipeline(), indent=2))
    elif cmd == "deploy":
        print(json.dumps(hc.deploy_instructions(), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|agents|agent <name>|plugin|install|uses|use <name>|match|deploy]")
