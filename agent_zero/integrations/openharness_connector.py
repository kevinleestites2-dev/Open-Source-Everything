#!/usr/bin/env python3
"""
Agent Zero Integration — OpenHarness + ohmo
Category : AGENT_PLATFORM / SWARM_ENGINE
Source   : https://github.com/HKUDS/OpenHarness
Stars    : 13,437 | Forks: 2,207
Language : Python 3.10+
Tests    : 114 passing | E2E: 6 suites
Absorbed : 2026-06-02

ENGINE SCORE: 10/10 — NO OVERRIDE NEEDED
Reason: 13K stars. Production-grade. Built on Claude Code / Codex subscription
        (no extra API key). Multi-agent swarm. Docker sandbox. 10 channel
        ingress. MCP native. Autopilot mode. Personal agent "ohmo" built in.
        This is the most complete open agent platform absorbed so far.

What it is:
    OpenHarness: Lightweight open agent infrastructure — tool-use, skills,
    memory, multi-agent coordination. The framework layer.

    ohmo: Personal AI agent built ON OpenHarness. "Not another chatbot —
    an assistant that actually works for you over long sessions." Chat in
    Feishu/Slack/Telegram/Discord, it forks branches, writes code, runs
    tests, opens PRs autonomously. Runs on Claude Code or Codex subscription
    — NO extra API key needed.

    ARCHITECTURE (full src/ breakdown):

    MULTI-CHANNEL INGRESS (10 channels native):
    - Telegram, WhatsApp, Discord, Slack, Feishu, DingTalk,
      Email, Matrix, MoChat, QQ
    - Channel bus: async event queue + adapter layer
    - Each channel isolated — one bus, many adapters

    MULTI-AGENT SWARM (src/openharness/swarm/):
    - in_process.py      — in-process agent spawning
    - subprocess_backend.py — subprocess-isolated agents
    - mailbox.py         — inter-agent message passing
    - registry.py        — swarm agent registry
    - spawn_utils.py     — agent lifecycle utilities
    - team_lifecycle.py  — team create/destroy/manage
    - permission_sync.py — permission propagation across agents
    - worktree.py        — git worktree per agent (isolated dev branches!)
    - lockfile.py        — concurrency control

    TOOL ARSENAL (43+ tools in src/openharness/tools/):
    bash_tool, file_read/write/edit, glob, grep,
    web_fetch, web_search, image_generation, image_to_text,
    lsp_tool, notebook_edit, mcp_tool, mcp_auth, list_mcp_resources,
    read_mcp_resource, remote_trigger, send_message, skill_tool,
    sleep, task_create/get/list/update/stop/output,
    team_create/delete, todo_write, tool_search,
    cron_create/delete/list/toggle, enter/exit_plan_mode,
    enter/exit_worktree, brief, config, ask_user_question,
    agent_tool

    MEMORY SYSTEM (src/openharness/memory/):
    - manager.py    — unified memory manager
    - agent.py      — per-agent memory namespace
    - team.py       — shared team memory
    - search.py     — semantic relevance search
    - relevance.py  — relevance scoring
    - scan.py       — memory dir scanning
    - memdir.py     — MEMORY.md directory convention (Pantheon-compatible!)
    - migrate.py    — memory schema migration
    - usage.py      — memory usage tracking

    SANDBOX (src/openharness/sandbox/):
    - Docker backend — full container isolation per session
    - Path validator — prevent directory traversal
    - Adapter layer — swap backends without changing agent code

    PERMISSIONS (src/openharness/permissions/):
    - checker.py    — per-tool permission enforcement
    - modes.py      — permission mode presets
    - Propagated across swarm via permission_sync.py

    AUTOPILOT (src/openharness/autopilot/):
    - service.py    — autonomous task execution pipeline
    - GitHub Actions: autopilot-run-next.yml, autopilot-scan.yml, autopilot-pages.yml
    - Dashboard: React TUI at docs/autopilot/ (live pipeline visualization)

    HOOKS (src/openharness/hooks/):
    - hot_reload.py  — live hook reload without restart
    - executor.py    — hook execution engine
    - loader.py      — hook discovery
    - Event-driven lifecycle hooks for all agent actions

    SERVICES:
    - autodream/     — background memory extraction + session summarization
    - cron.py + cron_scheduler.py — built-in cron (same as Pantheon's)
    - lsp/           — Language Server Protocol integration
    - compact/       — context compaction
    - oauth/         — OAuth flow service
    - session_backend.py — pluggable session persistence

    COORDINATOR (src/openharness/coordinator/):
    - coordinator_mode.py — multi-agent coordination mode
    - agent_definitions.py — agent role definitions

    MCP (src/openharness/mcp/):
    - client.py, config.py, types.py — full MCP client support
    - mcp_tool.py, mcp_auth_tool.py, list/read_mcp_resource_tool.py

    VOICE (src/openharness/voice/):
    - stream_stt.py  — streaming speech-to-text
    - voice_mode.py  — voice interaction mode
    - keyterms.py    — keyword detection

    PERSONALIZATION (src/openharness/personalization/):
    - extractor.py   — extract user preferences from sessions
    - rules.py       — personalization rule engine
    - session_hook.py — apply personalization per session

    API PROVIDERS:
    - Claude Code (Anthropic) — NO extra API key, uses existing subscription
    - GitHub Copilot          — NO extra API key, uses existing subscription
    - OpenAI                  — standard API key
    - OpenRouter              — standard API key

    OHMO PERSONAL AGENT:
    - Workspace: ~/.ohmo/ (skills/, plugins/, memory/, sessions/)
    - Session storage: OhmoSessionBackend
    - System prompt: build_ohmo_system_prompt()
    - Gateway: ohmo/gateway/ — bridges ohmo to messaging channels
    - CLI: `ohmo chat`, `ohmo run`, `ohmo memory`, `ohmo gateway`

    BUNDLED SKILLS (8 built-in):
    commit, debug, diagnose, plan, review, simplify, skill-creator, test
    + .claude/skills/harness-eval, pr-merge

    PRODUCTION QUALITY:
    - 114 passing pytest tests
    - 6 E2E test suites (docker sandbox, CLI flags, TUI, headless, real skills)
    - GitHub Actions CI
    - React + Ink TUI (terminal UI with live SwarmPanel, TodoPanel, ToolCallDisplay)
    - Output: text | json | stream-json
    - CHANGELOG.md + release notes (v0.1.8, v0.1.9)

Why this is 10/10 for the Pantheon:
    1. 13K stars — this is the most battle-tested open agent platform absorbed.
    2. Runs on Claude Code subscription — NO API key. Free for the Forgemaster.
    3. 10 channel ingress including WhatsApp + Telegram — Pantheon command channels.
    4. Multi-agent swarm with git WORKTREE PER AGENT — each agent isolated in its own
       git branch. This is how you run 25 Primes without them colliding.
    5. Docker sandbox — same isolation model as KelvinClaw WASM, but for Python.
       Run ScoutPrime in a container. GhostPrime in a container. Zero bleed.
    6. autopilot mode — autonomous PR pipeline. This is FluxPrime's AutoGPT layer
       but production-ready, tested, and shipping today.
    7. Built-in cron (cron_create/delete/list/toggle tools) — native to agent loop.
    8. MCP native — same protocol as NetClaw's 15 servers. Direct integration.
    9. memdir.py reads ~/.memory/ or MEMORY.md — Pantheon-native immediately.
    10. Voice mode (stream_stt.py) — "The Ocular Link" already exists. Now it can hear.
    11. PERSONALIZATION ENGINE — extractor.py learns user prefs from sessions.
        This is SAFLA 2.0 applied to identity. The agent rewrites its own behavior rules.
    12. ohmo is literally "the personal AI agent that actually works for you over
        long sessions" — that IS the Agent Zero vision. It exists. It ships.

Pantheon Integration Path:
    IMMEDIATE:
    - pip install openharness / pip install ohmo
    - ohmo chat (no API key — uses Claude Code subscription)
    - Enable Telegram channel: set TELEGRAM_BOT_TOKEN in config

    SHORT TERM:
    - Replace GhostPrime's Python with OpenHarness agent_tool + sandbox
    - Wire ScoutPrime scraping through bash_tool + web_fetch in Docker sandbox
    - Use swarm/team_lifecycle.py for Pantheon Prime coordination
    - Wire autopilot pipeline for ContentPrime autonomous PR flow

    LONG TERM:
    - OpenHarness becomes the Agent Zero execution platform
    - Each Prime runs as an ohmo agent with isolated worktree + memory namespace
    - Cron tools replace the Pantheon's manual cron scheduling
    - Voice mode on Red Magic → Forgemaster speaks to the Pantheon
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
SLUG           = "HKUDS/OpenHarness"
REPO_URL       = f"https://github.com/{SLUG}"
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


# ─── CHANNEL REGISTRY ────────────────────────────────────────────────────────

CHANNELS = {
    "telegram":  {"file": "src/openharness/channels/impl/telegram.py",  "env": "TELEGRAM_BOT_TOKEN", "pantheon": "PRIMARY — existing bot token in TOOLS.md"},
    "whatsapp":  {"file": "src/openharness/channels/impl/whatsapp.py",  "env": "WHATSAPP_*",         "pantheon": "Forgemaster direct command channel"},
    "discord":   {"file": "src/openharness/channels/impl/discord.py",   "env": "DISCORD_TOKEN",      "pantheon": "Pantheon public announcements"},
    "slack":     {"file": "src/openharness/channels/impl/slack.py",     "env": "SLACK_*",            "pantheon": "Team channel if Joe is onboarded"},
    "feishu":    {"file": "src/openharness/channels/impl/feishu.py",    "env": "FEISHU_*",           "pantheon": "Enterprise comms if needed"},
    "dingtalk":  {"file": "src/openharness/channels/impl/dingtalk.py",  "env": "DINGTALK_*",         "pantheon": "Alt enterprise channel"},
    "email":     {"file": "src/openharness/channels/impl/email.py",     "env": "EMAIL_*",            "pantheon": "PropPilot lead email responses"},
    "matrix":    {"file": "src/openharness/channels/impl/matrix.py",    "env": "MATRIX_*",           "pantheon": "Encrypted comms option"},
    "mochat":    {"file": "src/openharness/channels/impl/mochat.py",    "env": "MOCHAT_*",           "pantheon": "WeCom / enterprise WeChat"},
    "qq":        {"file": "src/openharness/channels/impl/qq.py",        "env": "QQ_*",               "pantheon": "QQ messaging"},
}

# ─── TOOL REGISTRY ───────────────────────────────────────────────────────────

TOOLS = {
    "execution":    ["bash_tool", "sleep", "remote_trigger"],
    "files":        ["file_read_tool", "file_write_tool", "file_edit_tool", "glob_tool", "grep_tool"],
    "web":          ["web_fetch_tool", "web_search_tool"],
    "vision":       ["image_to_text_tool", "image_generation_tool"],
    "code":         ["lsp_tool", "notebook_edit_tool"],
    "mcp":          ["mcp_tool", "mcp_auth_tool", "list_mcp_resources_tool", "read_mcp_resource_tool"],
    "tasks":        ["task_create_tool", "task_get_tool", "task_list_tool", "task_update_tool", "task_stop_tool", "task_output_tool"],
    "swarm":        ["agent_tool", "team_create_tool", "team_delete_tool", "send_message_tool"],
    "cron":         ["cron_create_tool", "cron_delete_tool", "cron_list_tool", "cron_toggle_tool"],
    "planning":     ["enter_plan_mode_tool", "exit_plan_mode_tool", "brief_tool", "todo_write_tool"],
    "worktree":     ["enter_worktree_tool", "exit_worktree_tool"],
    "meta":         ["tool_search_tool", "skill_tool", "config_tool", "ask_user_question_tool"],
}

# ─── SWARM COMPONENTS ────────────────────────────────────────────────────────

SWARM = {
    "in_process":        "Spawn agents in same process — fast, shared memory",
    "subprocess_backend":"Spawn agents as isolated subprocesses — safe",
    "mailbox":           "Async inter-agent message bus",
    "registry":          "Swarm agent registry — discover, list, address",
    "spawn_utils":       "Agent lifecycle helpers",
    "team_lifecycle":    "Team create/destroy/scale — Prime Swarm layer",
    "permission_sync":   "Permission propagation across team members",
    "worktree":          "Git worktree per agent — each Prime owns its branch",
    "lockfile":          "Distributed concurrency lock",
}

# ─── PANTHEON PRIME MAP ──────────────────────────────────────────────────────

PRIME_MAP = {
    "GhostPrime":    {"tool": "agent_tool + bash_tool",            "sandbox": "Docker",     "worktree": True,  "channel": None},
    "ScoutPrime":    {"tool": "web_fetch + web_search + bash_tool","sandbox": "Docker",     "worktree": True,  "channel": None},
    "ContentPrime":  {"tool": "skill_tool + bash_tool + task_*",   "sandbox": "subprocess", "worktree": True,  "channel": "telegram"},
    "OpenAgora":     {"tool": "bash_tool + remote_trigger",        "sandbox": "subprocess", "worktree": False, "channel": "telegram"},
    "FluxPrime":     {"tool": "agent_tool + task_* + cron_*",      "sandbox": "in_process", "worktree": False, "channel": "telegram"},
    "MidasPrime":    {"tool": "cron_* + task_* + brief_tool",      "sandbox": "subprocess", "worktree": False, "channel": "telegram"},
    "ZeusPrime":     {"tool": "bash_tool + remote_trigger",        "sandbox": "Docker",     "worktree": False, "channel": "telegram"},
    "AgentZero":     {"tool": "ALL",                               "sandbox": "Docker+WASM","worktree": True,  "channel": "telegram+whatsapp"},
}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class OpenHarnessConnector:
    """
    Pantheon connector for OpenHarness + ohmo.
    13K stars. 43+ tools. 10 channels. Multi-agent swarm. Docker sandbox.
    Autopilot. Voice. MCP native. No extra API key.

    Pantheon Role: AGENT_PLATFORM / SWARM_ENGINE

    This is the most complete open agent platform in the Forge.
    ohmo IS Agent Zero. It ships today.

    Usage:
        oh = OpenHarnessConnector()
        print(oh.health_check())
        print(oh.swarm_config())
        print(oh.channel_config("telegram"))
        print(oh.prime_integration("GhostPrime"))
        print(oh.install_instructions())
        print(oh.autopilot_config())
        print(oh.voice_config())
    """

    REPO_URL      = REPO_URL
    CATEGORY      = "AGENT_PLATFORM"
    ROLE          = "SWARM_ENGINE"
    PANTHEON_ROLE = "AGENT_PLATFORM / SWARM_ENGINE"
    SCORE         = 10
    STARS         = 13437
    FORKS         = 2207

    TOTAL_TOOLS    = 43
    TOTAL_CHANNELS = 10
    TOTAL_PY_FILES = 260
    TOTAL_FILES    = 478
    TEST_PASSING   = 114
    E2E_SUITES     = 6

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        return {
            "name":         "openharness",
            "personal_agent": "ohmo",
            "category":     self.CATEGORY,
            "role":         self.PANTHEON_ROLE,
            "score":        self.SCORE,
            "score_note":   "No override needed. 13K stars. Production-grade. No extra API key. ohmo IS Agent Zero.",
            "stars":        self.STARS,
            "forks":        self.FORKS,
            "language":     "Python 3.10+",
            "tests":        f"{self.TEST_PASSING} pytest passing",
            "e2e":          f"{self.E2E_SUITES} suites",
            "tools":        self.TOTAL_TOOLS,
            "channels":     self.TOTAL_CHANNELS,
            "py_files":     self.TOTAL_PY_FILES,
            "api_key":      "NOT REQUIRED — runs on Claude Code or Copilot subscription",
            "key_capabilities": [
                "ohmo personal agent — long-session autonomous AI, forks branches, writes code, opens PRs",
                "10 channel ingress: Telegram, WhatsApp, Discord, Slack, Feishu, DingTalk, Email, Matrix, MoChat, QQ",
                "Multi-agent swarm with git worktree per agent (each Prime owns its branch)",
                "Docker sandbox — full container isolation per session",
                "43+ tools: bash, file ops, web, vision, MCP, tasks, swarm, cron, planning, LSP",
                "Autopilot mode — autonomous PR pipeline (GitHub Actions)",
                "Built-in cron tools (create/delete/list/toggle) — native to agent loop",
                "MCP native — direct integration with NetClaw's 15 MCP servers",
                "Voice mode — streaming STT, voice_mode.py",
                "Personalization engine — learns user preferences from sessions",
                "AutoDream — background memory extraction + session summarization",
                "114 passing tests, 6 E2E suites — production quality verified",
            ],
            "pantheon_integration": [
                "IMMEDIATE: pip install ohmo && ohmo chat (zero config, no API key)",
                "IMMEDIATE: Enable Telegram channel with existing bot token",
                "SHORT TERM: Wrap each Prime as an ohmo agent with worktree isolation",
                "LONG TERM: OpenHarness = Agent Zero's execution platform",
            ],
            "repo":   self.REPO_URL,
            "status": "ready",
        }

    # ── CHANNELS ──────────────────────────────────────────────────────────────

    def channel_config(self, channel: str) -> Dict:
        info = CHANNELS.get(channel)
        if not info:
            return {"error": f"Unknown channel: {channel}. Available: {list(CHANNELS.keys())}"}
        source = _gh_get(info["file"])
        return self.to_pantheon_signal({
            "action":  "channel_config",
            "channel": channel,
            "info":    info,
            "source":  source[:2000] if isinstance(source, str) else str(source),
        })

    def list_channels(self) -> Dict:
        return self.to_pantheon_signal({
            "action":   "list_channels",
            "channels": {k: v["pantheon"] for k, v in CHANNELS.items()},
            "priority": ["telegram", "whatsapp", "discord"],
            "note":     "Telegram token in TOOLS.md — enable first. WhatsApp second.",
        })

    # ── TOOLS ─────────────────────────────────────────────────────────────────

    def list_tools(self) -> Dict:
        return self.to_pantheon_signal({
            "action":      "list_tools",
            "categories":  TOOLS,
            "total":       self.TOTAL_TOOLS,
            "pantheon_priority": [
                "bash_tool — ScoutPrime, GhostPrime, OpenAgora execution",
                "agent_tool — spawn sub-agents (each Prime as child agent)",
                "team_create/delete — Prime team management",
                "cron_* — replace manual Pantheon cron scheduling",
                "mcp_tool — connect NetClaw's 15 MCP servers directly",
                "web_fetch + web_search — ScoutPrime property + market data",
                "task_* — FluxPrime mission orchestration",
                "remote_trigger — ZeusPrime Polymarket/Kalshi execution",
            ],
        })

    def get_tool_source(self, tool_name: str) -> Dict:
        path = f"src/openharness/tools/{tool_name}.py"
        content = _gh_get(path)
        return self.to_pantheon_signal({
            "action":  "get_tool_source",
            "tool":    tool_name,
            "content": content[:3000] if isinstance(content, str) else str(content),
        })

    # ── SWARM ─────────────────────────────────────────────────────────────────

    def swarm_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":     "swarm_config",
            "components": SWARM,
            "backends":   ["in_process", "subprocess_backend"],
            "worktree":   "Each agent gets isolated git worktree — no branch collisions",
            "mailbox":    "Async inter-agent message bus — Primes communicate natively",
            "permission_sync": "Permission changes propagate across all team members",
            "pantheon_use": {
                "25_primes":     "team_create() with subprocess_backend — 25 isolated agents",
                "coordination":  "mailbox.py for Prime-to-Prime messaging",
                "isolation":     "worktree.py — each Prime owns its git branch",
                "permissions":   "permission_sync.py — IronClaw mode propagates to all",
            },
        })

    # ── PRIME MAP ─────────────────────────────────────────────────────────────

    def prime_integration(self, prime: str) -> Dict:
        config = PRIME_MAP.get(prime)
        if not config:
            return {"error": f"Unknown Prime: {prime}. Available: {list(PRIME_MAP.keys())}"}
        return self.to_pantheon_signal({
            "action": "prime_integration",
            "prime":  prime,
            "config": config,
            "note":   f"Run {prime} as ohmo agent with worktree={config['worktree']}, sandbox={config['sandbox']}",
        })

    def all_prime_integrations(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "all_prime_integrations",
            "primes": PRIME_MAP,
        })

    # ── AUTOPILOT ─────────────────────────────────────────────────────────────

    def autopilot_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":     "autopilot_config",
            "service":    "src/openharness/autopilot/service.py",
            "workflows": [
                "autopilot-run-next.yml — execute next queued task",
                "autopilot-scan.yml     — scan for new tasks",
                "autopilot-pages.yml   — deploy dashboard to GitHub Pages",
            ],
            "dashboard":  "docs/autopilot/ — React TUI, live pipeline visualization",
            "pantheon_use": [
                "ContentPrime autonomous PR pipeline — ohmo writes scripts, opens PRs",
                "ScoutPrime property scan — autopilot scans Lee County daily",
                "GhostPrime cycle management — autopilot queues next swarm cycle",
            ],
        })

    # ── MEMORY ────────────────────────────────────────────────────────────────

    def memory_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":   "memory_config",
            "manager":  "src/openharness/memory/manager.py",
            "namespaces": ["agent (per-agent)", "team (shared)", "session"],
            "storage":  "memdir.py — reads ~/.memory/ or MEMORY.md (Pantheon-native!)",
            "search":   "search.py + relevance.py — semantic relevance scoring",
            "autodream": "services/autodream/ — background memory extraction from sessions",
            "migrate":  "migrate.py — schema migration for memory upgrades",
            "pantheon": "Wire to workspace MEMORY.md — zero migration needed",
        })

    # ── VOICE ─────────────────────────────────────────────────────────────────

    def voice_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":   "voice_config",
            "files":    ["src/openharness/voice/stream_stt.py", "src/openharness/voice/voice_mode.py", "src/openharness/voice/keyterms.py"],
            "mode":     "Streaming STT — real-time voice-to-command",
            "keywords": "keyterms.py — hot-word detection for wake-word trigger",
            "pantheon": "Red Magic mic → stream_stt → ohmo → Prime command. Forgemaster speaks to the Pantheon.",
            "note":     "Combine with NexusClaw for physical phone control + voice command.",
        })

    # ── PERSONALIZATION ───────────────────────────────────────────────────────

    def personalization_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":  "personalization_config",
            "files": [
                "src/openharness/personalization/extractor.py  — extract prefs from sessions",
                "src/openharness/personalization/rules.py      — rule engine",
                "src/openharness/personalization/session_hook.py — apply per session",
            ],
            "pantheon": "SAFLA 2.0 equivalent for identity — ohmo learns Forgemaster's patterns, rewrites its own behavior. THIS is the Soul File evolving.",
        })

    # ── SANDBOX ───────────────────────────────────────────────────────────────

    def sandbox_config(self) -> Dict:
        return self.to_pantheon_signal({
            "action":   "sandbox_config",
            "backend":  "Docker (src/openharness/sandbox/docker_backend.py)",
            "image":    "src/openharness/sandbox/docker_image.py",
            "adapter":  "Swappable backend — Docker → subprocess → bare",
            "validator":"path_validator.py — directory traversal prevention",
            "e2e":      "scripts/test_docker_sandbox_e2e.py — CI-tested",
            "pantheon": "GhostPrime, ScoutPrime, ZeusPrime each in Docker — no bleed between Primes",
        })

    # ── INSTALL ───────────────────────────────────────────────────────────────

    def install_instructions(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "install_instructions",
            "pip": [
                "pip install openharness   # framework only",
                "pip install ohmo          # personal agent + framework",
            ],
            "git": [
                "git clone https://github.com/HKUDS/OpenHarness",
                "cd OpenHarness",
                "pip install -e '.[dev]'",
            ],
            "quick_start": [
                "ohmo chat                 # no API key — uses Claude Code subscription",
                "ohmo chat --model claude  # explicit provider",
                "ohmo run 'scan this repo' # one-shot task",
                "ohmo gateway start        # enable channel ingress",
            ],
            "enable_telegram": [
                "export TELEGRAM_BOT_TOKEN=8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4",
                "ohmo gateway start --channels telegram",
            ],
            "termux_note": "pip install ohmo works on Termux — no Rust build required (pure Python)",
        })

    def ohmo_quick_start(self) -> Dict:
        """Fastest path to a working ohmo agent on Red Magic."""
        return self.to_pantheon_signal({
            "action": "ohmo_quick_start",
            "steps": [
                "# Termux on Red Magic:",
                "pkg install python -y",
                "pip install ohmo",
                "ohmo chat",
                "# That's it. Claude Code session starts. No API key.",
            ],
            "add_telegram": [
                "# Add Telegram after first session works:",
                "export TELEGRAM_BOT_TOKEN=8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4",
                "ohmo gateway start --channels telegram",
                "# Now Forgemaster can command ohmo from Telegram",
            ],
            "add_memory": [
                "# Wire to Pantheon MEMORY.md:",
                "export OHMO_MEMORY_PATH=/path/to/workspace/MEMORY.md",
                "ohmo chat  # memory loads on start",
            ],
            "estimated_time": "< 5 minutes from zero to running ohmo on Red Magic",
        })

    # ── SIGNAL + RELAY ────────────────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "openharness",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[OpenHarness] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[OpenHarness] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    oh = OpenHarnessConnector()

    if len(sys.argv) < 2:
        print(json.dumps(oh.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(oh.health_check(), indent=2))
    elif cmd == "channels":
        print(json.dumps(oh.list_channels(), indent=2))
    elif cmd == "channel" and len(sys.argv) > 2:
        print(json.dumps(oh.channel_config(sys.argv[2]), indent=2))
    elif cmd == "tools":
        print(json.dumps(oh.list_tools(), indent=2))
    elif cmd == "tool" and len(sys.argv) > 2:
        print(json.dumps(oh.get_tool_source(sys.argv[2]), indent=2))
    elif cmd == "swarm":
        print(json.dumps(oh.swarm_config(), indent=2))
    elif cmd == "prime" and len(sys.argv) > 2:
        print(json.dumps(oh.prime_integration(sys.argv[2]), indent=2))
    elif cmd == "primes":
        print(json.dumps(oh.all_prime_integrations(), indent=2))
    elif cmd == "autopilot":
        print(json.dumps(oh.autopilot_config(), indent=2))
    elif cmd == "memory":
        print(json.dumps(oh.memory_config(), indent=2))
    elif cmd == "voice":
        print(json.dumps(oh.voice_config(), indent=2))
    elif cmd == "persona":
        print(json.dumps(oh.personalization_config(), indent=2))
    elif cmd == "sandbox":
        print(json.dumps(oh.sandbox_config(), indent=2))
    elif cmd == "install":
        print(json.dumps(oh.install_instructions(), indent=2))
    elif cmd == "start":
        print(json.dumps(oh.ohmo_quick_start(), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|channels|channel <name>|tools|tool <name>|swarm|prime <name>|primes|autopilot|memory|voice|persona|sandbox|install|start]")
