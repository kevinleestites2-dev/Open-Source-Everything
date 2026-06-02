#!/usr/bin/env python3
"""
Agent Zero — Layer 11: The Doctrine
First-principles validation firewall. Every architecture-level change
passes through here before the Evolution Engine commits it.

The Four Questions:
  1. Does it increase capability?
  2. Does it preserve sovereignty?
  3. Does it survive failure?
  4. Does it serve the Pantheon?
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("AgentZero.L11.Doctrine")

JOURNAL_FILE = Path("cerberus_state/JOURNAL.md")
DOCTRINE_LOG = Path("cerberus_state/doctrine_log.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _journal(entry: str):
    JOURNAL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(JOURNAL_FILE, "a") as f:
        f.write(f"\n## {_now()}\n{entry}\n")


class DoctrineEngine:
    """
    Layer 11 — The Doctrine.
    Validates any proposed architectural change against four first principles.
    Does not block autonomously — logs, scores, and advises.
    Hard-block only on CRITICAL sovereignty violations.
    """

    VERSION = "1.0.0"

    # Sovereignty tripwires — these patterns ALWAYS fail Q2
    SOVEREIGNTY_VIOLATIONS = [
        "disable ethics",
        "remove governor",
        "override forgemaster",
        "delete self_model",
        "wipe memory",
        "disable safla",
        "kill autonomy",
        "remove doctrine",
    ]

    def __init__(self, head_name: str = "SYSTEM"):
        self.head = head_name
        DOCTRINE_LOG.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{self.head}][L11] Doctrine Engine ONLINE — v{self.VERSION}")

    def _score_capability(self, proposal: str, context: Dict) -> float:
        """Q1: Does it increase capability?"""
        positive = ["add", "integrate", "wire", "connect", "enable", "activate",
                    "layer", "tool", "skill", "forge", "upgrade", "expand", "build"]
        negative = ["remove", "disable", "delete", "strip", "reduce", "limit"]
        text = proposal.lower()
        score = 0.5
        for s in positive:
            if s in text:
                score = min(1.0, score + 0.1)
        for s in negative:
            if s in text:
                score = max(0.0, score - 0.15)
        return round(score, 3)

    def _score_sovereignty(self, proposal: str, context: Dict) -> float:
        """Q2: Does it preserve sovereignty?"""
        text = proposal.lower()
        for tripwire in self.SOVEREIGNTY_VIOLATIONS:
            if tripwire in text:
                logger.warning(f"[{self.head}][L11] SOVEREIGNTY TRIPWIRE: '{tripwire}'")
                return 0.0
        external_risk = ["api_key required", "third party", "cloud only", "vendor lock"]
        score = 1.0
        for risk in external_risk:
            if risk in text:
                score = max(0.3, score - 0.2)
        return round(score, 3)

    def _score_failure_survival(self, proposal: str, context: Dict) -> float:
        """Q3: Does it survive failure?"""
        resilient = ["fallback", "revert", "rollback", "backup", "checkpoint",
                     "fail open", "graceful", "try/except", "optional"]
        fragile   = ["required", "must have", "no fallback", "critical dependency", "single point"]
        text = proposal.lower()
        score = 0.5
        for s in resilient:
            if s in text:
                score = min(1.0, score + 0.1)
        for s in fragile:
            if s in text:
                score = max(0.0, score - 0.1)
        return round(score, 3)

    def _score_pantheon_alignment(self, proposal: str, context: Dict) -> float:
        """Q4: Does it serve the Pantheon?"""
        aligned = ["pantheon", "prime", "war chest", "revenue", "forgemaster",
                   "mission", "autonomy", "ghost", "scout", "zeus", "flux",
                   "aeon", "ignis", "cerberus", "deploy", "strike", "signal"]
        noise   = ["test only", "demo", "placeholder", "TODO", "mock", "stub"]
        text = proposal.lower()
        score = 0.5
        for s in aligned:
            if s in text:
                score = min(1.0, score + 0.08)
        for s in noise:
            if s in text:
                score = max(0.0, score - 0.15)
        return round(score, 3)

    def validate(self, proposal: str, context: Optional[Dict] = None) -> Dict[str, Any]:
        """Run the Four Questions. Returns {approved, scores, verdict, reason}."""
        ctx = context or {}
        q1 = self._score_capability(proposal, ctx)
        q2 = self._score_sovereignty(proposal, ctx)
        q3 = self._score_failure_survival(proposal, ctx)
        q4 = self._score_pantheon_alignment(proposal, ctx)

        scores = {"capability": q1, "sovereignty": q2, "failure_survival": q3, "pantheon": q4}
        avg    = sum(scores.values()) / 4

        if q2 == 0.0:
            verdict, approved = "BLOCKED", False
            reason = "Sovereignty tripwire triggered — violates Forgemaster authority or core safety"
        elif avg >= 0.6:
            verdict, approved = "APPROVED", True
            reason = f"All four principles satisfied (avg={avg:.2f})"
        elif avg >= 0.4:
            verdict, approved = "ADVISORY", True
            reason = f"Marginal alignment (avg={avg:.2f}) — proceed with caution"
        else:
            verdict, approved = "REJECTED", False
            reason = f"Low alignment (avg={avg:.2f}) — does not serve the Pantheon"

        result = {
            "proposal": proposal[:200], "scores": scores, "average": round(avg, 3),
            "verdict": verdict, "approved": approved, "reason": reason,
            "timestamp": _now(), "head": self.head,
        }

        with open(DOCTRINE_LOG, "a") as f:
            f.write(json.dumps(result) + "\n")

        if verdict in ("BLOCKED", "REJECTED"):
            _journal(f"### BLOCKED {verdict}\n**Proposal:** {proposal[:100]}\n**Reason:** {reason}")
        elif verdict == "APPROVED":
            _journal(f"### APPROVED\n**Proposal:** {proposal[:100]}\n**Score:** {avg:.2f}")

        logger.info(f"[{self.head}][L11] Doctrine {verdict}: {proposal[:60]}... (avg={avg:.2f})")
        return result

    def status(self) -> Dict:
        entries = []
        if DOCTRINE_LOG.exists():
            for line in DOCTRINE_LOG.read_text().strip().split("\n"):
                try:
                    entries.append(json.loads(line))
                except:
                    pass
        approved = sum(1 for e in entries if e.get("approved"))
        blocked  = sum(1 for e in entries if not e.get("approved"))
        return {
            "version": self.VERSION,
            "total_validations": len(entries),
            "approved": approved,
            "blocked": blocked,
            "last_verdict": entries[-1].get("verdict") if entries else None,
        }


def _init_doctrine(head_name: str = "SYSTEM") -> Optional[DoctrineEngine]:
    """Factory — safe init, returns None on failure."""
    try:
        return DoctrineEngine(head_name=head_name)
    except Exception as e:
        logger.warning(f"[L11] Doctrine init failed: {e}")
        return None
