#!/usr/bin/env python3
"""
Agent Zero — Layer 12: Prime Cycle
Pantheon Prime orchestration layer. Agent Zero becomes the conductor
of the entire fleet: GhostPrime, ScoutPrime, OpenAgora, ZeusPrime.

Flow:
  Agent Zero cycle result -> Prime Cycle router -> dispatch to Prime
  Prime result -> SAFLA reflect -> weight update -> next cycle
"""

import json
import logging
import threading
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Any, List, Optional

logger = logging.getLogger("AgentZero.L12.PrimeCycle")

CYCLE_LOG    = Path("cerberus_state/prime_cycle_log.jsonl")
DISPATCH_LOG = Path("cerberus_state/prime_dispatch_log.jsonl")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class PrimeCycleEngine:
    """
    Layer 12 — Prime Cycle.
    Routes Agent Zero decisions to the correct Pantheon Prime for execution.

    Strategy -> Prime routing:
      STRIKE  -> GhostPrime, ZeusPrime
      EXPLORE -> ScoutPrime, OpenAgora
      HOLD    -> NexusRelay (status check)
      PIVOT   -> ScoutPrime, GhostPrime
    """

    VERSION = "1.0.0"

    ROUTING_TABLE = {
        "STRIKE":  ["GhostPrime", "ZeusPrime"],
        "EXPLORE": ["ScoutPrime", "OpenAgora"],
        "HOLD":    ["NexusRelay"],
        "PIVOT":   ["ScoutPrime", "GhostPrime"],
    }

    def __init__(
        self,
        head_name: str,
        telegram_fn: Callable,
        github_token: Optional[str] = None,
        nexus_relay_url: Optional[str] = None,
        nexus_secret: Optional[str] = None,
    ):
        self.head         = head_name
        self.tg           = telegram_fn
        self.gh_token     = github_token
        self.nexus_url    = nexus_relay_url or "https://nexus-relay-production.up.railway.app"
        self.nexus_secret = nexus_secret or "pantheon_prime"
        self.lock         = threading.Lock()
        self.dispatch_count = 0
        self.success_count  = 0

        CYCLE_LOG.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"[{self.head}][L12] Prime Cycle Engine ONLINE — v{self.VERSION}")

    def _dispatch_ghost(self, plan: Dict) -> Dict:
        """Trigger GhostPrime via GitHub Actions workflow_dispatch."""
        if not self.gh_token:
            return {"prime": "GhostPrime", "success": False, "reason": "no_gh_token"}
        try:
            repo    = "kevinleestites2-dev/CloakPrime"
            url     = f"https://api.github.com/repos/{repo}/actions/workflows/ghost.yml/dispatches"
            payload = json.dumps({
                "ref": "main",
                "inputs": {"mission": plan.get("mission", "auto")}
            }).encode()
            req = urllib.request.Request(url, data=payload, method="POST", headers={
                "Authorization": f"token {self.gh_token}",
                "Content-Type":  "application/json",
                "User-Agent":    "AgentZero-L12",
            })
            with urllib.request.urlopen(req, timeout=10) as r:
                success = r.status == 204
            logger.info(f"[{self.head}][L12] GhostPrime: {'OK' if success else 'FAIL'}")
            return {"prime": "GhostPrime", "success": success, "action": "workflow_dispatch"}
        except Exception as e:
            logger.warning(f"[{self.head}][L12] GhostPrime error: {e}")
            return {"prime": "GhostPrime", "success": False, "error": str(e)}

    def _dispatch_nexus(self, plan: Dict) -> Dict:
        """Send heartbeat command to Nexus Relay."""
        try:
            command = {
                "action":   "agent_zero_cycle",
                "head":     self.head,
                "cycle":    plan.get("cycle", 0),
                "mission":  plan.get("mission", "status_check"),
                "strategy": plan.get("strategy", "HOLD"),
            }
            payload = json.dumps({"command": json.dumps(command)}).encode()
            req = urllib.request.Request(
                f"{self.nexus_url}/command",
                data=payload, method="POST",
                headers={
                    "Content-Type": "application/json",
                    "X-Secret":     self.nexus_secret,
                }
            )
            with urllib.request.urlopen(req, timeout=8) as r:
                result = json.load(r)
            cmd_id = result.get("_id", "unknown")
            logger.info(f"[{self.head}][L12] Nexus dispatch: cmd_id={cmd_id}")
            return {"prime": "NexusRelay", "success": True, "cmd_id": cmd_id}
        except Exception as e:
            logger.warning(f"[{self.head}][L12] Nexus error: {e}")
            return {"prime": "NexusRelay", "success": False, "error": str(e)}

    def route(self, plan: Dict, result: Dict) -> List[Dict]:
        """
        Route an Agent Zero cycle result to the appropriate Primes.
        Returns list of dispatch results.
        """
        strategy  = plan.get("strategy", "HOLD")
        targets   = self.ROUTING_TABLE.get(strategy, ["NexusRelay"])
        dispatches = []

        with self.lock:
            for prime in targets:
                self.dispatch_count += 1

                if prime == "GhostPrime":
                    dr = self._dispatch_ghost(plan)
                elif prime == "NexusRelay":
                    dr = self._dispatch_nexus(plan)
                else:
                    # Other Primes: Telegram signal only
                    dr = {
                        "prime": prime, "success": True,
                        "action": "telegram_signal",
                    }
                    self.tg(
                        f"SIGNAL -> {prime} | "
                        f"Strategy: {strategy} | "
                        f"Mission: {plan.get('mission','')[:60]}"
                    )

                if dr.get("success"):
                    self.success_count += 1

                dispatches.append(dr)

                log_entry = {
                    "ts": _now(), "head": self.head, "prime": prime,
                    "strategy": strategy, "cycle": plan.get("cycle", 0),
                    "success": dr.get("success", False),
                }
                with open(DISPATCH_LOG, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")

        return dispatches

    def status(self) -> Dict:
        return {
            "version":      self.VERSION,
            "dispatches":   self.dispatch_count,
            "successes":    self.success_count,
            "success_rate": round(self.success_count / max(1, self.dispatch_count), 3),
            "routing_table": self.ROUTING_TABLE,
        }


def _init_prime_cycle(
    head_name: str,
    telegram_fn: Callable,
    github_token: Optional[str] = None,
    nexus_relay_url: Optional[str] = None,
) -> Optional[PrimeCycleEngine]:
    """Factory — safe init."""
    try:
        return PrimeCycleEngine(
            head_name=head_name,
            telegram_fn=telegram_fn,
            github_token=github_token,
            nexus_relay_url=nexus_relay_url,
        )
    except Exception as e:
        logger.warning(f"[L12] Prime Cycle init failed: {e}")
        return None
