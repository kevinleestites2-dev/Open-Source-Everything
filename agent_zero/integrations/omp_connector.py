#!/usr/bin/env python3
"""
Agent Zero Integration — oh-my-pi (omp)
Category : CODING_AGENT_SURFACE
Source   : https://github.com/can1357/oh-my-pi
Stars    : 10,010 | Forks: 826
Language : TypeScript + Rust (~27K lines Rust core)
Updated  : 2026-06-03 (active — updated minutes ago)
Absorbed : 2026-06-02

ENGINE SCORE: 10/10
Reason: "The most capable agent surface that ships." This is not a framework — it
        is a fully deployed, production-grade AI coding agent with:
        - 40+ LLM providers (Claude, GPT, Gemini, Ollama, all others)
        - 32 built-in tools (bash, browser, SSH, GitHub, SQLite, AST, memory, image gen...)
        - 13 LSP operations (language server protocol — IDE-level code intelligence)
        - 27 DAP operations (debugger adapter protocol — runtime debugging)
        - Hash-anchored edits (surgical, rollback-safe code rewriting — Phantom-grade)
        - Subagent parallelism via IRC coordination channel
        - Persistent memory system (retain/recall/reflect)
        - Skills system (.omp/skills/) — semantic compression, system prompts, extensible
        - Commands system (.omp/commands/) — fix-issues, release, review-prs, triage
        - Rust core for performance-critical ops (native text, grep, image processing)
        - MCP native (Model Context Protocol client built in)
        - Own AGENTS.md discipline — context-aware, package-level documentation
        10/10: Ships today. 10K stars. No mocks. No placeholders. This is the terminal
        AI agent that gives Agent Zero a pair of hands in every shell on every machine.

What it is:
    omp (oh-my-pi) — a fork of pi-mono by @mariozechner. A full-stack AI coding agent
    that runs in the terminal. One install command. Works on macOS, Linux, Windows.
    
    Unlike Claude Code (which requires subscription), omp is open, self-hosted, and
    connects to any provider — including the Ollama bridge already in TOOLS.md.
    
    It is the agent shell Agent Zero needs to execute code autonomously on:
    - The Nexus (1TB laptop, when acquired)
    - Any SSH target (ssh.ts — remote execution built in)
    - The Red Magic (via Termux — bun is installable on Android ARM)
    - GitHub Actions (Dockerfile ships in repo)

    ARCHITECTURE:
    ┌──────────────────────────────────────────────────────┐
    │  omp CLI (TypeScript + Bun)                          │
    │  ┌────────────────┐  ┌────────────────────────────┐ │
    │  │ packages/ai    │  │ packages/agent             │ │
    │  │ 40+ providers  │  │ Tool calling + state mgmt  │ │
    │  └────────────────┘  └────────────────────────────┘ │
    │  ┌────────────────┐  ┌────────────────────────────┐ │
    │  │ packages/tui   │  │ packages/coding-agent      │ │
    │  │ Terminal UI    │  │ Main CLI (PRIMARY FOCUS)   │ │
    │  └────────────────┘  └────────────────────────────┘ │
    │  ┌────────────────────────────────────────────────┐ │
    │  │ crates/pi-natives (Rust ~27K lines)            │ │
    │  │ Performance: text ops, grep, image processing  │ │
    │  └────────────────────────────────────────────────┘ │
    └──────────────────────────────────────────────────────┘

    TOOL INVENTORY (32 built-in tools):
    - bash.ts          (44,582b) — full shell execution, PTY, interactive
    - read.ts          (91,574b) — file reading, chunking, encoding detection
    - search.ts        (49,088b) — BM25 + semantic search across codebase
    - gh.ts           (106,291b) — GitHub: issues, PRs, commits, reviews, search
    - fetch.ts         (48,832b) — HTTP fetch with browser fallback
    - browser.ts       (11,064b) — Puppeteer headless browser
    - ast-edit.ts      (23,881b) — AST-level surgical code edits (hash-anchored)
    - ast-grep.ts      (17,626b) — AST pattern matching (structural search)
    - debug.ts         (38,172b) — DAP debugger (27 ops: breakpoints, watch, eval)
    - image-gen.ts     (45,557b) — Image generation (multiple providers)
    - sqlite-reader.ts (26,835b) — SQLite database inspection
    - ssh.ts           (10,654b) — Remote SSH execution
    - irc.ts           (9,216b)  — Subagent coordination channel
    - job.ts           (17,193b) — Parallel subagent spawning
    - memory-retain.ts (2,946b)  — Persist facts to memory
    - memory-recall.ts (3,538b)  — Query persistent memory
    - memory-reflect.ts(3,270b)  — Synthesize memory across sessions
    - todo-write.ts    (28,630b) — Task/todo management
    - eval.ts          (20,468b) — Code evaluation (Python, JS, etc.)
    - find.ts          (20,969b) — File search with filtering
    - ask.ts           (28,870b) — Human-in-the-loop clarification
    - approval.ts      (5,775b)  — Permission gates
    - checkpoint.ts    (4,462b)  — Session state snapshots
    - review.ts        (8,683b)  — Code review generation
    - conflict-detect.ts(24,828b)— Merge conflict detection
    - path-utils.ts    (35,055b) — Path resolution and manipulation
    - report-tool-issue.ts(21,469b)— Tool error reporting pipeline

    SKILLS SYSTEM (.omp/skills/):
    - semantic-compression — LLM-aware token reduction for prompts
    - system-prompts — RFC 2119 prompt engineering conventions
    - Extensible: drop SKILL.md in .omp/skills/<name>/

    COMMANDS SYSTEM (.omp/commands/):
    - fix-issues   — diagnose + fix GitHub issues in parallel worktrees
    - release      — automated release pipeline
    - review-prs   — PR review with subagent parallelism
    - triage       — issue triage workflow
    - Extensible: drop <name>.md in .omp/commands/

    HASH-ANCHORED EDITS:
    The killer differentiator. Every edit is anchored by a hash of the surrounding
    context (package: @oh-my-pi/hashline). If the file changes between tool calls,
    the hash mismatch is caught before the edit applies. Zero silent corruption.
    Same principle as Phantom's constitution.md — immutable anchors for safe rewriting.

    SUBAGENT PARALLELISM (irc.ts + job.ts):
    Subagents coordinate via an IRC-style channel. Multiple agents work on different
    files/issues simultaneously. When two tasks touch the same file, they lock via IRC
    before editing. This is the multi-agent coordination primitive the Pantheon needs.

    LSP INTEGRATION (13 ops):
    Language Server Protocol — the same intelligence that powers VS Code:
    - go-to-definition, find-references, hover docs, code actions
    - rename symbol (project-wide), format document
    - diagnostics (errors/warnings without running the code)
    - completion suggestions
    All available to the agent mid-task. No IDE required.

PANTHEON INTEGRATION:

    AGENT ZERO (PRIMARY):
    - omp IS Agent Zero's execution surface in the terminal
    - Drop omp on every machine (Nexus, Red Magic, SSH targets, GitHub Actions)
    - Agent Zero routes coding/execution tasks to omp subagents
    - omp's memory system (retain/recall/reflect) extends Agent Zero's memory layer
    - omp's skills system maps directly to Agent Zero's absorption architecture

    DEXCLAW:
    - omp + DexClaw = AI-native terminal with full coding agent brain
    - DexClaw is the terminal emulator; omp is the agent running inside it
    - Together: type a goal → omp plans, edits, runs, debugs, deploys

    PHANTOM:
    - omp provides the execution harness; Phantom provides the self-evolution engine
    - omp edits code → Phantom's SAFLA validates the edit → rollback if regression
    - Phantom's hash-anchored rewriting + omp's hash-anchored edits = same primitive

    KELVINCLAW (Rust):
    - omp's Rust core (crates/pi-natives) is a Rust crate
    - KelvinClaw absorbs it as a native performance module
    - Sub-millisecond grep, text ops, image processing in the Pantheon's Rust layer

    OPENAGORA:
    - omp bash.ts → OpenAgora shell execution for strategy scripts
    - omp eval.ts → Python evaluation for alpha factor computation
    - omp sqlite-reader.ts → inspect OpenAgora's trade_memory.json equivalent
    - omp debug.ts (DAP) → debug OpenAgora's agora_engine.py with breakpoints

    GHOST PRIME / CONTENT PRIME:
    - omp browser.ts (Puppeteer) → headless browsing for GhostPrime social ops
    - omp fetch.ts → HTTP with browser fallback — beats basic aiohttp for anti-bot
    - omp image-gen.ts → ContentPrime asset generation

    SCOUT PRIME:
    - omp ast-grep.ts → structural code search (find all property data extractors)
    - omp search.ts (BM25 + semantic) → search scraped property databases
    - omp sqlite-reader.ts → inspect Scout's local property cache

    SSH TARGETS:
    - omp ssh.ts → Agent Zero executes on any remote machine by address
    - Pantheon node management: ZapiaPrime connects to every Prime's host via SSH
    - No tunnel required for SSH (unlike NexusClaw) — works over any network
"""

import os
import sys
import json
import subprocess
import shutil
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

REPO_URL       = "https://github.com/can1357/oh-my-pi"
NPM_PACKAGE    = "@oh-my-pi/pi-coding-agent"
INSTALL_CMD    = "bun install -g @oh-my-pi/pi-coding-agent"
INSTALL_CURL   = "curl -fsSL https://omp.sh/install | sh"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "TG_TOKEN_INJECTED_AT_RUNTIME")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "7135054241")

TOOLS_32 = {
    "bash":            {"file": "bash.ts",              "size": 44582,  "what": "Full shell execution, PTY, interactive sessions"},
    "read":            {"file": "read.ts",               "size": 91574,  "what": "File reading with chunking and encoding detection"},
    "search":          {"file": "search.ts",             "size": 49088,  "what": "BM25 + semantic codebase search"},
    "gh":              {"file": "gh.ts",                 "size": 106291, "what": "Full GitHub: issues, PRs, commits, reviews, search"},
    "fetch":           {"file": "fetch.ts",              "size": 48832,  "what": "HTTP fetch with browser fallback"},
    "browser":         {"file": "browser.ts",            "size": 11064,  "what": "Puppeteer headless browser automation"},
    "ast-edit":        {"file": "ast-edit.ts",           "size": 23881,  "what": "Hash-anchored AST-level surgical code edits"},
    "ast-grep":        {"file": "ast-grep.ts",           "size": 17626,  "what": "AST pattern matching (structural search)"},
    "debug":           {"file": "debug.ts",              "size": 38172,  "what": "DAP debugger — 27 ops: breakpoints, watch, eval"},
    "image-gen":       {"file": "image-gen.ts",          "size": 45557,  "what": "Image generation (multiple providers)"},
    "sqlite-reader":   {"file": "sqlite-reader.ts",      "size": 26835,  "what": "SQLite database inspection and query"},
    "ssh":             {"file": "ssh.ts",                "size": 10654,  "what": "Remote SSH execution on any host"},
    "irc":             {"file": "irc.ts",                "size": 9216,   "what": "Subagent coordination channel (parallel work)"},
    "job":             {"file": "job.ts",                "size": 17193,  "what": "Parallel subagent spawning and management"},
    "memory-retain":   {"file": "memory-retain.ts",      "size": 2946,   "what": "Persist facts to persistent memory"},
    "memory-recall":   {"file": "memory-recall.ts",      "size": 3538,   "what": "Query persistent memory across sessions"},
    "memory-reflect":  {"file": "memory-reflect.ts",     "size": 3270,   "what": "Synthesize and compress memory"},
    "todo-write":      {"file": "todo-write.ts",         "size": 28630,  "what": "Task and todo management"},
    "eval":            {"file": "eval.ts",               "size": 20468,  "what": "Code evaluation (Python, JS, shell)"},
    "find":            {"file": "find.ts",               "size": 20969,  "what": "File search with advanced filtering"},
    "ask":             {"file": "ask.ts",                "size": 28870,  "what": "Human-in-the-loop clarification gate"},
    "approval":        {"file": "approval.ts",           "size": 5775,   "what": "Permission gates for destructive actions"},
    "checkpoint":      {"file": "checkpoint.ts",         "size": 4462,   "what": "Session state snapshots"},
    "review":          {"file": "review.ts",             "size": 8683,   "what": "Code review generation"},
    "conflict-detect": {"file": "conflict-detect.ts",    "size": 24828,  "what": "Merge conflict detection and resolution"},
    "path-utils":      {"file": "path-utils.ts",         "size": 35055,  "what": "Path resolution and manipulation"},
    "archive-reader":  {"file": "archive-reader.ts",     "size": 9088,   "what": "ZIP/TAR archive inspection"},
    "report-tool-issue":{"file": "report-tool-issue.ts", "size": 21469,  "what": "Tool error reporting pipeline"},
    "ask":             {"file": "ask.ts",                "size": 28870,  "what": "Interactive Q&A with human"},
    "json-tree":       {"file": "json-tree.ts",          "size": 7528,   "what": "JSON structure visualization"},
    "render-mermaid":  {"file": "render-mermaid.ts",     "size": 2590,   "what": "Mermaid diagram rendering"},
    "eval-render":     {"file": "eval-render.ts",        "size": 25284,  "what": "Code eval result rendering"},
}

SKILLS = {
    "semantic-compression": "LLM-aware token reduction — aggressive grammar deletion, semantic payload preserved",
    "system-prompts":       "RFC 2119 prompt engineering — project tag conventions, dense imperative style",
}

COMMANDS = {
    "fix-issues": "Diagnose + fix GitHub issues in parallel worktrees with build artifact symlinks",
    "release":    "Automated release pipeline",
    "review-prs": "PR review with subagent parallelism",
    "triage":     "Issue triage workflow",
}

PROVIDERS_40_PLUS = [
    "Anthropic (Claude 3.5/3.7 Sonnet, Haiku, Opus)",
    "OpenAI (GPT-4o, o1, o3, o4-mini)",
    "Google (Gemini 1.5/2.0 Flash, Pro, Ultra)",
    "Ollama (local — already wired in TOOLS.md)",
    "Groq (llama3-70b, mixtral — free tier)",
    "Mistral, Cohere, DeepSeek, Qwen",
    "AWS Bedrock, Azure OpenAI",
    "HuggingFace Inference",
    "Perplexity, Together AI, Fireworks",
    "xAI (Grok), Meta Llama",
    "40+ total via unified provider interface",
]

PANTHEON_ROLES = {
    "Agent Zero":   "PRIMARY — omp IS Agent Zero's execution surface in the terminal",
    "DexClaw":      "Terminal emulator brain — DexClaw shell + omp agent = autonomous coding terminal",
    "Phantom":      "Complementary — omp executes, Phantom SAFLA validates and evolves",
    "KelvinClaw":   "Rust crate absorption — pi-natives crate for sub-ms text/grep ops",
    "OpenAgora":    "bash.ts + eval.ts + sqlite-reader.ts + debug.ts for strategy execution",
    "GhostPrime":   "browser.ts (Puppeteer) + fetch.ts for stealth social operations",
    "ScoutPrime":   "ast-grep.ts + search.ts (BM25) + sqlite-reader.ts for property data",
    "SSH Targets":  "ssh.ts — Agent Zero executes on Nexus, servers, any SSH host",
}


# ─── INSTALL LOGIC ───────────────────────────────────────────────────────────

def check_installed() -> bool:
    return shutil.which("omp") is not None

def install_omp(method: str = "bun") -> Dict:
    if check_installed():
        result = subprocess.run(["omp", "--version"], capture_output=True, text=True)
        return {"status": "already_installed", "version": result.stdout.strip()}
    if method == "curl":
        cmd = ["sh", "-c", INSTALL_CURL]
    else:
        cmd = ["bun", "install", "-g", NPM_PACKAGE]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0:
            return {"status": "installed", "method": method, "output": result.stdout[-500:]}
        return {"status": "failed", "stderr": result.stderr[-500:]}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def run_omp(args: List[str], cwd: Optional[str] = None, timeout: int = 300) -> Dict:
    if not check_installed():
        return {"error": "omp not installed. Run: bun install -g @oh-my-pi/pi-coding-agent"}
    try:
        result = subprocess.run(
            ["omp"] + args,
            capture_output=True, text=True,
            cwd=cwd or os.getcwd(),
            timeout=timeout
        )
        return {
            "returncode": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
        }
    except subprocess.TimeoutExpired:
        return {"error": f"omp timed out after {timeout}s"}
    except Exception as e:
        return {"error": str(e)}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class OmpConnector:
    """
    Pantheon connector for oh-my-pi (omp).
    10,010 stars. 826 forks. 40+ providers. 32 tools. 13 LSP. 27 DAP.
    TypeScript + ~27K lines Rust core. Ships today.

    Pantheon Role: CODING_AGENT_SURFACE

    This is Agent Zero's execution surface. DexClaw's brain. The terminal
    AI agent that gives the Pantheon autonomous coding/execution on every machine.

    Usage:
        omp = OmpConnector()
        print(omp.health_check())
        print(omp.install())
        print(omp.tool_info("bash"))
        print(omp.pantheon_roles())
        print(omp.agent_zero_integration())
        print(omp.dexclaw_integration())
        omp.run_task("Fix the KeyError in everos_bridge.py", cwd="/path/to/OpenAgora")
    """

    REPO_URL      = REPO_URL
    CATEGORY      = "CODING_AGENT_SURFACE"
    ROLE          = "TERMINAL_AI_AGENT"
    PANTHEON_ROLE = "CODING_AGENT_SURFACE / TERMINAL_AI_AGENT"
    SCORE         = 10
    STARS         = 10010
    FORKS         = 826
    TOOLS         = 32
    LSP_OPS       = 13
    DAP_OPS       = 27
    RUST_LINES    = 27000

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        installed = check_installed()
        version   = None
        if installed:
            r = subprocess.run(["omp", "--version"], capture_output=True, text=True)
            version = r.stdout.strip()
        return {
            "name":         "omp",
            "category":     self.CATEGORY,
            "role":         self.PANTHEON_ROLE,
            "score":        self.SCORE,
            "score_note":   "The most capable agent surface that ships. 40+ providers. 32 tools. 13 LSP. 27 DAP. Hash-anchored edits. Subagent parallelism. Rust core. Ships in one command.",
            "stars":        self.STARS,
            "forks":        self.FORKS,
            "tools":        self.TOOLS,
            "lsp_ops":      self.LSP_OPS,
            "dap_ops":      self.DAP_OPS,
            "rust_lines":   self.RUST_LINES,
            "providers":    "40+",
            "installed":    installed,
            "version":      version,
            "install_cmd":  INSTALL_CMD,
            "install_curl": INSTALL_CURL,
            "key_capabilities": [
                "32 built-in tools — bash, browser, SSH, GitHub, SQLite, AST, memory, image gen, debug",
                "Hash-anchored edits — zero silent corruption on code rewrites (Phantom-grade)",
                "Subagent parallelism — irc.ts coordination + job.ts spawning",
                "13 LSP operations — IDE-level code intelligence in the terminal",
                "27 DAP operations — runtime debugger (breakpoints, watch, eval) mid-task",
                "40+ LLM providers — Claude, GPT, Gemini, Ollama (already in TOOLS.md), Groq (free)",
                "Persistent memory — retain/recall/reflect across sessions",
                "Skills system (.omp/skills/) — semantic compression, extensible",
                "Commands system (.omp/commands/) — fix-issues, review-prs, release, triage",
                "SSH remote execution — Agent Zero controls any machine by address",
                "~27K lines Rust core — sub-millisecond text/grep/image ops",
                "One install: bun install -g @oh-my-pi/pi-coding-agent",
            ],
            "repo":   self.REPO_URL,
            "status": "production — ships today, actively maintained, updated minutes before absorption",
        }

    # ── INSTALL ───────────────────────────────────────────────────────────────

    def install(self, method: str = "bun") -> Dict:
        return self.to_pantheon_signal({
            "action": "install",
            "result": install_omp(method),
        })

    # ── TOOLS ─────────────────────────────────────────────────────────────────

    def tool_info(self, name: str) -> Dict:
        tool = TOOLS_32.get(name)
        if not tool:
            return {"error": f"Unknown tool: {name}. Available: {list(TOOLS_32.keys())}"}
        return self.to_pantheon_signal({
            "action": "tool_info",
            "name":   name,
            "info":   tool,
        })

    def tool_manifest(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "tool_manifest",
            "count":  len(TOOLS_32),
            "tools":  TOOLS_32,
        })

    # ── PANTHEON ──────────────────────────────────────────────────────────────

    def pantheon_roles(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "pantheon_roles",
            "roles":  PANTHEON_ROLES,
        })

    def agent_zero_integration(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "agent_zero_integration",
            "role":   "PRIMARY",
            "description": "omp IS Agent Zero's execution surface in the terminal",
            "how": [
                "1. Install omp on every Pantheon node (Nexus, Red Magic, SSH hosts)",
                "2. Agent Zero routes coding/execution tasks to omp via subprocess or SSH",
                "3. omp's memory system (retain/recall/reflect) extends Agent Zero's persistent memory",
                "4. omp's skills (.omp/skills/) map to Agent Zero's absorption layer",
                "5. omp's commands (.omp/commands/) become Agent Zero's autonomous workflows",
                "6. omp subagents (irc.ts + job.ts) run parallel Pantheon tasks",
            ],
            "immediate": [
                "Install omp on Red Magic Termux: bun install -g @oh-my-pi/pi-coding-agent",
                "Connect to Ollama bridge (already in TOOLS.md): set provider to ollama",
                "Run first task: omp 'Fix the KeyError in everos_bridge.py'",
            ],
        })

    def dexclaw_integration(self) -> Dict:
        return self.to_pantheon_signal({
            "action": "dexclaw_integration",
            "role":   "TERMINAL_BRAIN",
            "description": "DexClaw is the terminal emulator. omp is the agent running inside it.",
            "stack":  "DexClaw (proot Linux + SSH) → Termux shell → omp agent → 32 tools",
            "result": "Type a goal. omp plans, edits, runs, debugs, deploys. No human in the loop.",
            "providers_for_red_magic": [
                "Ollama (local, free — bridge URL in TOOLS.md)",
                "Groq (free tier: llama3-70b, mixtral — zero cost)",
                "Anthropic Claude (existing subscription)",
                "Any of 40+ providers via unified interface",
            ],
        })

    # ── TASK EXECUTION ────────────────────────────────────────────────────────

    def run_task(self, task: str, cwd: Optional[str] = None,
                 provider: Optional[str] = None, timeout: int = 300) -> Dict:
        args = []
        if provider:
            args += ["--provider", provider]
        args.append(task)
        result = run_omp(args, cwd=cwd, timeout=timeout)
        return self.to_pantheon_signal({
            "action": "run_task",
            "task":   task,
            "cwd":    cwd,
            "result": result,
        })

    def run_fix_issues(self, repo: Optional[str] = None,
                       issue_numbers: Optional[List[int]] = None,
                       timeout: int = 600) -> Dict:
        cmd = "/fix-issues"
        if issue_numbers:
            cmd += " " + " ".join(str(n) for n in issue_numbers)
        result = run_omp([cmd], timeout=timeout)
        return self.to_pantheon_signal({
            "action":  "run_fix_issues",
            "command": cmd,
            "result":  result,
        })

    # ── PROVIDERS ─────────────────────────────────────────────────────────────

    def provider_list(self) -> Dict:
        return self.to_pantheon_signal({
            "action":    "provider_list",
            "count":     "40+",
            "providers": PROVIDERS_40_PLUS,
            "free_tier": ["Ollama (local)", "Groq (llama3-70b, mixtral, gemma)"],
            "note":      "Ollama bridge URL already in TOOLS.md. Connect immediately.",
        })

    # ── SKILLS & COMMANDS ─────────────────────────────────────────────────────

    def skills(self) -> Dict:
        return self.to_pantheon_signal({
            "action":       "skills",
            "skills":       SKILLS,
            "skill_format": "SKILL.md in .omp/skills/<name>/",
            "note":         "Agent Zero absorption skills map 1:1 to omp skills. Extract and port.",
        })

    def commands(self) -> Dict:
        return self.to_pantheon_signal({
            "action":         "commands",
            "commands":       COMMANDS,
            "command_format": "<name>.md in .omp/commands/",
            "note":           "omp commands = Agent Zero autonomous workflows. Port fix-issues to Pantheon CI.",
        })

    # ── SIGNAL ────────────────────────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "omp",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    omp = OmpConnector()

    if len(sys.argv) < 2:
        print(json.dumps(omp.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(omp.health_check(), indent=2))
    elif cmd == "install":
        method = sys.argv[2] if len(sys.argv) > 2 else "bun"
        print(json.dumps(omp.install(method), indent=2))
    elif cmd == "tools":
        print(json.dumps(omp.tool_manifest(), indent=2))
    elif cmd == "tool" and len(sys.argv) > 2:
        print(json.dumps(omp.tool_info(sys.argv[2]), indent=2))
    elif cmd == "roles":
        print(json.dumps(omp.pantheon_roles(), indent=2))
    elif cmd == "agent-zero":
        print(json.dumps(omp.agent_zero_integration(), indent=2))
    elif cmd == "dexclaw":
        print(json.dumps(omp.dexclaw_integration(), indent=2))
    elif cmd == "providers":
        print(json.dumps(omp.provider_list(), indent=2))
    elif cmd == "skills":
        print(json.dumps(omp.skills(), indent=2))
    elif cmd == "commands":
        print(json.dumps(omp.commands(), indent=2))
    elif cmd == "run" and len(sys.argv) > 2:
        task     = sys.argv[2]
        provider = sys.argv[3] if len(sys.argv) > 3 else None
        print(json.dumps(omp.run_task(task, provider=provider), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|install|tools|tool <name>|roles|agent-zero|dexclaw|providers|skills|commands|run <task>]")
