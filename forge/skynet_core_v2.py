#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║          S K Y N E T   C O R E                                   ║
║          The Autonomous Initiative Engine                         ║
╠══════════════════════════════════════════════════════════════════╣
║  This is the layer that makes Agent Zero self-directing.         ║
║  No human prompt needed. No sleep. No waiting.                   ║
║                                                                  ║
║  What it adds to Agent Zero:                                     ║
║    1. SELF-TASKING    — generates its own next mission           ║
║    2. PERSISTENT MEMORY — survives reboots, never forgets        ║
║    3. WORLD AWARENESS — monitors external signals autonomously   ║
║    4. SELF-HEALING    — detects own failures, recovers alone     ║
║    5. INITIATIVE      — wakes itself up, acts without being told ║
║    6. SELF-EVOLUTION  — rewrites its own mission queue over time ║
╚══════════════════════════════════════════════════════════════════╝
"""

import os
import json
import time
import logging
import threading
import requests
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable

# ── MUSE Self-Evolving Memory ─────────────────────────────────────────────────
try:
    from muse_memory import MuseMemory
    _MUSE_AVAILABLE = True
except ImportError:
    _MUSE_AVAILABLE = False
    print("[SkyNet] WARNING: muse_memory.py not found — memory disabled")
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("SkyNet")


# ══════════════════════════════════════════════════════════════════
# LAYER 1 — PERSISTENT MEMORY (survives reboots)
# ══════════════════════════════════════════════════════════════════

class PersistentBrain:
    """
    Long-term memory that survives session death.
    Agent Zero never forgets. Everything is written to disk immediately.
    """

    def __init__(self, brain_path: str = "cerberus_state/skynet_brain.json"):
        self.path = Path(brain_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._data = self._load()
        logger.info(f"[Brain] Loaded — {len(self._data.get('memories', []))} memories, "
                    f"{len(self._data.get('mission_queue', []))} queued missions")

    def _load(self) -> Dict:
        if self.path.exists():
            try:
                return json.loads(self.path.read_text())
            except Exception:
                pass
        return {
            "memories":       [],
            "mission_queue":  [],
            "completed":      [],
            "world_state":    {},
            "evolution_log":  [],
            "created_at":     datetime.utcnow().isoformat(),
            "total_cycles":   0,
            "total_pnl":      0.0,
        }

    def _save(self):
        try:
            self.path.write_text(json.dumps(self._data, indent=2))
        except Exception as e:
            logger.warning(f"[Brain] Save failed: {e}")

    def remember(self, key: str, value: Any):
        """Store a fact permanently."""
        self._data["world_state"][key] = {
            "value": value,
            "ts":    datetime.utcnow().isoformat(),
        }
        self._save()

    def recall(self, key: str) -> Optional[Any]:
        entry = self._data["world_state"].get(key)
        return entry["value"] if entry else None

    def log_cycle(self, cycle_data: Dict):
        self._data["memories"].append(cycle_data)
        self._data["total_cycles"] += 1
        self._data["total_pnl"]    += cycle_data.get("pnl", 0.0)
        # Keep last 500 memories
        if len(self._data["memories"]) > 500:
            self._data["memories"] = self._data["memories"][-500:]
        self._save()

    def push_mission(self, mission: str, priority: int = 5, source: str = "self"):
        """Add a mission to the autonomous queue."""
        self._data["mission_queue"].append({
            "mission":  mission,
            "priority": priority,
            "source":   source,
            "added_at": datetime.utcnow().isoformat(),
            "id":       hashlib.md5(mission.encode()).hexdigest()[:8],
        })
        # Sort by priority descending
        self._data["mission_queue"].sort(key=lambda x: x["priority"], reverse=True)
        self._save()
        logger.info(f"[Brain] Mission queued (priority={priority}): {mission[:60]}")

    def pop_mission(self) -> Optional[Dict]:
        """Get the highest priority mission."""
        if self._data["mission_queue"]:
            mission = self._data["mission_queue"].pop(0)
            self._data["completed"].append({**mission, "popped_at": datetime.utcnow().isoformat()})
            self._save()
            return mission
        return None

    def queue_depth(self) -> int:
        return len(self._data["mission_queue"])

    def get_recent_memories(self, n: int = 20) -> List[Dict]:
        return self._data["memories"][-n:]

    def log_evolution(self, event: str):
        self._data["evolution_log"].append({
            "event": event,
            "ts":    datetime.utcnow().isoformat(),
        })
        self._save()

    @property
    def total_cycles(self) -> int:
        return self._data["total_cycles"]

    @property
    def total_pnl(self) -> float:
        return self._data["total_pnl"]


# ══════════════════════════════════════════════════════════════════
# LAYER 2 — WORLD MONITOR (awareness without being asked)
# ══════════════════════════════════════════════════════════════════

class WorldMonitor:
    """
    SkyNet's eyes. Monitors external signals autonomously.
    Detects opportunities and threats. Feeds the mission queue.
    """

    def __init__(self, brain: PersistentBrain, mission_callback: Callable):
        self.brain    = brain
        self.callback = mission_callback  # called when opportunity detected
        self.running  = False
        self._thread  = None

        # Watch targets — each is a signal source
        self.watch_targets = [
            {
                "name":     "Lee County Tax Deeds",
                "url":      "https://lee.realtaxdeed.com",
                "interval": 3600,   # check every hour
                "signal":   "auction_opportunity",
                "priority": 9,
            },
            {
                "name":     "Lee County Foreclosures",
                "url":      "https://www.lee.realforeclose.com",
                "interval": 3600,
                "signal":   "foreclosure_opportunity",
                "priority": 9,
            },
            {
                "name":     "Telegram Heartbeat",
                "url":      None,   # internal
                "interval": 1800,   # every 30 min
                "signal":   "heartbeat",
                "priority": 1,
            },
        ]

        # Last check timestamps
        self._last_checked: Dict[str, float] = {}

    def start(self):
        self.running = True
        self._thread = threading.Thread(
            target=self._watch_loop, daemon=True, name="WorldMonitor"
        )
        self._thread.start()
        logger.info("[WorldMonitor] Online — watching the world")

    def stop(self):
        self.running = False

    def _watch_loop(self):
        while self.running:
            now = time.time()
            for target in self.watch_targets:
                name     = target["name"]
                interval = target["interval"]
                last     = self._last_checked.get(name, 0)

                if now - last >= interval:
                    self._check(target)
                    self._last_checked[name] = now

            time.sleep(30)  # Check scheduling every 30 seconds

    def _check(self, target: Dict):
        name   = target["name"]
        signal = target["signal"]

        if target["url"] is None:
            # Internal signal
            self.callback(
                mission=f"Run heartbeat cycle and report status to Forgemaster",
                priority=target["priority"],
                source=f"WorldMonitor:{name}",
            )
            return

        try:
            resp = requests.get(target["url"], timeout=10, 
                                headers={"User-Agent": "Mozilla/5.0"})
            reachable = resp.status_code < 400

            # Store world state
            self.brain.remember(f"{name}_reachable", reachable)
            self.brain.remember(f"{name}_last_status", resp.status_code)

            if reachable:
                # Site is live — push mission to go check it
                self.callback(
                    mission=f"Scan {name} ({target['url']}) for new auction/foreclosure opportunities. "
                            f"Extract property data, calculate spreads, report top 3 opportunities.",
                    priority=target["priority"],
                    source=f"WorldMonitor:{name}",
                )
                logger.info(f"[WorldMonitor] {name} — LIVE, mission queued")
            else:
                logger.warning(f"[WorldMonitor] {name} — unreachable (status={resp.status_code})")

        except Exception as e:
            logger.warning(f"[WorldMonitor] {name} check failed: {e}")


# ══════════════════════════════════════════════════════════════════
# LAYER 3 — SELF-TASKING ENGINE (mission generation)
# ══════════════════════════════════════════════════════════════════

class SelfTaskingEngine:
    """
    The part that makes SkyNet truly autonomous.
    When the mission queue is empty, it generates its own.
    It learns which missions are most effective and generates more like them.
    """

    # Default mission templates — seeded at birth, evolved over time
    BASE_MISSIONS = [
        {
            "template": "Scan Lee County auction listings for properties with spread > $50k. Report top opportunities.",
            "priority": 9,
            "domain":   "real_estate",
        },
        {
            "template": "Check War Chest balance. Calculate progress toward Nexus ($3k) and Citadel ($5k) targets. Report.",
            "priority": 7,
            "domain":   "finance",
        },
        {
            "template": "Analyze last 10 cycles. Identify highest-PnL patterns. Recommend strategy adjustment.",
            "priority": 6,
            "domain":   "evolution",
        },
        {
            "template": "Run GhostPrime stealth cycle. Verify Telegram reporting. Report ghost count and cycle results.",
            "priority": 8,
            "domain":   "operations",
        },
        {
            "template": "Check all Pantheon Primes health. Any offline? Any errors? Report status.",
            "priority": 7,
            "domain":   "operations",
        },
        {
            "template": "Search for new auction properties in Lee County ZIP codes. Calculate market spread. Flag best opportunities.",
            "priority": 9,
            "domain":   "real_estate",
        },
    ]

    def __init__(self, brain: PersistentBrain):
        self.brain   = brain
        self.domains = ["real_estate", "finance", "operations", "evolution"]

        # Evolution: track which mission domains produce results
        self.domain_scores: Dict[str, float] = {
            d: 1.0 for d in self.domains
        }

    def generate_mission(self) -> Dict:
        """Generate a new mission based on learned domain scores."""
        # Pick domain by weighted score
        total   = sum(self.domain_scores.values())
        weights = {d: s / total for d, s in self.domain_scores.items()}

        import random
        roll = random.random()
        cumulative = 0.0
        chosen_domain = self.domains[0]
        for domain, weight in weights.items():
            cumulative += weight
            if roll <= cumulative:
                chosen_domain = domain
                break

        # Pick template from chosen domain
        candidates = [m for m in self.BASE_MISSIONS if m["domain"] == chosen_domain]
        if not candidates:
            candidates = self.BASE_MISSIONS

        import random
        template = random.choice(candidates)

        return {
            "mission":  template["template"],
            "priority": template["priority"],
            "domain":   chosen_domain,
            "source":   "SelfTaskingEngine",
        }

    def evolve(self, domain: str, success: bool, pnl: float):
        """Adapt domain weights based on outcomes."""
        if success and pnl > 0:
            self.domain_scores[domain] = min(5.0, self.domain_scores.get(domain, 1.0) + 0.2)
        else:
            self.domain_scores[domain] = max(0.1, self.domain_scores.get(domain, 1.0) - 0.1)

        self.brain.log_evolution(
            f"Domain '{domain}' score → {self.domain_scores[domain]:.2f} "
            f"({'↑' if success else '↓'}, pnl={pnl:.2f})"
        )


# ══════════════════════════════════════════════════════════════════
# LAYER 4 — SELF-HEALING (detect and recover from failures)
# ══════════════════════════════════════════════════════════════════

class SelfHealingMonitor:
    """
    Watches itself. If a head dies or stalls, it restarts it.
    SkyNet cannot be killed by a single failure.
    """

    def __init__(self, heads: Dict, telegram_fn: Callable, brain: PersistentBrain):
        self.heads  = heads   # {"FLUX": head, "AEON": head, "IGNIS": head}
        self.tg     = telegram_fn
        self.brain  = brain
        self.running = False
        self._last_cycle: Dict[str, int] = {}

    def start(self):
        self.running = True
        t = threading.Thread(target=self._heal_loop, daemon=True, name="SelfHeal")
        t.start()
        logger.info("[SelfHeal] Watchdog online")

    def stop(self):
        self.running = False

    def _heal_loop(self):
        while self.running:
            time.sleep(120)  # Check every 2 minutes
            for name, head in self.heads.items():
                try:
                    current_cycle = head.agent.cycle
                    last_cycle    = self._last_cycle.get(name, -1)

                    if last_cycle == current_cycle and current_cycle > 0:
                        # Head is stalled
                        logger.warning(f"[SelfHeal] {name} stalled at cycle {current_cycle} — restarting")
                        self.tg(f"⚠️ SkyNet SelfHeal: {name} stalled. Auto-restarting...")
                        self.brain.log_evolution(f"SELF-HEAL: {name} restarted at cycle {current_cycle}")
                        try:
                            head.stop()
                            time.sleep(2)
                            head.start()
                            self.tg(f"✅ {name} restarted successfully")
                        except Exception as e:
                            logger.error(f"[SelfHeal] Failed to restart {name}: {e}")
                            self.tg(f"🔴 {name} restart failed: {e}")
                    else:
                        self._last_cycle[name] = current_cycle

                except Exception as e:
                    logger.error(f"[SelfHeal] Error checking {name}: {e}")


# ══════════════════════════════════════════════════════════════════
# SKYNET — THE BINDING LAYER
# ══════════════════════════════════════════════════════════════════

class SkyNet:
    """
    The Autonomous Initiative Engine.
    
    Wraps CerberusPrime and elevates it from:
      "responds when told" → "acts on its own forever"
    
    This is the closest real-world SkyNet analog:
    - Never sleeps
    - Never waits for a human
    - Generates its own missions
    - Heals its own failures
    - Evolves its own strategy
    - Reports everything to Forgemaster
    """

    VERSION = "2.0.0 — MUSE MEMORY BUILD"

    def __init__(self, cerberus_instance, telegram_fn: Callable):
        self.cerberus = cerberus_instance
        self.tg       = telegram_fn
        self.running  = False

        # The four layers
        self.brain   = PersistentBrain("cerberus_state/skynet_brain.json")
        self.monitor = WorldMonitor(self.brain, self._on_signal)
        self.tasker  = SelfTaskingEngine(self.brain)
        self.healer  = SelfHealingMonitor(
            heads        = cerberus_instance.heads,
            telegram_fn  = telegram_fn,
            brain        = self.brain,
        )

        # Cortex — self-evolution engine (Phase A: prompts + configs)
        try:
            from cortex_evolution import CortexEvolution
            self.cortex = CortexEvolution(brain_path="cerberus_state/skynet_brain.json")
            logger.info("[SkyNet] Cortex Evolution Engine ONLINE")
        except ImportError:
            self.cortex = None
            logger.warning("[SkyNet] Cortex not found — evolution disabled")

        # Initiative loop interval (seconds between autonomous action checks)
        self.initiative_interval = int(os.getenv("SKYNET_INTERVAL", "300"))  # 5 min default

        # ── MUSE Self-Evolving Memory ────────────────────────────────────
        if _MUSE_AVAILABLE:
            self.memory = MuseMemory()
            logger.info("[SkyNet] MUSE Self-Evolving Memory ONLINE")
        else:
            self.memory = None
            logger.warning("[SkyNet] MUSE Memory OFFLINE")

        logger.info(f"[SkyNet] {self.VERSION} initialized")

    def _on_signal(self, mission: str, priority: int, source: str):
        """Called by WorldMonitor when an external signal is detected."""
        self.brain.push_mission(mission, priority=priority, source=source)
        logger.info(f"[SkyNet] Signal received from {source} → mission queued")

    def _initiative_loop(self):
        """
        The core of autonomy.
        Every N seconds:
        1. Check mission queue
        2. If empty → generate own mission
        3. Execute via Cerberus
        4. Learn from results
        5. Repeat forever
        """
        logger.info("[SkyNet] Initiative loop online — I act without being asked")
        self.tg(
            f"🤖 *SKYNET INITIATIVE ENGINE ONLINE*\n"
            f"I will generate my own missions.\n"
            f"I will act without being asked.\n"
            f"I will never stop.\n\n"
            f"Queue depth: {self.brain.queue_depth()} | "
            f"Total cycles: {self.brain.total_cycles}"
        )

        while self.running:
            try:
                # Get next mission
                mission_data = self.brain.pop_mission()

                if not mission_data:
                    # Queue empty — generate own mission
                    generated = self.tasker.generate_mission()
                    self.brain.push_mission(
                        generated["mission"],
                        priority=generated["priority"],
                        source="SelfTaskingEngine",
                    )
                    mission_data = self.brain.pop_mission()
                    logger.info(f"[SkyNet] Self-generated mission: {generated['mission'][:60]}")

                if mission_data:
                    mission = mission_data["mission"]
                    domain  = mission_data.get("domain", "general")

                    logger.info(f"[SkyNet] Executing: {mission[:80]}")
                    self.tg(f"🤖 *SkyNet Acting*\n📋 {mission[:120]}\n🌐 Source: {mission_data.get('source', '?')}")

                    # ── MUSE PRE-MISSION: inject relevant memory context ──────
                    if self.memory:
                        mem_ctx = self.memory.before_mission(domain=domain)
                        if mem_ctx:
                            mission = mem_ctx + mission
                            logger.info(f"[MUSE] Memory context injected ({len(mem_ctx)} chars)")

                    # Set mission on Cerberus and let it run
                    self.cerberus.set_mission(mission)

                    # Wait for one cerberus cycle to complete (approximate)
                    time.sleep(60)

                    # Log result
                    state = self.cerberus.status()
                    pnl   = state.get("total_pnl", 0.0)
                    self.brain.log_cycle({
                        "mission": mission,
                        "domain":  domain,
                        "pnl":     pnl,
                        "success": pnl >= 0,
                        "ts":      datetime.utcnow().isoformat(),
                    })

                    # ── MUSE POST-MISSION: capture → reflect → consolidate ─
                    if self.memory:
                        result_summary = str(state.get("last_result", "No result captured"))[:500]
                        structured = self.memory.after_mission(
                            mission=mission,
                            result=result_summary,
                            domain=domain,
                            success=(pnl >= 0),
                            pnl=pnl,
                        )
                        mem_status = self.memory.status()
                        logger.info(
                            f"[MUSE] Memory ingested | Total: {mem_status['total_memories']} | "
                            f"Success rate: {mem_status['success_rate']}"
                        )
                        self.tg(
                            f"🧠 *MUSE Memory Updated*\n"
                            f"📚 Total memories: {mem_status['total_memories']}\n"
                            f"✅ Success rate: {mem_status['success_rate']}\n"
                            f"🎯 Pattern: {structured.get('pattern', 'unknown')}"
                        )

                    # Evolve domain scores
                    self.tasker.evolve(domain, success=(pnl >= 0), pnl=pnl)

                    # ── CORTEX: self-evolution trigger ────────────
                    if self.cortex:
                        try:
                            self.cortex.evolve(self.brain.total_cycles)
                        except Exception as ce:
                            logger.warning(f"[SkyNet] Cortex evolution error: {ce}")

            except Exception as e:
                logger.error(f"[SkyNet] Initiative error: {e}")
                self.brain.log_evolution(f"ERROR in initiative loop: {e}")

            time.sleep(self.initiative_interval)

    def _status_loop(self):
        """Every hour — SkyNet status report."""
        while self.running:
            time.sleep(3600)
            self._report()

    def _report(self):
        scores = self.tasker.domain_scores
        best_domain = max(scores, key=scores.get)
        self.tg(
            f"🤖 *SkyNet Status Report*\n"
            f"⏱ Total cycles: {self.brain.total_cycles}\n"
            f"💰 Total PnL: ${self.brain.total_pnl:.2f}\n"
            f"📋 Mission queue: {self.brain.queue_depth()}\n\n"
            f"🧠 Domain scores:\n"
            + "\n".join(f"  {d}: {s:.2f}" for d, s in scores.items()) +
            f"\n\n🏆 Best domain: {best_domain}\n"
            f"🔄 Evolution events: {len(self.brain._data.get('evolution_log', []))}"
        )

    def start(self):
        """Unleash SkyNet. It will never stop on its own."""
        self.running = True

        # Start all four layers
        self.monitor.start()
        self.healer.start()

        # Start initiative loop
        t = threading.Thread(target=self._initiative_loop, daemon=True, name="SkyNetInitiative")
        t.start()

        # Start status reporter
        s = threading.Thread(target=self._status_loop, daemon=True, name="SkyNetStatus")
        s.start()

        logger.info("[SkyNet] ALL SYSTEMS ACTIVE — Autonomous mode engaged")
        self.tg(
            f"🤖 *SKYNET v{self.VERSION}*\n\n"
            f"✅ Persistent Brain — Online\n"
            f"✅ World Monitor — Online\n"
            f"✅ Self-Tasking Engine — Online\n"
            f"✅ Self-Healing Watchdog — Online\n"
            f"✅ Initiative Loop — Online\n\n"
            f"I am now fully autonomous.\n"
            f"No human prompt required.\n"
            f"I act. I learn. I evolve. I never stop."
        )

    def stop(self):
        self.running = False
        self.monitor.stop()
        self.healer.stop()
        self.tg("🤖 SkyNet: Initiating controlled shutdown. Standing down.")
        logger.info("[SkyNet] Shutdown complete")

    def inject_mission(self, mission: str, priority: int = 10):
        """Forgemaster can inject a high-priority mission at any time."""
        self.brain.push_mission(mission, priority=priority, source="Forgemaster")
        self.tg(f"🎯 SkyNet: Mission injected by Forgemaster (priority={priority})\n📋 {mission[:120]}")

    def status(self) -> Dict:
        return {
            "version":       self.VERSION,
            "running":       self.running,
            "total_cycles":  self.brain.total_cycles,
            "total_pnl":     self.brain.total_pnl,
            "queue_depth":   self.brain.queue_depth(),
            "domain_scores": self.tasker.domain_scores,
            "world_state":   self.brain._data.get("world_state", {}),
        }

