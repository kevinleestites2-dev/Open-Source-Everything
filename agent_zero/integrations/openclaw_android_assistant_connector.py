#!/usr/bin/env python3
"""
Agent Zero Integration — AnyClaw / OpenClaw Platform (FULL IMPLEMENTATION)
Category : AGENT_PLATFORM / MOBILE_COMMAND_CENTER
Source   : https://github.com/OpenClawAndroid/openclaw-android-assistant
Stars    : 395 (early — platform just launched publicly)
Absorbed : 2026-06-02

ENGINE SCORE OVERRIDE: 3/10 → 10/10
Reason: Engine scored stars. This is not a tool. This is a PLATFORM.
        It IS the Pantheon architecture, built by a different team, in parallel.

What it is:
    AnyClaw = OpenClaw + OpenAI Codex CLI + Claw Code (Claude Code) — three agents, one APK.
    But zoom out: this is the full OpenClaw Platform:

    AGENTS (3 coding agents in one APK):
    - OpenClaw         — personal AI assistant, multi-channel, skills system, Canvas, Control UI
    - OpenAI Codex CLI — terminal coding agent, reads codebase, writes code, runs commands
    - Claw Code        — leaked Claude Code architecture (48K+ stars), ported to Android

    SKILLS ECOSYSTEM (55+ built-in skills):
    - WhatsApp (wacli)       — send messages, sync history, search
    - GitHub (gh-issues)     — issues, PRs, code review
    - Slack, Discord, Notion — full integrations
    - skill-creator          — build new skills inline
    - coding-agent           — delegate to Codex/Claude Code as background workers
    - Google services (gog)  — calendar, gmail, drive
    - GoPlaces               — location/places lookup
    - canvas, diagram-maker  — visual output
    - summarize, nano-pdf    — document tools
    - weather, spotify, trello, tmux, oracle, node-connect...
    55+ total, all SKILL.md structured

    PLATFORM STACK:
    - TypeScript monorepo (pnpm workspaces)
    - Android APK (embedded Linux, no root)
    - iOS/macOS companion apps
    - Docker deployable (docker-compose.yml)
    - Fly.io deployable (fly.toml)
    - Skill SDK — anyone can build+publish skills
    - MCP integration — connects to any MCP server

    AGENTS.md / CLAUDE.md — full agent workspace protocol (mirrors Pantheon's own)

Pantheon Role:
    MOBILE COMMAND CENTER + SKILL FACTORY.

    Two distinct values:

    1. SKILL ABSORPTION: The 55+ skills are a goldmine. Each SKILL.md is a
       structured workflow Agent Zero can absorb. wacli, coding-agent, gog,
       goplaces, canvas, summarize — all directly usable in the Pantheon.
       The skill-creator skill itself is the pattern for building Pantheon skills.

    2. PLATFORM BLUEPRINT: OpenClaw's architecture IS the reference implementation
       for what Agent Zero is becoming:
       - Skills = Agent Zero's integrations
       - AGENTS.md = Agent Zero's own workspace protocol (they converged independently)
       - background workers + notification routing = Pantheon's Prime delegation pattern
       - Multi-channel (WhatsApp, Slack, Discord) = Pantheon's comms layer

    The Red Magic runs this. All three coding agents. On-device. No PC.
    DexClaw terminal + EleftheriaPrime hands + OpenClaude brain + AnyClaw platform
    = fully armed Red Magic Pantheon node.

Install:
    APK: https://friuns2.github.io/openclaw-android-assistant/
    Google Play: gptos.intelligence.assistant
    Self-host: docker compose up
    Fly.io: fly deploy

Skill SDK:
    Skills live in skills/<name>/SKILL.md
    Structure: frontmatter (name, description, metadata) + body (workflow)
    scripts/ references/ assets/ agents/ subdirs optional
"""

import os
import sys
import json
import subprocess
import shutil
import urllib.request
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

OPENCLAW_BASE_URL = os.environ.get("OPENCLAW_BASE_URL", "http://localhost:3000")
OPENCLAW_API_KEY  = os.environ.get("OPENCLAW_API_KEY", "")
TELEGRAM_TOKEN    = os.environ.get("TELEGRAM_BOT_TOKEN", "8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4")
TELEGRAM_CHAT     = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")

# Skill repo cache dir
SKILLS_CACHE = Path.home() / ".pantheon" / "openclaw_skills"


# ─── HTTP HELPER ─────────────────────────────────────────────────────────────

def _api(method: str, path: str, payload: Optional[Dict] = None) -> Dict:
    url = f"{OPENCLAW_BASE_URL.rstrip('/')}{path}"
    headers = {"Content-Type": "application/json", "Accept": "application/json"}
    if OPENCLAW_API_KEY:
        headers["Authorization"] = f"Bearer {OPENCLAW_API_KEY}"
    data = json.dumps(payload).encode() if payload else None
    req  = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            body = r.read().decode()
            return json.loads(body) if body else {"status": "ok"}
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:    return {"error": json.loads(body), "status_code": e.code}
        except: return {"error": body[:300], "status_code": e.code}
    except Exception as e:
        return {"error": str(e), "status": "request_failed"}


# ─── SKILL FETCHER ───────────────────────────────────────────────────────────

def fetch_skill(skill_name: str, token: str = "") -> Optional[Dict]:
    """
    Fetch a specific skill's SKILL.md from the OpenClaw skills ecosystem.
    Returns parsed skill dict with name, description, body.
    """
    tok = token or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if tok:
        headers["Authorization"] = f"token {tok}"

    url  = f"https://api.github.com/repos/OpenClawAndroid/openclaw-android-assistant/contents/skills/{skill_name}/SKILL.md"
    req  = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data    = json.loads(r.read())
            content = __import__("base64").b64decode(data["content"]).decode()
        return {"name": skill_name, "content": content, "size": len(content)}
    except Exception as e:
        return {"error": str(e), "name": skill_name}


def fetch_all_skills(token: str = "") -> List[Dict]:
    """
    Fetch the full list of available skills from the OpenClaw ecosystem.
    Returns list of skill names.
    """
    tok = token or os.environ.get("GITHUB_TOKEN", "")
    headers = {"Accept": "application/vnd.github.v3+json"}
    if tok:
        headers["Authorization"] = f"token {tok}"

    url = "https://api.github.com/repos/OpenClawAndroid/openclaw-android-assistant/contents/skills"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            items = json.loads(r.read())
        return [
            {"name": i["name"], "type": i["type"]}
            for i in items if i["type"] == "dir"
        ]
    except Exception as e:
        return [{"error": str(e)}]


# ─── SKILL BUILDER ───────────────────────────────────────────────────────────

def build_pantheon_skill(name: str, description: str, workflow: str,
                          scripts: Optional[Dict[str, str]] = None) -> str:
    """
    Generate a SKILL.md in OpenClaw format for a Pantheon capability.
    Use this to create new Agent Zero skills following the OpenClaw pattern.

    :param name:        Skill name (slug)
    :param description: Short trigger description (frontmatter)
    :param workflow:    Markdown body — the actual workflow instructions
    :param scripts:     Optional dict of {filename: content} for scripts/
    :return:            Full SKILL.md content string
    """
    frontmatter = f'''---
name: {name}
description: "{description}"
metadata:
  {{
    "pantheon": {{
      "emoji": "🔱",
      "prime": "agent_zero",
      "layer": 20
    }}
  }}
---'''

    body = f"""# {name.replace('-', ' ').title()}

{workflow}
"""
    return f"{frontmatter}\n\n{body}"


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class AnyclawConnector:
    """
    Pantheon connector for AnyClaw / OpenClaw Platform.
    Mobile Command Center + Skill Factory for Agent Zero.

    Two modes:
    1. SKILL FACTORY — absorb the 55+ OpenClaw skills into Pantheon
    2. PLATFORM BRIDGE — connect to a running OpenClaw instance via REST

    Usage:
        ac = AnyclawConnector()

        # List all available skills from the ecosystem
        skills = ac.list_ecosystem_skills()

        # Absorb a specific skill into the Pantheon
        skill = ac.absorb_skill("wacli")
        skill = ac.absorb_skill("coding-agent")
        skill = ac.absorb_skill("goplaces")

        # Batch absorb the most relevant skills
        ac.absorb_pantheon_priority_skills()

        # Build a new Pantheon skill in OpenClaw format
        md = ac.build_skill("scout-prime-scan", "Scan Lee County auctions", workflow="...")

        # Bridge to running OpenClaw instance
        result = ac.send_message("channel_id", "task text")
        result = ac.run_skill("wacli", {"recipient": "+1...", "message": "..."})
    """

    REPO_URL       = "https://github.com/OpenClawAndroid/openclaw-android-assistant"
    CATEGORY       = "AGENT_PLATFORM"
    PANTHEON_ROLE  = "MOBILE_COMMAND_CENTER"
    SCORE          = 10  # engine said 3 — this is the full OpenClaw platform

    # Skills most directly relevant to the Pantheon — absorb these first
    PRIORITY_SKILLS = [
        "wacli",           # WhatsApp — send, sync, search
        "coding-agent",    # delegate to Codex/Claude Code/OpenCode as background workers
        "gog",             # Google services — calendar, gmail, drive
        "goplaces",        # Google Places — location, businesses
        "github",          # GitHub integration
        "gh-issues",       # GitHub issues + PRs
        "slack",           # Slack
        "skill-creator",   # build new skills — the meta-skill
        "summarize",       # document summarization
        "weather",         # weather lookup
        "canvas",          # visual output / canvas
        "nano-pdf",        # PDF tools
        "tmux",            # terminal multiplexer control
        "notion",          # Notion integration
        "taskflow",        # task management
        "oracle",          # Oracle DB (interesting for data layer)
        "healthcheck",     # system health monitoring
        "session-logs",    # session log access
        "node-connect",    # Node.js connectivity
        "mcporter",        # MCP server bridge
    ]

    def __init__(self, github_token: str = ""):
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN", "")

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        local_ok = False
        try:
            result = _api("GET", "/health")
            local_ok = "error" not in result
        except Exception:
            pass
        return {
            "name":           "anyclaw",
            "category":       self.CATEGORY,
            "role":           self.PANTHEON_ROLE,
            "score_override": self.SCORE,
            "local_instance": local_ok,
            "base_url":       OPENCLAW_BASE_URL,
            "ecosystem_url":  self.REPO_URL,
            "priority_skills": len(self.PRIORITY_SKILLS),
            "status":         "ready",
        }

    # ── SKILL FACTORY ─────────────────────────────────────────────────────────

    def list_ecosystem_skills(self) -> Dict:
        """List all 55+ skills available in the OpenClaw ecosystem."""
        skills = fetch_all_skills(self.github_token)
        return self.to_pantheon_signal({
            "action": "list_ecosystem_skills",
            "count":  len(skills),
            "skills": skills,
        })

    def absorb_skill(self, skill_name: str) -> Dict:
        """
        Absorb a specific OpenClaw skill into the Pantheon.
        Fetches SKILL.md and stores locally for Agent Zero to reference.

        :param skill_name: Skill directory name (e.g. "wacli", "coding-agent")
        :return:           Pantheon signal with skill content
        """
        skill = fetch_skill(skill_name, self.github_token)
        if "error" in skill:
            return self.to_pantheon_signal({"action": "absorb_skill", "name": skill_name, **skill})

        # Cache locally
        SKILLS_CACHE.mkdir(parents=True, exist_ok=True)
        cache_path = SKILLS_CACHE / f"{skill_name}.md"
        cache_path.write_text(skill["content"])

        return self.to_pantheon_signal({
            "action":   "absorb_skill",
            "name":     skill_name,
            "size":     skill["size"],
            "cached":   str(cache_path),
            "status":   "absorbed",
            "preview":  skill["content"][:300],
        })

    def absorb_pantheon_priority_skills(self) -> Dict:
        """
        Batch absorb the 20 most Pantheon-relevant OpenClaw skills.
        Stores all locally. Returns summary.
        """
        results = []
        ok = 0
        for skill_name in self.PRIORITY_SKILLS:
            result = self.absorb_skill(skill_name)
            status = result["data"].get("status", "error")
            results.append({"name": skill_name, "status": status})
            if status == "absorbed":
                ok += 1
            print(f"  {'✅' if status == 'absorbed' else '❌'} {skill_name}")

        self.relay_to_telegram(
            f"Skill absorption complete: {ok}/{len(self.PRIORITY_SKILLS)} skills absorbed\n"
            f"Cached at: {SKILLS_CACHE}"
        )
        return self.to_pantheon_signal({
            "action":  "absorb_pantheon_priority_skills",
            "total":   len(self.PRIORITY_SKILLS),
            "ok":      ok,
            "results": results,
            "cache":   str(SKILLS_CACHE),
        })

    def get_cached_skill(self, skill_name: str) -> Optional[str]:
        """Read a previously absorbed skill from local cache."""
        path = SKILLS_CACHE / f"{skill_name}.md"
        return path.read_text() if path.exists() else None

    def list_cached_skills(self) -> List[str]:
        """List all skills currently in local cache."""
        if not SKILLS_CACHE.exists():
            return []
        return [f.stem for f in SKILLS_CACHE.glob("*.md")]

    # ── SKILL BUILDER ─────────────────────────────────────────────────────────

    def build_skill(self, name: str, description: str, workflow: str,
                     scripts: Optional[Dict[str, str]] = None) -> Dict:
        """
        Build a new Pantheon skill in OpenClaw SKILL.md format.
        Follow the skill-creator pattern: lean frontmatter + focused workflow.

        :return: Pantheon signal with generated SKILL.md content
        """
        content = build_pantheon_skill(name, description, workflow, scripts)
        # Save locally
        SKILLS_CACHE.mkdir(parents=True, exist_ok=True)
        path = SKILLS_CACHE / f"pantheon_{name}.md"
        path.write_text(content)
        return self.to_pantheon_signal({
            "action":  "build_skill",
            "name":    name,
            "path":    str(path),
            "content": content,
            "status":  "built",
        })

    # ── PLATFORM BRIDGE (requires running OpenClaw instance) ──────────────────

    def send_message(self, channel_id: str, text: str) -> Dict:
        """Send a message through a connected OpenClaw channel."""
        result = _api("POST", f"/api/channels/{channel_id}/messages", {"text": text})
        return self.to_pantheon_signal({"action": "send_message", "channel": channel_id, "result": result})

    def run_skill(self, skill_name: str, params: Optional[Dict] = None) -> Dict:
        """Trigger a skill on a running OpenClaw instance."""
        result = _api("POST", f"/api/skills/{skill_name}/run", params or {})
        return self.to_pantheon_signal({"action": "run_skill", "skill": skill_name, "result": result})

    def list_channels(self) -> Dict:
        """List all connected channels on a running OpenClaw instance."""
        result = _api("GET", "/api/channels")
        return self.to_pantheon_signal({"action": "list_channels", "result": result})

    def list_agents(self) -> Dict:
        """List active agents on a running OpenClaw instance."""
        result = _api("GET", "/api/agents")
        return self.to_pantheon_signal({"action": "list_agents", "result": result})

    # ── DOCKER / DEPLOY ───────────────────────────────────────────────────────

    def docker_start(self, detach: bool = True) -> Dict:
        """Start OpenClaw via docker compose (self-hosted mode)."""
        cmd = ["docker", "compose", "up"]
        if detach:
            cmd.append("-d")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            return self.to_pantheon_signal({
                "action":    "docker_start",
                "status":    "ok" if result.returncode == 0 else "error",
                "stdout":    result.stdout[-500:],
                "stderr":    result.stderr[-300:],
            })
        except Exception as e:
            return self.to_pantheon_signal({"action": "docker_start", "error": str(e)})

    # ── SHORTCUTS FOR PANTHEON PRIMES ─────────────────────────────────────────

    def get_wacli_skill(self) -> str:
        """Get the WhatsApp wacli skill — most relevant for Pantheon comms."""
        cached = self.get_cached_skill("wacli")
        if cached:
            return cached
        skill = fetch_skill("wacli", self.github_token)
        return skill.get("content", "")

    def get_coding_agent_skill(self) -> str:
        """Get the coding-agent skill — background worker delegation pattern."""
        cached = self.get_cached_skill("coding-agent")
        if cached:
            return cached
        skill = fetch_skill("coding-agent", self.github_token)
        return skill.get("content", "")

    def architecture_summary(self) -> Dict:
        """Return a structured summary of the OpenClaw platform architecture."""
        return self.to_pantheon_signal({
            "platform":   "AnyClaw / OpenClaw",
            "agents":     ["OpenClaw", "OpenAI Codex CLI", "Claw Code (Claude Code)"],
            "skills":     55,
            "priority_absorbed": self.PRIORITY_SKILLS,
            "apps":       ["Android APK", "iOS", "macOS", "Docker", "Fly.io"],
            "key_skills": {
                "comms":    ["wacli (WhatsApp)", "slack", "discord"],
                "coding":   ["coding-agent", "github", "gh-issues"],
                "google":   ["gog", "goplaces"],
                "ai":       ["skill-creator", "mcporter (MCP bridge)"],
                "docs":     ["summarize", "nano-pdf", "canvas"],
                "infra":    ["tmux", "healthcheck", "oracle", "node-connect"],
            },
            "pantheon_alignment": {
                "AGENTS.md":          "mirrors Pantheon workspace protocol",
                "skill_system":       "maps to Agent Zero Layer 20 integrations",
                "background_workers": "maps to Pantheon Prime delegation",
                "multi_channel":      "maps to Pantheon comms layer (WhatsApp, Telegram, Slack)",
                "MCP":                "Agent Zero can connect via mcporter skill",
            },
        })

    # ── PANTHEON SIGNAL + RELAY ───────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "anyclaw",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[AnyClaw] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as r:
                return json.loads(r.read())
        except Exception as e:
            print(f"[AnyClaw] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    ac = AnyclawConnector()

    if len(sys.argv) < 2:
        print(json.dumps(ac.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(ac.health_check(), indent=2))

    elif cmd == "arch":
        print(json.dumps(ac.architecture_summary(), indent=2))

    elif cmd == "skills":
        result = ac.list_ecosystem_skills()
        for s in result["data"]["skills"]:
            print(f"  {s['name']}")

    elif cmd == "absorb" and len(sys.argv) > 2:
        result = ac.absorb_skill(sys.argv[2])
        print(json.dumps(result, indent=2))

    elif cmd == "absorb-all":
        print("Absorbing priority skills...")
        result = ac.absorb_pantheon_priority_skills()
        print(f"\nDone: {result['data']['ok']}/{result['data']['total']} absorbed")

    elif cmd == "cached":
        skills = ac.list_cached_skills()
        print(f"Cached skills ({len(skills)}): {', '.join(skills)}")

    else:
        print(f"Usage: {sys.argv[0]} [health|arch|skills|absorb <name>|absorb-all|cached]")
