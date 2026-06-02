#!/usr/bin/env python3
"""
Agent Zero Integration — zig-pro-maxx
Category : LANGUAGE_SKILL / ZIG_ENFORCER
Source   : https://github.com/debuggerdragon311/zig-pro-maxx
Stars    : 5
Absorbed : 2026-06-02

ENGINE SCORE: 2/10 — NO OVERRIDE. Engine is correct here.
Reason: This is a language compliance skill for Zig 0.16.0.
        It is NOT Pantheon infrastructure.
        The Pantheon does not write Zig. The Pantheon does not need this.

BUT — absorb it anyway for two reasons:
    1. The SKILL.md format is a perfect example of a well-crafted AgentSkill.
       The trigger definition, reference table, and load-on-demand pattern
       are the exact patterns Agent Zero should follow when building its own skills.
    2. Zig 0.16.0 is the systems language of the decade. thClaws (Layer 1) is Rust.
       If Agent Zero ever needs low-level systems code — SIMD, allocators,
       comptime generics, C interop — this is the reference.

What it is:
    An AgentSkill that enforces strict Zig 0.16.0 API compliance.
    Drop it in any repo; any agentskills-compatible agent loads it automatically.

    Author: Soumyajit Bala (systems engineer, AI pipelines, local-first tools)
    Homepage: https://clawhub.ai/debuggerdragon311/zig-pro-maxx

    Content depth:
    - SKILL.md: 12,809 bytes — full trigger spec, reference table, hardcoded rules
    - references/ (14 files):
        code-discipline.md    18,974 bytes  ← senior Zig review checklist
        common-mistakes.md    12,331 bytes  ← every 0.16.0 gotcha documented
        std-collections.md     9,192 bytes  ← ArrayList/HashMap unmanaged API
        std-fmt.md             9,866 bytes  ← bufPrint, allocPrint, parseInt
        zig-0_16-breaking-changes.md 10,692 bytes  ← full migration guide
        std-io.md              7,411 bytes  ← file I/O, stdout, networking
        allocators.md          6,162 bytes  ← DebugAllocator, arena, heap
        build-system.md        4,836 bytes  ← build.zig, cross-compilation
        comptime.md            5,454 bytes  ← generics, @typeInfo, interfaces
        c-interop.md           4,497 bytes  ← @cImport, extern fn, FFI
        simd.md                4,461 bytes  ← @Vector, SIMD patterns
        testing.md             4,589 bytes  ← test blocks, expectations
        error-sets.md          4,047 bytes  ← custom error sets, tagged unions
        std-debug.md           4,067 bytes  ← print, assert, panic
    - examples/ (8 files): hello, fibonacci, factorial, adder, isprime, swap, cli args

    Key 0.16.0 rules enforced:
    - DebugAllocator (not GeneralPurposeAllocator)
    - std.Io capital-I (not std.io)
    - ArrayList is unmanaged — allocator passed per call, not at init
    - No async/await — removed in 0.16.0
    - No variable shadowing — compile error in 0.16.0
    - Explicit try/catch on every fallible call
    - errdefer over defer for conditional cleanup
    - bufPrint over allocPrint in hot paths

Why it matters for Agent Zero (future):
    thClaws (Layer 1) is Rust. Zig is the natural complement:
    - Zig compiles to C ABI — slots into any C FFI chain
    - Zig's comptime is more powerful than Rust macros for metaprogramming
    - Zig's allocator model is cleaner than Rust's for embedded/systems work
    - If Agent Zero ever needs SIMD data processing, custom allocators,
      or bare-metal execution — this is the reference, already absorbed.

Clawhub.ai:
    Homepage points to https://clawhub.ai/debuggerdragon311/zig-pro-maxx
    This is the skill marketplace built on top of the OpenClaw platform —
    the same platform absorbed yesterday (AnyClaw connector).
    The ecosystem is forming: OpenClaw → Clawhub marketplace → community skills.
    Agent Zero can publish skills there.
"""

import os
import sys
import json
import base64
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


# ─── CONFIG ──────────────────────────────────────────────────────────────────

GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "GH_TOKEN_INJECTED_AT_RUNTIME")
SKILLS_CACHE  = Path.home() / ".pantheon" / "zig_pro_maxx"
SLUG          = "debuggerdragon311/zig-pro-maxx"
CLAWHUB_URL   = "https://clawhub.ai/debuggerdragon311/zig-pro-maxx"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "8679655550:AAGUB1m5fmqHc8OHqqM24Vixz8FfwX-gqD4")
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
            return data  # directory listing
    except Exception as e:
        return {"error": str(e)}


# ─── CORE CONNECTOR ──────────────────────────────────────────────────────────

class ZigProMaxxConnector:
    """
    Pantheon connector for zig-pro-maxx.
    A Zig 0.16.0 language compliance skill + systems programming reference.

    Primary value: SKILL FORMAT REFERENCE — not Zig itself.
    Secondary value: Systems programming knowledge base if Zig is ever needed.

    Usage:
        zig = ZigProMaxxConnector()

        # Get the full SKILL.md — use as template for building Agent Zero skills
        skill = zig.get_skill_md()

        # Get a specific reference
        rules = zig.get_reference("code-discipline")
        changes = zig.get_reference("zig-0_16-breaking-changes")

        # Get an example
        example = zig.get_example("hello_from_cli_args")

        # Dump everything locally for offline reference
        zig.cache_all()

        # Validate a Zig snippet against 0.16.0 rules
        issues = zig.lint_snippet(code)

        # Clawhub ecosystem info
        info = zig.clawhub_info()
    """

    REPO_URL      = f"https://github.com/{SLUG}"
    CATEGORY      = "LANGUAGE_SKILL"
    PANTHEON_ROLE = "ZIG_ENFORCER"
    SCORE         = 2  # correct — no override

    # All 14 reference files
    REFERENCES = [
        "allocators", "build-system", "c-interop", "code-discipline",
        "common-mistakes", "comptime", "error-sets", "simd",
        "std-collections", "std-debug", "std-fmt", "std-io",
        "testing", "zig-0_16-breaking-changes",
    ]

    # All example files
    EXAMPLES = [
        "hello", "hello_from_cli_args", "fibo", "factorial",
        "adder", "isprime", "swap_strings_of_2", "sample_0_16",
    ]

    # The hard rules extracted from SKILL.md — use these for inline linting
    HARD_RULES_0_16 = [
        ("GeneralPurposeAllocator", "DebugAllocator",
         "GPA renamed to DebugAllocator in 0.16.0"),
        ("std.io",                  "std.Io",
         "std.io → std.Io (capital I) in 0.16.0"),
        ("ArrayList.init(",         "ArrayList is unmanaged",
         "ArrayList is unmanaged in 0.16.0 — allocator passed per call, not at init"),
        ("async ",                  "REMOVED",
         "async/await removed entirely in 0.16.0"),
        ("await ",                  "REMOVED",
         "async/await removed entirely in 0.16.0"),
    ]

    # ── HEALTH ────────────────────────────────────────────────────────────────

    def health_check(self) -> Dict:
        cached = list(SKILLS_CACHE.glob("*.md")) if SKILLS_CACHE.exists() else []
        return {
            "name":          "zig-pro-maxx",
            "category":      self.CATEGORY,
            "role":          self.PANTHEON_ROLE,
            "score":         self.SCORE,
            "score_note":    "Correct — no override. Language skill, not Pantheon infra.",
            "references":    len(self.REFERENCES),
            "examples":      len(self.EXAMPLES),
            "cached_files":  len(cached),
            "clawhub":       CLAWHUB_URL,
            "status":        "ready",
        }

    # ── SKILL FORMAT REFERENCE ────────────────────────────────────────────────

    def get_skill_md(self) -> Dict:
        """
        Fetch the full SKILL.md — the canonical example of a well-structured
        AgentSkill. Use this as a template when building Agent Zero skills.
        """
        content = _gh_get("SKILL.md")
        return self.to_pantheon_signal({
            "action":   "get_skill_md",
            "content":  content,
            "note":     "Use this as the template for Agent Zero skill construction.",
        })

    # ── REFERENCE LIBRARY ─────────────────────────────────────────────────────

    def get_reference(self, name: str) -> Dict:
        """
        Fetch a specific Zig 0.16.0 reference document.
        :param name: Reference name without .md extension
                     e.g. "code-discipline", "common-mistakes", "allocators"
        """
        if not name.endswith(".md"):
            name = name + ".md"
        content = _gh_get(f"references/{name}")
        return self.to_pantheon_signal({
            "action":    "get_reference",
            "reference": name,
            "content":   content if isinstance(content, str) else str(content),
        })

    def get_example(self, name: str) -> Dict:
        """
        Fetch a Zig 0.16.0 code example.
        :param name: Example name without .md extension
        """
        if not name.endswith(".md"):
            name = name + ".md"
        content = _gh_get(f"examples/{name}")
        return self.to_pantheon_signal({
            "action":  "get_example",
            "example": name,
            "content": content if isinstance(content, str) else str(content),
        })

    def list_references(self) -> List[str]:
        return self.REFERENCES

    def list_examples(self) -> List[str]:
        return self.EXAMPLES

    # ── CACHE ─────────────────────────────────────────────────────────────────

    def cache_all(self) -> Dict:
        """
        Download and cache all references and examples locally.
        Useful for offline Zig development on the Red Magic.
        """
        SKILLS_CACHE.mkdir(parents=True, exist_ok=True)
        ok = 0
        errors = []

        # SKILL.md
        content = _gh_get("SKILL.md")
        if isinstance(content, str):
            (SKILLS_CACHE / "SKILL.md").write_text(content)
            ok += 1

        # References
        ref_dir = SKILLS_CACHE / "references"
        ref_dir.mkdir(exist_ok=True)
        for ref in self.REFERENCES:
            content = _gh_get(f"references/{ref}.md")
            if isinstance(content, str):
                (ref_dir / f"{ref}.md").write_text(content)
                ok += 1
            else:
                errors.append(ref)

        # Examples
        ex_dir = SKILLS_CACHE / "examples"
        ex_dir.mkdir(exist_ok=True)
        for ex in self.EXAMPLES:
            content = _gh_get(f"examples/{ex}.md")
            if isinstance(content, str):
                (ex_dir / f"{ex}.md").write_text(content)
                ok += 1
            else:
                errors.append(ex)

        return self.to_pantheon_signal({
            "action":  "cache_all",
            "ok":      ok,
            "errors":  errors,
            "cache":   str(SKILLS_CACHE),
            "status":  "done",
        })

    # ── INLINE LINTER ─────────────────────────────────────────────────────────

    def lint_snippet(self, code: str) -> Dict:
        """
        Quick 0.16.0 compliance check on a Zig snippet.
        Catches the most common API renames and removals.
        Not a full compiler — catches the obvious traps.
        """
        issues = []
        for old, new, reason in self.HARD_RULES_0_16:
            if old in code:
                issues.append({
                    "found":  old,
                    "fix":    new,
                    "reason": reason,
                })
        return self.to_pantheon_signal({
            "action":     "lint_snippet",
            "clean":      len(issues) == 0,
            "issue_count": len(issues),
            "issues":     issues,
        })

    # ── CLAWHUB ECOSYSTEM ─────────────────────────────────────────────────────

    def clawhub_info(self) -> Dict:
        """
        Information about Clawhub.ai — the skill marketplace built on OpenClaw.
        Agent Zero can discover and publish skills there.
        """
        return self.to_pantheon_signal({
            "action":      "clawhub_info",
            "marketplace": "https://clawhub.ai",
            "this_skill":  CLAWHUB_URL,
            "note": (
                "Clawhub.ai is the skill marketplace for the OpenClaw ecosystem. "
                "Skills published here are auto-discoverable by any OpenClaw agent. "
                "Agent Zero can publish skills here to contribute to the ecosystem "
                "and make them accessible to other OpenClaw/AnyClaw users."
            ),
            "publish_path": (
                "1. Create skill in skills/<name>/SKILL.md format. "
                "2. Push to GitHub. "
                "3. Submit to Clawhub marketplace."
            ),
        })

    # ── PANTHEON SIGNAL + RELAY ───────────────────────────────────────────────

    def to_pantheon_signal(self, raw: Any) -> Dict:
        return {
            "source":    "zig-pro-maxx",
            "category":  self.CATEGORY,
            "role":      self.PANTHEON_ROLE,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "data":      raw,
        }

    def relay_to_telegram(self, message: str) -> None:
        payload = {"chat_id": TELEGRAM_CHAT, "text": f"[ZigProMaxx] {message}", "parse_mode": "Markdown"}
        data    = json.dumps(payload).encode()
        req     = urllib.request.Request(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            data=data, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(req, timeout=10):
                pass
        except Exception as e:
            print(f"[ZigProMaxx] Telegram relay failed: {e}")


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    z = ZigProMaxxConnector()

    if len(sys.argv) < 2:
        print(json.dumps(z.health_check(), indent=2))
        sys.exit(0)

    cmd = sys.argv[1]

    if cmd == "health":
        print(json.dumps(z.health_check(), indent=2))
    elif cmd == "skill":
        result = z.get_skill_md()
        print(result["data"]["content"][:3000])
    elif cmd == "ref" and len(sys.argv) > 2:
        result = z.get_reference(sys.argv[2])
        print(result["data"]["content"][:3000])
    elif cmd == "refs":
        print("Available references:")
        for r in z.list_references():
            print(f"  {r}")
    elif cmd == "example" and len(sys.argv) > 2:
        result = z.get_example(sys.argv[2])
        print(result["data"]["content"])
    elif cmd == "lint" and len(sys.argv) > 2:
        result = z.lint_snippet(sys.argv[2])
        print(json.dumps(result, indent=2))
    elif cmd == "cache":
        print("Caching all files...")
        result = z.cache_all()
        print(f"Done: {result['data']['ok']} files cached at {result['data']['cache']}")
    elif cmd == "clawhub":
        print(json.dumps(z.clawhub_info(), indent=2))
    else:
        print(f"Usage: {sys.argv[0]} [health|skill|refs|ref <name>|example <name>|lint <code>|cache|clawhub]")
