"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              ABSORB PRIME — The Assimilation Engine                         ║
║              Pantheon Self-Evolution Core                                    ║
║                                                                              ║
║  Architecture ported from ghostwright/phantom (Apache 2.0)                  ║
║  src/evolution/ → Python translation + Pantheon integration                 ║
║                                                                              ║
║  Loop: Session ends → Gate (Haiku judge) → Reflection subprocess            ║
║        → VersionChange proposals → Invariant check → Apply delta            ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import uuid
import logging
import threading
import hashlib
from datetime import datetime, timezone
from typing import Optional, Literal
from dataclasses import dataclass, field, asdict
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
log = logging.getLogger("Pantheon.AbsorbPrime")

# ============================================================================
# PATHS
# ============================================================================

BASE_DIR       = Path(os.getenv("PANTHEON_BASE", Path.home() / "pantheon"))
CONSTITUTION   = BASE_DIR / "CONSTITUTION.md"       # The law above all laws (Ma'at)
MEMORY_DIR     = BASE_DIR / "memory"
EVOLUTION_LOG  = BASE_DIR / "evolution-log.jsonl"
GATE_LOG       = BASE_DIR / "evolution-gate-log.jsonl"
METRICS_FILE   = BASE_DIR / "evolution-metrics.json"
VERSIONS_FILE  = BASE_DIR / "evolution-versions.jsonl"

# Paths AbsorbPrime is NEVER allowed to modify
PROTECTED_PATHS = {
    "CONSTITUTION.md",
    "absorb_prime.py",       # self-modification forbidden
    "sentinel_prime.py",
    ".env",
}

# ============================================================================
# TYPES
# ============================================================================

ObservationType = Literal["correction", "preference", "error", "success", "tool_pattern", "domain_fact"]
ChangeType      = Literal["edit", "compact", "new", "delete"]
Outcome         = Literal["success", "failure", "partial", "abandoned"]

@dataclass
class SessionObservation:
    type:            ObservationType
    content:         str
    context:         str
    confidence:      float   # 0.0 – 1.0
    source_messages: list[str] = field(default_factory=list)

@dataclass
class SessionSummary:
    session_id:         str
    session_key:        str
    user_id:            str
    user_messages:      list[str]
    assistant_messages: list[str]
    tools_used:         list[str]
    files_tracked:      list[str]
    outcome:            Outcome
    cost_usd:           float
    started_at:         str
    ended_at:           str

@dataclass
class VersionChange:
    file:       str
    type:       ChangeType
    summary:    str
    rationale:  str
    session_ids: list[str] = field(default_factory=list)

@dataclass
class EvolutionResult:
    version:           int
    changes_applied:   list[VersionChange]
    changes_rejected:  list[dict]   # {"change": VersionChange, "reasons": [str]}

@dataclass
class GateDecision:
    fire:          bool
    source:        Literal["judge", "failsafe"]
    reason:        str
    cost_usd:      float = 0.0

@dataclass
class EvolutionMetrics:
    session_count:     int   = 0
    success_count:     int   = 0
    failure_count:     int   = 0
    evolution_count:   int   = 0
    last_session_at:   Optional[str] = None
    last_evolution_at: Optional[str] = None
    success_rate_7d:   float = 0.0

# ============================================================================
# METRICS
# ============================================================================

class MetricsStore:
    def __init__(self):
        self.path = METRICS_FILE
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def load(self) -> EvolutionMetrics:
        if self.path.exists():
            try:
                data = json.loads(self.path.read_text())
                return EvolutionMetrics(**data)
            except Exception:
                pass
        return EvolutionMetrics()

    def save(self, m: EvolutionMetrics):
        self.path.write_text(json.dumps(asdict(m), indent=2))

    def record_session(self, outcome: Outcome):
        m = self.load()
        m.session_count += 1
        m.last_session_at = datetime.now(timezone.utc).isoformat()
        if outcome == "success":
            m.success_count += 1
        elif outcome == "failure":
            m.failure_count += 1
        self.save(m)

    def record_evolution(self, n_changes: int):
        m = self.load()
        m.evolution_count += 1
        m.last_evolution_at = datetime.now(timezone.utc).isoformat()
        self.save(m)
        log.info(f"[AbsorbPrime] Evolution recorded — v{m.evolution_count}, {n_changes} changes")

    def snapshot(self) -> dict:
        m = self.load()
        return {"session_count": m.session_count, "success_rate_7d": m.success_rate_7d}

# ============================================================================
# GATE — Haiku judge decides if evolution is warranted
# ============================================================================

class EvolutionGate:
    """
    Ported from ghostwright/phantom src/evolution/gate.ts

    Asks Claude Haiku whether the session carries durable learning signal.
    Failsafe: any error → fire=True (never drop learning signal silently).
    """

    GATE_PROMPT = """You are the evolution gate for AbsorbPrime, the self-improvement engine of the Pantheon.

Your job: decide whether this session contains DURABLE LEARNING SIGNAL that warrants updating the Pantheon's memory or behavior files.

Fire = YES → the session revealed a correction, new preference, error pattern, or domain fact worth remembering.
Skip = NO  → small talk, routine tasks, no new signal.

Session data:
- Outcome: {outcome}
- Turn count: {turn_count}
- Duration: {duration_s}s
- Tools used: {tools}
- First user message: {first_user}
- Last user message: {last_user}
- Last agent message: {last_agent}

Respond with JSON only:
{{"fire": true/false, "reason": "one sentence"}}"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def decide(self, session: SessionSummary) -> GateDecision:
        if not self.api_key:
            return GateDecision(fire=True, source="failsafe", reason="no API key — defaulting to fire")

        try:
            import urllib.request as urlreq

            duration_s = 0
            try:
                t0 = datetime.fromisoformat(session.started_at)
                t1 = datetime.fromisoformat(session.ended_at)
                duration_s = int((t1 - t0).total_seconds())
            except Exception:
                pass

            prompt = self.GATE_PROMPT.format(
                outcome    = session.outcome,
                turn_count = len(session.user_messages),
                duration_s = duration_s,
                tools      = ", ".join(session.tools_used) or "(none)",
                first_user = (session.user_messages[0][:240] if session.user_messages else "(none)"),
                last_user  = (session.user_messages[-1][:240] if session.user_messages else "(none)"),
                last_agent = (session.assistant_messages[-1][:400] if session.assistant_messages else "(none)"),
            )

            payload = json.dumps({
                "model": "claude-haiku-4-5",
                "max_tokens": 200,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urlreq.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                method="POST"
            )
            req.add_header("x-api-key", self.api_key)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("content-type", "application/json")

            with urlreq.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                # Strip markdown code fences if present
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                result = json.loads(text)
                decision = GateDecision(
                    fire   = bool(result.get("fire", True)),
                    source = "judge",
                    reason = result.get("reason", ""),
                )
                self._log(session.session_id, decision)
                return decision

        except Exception as e:
            log.warning(f"[Gate] Haiku error — failsafe fire: {e}")
            decision = GateDecision(fire=True, source="failsafe", reason=str(e))
            self._log(session.session_id, decision)
            return decision

    def _log(self, session_id: str, decision: GateDecision):
        GATE_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "session_id": session_id,
            "fire": decision.fire,
            "source": decision.source,
            "reason": decision.reason,
        }
        with open(GATE_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

# ============================================================================
# INVARIANT CHECK — Ma'at's law: protected files never touched
# ============================================================================

class InvariantCheck:
    """
    Ported from ghostwright/phantom src/evolution/invariant-check.ts

    Validates proposed VersionChanges against the Pantheon's immutable law.
    Any change touching a protected path is rejected.
    Constitution.md hash is verified before and after — it must never change.
    """

    def __init__(self):
        self._constitution_hash = self._hash_constitution()

    def _hash_constitution(self) -> Optional[str]:
        if CONSTITUTION.exists():
            return hashlib.sha256(CONSTITUTION.read_bytes()).hexdigest()
        return None

    def check(self, changes: list[VersionChange]) -> tuple[list[VersionChange], list[dict]]:
        """Returns (approved, rejected) lists."""
        approved = []
        rejected = []

        # Verify constitution hasn't been touched externally
        current_hash = self._hash_constitution()
        if self._constitution_hash and current_hash != self._constitution_hash:
            log.critical("[InvariantCheck] CONSTITUTION HASH MISMATCH — aborting evolution cycle")
            return [], [{"change": c, "reasons": ["constitution tampered"]} for c in changes]

        for change in changes:
            reasons = []
            fname = Path(change.file).name

            if fname in PROTECTED_PATHS:
                reasons.append(f"{fname} is a protected path — modifications forbidden")
            if change.type == "delete" and fname.endswith(".py"):
                reasons.append("delete of .py files requires manual authorization")
            if ".." in change.file or change.file.startswith("/"):
                reasons.append("path traversal detected")

            if reasons:
                rejected.append({"change": change, "reasons": reasons})
                log.warning(f"[InvariantCheck] REJECTED {change.file}: {reasons}")
            else:
                approved.append(change)

        return approved, rejected

# ============================================================================
# REFLECTION ENGINE — proposes VersionChanges from session observations
# ============================================================================

class ReflectionEngine:
    """
    Ported from ghostwright/phantom src/evolution/reflection-subprocess.ts

    Analyzes a batch of sessions and proposes file edits that would make
    the Pantheon better at the Forgemaster's work.
    """

    REFLECTION_PROMPT = """You are AbsorbPrime — the self-evolution engine of the Pantheon.

Your job: analyze these Pantheon sessions and propose concrete file edits that would make the system better.

Sessions:
{sessions_json}

Current metrics:
{metrics_json}

Propose changes as a JSON array. Each change:
{{
  "file": "relative/path/to/file.md",
  "type": "edit" | "compact" | "new" | "delete",
  "summary": "what changes",
  "rationale": "why this makes the Pantheon better",
  "session_ids": ["id1", "id2"]
}}

Rules:
- Only propose changes to .md files and non-core .py files
- Never propose changes to CONSTITUTION.md, absorb_prime.py, sentinel_prime.py, or .env
- Changes must be specific and actionable — no vague improvements
- Maximum 5 changes per cycle
- If no meaningful changes warranted, return []

Respond with JSON array only."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    def reflect(self, sessions: list[SessionSummary], metrics: dict) -> list[VersionChange]:
        if not self.api_key or not sessions:
            return []

        try:
            import urllib.request as urlreq

            sessions_data = [asdict(s) for s in sessions]
            prompt = self.REFLECTION_PROMPT.format(
                sessions_json = json.dumps(sessions_data, indent=2)[:4000],
                metrics_json  = json.dumps(metrics, indent=2),
            )

            payload = json.dumps({
                "model": "claude-sonnet-4-5",
                "max_tokens": 1000,
                "messages": [{"role": "user", "content": prompt}]
            }).encode()

            req = urlreq.Request(
                "https://api.anthropic.com/v1/messages",
                data=payload,
                method="POST"
            )
            req.add_header("x-api-key", self.api_key)
            req.add_header("anthropic-version", "2023-06-01")
            req.add_header("content-type", "application/json")

            with urlreq.urlopen(req, timeout=60) as resp:
                data = json.loads(resp.read())
                text = data["content"][0]["text"].strip()
                if text.startswith("```"):
                    text = text.split("```")[1]
                    if text.startswith("json"):
                        text = text[4:]
                proposals = json.loads(text)
                changes = [VersionChange(**p) for p in proposals if isinstance(p, dict)]
                log.info(f"[Reflection] Proposed {len(changes)} changes")
                return changes

        except Exception as e:
            log.error(f"[Reflection] Error: {e}")
            return []

# ============================================================================
# EVOLUTION ENGINE — The Core Loop
# ============================================================================

class AbsorbPrime:
    """
    The Assimilation Engine.

    After every Pantheon session:
      1. Gate (Haiku) → does this session have learning signal?
      2. If yes → Reflection (Sonnet) → propose VersionChanges
      3. InvariantCheck → filter against Ma'at's law
      4. Apply approved changes → log version
      5. Update metrics

    Thread-safe via mutex — only one evolution cycle runs at a time.
    """

    def __init__(self):
        self.gate       = EvolutionGate()
        self.reflection = ReflectionEngine()
        self.invariant  = InvariantCheck()
        self.metrics    = MetricsStore()
        self._mutex     = threading.Lock()
        self._version   = self._load_version()
        self._pending:  list[SessionSummary] = []
        BASE_DIR.mkdir(parents=True, exist_ok=True)
        log.info(f"AbsorbPrime initialized ✅ | version: {self._version}")

    def _load_version(self) -> int:
        if VERSIONS_FILE.exists():
            lines = VERSIONS_FILE.read_text().strip().split("\n")
            if lines and lines[-1]:
                try:
                    return json.loads(lines[-1]).get("version", 0)
                except Exception:
                    pass
        return 0

    def after_session(self, session: SessionSummary) -> Optional[EvolutionResult]:
        """
        Call this after every Pantheon session ends.
        Non-blocking — acquires mutex, runs cycle, releases.
        Returns EvolutionResult if evolution fired, None if gated out.
        """
        self.metrics.record_session(session.outcome)

        if self._mutex.locked():
            log.debug("[AbsorbPrime] Cycle already in progress — queuing session")
            self._pending.append(session)
            return None

        with self._mutex:
            return self._run_cycle([session] + self._pending)

    def _run_cycle(self, sessions: list[SessionSummary]) -> Optional[EvolutionResult]:
        if not sessions:
            return None

        drain_id = str(uuid.uuid4())[:8]
        log.info(f"[AbsorbPrime] Cycle {drain_id} — {len(sessions)} sessions")

        # Phase 1: Gate
        primary = sessions[0]
        gate_decision = self.gate.decide(primary)
        log.info(f"[Gate] fire={gate_decision.fire} | {gate_decision.reason}")

        if not gate_decision.fire:
            self._log_entry(drain_id, sessions, "skip", "gated_out", 0, [])
            return None

        # Phase 2: Reflection
        metrics_snap = self.metrics.snapshot()
        proposed = self.reflection.reflect(sessions, metrics_snap)

        if not proposed:
            self._log_entry(drain_id, sessions, "reflect", "no_changes", 0, [])
            return None

        # Phase 3: Invariant check (Ma'at)
        approved, rejected = self.invariant.check(proposed)

        # Phase 4: Apply approved changes
        applied = []
        for change in approved:
            if self._apply_change(change):
                applied.append(change)

        # Phase 5: Version bump + metrics
        if applied:
            self._version += 1
            self._write_version(applied, sessions)
            self.metrics.record_evolution(len(applied))

        result = EvolutionResult(
            version          = self._version,
            changes_applied  = applied,
            changes_rejected = rejected,
        )

        self._log_entry(drain_id, sessions, "reflect", "completed", len(applied), applied)
        self._pending.clear()

        log.info(f"[AbsorbPrime] Cycle complete — v{self._version} | applied={len(applied)} | rejected={len(rejected)}")
        return result

    def _apply_change(self, change: VersionChange) -> bool:
        """Apply a single VersionChange to the filesystem."""
        try:
            target = BASE_DIR / change.file

            if change.type == "new":
                target.parent.mkdir(parents=True, exist_ok=True)
                if not target.exists():
                    target.write_text(f"# {change.file}\n\n{change.summary}\n")
                    log.info(f"[Apply] NEW {change.file}")
                    return True

            elif change.type in ("edit", "compact"):
                # Reflection engine proposes the SUMMARY of what to change.
                # Actual content editing happens via a follow-up Sonnet call
                # or manual application — we log the intent here.
                target.parent.mkdir(parents=True, exist_ok=True)
                annotation = (
                    f"\n\n<!-- AbsorbPrime v{self._version} | {datetime.now(timezone.utc).date()} "
                    f"| {change.summary} -->\n"
                )
                if target.exists():
                    content = target.read_text()
                    target.write_text(content + annotation)
                log.info(f"[Apply] EDIT {change.file}: {change.summary}")
                return True

            elif change.type == "delete":
                if target.exists():
                    target.unlink()
                    log.info(f"[Apply] DELETE {change.file}")
                    return True

        except Exception as e:
            log.error(f"[Apply] Failed {change.file}: {e}")

        return False

    def _write_version(self, changes: list[VersionChange], sessions: list[SessionSummary]):
        VERSIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "version":   self._version,
            "parent":    self._version - 1,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "changes":   [asdict(c) for c in changes],
            "metrics":   self.metrics.snapshot(),
        }
        with open(VERSIONS_FILE, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _log_entry(self, drain_id, sessions, tier, status, n_applied, applied):
        EVOLUTION_LOG.parent.mkdir(parents=True, exist_ok=True)
        entry = {
            "ts":              datetime.now(timezone.utc).isoformat(),
            "drain_id":        drain_id,
            "version":         self._version,
            "session_ids":     [s.session_id for s in sessions],
            "tier":            tier,
            "status":          status,
            "changes_applied": n_applied,
            "details":         [asdict(c) for c in applied],
        }
        with open(EVOLUTION_LOG, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def get_status(self) -> str:
        m = self.metrics.load()
        lines = [
            "🧬 *AbsorbPrime — Assimilation Engine*",
            f"  Version:        v{self._version}",
            f"  Sessions:       {m.session_count}",
            f"  Evolutions:     {m.evolution_count}",
            f"  Success rate:   {m.success_rate_7d:.1%}",
            f"  Last evolution: {m.last_evolution_at or 'never'}",
        ]
        return "\n".join(lines)


# ============================================================================
# STANDALONE TEST
# ============================================================================

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

    engine = AbsorbPrime()

    # Simulate a session
    session = SessionSummary(
        session_id         = str(uuid.uuid4()),
        session_key        = "test-session-001",
        user_id            = "forgemaster",
        user_messages      = ["Add Solana to OpenTrade", "Fork ghostwright/phantom"],
        assistant_messages = ["SolanaClient built and pushed.", "phantom forked and analyzed."],
        tools_used         = ["github_api", "bash"],
        files_tracked      = ["solana_client.py", "absorb_prime.py"],
        outcome            = "success",
        cost_usd           = 0.02,
        started_at         = datetime.now(timezone.utc).isoformat(),
        ended_at           = datetime.now(timezone.utc).isoformat(),
    )

    print("\n=== STATUS ===")
    print(engine.get_status())

    print("\n=== RUNNING CYCLE ===")
    result = engine.after_session(session)
    if result:
        print(f"Version: {result.version}")
        print(f"Applied: {len(result.changes_applied)}")
        print(f"Rejected: {len(result.changes_rejected)}")
    else:
        print("Gated out — no evolution this cycle")

    print("\n=== STATUS AFTER ===")
    print(engine.get_status())
