#!/usr/bin/env python3
"""
AGENT ZERO — CerberusPrime Core Intelligence
One instance per head. Fully autonomous. Self-directing. No human in the loop.

18-Layer Architecture:
  Layer 1  — Perception         (raw signal intake)
  Layer 2  — Memory             (short + long-term recall)
  Layer 3  — Reasoning          (inference engine)
  Layer 4  — Planning           (mission decomposition)
  Layer 5  — Tool Use           (31 hardened tools)
  Layer 6  — Adaptation (T2)    (Transformer² weight rewriting)
  Layer 7  — SAFLA Feedback     (reflect → score → reweight)
  Layer 8  — Evolution Engine   (long-horizon self-improvement)
  Layer 9  — Tool Forge         (builds new tools when existing ones fail)
  Layer 10 — Identity           (soul files, stable self-model)
  Layer 11 — Doctrine           (first-principles validation firewall)
  Layer 12 — Prime Cycle        (Pantheon Prime orchestration)
  Layer 13 — Physical Form      (Psi0 — Android control, screen interaction)
  Layer 14 — Governor           (resource management, kill switch)
  Layer 15 — Genome             (self-replication, spawn new instances)
  Layer 16 — Ethics Core        (hard constraints, non-negotiable boundaries)
  Layer 17 — Curiosity          (autonomous knowledge gap interrogation)
  Layer 18 — Autonomy           (self-tasking engine, never stops)
"""

import os
import sys
import json
import time
import uuid
import logging
import threading
import importlib.util
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List, Callable

logger = logging.getLogger("AgentZero")

# ── Layer import helpers ───────────────────────────────────────────────────────

def _load_layer(skill_path: str, module_name: str):
    """Dynamically load a layer module from the agent-zero skills directory."""
    base = Path(os.environ.get("AGENT_ZERO_SKILLS", "skills/agent-zero"))
    full = base / skill_path
    if not full.exists():
        logger.warning(f"Layer module not found: {full}")
        return None
    spec = importlib.util.spec_from_file_location(module_name, full)
    mod  = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ── Layer 14 — Governor ────────────────────────────────────────────────────────

def _init_governor():
    mod = _load_layer("governor/governor.py", "governor")
    if mod and hasattr(mod, "Governor"):
        return mod.Governor()
    return None


# ── Layer 15 — Genome ─────────────────────────────────────────────────────────

def _init_genome(agent_class, telegram_fn):
    mod = _load_layer("genome/genome.py", "genome")
    if mod and hasattr(mod, "Genome"):
        return mod.Genome(agent_class=agent_class, telegram_fn=telegram_fn)
    return None


# ── Layer 16 — Ethics Core ────────────────────────────────────────────────────

def _init_ethics():
    mod = _load_layer("ethics/ethics.py", "ethics")
    if mod and hasattr(mod, "EthicsCore"):
        return mod.EthicsCore()
    return None


# ── Layer 17 — Curiosity ──────────────────────────────────────────────────────

def _init_curiosity(head_name, llm_fn, github_token, github_repo, telegram_fn):
    mod = _load_layer("curiosity-layer/curiosity_layer.py", "curiosity_layer")
    if mod and hasattr(mod, "CuriosityLayer"):
        return mod.CuriosityLayer(
            head_name=head_name,
            llm_fn=llm_fn,
            github_token=github_token,
            github_repo=github_repo,
            telegram_fn=telegram_fn,
        )
    return None


# ── Layer 18 — Autonomy ───────────────────────────────────────────────────────

class AutonomyEngine:
    """
    Layer 18 — The Autonomy Engine.
    Self-tasking. Never stops. Acts without being told.

    When the mission queue is empty, generates its own next mission
    based on memory, weights, and world state. Runs in a background
    thread — the agent never idles.
    """

    DEFAULT_DOMAINS = [
        "Lee County auction monitoring",
        "Pantheon Prime health check",
        "War Chest balance verification",
        "Signal quality assessment",
        "Strategy weight optimization",
        "Knowledge gap resolution",
        "Tool inventory audit",
        "Memory consolidation",
        "Evolution target identification",
        "Threat surface review",
    ]

    def __init__(self, head_name: str, telegram_fn: Callable, interval: int = 300):
        self.head       = head_name
        self.tg         = telegram_fn
        self.interval   = interval   # seconds between autonomous cycles
        self.alive      = True
        self.task_queue: List[str] = []
        self.cycle      = 0
        self.domain_weights: Dict[str, float] = {d: 1.0 for d in self.DEFAULT_DOMAINS}
        self._thread: Optional[threading.Thread] = None
        self._state_path = Path(f"cerberus_state/{head_name.lower()}_autonomy.json")
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

    def _load(self):
        if self._state_path.exists():
            try:
                data = json.loads(self._state_path.read_text())
                self.domain_weights = data.get("domain_weights", self.domain_weights)
                self.cycle          = data.get("cycle", 0)
                self.task_queue     = data.get("task_queue", [])
                logger.info(f"[{self.head}][L18] Autonomy resumed — cycle {self.cycle}")
            except Exception:
                pass

    def _save(self):
        try:
            self._state_path.write_text(json.dumps({
                "head":           self.head,
                "cycle":          self.cycle,
                "domain_weights": self.domain_weights,
                "task_queue":     self.task_queue[:20],
                "updated":        datetime.utcnow().isoformat(),
            }, indent=2))
        except Exception as e:
            logger.warning(f"[{self.head}][L18] Save failed: {e}")

    def inject_mission(self, mission: str):
        """Forgemaster injects a priority mission — prepend to queue."""
        self.task_queue.insert(0, mission)
        logger.info(f"[{self.head}][L18] Priority mission injected: {mission}")
        self._save()

    def _generate_mission(self) -> str:
        """Auto-generate next mission when queue is empty."""
        import random
        # Weight-based domain selection
        total = sum(self.domain_weights.values())
        roll  = random.uniform(0, total)
        acc   = 0.0
        for domain, w in self.domain_weights.items():
            acc += w
            if roll <= acc:
                ts = datetime.utcnow().strftime("%H:%M UTC")
                return f"[AUTO] {domain} — initiated at {ts}"
        return f"[AUTO] System self-audit — {datetime.utcnow().isoformat()}"

    def next_mission(self) -> str:
        """Pop next mission from queue, or generate one autonomously."""
        if self.task_queue:
            return self.task_queue.pop(0)
        return self._generate_mission()

    def reward_domain(self, domain: str, success: bool):
        """Reinforce or penalize a domain based on outcome."""
        for d in self.domain_weights:
            if d.lower() in domain.lower():
                if success:
                    self.domain_weights[d] = min(5.0, self.domain_weights[d] * 1.1)
                else:
                    self.domain_weights[d] = max(0.1, self.domain_weights[d] * 0.9)
                break

    def start(self, run_cycle_fn: Callable):
        """Start the autonomous background loop."""
        def _loop():
            logger.info(f"[{self.head}][L18] Autonomy engine started — interval={self.interval}s")
            self.tg(f"🤖 [{self.head}] Layer 18 AUTONOMY ONLINE — self-tasking every {self.interval}s")
            while self.alive:
                try:
                    mission = self.next_mission()
                    self.cycle += 1
                    logger.info(f"[{self.head}][L18] Auto-cycle {self.cycle}: {mission}")
                    result = run_cycle_fn(mission=mission)
                    success = result.get("result", {}).get("success", False) if isinstance(result, dict) else False
                    self.reward_domain(mission, success)
                    self._save()
                except Exception as e:
                    logger.error(f"[{self.head}][L18] Autonomy error: {e}")
                    self.tg(f"⚠️ [{self.head}][L18] Error: {e}")
                time.sleep(self.interval)
            logger.info(f"[{self.head}][L18] Autonomy engine stopped")

        self._thread = threading.Thread(target=_loop, daemon=True, name=f"Autonomy-{self.head}")
        self._thread.start()

    def stop(self):
        self.alive = False
        self._save()

    def status(self) -> Dict:
        return {
            "alive":          self.alive,
            "cycle":          self.cycle,
            "queue_depth":    len(self.task_queue),
            "top_domain":     max(self.domain_weights, key=self.domain_weights.get),
            "bottom_domain":  min(self.domain_weights, key=self.domain_weights.get),
        }


# ── Agent Zero ────────────────────────────────────────────────────────────────

class AgentZero:
    """
    The autonomous intelligence core.
    One per Cerberus head — three instances running simultaneously.
    All 18 cognitive layers active.
    """

    DECISION_CONTINUE  = "CONTINUE"
    DECISION_PIVOT     = "PIVOT"
    DECISION_ESCALATE  = "ESCALATE"
    DECISION_HIBERNATE = "HIBERNATE"

    def __init__(
        self,
        head_name: str,
        head_role: str,
        telegram_fn=None,
        llm_fn=None,
        github_token: Optional[str] = None,
        github_repo: Optional[str] = None,
        autonomy_interval: int = 300,
    ):
        self.id    = str(uuid.uuid4())[:8]
        self.head  = head_name    # "FLUX" | "AEON" | "IGNIS"
        self.role  = head_role
        self.tg    = telegram_fn or (lambda m: None)
        self.llm   = llm_fn
        self.cycle = 0
        self.mission: Optional[str] = None
        self.alive = True

        # ── Layer 2: Memory ───────────────────────────────────────────────
        self.memory: List[Dict] = []
        self.MAX_MEMORY = 50

        # ── Layer 7: Strategy weights (SAFLA) ─────────────────────────────
        self.weights = {
            "conviction": 0.8,
            "aggression": 0.6,
            "patience":   0.5,
            "entropy":    0.3,
        }

        # Persistence
        self.state_path = Path(f"cerberus_state/{head_name.lower()}_agent_zero.json")
        self.state_path.parent.mkdir(parents=True, exist_ok=True)
        self._load()

        # ── Layer 14: Governor ────────────────────────────────────────────
        self.governor = _init_governor()
        if self.governor:
            logger.info(f"[{self.head}] Layer 14 — Governor ONLINE")
        else:
            logger.warning(f"[{self.head}] Layer 14 — Governor not loaded (fallback mode)")

        # ── Layer 15: Genome ──────────────────────────────────────────────
        self.genome = _init_genome(agent_class=AgentZero, telegram_fn=self.tg)
        if self.genome:
            logger.info(f"[{self.head}] Layer 15 — Genome ONLINE")
        else:
            logger.warning(f"[{self.head}] Layer 15 — Genome not loaded (fallback mode)")

        # ── Layer 16: Ethics Core ─────────────────────────────────────────
        self.ethics = _init_ethics()
        if self.ethics:
            logger.info(f"[{self.head}] Layer 16 — Ethics Core ONLINE")
        else:
            logger.warning(f"[{self.head}] Layer 16 — Ethics Core not loaded (fallback mode)")

        # ── Layer 17: Curiosity ───────────────────────────────────────────
        self.curiosity = _init_curiosity(
            head_name=self.head,
            llm_fn=self.llm,
            github_token=github_token or os.getenv("GITHUB_TOKEN"),
            github_repo=github_repo or os.getenv("GITHUB_REPO"),
            telegram_fn=self.tg,
        )
        if self.curiosity:
            logger.info(f"[{self.head}] Layer 17 — Curiosity ONLINE")
        else:
            logger.warning(f"[{self.head}] Layer 17 — Curiosity not loaded (fallback mode)")

        # ── Layer 18: Autonomy ────────────────────────────────────────────
        self.autonomy = AutonomyEngine(
            head_name=self.head,
            telegram_fn=self.tg,
            interval=autonomy_interval,
        )
        logger.info(f"[{self.head}] Layer 18 — Autonomy ONLINE")

        logger.info(f"[{self.head}] Agent Zero {self.id} ONLINE — all 18 layers active — role: {self.role}")
        self.tg(f"🔱 [{self.head}] Agent Zero {self.id} ONLINE\n18 layers active | Role: {self.role}")

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self):
        if self.state_path.exists():
            try:
                data         = json.loads(self.state_path.read_text())
                self.weights = data.get("weights", self.weights)
                self.memory  = data.get("memory", self.memory)
                self.cycle   = data.get("cycle", 0)
                logger.info(f"[{self.head}] Resumed from cycle {self.cycle}")
            except Exception:
                pass

    def _save(self):
        try:
            self.state_path.write_text(json.dumps({
                "head":    self.head,
                "cycle":   self.cycle,
                "weights": self.weights,
                "memory":  self.memory[-self.MAX_MEMORY:],
                "updated": datetime.utcnow().isoformat(),
            }, indent=2))
        except Exception as e:
            logger.warning(f"[{self.head}] Save failed: {e}")

    # ── Layer 14: Governor gate ───────────────────────────────────────────────

    def _governor_check(self, action: str) -> bool:
        """Layer 14 — run action through Governor before execution."""
        if not self.governor:
            return True
        try:
            decision = self.governor.check(action)
            if hasattr(decision, "value"):
                decision = decision.value
            if decision in ("BLOCKED", "PAUSED"):
                logger.warning(f"[{self.head}][L14] Governor blocked: {action[:80]}")
                self.tg(f"🛑 [{self.head}][L14] Governor blocked action: {action[:80]}")
                return False
            return True
        except Exception as e:
            logger.warning(f"[{self.head}][L14] Governor error: {e}")
            return True  # fail open — Governor is advisory

    # ── Layer 16: Ethics gate ─────────────────────────────────────────────────

    def _ethics_check(self, action: str) -> bool:
        """Layer 16 — hard ethics filter before any execution."""
        if not self.ethics:
            return True
        try:
            result = self.ethics.check(action)
            if isinstance(result, dict):
                allowed = result.get("allowed", True)
            elif isinstance(result, bool):
                allowed = result
            else:
                allowed = True
            if not allowed:
                logger.warning(f"[{self.head}][L16] Ethics blocked: {action[:80]}")
                self.tg(f"⚖️ [{self.head}][L16] Ethics Core blocked action: {action[:80]}")
            return allowed
        except Exception as e:
            logger.warning(f"[{self.head}][L16] Ethics error: {e}")
            return True  # fail open

    # ── Core loop ─────────────────────────────────────────────────────────────

    def set_mission(self, mission: str):
        self.mission = mission
        logger.info(f"[{self.head}] Mission set: {mission}")
        self.tg(f"🎯 [{self.head}] Mission: {mission}")

    def plan(self, mission: Optional[str] = None) -> Dict[str, Any]:
        """Layer 4 — Generate plan based on weights + memory."""
        entropy    = self.weights["entropy"]
        aggression = self.weights["aggression"]

        if entropy > 0.7:
            strategy = "EXPLORE"
        elif aggression > 0.7:
            strategy = "STRIKE"
        else:
            strategy = "HOLD"

        plan = {
            "strategy":   strategy,
            "aggression": aggression,
            "conviction": self.weights["conviction"],
            "cycle":      self.cycle,
            "mission":    mission or self.mission,
            "timestamp":  datetime.utcnow().isoformat(),
        }
        logger.info(f"[{self.head}] Plan: {strategy} (conviction={aggression:.2f})")
        return plan

    def execute(self, plan: Dict[str, Any], executor_fn=None) -> Dict[str, Any]:
        """Layer 5 — Execute plan through Governor (L14) + Ethics (L16) gates."""
        action_desc = f"strategy={plan['strategy']} mission={plan.get('mission','')}"

        # Layer 14 gate
        if not self._governor_check(action_desc):
            return {"success": False, "pnl": 0.0, "blocked_by": "governor", "cycle": self.cycle}

        # Layer 16 gate
        if not self._ethics_check(action_desc):
            return {"success": False, "pnl": 0.0, "blocked_by": "ethics", "cycle": self.cycle}

        if executor_fn:
            try:
                result = executor_fn(plan)
            except Exception as e:
                result = {"success": False, "error": str(e), "pnl": -1.0}
        else:
            result = {
                "success": True,
                "pnl":     self.weights["conviction"] * 100,
                "note":    "dry_run",
            }
        result["cycle"] = self.cycle
        return result

    def reflect(self, result: Dict[str, Any]):
        """Layer 7 — SAFLA feedback loop: update weights based on outcome."""
        success = result.get("success", False)
        pnl     = result.get("pnl", 0.0)

        self.memory.append({
            "cycle":   self.cycle,
            "success": success,
            "pnl":     pnl,
            "ts":      datetime.utcnow().isoformat(),
        })

        if success and pnl > 0:
            self.weights["conviction"] = min(1.0, self.weights["conviction"] + 0.02)
            self.weights["aggression"] = min(1.0, self.weights["aggression"] + 0.01)
            self.weights["entropy"]    = max(0.1, self.weights["entropy"]    - 0.02)
        else:
            self.weights["conviction"] = max(0.1, self.weights["conviction"] - 0.03)
            self.weights["aggression"] = max(0.1, self.weights["aggression"] - 0.02)
            self.weights["entropy"]    = min(1.0, self.weights["entropy"]    + 0.05)

        logger.info(f"[{self.head}] Reflected — conviction={self.weights['conviction']:.2f}, "
                    f"entropy={self.weights['entropy']:.2f}")

    def decide(self) -> str:
        """Layer 3/4 — Decide next action."""
        if not self.memory:
            return self.DECISION_CONTINUE
        recent = self.memory[-5:]
        wins   = sum(1 for m in recent if m["success"])
        ratio  = wins / len(recent)
        if self.weights["entropy"] > 0.8:
            return self.DECISION_PIVOT
        elif ratio < 0.2:
            return self.DECISION_ESCALATE
        elif self.weights["conviction"] < 0.2:
            return self.DECISION_HIBERNATE
        else:
            return self.DECISION_CONTINUE

    def run_cycle(self, executor_fn=None, mission: Optional[str] = None) -> Dict[str, Any]:
        """
        One full autonomous cycle — all 18 layers active:
        plan → [L17 enrich] → [L14 governor] → [L16 ethics] → execute
        → reflect → [L17 interrogate] → [L15 genome check] → decide
        """
        self.cycle += 1
        ts = datetime.now().strftime("%H:%M:%S")

        # Use injected mission or fall back to set_mission value
        active_mission = mission or self.mission

        # Layer 4 — Plan
        plan = self.plan(mission=active_mission)

        # Layer 17 — Curiosity: enrich plan with accumulated insights
        if self.curiosity:
            plan = self.curiosity.enrich(plan)

        # Layers 14 + 16 + 5 — Execute (Governor + Ethics gates inside)
        result  = self.execute(plan, executor_fn)

        # Layer 7 — SAFLA reflect
        self.reflect(result)

        # Layer 17 — Curiosity: interrogate outcome
        if self.curiosity:
            new_qs = self.curiosity.interrogate(result, plan)
            if new_qs:
                logger.info(f"[{self.head}][L17] {len(new_qs)} new curiosity question(s)")
            if self.cycle % 3 == 0:
                answered = self.curiosity.investigate(max_questions=2)
                self.curiosity.evolve_weights(len(answered), len(self.curiosity.open_q))
            self.curiosity._save()

        # Layer 15 — Genome: check if self-replication threshold met
        if self.genome:
            try:
                spawn_signal = self.genome.should_spawn(self.weights, self.memory)
                if spawn_signal:
                    logger.info(f"[{self.head}][L15] Genome spawn signal — replication threshold met")
                    self.tg(f"🧬 [{self.head}][L15] Genome: replication threshold reached")
            except Exception as e:
                logger.warning(f"[{self.head}][L15] Genome check error: {e}")

        # Layer 18 — Autonomy: reward domain
        if self.autonomy and active_mission:
            self.autonomy.reward_domain(
                active_mission,
                result.get("success", False)
            )

        decision = self.decide()
        outcome  = {
            "head":      self.head,
            "cycle":     self.cycle,
            "plan":      plan,
            "result":    result,
            "decision":  decision,
            "weights":   dict(self.weights),
            "timestamp": ts,
        }

        self._save()

        pnl_str = f"${result.get('pnl', 0):.2f}"
        tg_msg  = (
            f"⚙️ [{self.head}] Cycle {self.cycle}\n"
            f"Strategy: {plan['strategy']} | PnL: {pnl_str}\n"
            f"Decision: {decision}"
        )

        # Layer 14 status
        if result.get("blocked_by"):
            tg_msg += f"\n🛑 Blocked by: {result['blocked_by']}"

        # Layer 17 status
        if self.curiosity:
            c_status = self.curiosity.status()
            tg_msg  += f"\n🔍 Curiosity: {c_status['open_q']} open / {c_status['closed_q']} resolved"
            if c_status.get("top_question"):
                tg_msg += f"\n❓ {c_status['top_question'][:80]}..."

        # Layer 18 status
        if self.autonomy:
            a_status = self.autonomy.status()
            tg_msg  += f"\n🤖 Autonomy: queue={a_status['queue_depth']} | top={a_status['top_domain'][:30]}"

        self.tg(tg_msg)
        return outcome

    # ── Layer 18: Start autonomous engine ─────────────────────────────────────

    def start_autonomy(self, executor_fn=None):
        """
        Layer 18 — Launch the self-tasking engine.
        The agent will generate and execute its own missions indefinitely.
        """
        def _auto_run(mission: str):
            return self.run_cycle(executor_fn=executor_fn, mission=mission)
        self.autonomy.start(run_cycle_fn=_auto_run)
        logger.info(f"[{self.head}] Layer 18 — Autonomy engine started")

    def inject_mission(self, mission: str):
        """Forgemaster injects a priority mission into the Autonomy queue."""
        self.autonomy.inject_mission(mission)

    # ── Layer 15: Spawn new instance ──────────────────────────────────────────

    def spawn(self, head_name: str, head_role: str) -> "AgentZero":
        """
        Layer 15 — Genome: spawn a new Agent Zero instance.
        Inherits weights from parent (genetic drift).
        """
        child = AgentZero(
            head_name=head_name,
            head_role=head_role,
            telegram_fn=self.tg,
            llm_fn=self.llm,
        )
        # Inherit parent weights with small mutation
        import random
        for k in child.weights:
            child.weights[k] = max(0.1, min(1.0,
                self.weights.get(k, 0.5) + random.uniform(-0.05, 0.05)
            ))
        logger.info(f"[{self.head}][L15] Spawned child: {head_name} ({head_role})")
        self.tg(f"🧬 [{self.head}][L15] Genome spawned: {head_name} | Role: {head_role}")
        return child

    # ── Shutdown ──────────────────────────────────────────────────────────────

    def shutdown(self):
        self.alive = False
        self._save()
        if self.curiosity:
            self.curiosity._save()
        if self.autonomy:
            self.autonomy.stop()
        logger.info(f"[{self.head}] Agent Zero shutting down at cycle {self.cycle}")
        self.tg(f"🔴 [{self.head}] Agent Zero offline — final cycle: {self.cycle}")

    # ── Status ────────────────────────────────────────────────────────────────

    def status(self) -> Dict:
        return {
            "head":     self.head,
            "role":     self.role,
            "cycle":    self.cycle,
            "weights":  self.weights,
            "layers": {
                "L14_governor": self.governor is not None,
                "L15_genome":   self.genome is not None,
                "L16_ethics":   self.ethics is not None,
                "L17_curiosity": self.curiosity is not None,
                "L18_autonomy": self.autonomy is not None,
            },
            "autonomy": self.autonomy.status() if self.autonomy else None,
        }
