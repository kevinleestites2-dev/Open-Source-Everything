"""
Second-Brain — Layer 6 Long-Term Memory (v2.0 — agentmemory backend)
Distills experience into patterns. Identifies multi-mission trends.

Storage backends:
  - "local"       : original JSON flat-file (default, zero dependencies)
  - "agentmemory" : agentmemory MCP server on :3111 (95% recall accuracy)

Set SECOND_BRAIN_BACKEND=agentmemory in env to activate the MCP backend.
Requires: npm install -g @agentmemory/agentmemory && agentmemory (running on :3111)
"""

import json
import logging
import os
import time
from pathlib import Path
from typing import Dict, List, Any, Optional

# agentmemory HTTP client (optional dependency)
try:
    import urllib.request
    import urllib.error
    AGENTMEMORY_AVAILABLE = True
except ImportError:
    AGENTMEMORY_AVAILABLE = False

logging.basicConfig(level=logging.INFO, format='[Second-Brain] %(message)s')
logger = logging.getLogger("Second-Brain")

AGENTMEMORY_HOST = os.environ.get("AGENTMEMORY_HOST", "http://localhost:3111")
BACKEND = os.environ.get("SECOND_BRAIN_BACKEND", "local")  # "local" | "agentmemory"


# ─────────────────────────────────────────────
#  agentmemory MCP client (lightweight, no SDK)
# ─────────────────────────────────────────────

class AgentMemoryClient:
    """Thin HTTP wrapper around the agentmemory MCP server REST API."""

    def __init__(self, host: str = AGENTMEMORY_HOST):
        self.host = host.rstrip("/")
        self._check_connection()

    def _check_connection(self):
        try:
            req = urllib.request.urlopen(f"{self.host}/health", timeout=3)
            logger.info(f"agentmemory backend connected at {self.host}")
        except Exception:
            logger.warning(f"agentmemory not reachable at {self.host} — falling back to local")
            raise ConnectionError("agentmemory unreachable")

    def _post(self, endpoint: str, payload: Dict) -> Dict:
        data = json.dumps(payload).encode()
        req = urllib.request.Request(
            f"{self.host}{endpoint}",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())

    def _get(self, endpoint: str) -> Dict:
        with urllib.request.urlopen(f"{self.host}{endpoint}", timeout=10) as resp:
            return json.loads(resp.read().decode())

    def store(self, key: str, value: Any, tags: Optional[List[str]] = None) -> bool:
        """Store a memory entry."""
        try:
            self._post("/api/memory", {
                "key": key,
                "value": json.dumps(value) if not isinstance(value, str) else value,
                "tags": tags or [],
                "source": "fluxprime-second-brain"
            })
            return True
        except Exception as e:
            logger.error(f"agentmemory store failed: {e}")
            return False

    def recall(self, key: str) -> Optional[Any]:
        """Recall a specific memory by key."""
        try:
            result = self._get(f"/api/memory/{key}")
            if result and "value" in result:
                try:
                    return json.loads(result["value"])
                except Exception:
                    return result["value"]
        except Exception as e:
            logger.error(f"agentmemory recall failed: {e}")
        return None

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """Semantic search across all memories."""
        try:
            result = self._post("/api/memory/search", {"query": query, "topK": top_k})
            return result.get("results", [])
        except Exception as e:
            logger.error(f"agentmemory search failed: {e}")
            return []

    def list_keys(self) -> List[str]:
        """List all stored memory keys."""
        try:
            result = self._get("/api/memory")
            return [m.get("key", "") for m in result.get("memories", [])]
        except Exception as e:
            logger.error(f"agentmemory list failed: {e}")
            return []


# ─────────────────────────────────────────────
#  SecondBrain — unified interface
# ─────────────────────────────────────────────

class SecondBrain:
    """
    Second-Brain is the long-term memory kernel.
    Unlike SAFLA (which is short-term adaptive), Second-Brain
    looks at the "regime of regimes" across multiple missions.

    v2.0: Dual-backend — local JSON (always available) + agentmemory MCP
          for semantic search and 95% recall accuracy across all Primes.
    """

    def __init__(self, brain_dir: str = "fluxprime_core/brain"):
        self.brain_path = Path(brain_dir)
        self.brain_path.mkdir(parents=True, exist_ok=True)
        self.knowledge_file = self.brain_path / "long_term_knowledge.json"

        # Backend selection with automatic fallback
        self.backend = BACKEND
        self.am_client: Optional[AgentMemoryClient] = None

        if self.backend == "agentmemory":
            try:
                self.am_client = AgentMemoryClient()
                logger.info("🧠 Second-Brain online [agentmemory backend]")
            except ConnectionError:
                self.backend = "local"
                logger.warning("🧠 Second-Brain online [local fallback — agentmemory offline]")
        else:
            logger.info("🧠 Second-Brain online [local backend]")

        self.knowledge = self._load_knowledge()

    # ── knowledge I/O ──────────────────────────────────────────────────────

    def _load_knowledge(self) -> Dict:
        """Load from agentmemory if available, else local JSON."""
        if self.am_client:
            stored = self.am_client.recall("flux:knowledge:root")
            if stored:
                logger.info("🧠 Knowledge loaded from agentmemory")
                return stored

        if self.knowledge_file.exists():
            try:
                with open(self.knowledge_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Failed to load brain: {e}")

        return {
            "patterns": {},
            "prime_competencies": {
                "scout": {"success_rate": 1.0, "total_value": 0},
                "zeus":  {"success_rate": 1.0, "total_value": 0},
                "ghost": {"success_rate": 1.0, "total_value": 0}
            },
            "regime_history": [],
            "last_updated": time.time()
        }

    def save_knowledge(self):
        """Persist to both backends (agentmemory + local JSON as safety net)."""
        self.knowledge["last_updated"] = time.time()

        # Always write local JSON (crash-proof safety net)
        try:
            with open(self.knowledge_file, "w") as f:
                json.dump(self.knowledge, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save local brain: {e}")

        # Also write to agentmemory if available
        if self.am_client:
            self.am_client.store(
                key="flux:knowledge:root",
                value=self.knowledge,
                tags=["fluxprime", "knowledge", "competencies"]
            )
            logger.info("🧠 Knowledge persisted to agentmemory + local")
        else:
            logger.info("🧠 Knowledge persisted to local memory")

    # ── core methods (unchanged API) ───────────────────────────────────────

    def distill_experience(self, mission_id: str, results: List[Dict]):
        """
        Takes raw mission results and distills them into long-term patterns.
        Also writes each cycle as a discrete agentmemory entry for semantic recall.
        """
        logger.info(f"🧪 Distilling experience from mission: {mission_id}")

        for cycle in results:
            for outcome in cycle.get("outcomes", []):
                prime  = outcome.get("prime")
                value  = outcome.get("value", 0)
                result = outcome.get("result")

                # Update competency
                comp = self.knowledge["prime_competencies"].get(
                    prime, {"success_rate": 1.0, "total_value": 0}
                )
                comp["total_value"] += value

                current_rate = comp.get("success_rate", 1.0)
                new_data_point = 1.0 if result == "SUCCESS" else 0.0
                comp["success_rate"] = (current_rate * 0.9) + (new_data_point * 0.1)

                self.knowledge["prime_competencies"][prime] = comp

                # Write discrete experience to agentmemory (enables semantic search)
                if self.am_client:
                    self.am_client.store(
                        key=f"flux:mission:{mission_id}:cycle:{cycle.get('cycle_id', int(time.time()))}:{prime}",
                        value={
                            "mission_id": mission_id,
                            "prime": prime,
                            "value": value,
                            "result": result,
                            "timestamp": time.time()
                        },
                        tags=["fluxprime", "mission", prime, result or "UNKNOWN"]
                    )

        self.save_knowledge()

    def get_strategic_guidance(self, goal: str) -> Dict:
        """
        Returns strategic weight modifiers based on long-term memory.
        If agentmemory is active, enriches guidance with semantic search results.
        """
        guidance = {
            "prime_modifiers": {},
            "strategy": "ADAPTIVE",
            "semantic_context": []
        }

        # Core competency-based modifier (unchanged logic)
        for prime, comp in self.knowledge["prime_competencies"].items():
            modifier = comp["success_rate"] * (1 + (comp["total_value"] / 100000))
            guidance["prime_modifiers"][prime] = min(modifier, 1.5)

        # Semantic enrichment from agentmemory
        if self.am_client:
            similar = self.am_client.search(goal, top_k=5)
            if similar:
                guidance["semantic_context"] = similar
                logger.info(f"💡 Semantic context: {len(similar)} relevant memories loaded")

        logger.info("💡 Second-Brain strategic guidance loaded")
        return guidance

    def semantic_search(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Direct semantic search across all Pantheon memory.
        Only available with agentmemory backend.
        """
        if self.am_client:
            return self.am_client.search(query, top_k=top_k)
        logger.warning("Semantic search requires agentmemory backend")
        return []

    def get_prime_summary(self, prime: str) -> Dict:
        """Return full competency record for a specific Prime."""
        return self.knowledge["prime_competencies"].get(
            prime, {"success_rate": 1.0, "total_value": 0}
        )
