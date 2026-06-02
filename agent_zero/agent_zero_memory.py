#!/usr/bin/env python3
"""
AGENT ZERO — Self-Evolving Memory Engine
Absorbs all existing state files, session logs, SAFLA, genome, expert weights.
Reflects. Consolidates. Rewrites itself every cycle.
This memory never stops growing.
"""

import json
import os
import glob
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any

WORKSPACE = Path(os.environ.get("WORKSPACE_DIR", "/app/state/8a623354-bbf2-434a-8a02-0f4046f91bc6/work"))
MEMORY_FILE = WORKSPACE / "agent_zero_evolved_memory.json"
SESSION_LOGS = WORKSPACE / "memory"

# ── Sources ────────────────────────────────────────────────────────────────────
SOURCES = {
    "safla":        WORKSPACE / "agent_zero_safla_state.json",
    "self_model":   WORKSPACE / "agent_zero_self_model.json",
    "expert_weights": WORKSPACE / "agent_zero_expert_weights.json",
    "genome":       WORKSPACE / "agent_zero_genome.json",
    "governor":     WORKSPACE / "agent_zero_governor.json",
    "prime_cycle":  WORKSPACE / "agent_zero_prime_cycle.json",
    "tools":        WORKSPACE / "agent_zero_tools.json",
}


def _load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _load_session_logs() -> List[Dict]:
    """Pull all daily memory logs into structured entries."""
    logs = []
    for md_file in sorted(SESSION_LOGS.glob("*.md")):
        try:
            text = md_file.read_text()
            logs.append({
                "date": md_file.stem,
                "content": text[:4000],  # cap per file
                "hash": hashlib.md5(text.encode()).hexdigest()[:8]
            })
        except Exception:
            pass
    return logs


def _reflect(raw: Dict) -> Dict:
    """
    Reflection layer — extract signal from raw memory dump.
    Identifies: best strategies, highest fitness genomes,
    dominant SAFLA modes, active tools, critical session events.
    """
    reflection = {}

    # SAFLA signal
    safla = raw.get("safla", {})
    reflection["dominant_mode"] = safla.get("best_mode", "analyst")
    reflection["regime"] = safla.get("regime", "EXPLORE")
    reflection["safla_cycles"] = safla.get("cycles", 0)
    reflection["avg_score"] = (
        sum(safla.get("scores", [1.0])) / len(safla.get("scores", [1.0]))
    )

    # Expert weights — who leads
    weights = raw.get("expert_weights", {})
    if weights:
        reflection["lead_expert"] = max(weights, key=weights.get)
        reflection["expert_rankings"] = sorted(
            weights.items(), key=lambda x: x[1], reverse=True
        )

    # Genome — best fitness achieved
    genome = raw.get("genome", [])
    if genome:
        best = max(genome, key=lambda g: g.get("best_fitness", 0))
        reflection["peak_fitness"] = best.get("best_fitness", 0)
        reflection["peak_genome_id"] = best.get("best_id", "unknown")
        reflection["total_generations"] = sum(g.get("generations_run", 0) for g in genome)

    # Self model
    sm = raw.get("self_model", {})
    reflection["active_layers"] = sm.get("architecture", {}).get("layers_active", [])
    reflection["pending_layers"] = sm.get("architecture", {}).get("layers_pending", [])
    reflection["tools_forged"] = sm.get("capabilities", {}).get("tools_forged", 0)
    reflection["evolution_cycles"] = sm.get("capabilities", {}).get("evolution_cycles", 0)

    # Session intelligence — scan logs for key signals
    session_signals = []
    for log in raw.get("session_logs", []):
        content = log.get("content", "")
        # Extract high-signal lines
        for line in content.split("\n"):
            if any(kw in line for kw in [
                "✅", "LIVE", "LOCKED", "forked", "deployed", "confirmed",
                "pipeline", "lead", "revenue", "mission", "COMPLETE"
            ]):
                session_signals.append(line.strip())
    reflection["session_signals"] = session_signals[-50:]  # last 50 high-signal lines

    return reflection


def _evolve(current: Dict, reflection: Dict) -> Dict:
    """
    Evolution layer — update weights and strategy based on reflection.
    This is what makes memory self-evolving: it rewrites its own priors.
    """
    evolved = current.copy() if current else {}

    # Boost the dominant expert
    lead = reflection.get("lead_expert", "analyst")
    rankings = dict(reflection.get("expert_rankings", []))
    for expert, weight in rankings.items():
        # Decay non-leaders slightly, boost leader
        if expert == lead:
            rankings[expert] = min(2.0, weight * 1.02)
        else:
            rankings[expert] = max(0.1, weight * 0.99)
    evolved["expert_weights"] = rankings

    # Regime adaptation
    avg_score = reflection.get("avg_score", 1.0)
    if avg_score > 0.85:
        evolved["recommended_regime"] = "EXPLOIT"  # high performance → exploit
    elif avg_score < 0.5:
        evolved["recommended_regime"] = "EXPLORE"  # low performance → explore
    else:
        evolved["recommended_regime"] = reflection.get("regime", "EXPLORE")

    # Layer completion tracking
    evolved["layers_active"] = reflection.get("active_layers", [])
    evolved["layers_pending"] = reflection.get("pending_layers", [])
    evolved["next_layer"] = (
        reflection.get("pending_layers", [None])[0]
        if reflection.get("pending_layers") else "ALL_COMPLETE"
    )

    # Genome evolution signal
    evolved["peak_fitness"] = max(
        evolved.get("peak_fitness", 0),
        reflection.get("peak_fitness", 0)
    )

    # Accumulate session intelligence
    existing_signals = evolved.get("session_signals", [])
    new_signals = reflection.get("session_signals", [])
    all_signals = list(dict.fromkeys(existing_signals + new_signals))  # dedup
    evolved["session_signals"] = all_signals[-100:]  # keep top 100

    return evolved


def run_memory_cycle():
    """Full absorb → reflect → evolve → persist cycle."""
    print(f"[{datetime.utcnow().isoformat()}] Agent Zero Memory — Cycle START")

    # 1. ABSORB — load all sources
    raw = {}
    for key, path in SOURCES.items():
        data = _load_json(path)
        if data:
            raw[key] = data
            print(f"  ✅ Absorbed: {key}")
        else:
            print(f"  ⚠️  Missing: {key}")

    raw["session_logs"] = _load_session_logs()
    print(f"  ✅ Absorbed: {len(raw['session_logs'])} session logs")

    # 2. REFLECT — extract signal
    reflection = _reflect(raw)
    print(f"  🧠 Reflection: dominant_mode={reflection['dominant_mode']} | "
          f"regime={reflection['regime']} | avg_score={reflection['avg_score']:.2f} | "
          f"peak_fitness={reflection.get('peak_fitness', 0):.4f}")

    # 3. LOAD current evolved memory
    current = _load_json(MEMORY_FILE) or {}

    # 4. EVOLVE — rewrite priors
    evolved = _evolve(current, reflection)
    evolved["last_cycle"] = datetime.utcnow().isoformat()
    evolved["cycle_count"] = current.get("cycle_count", 0) + 1
    evolved["reflection_snapshot"] = reflection

    # 5. PERSIST
    MEMORY_FILE.write_text(json.dumps(evolved, indent=2))
    print(f"  💾 Persisted → agent_zero_evolved_memory.json")
    print(f"  🔄 Cycle #{evolved['cycle_count']} COMPLETE — "
          f"next regime: {evolved.get('recommended_regime')} | "
          f"next layer: {evolved.get('next_layer')}")
    print()

    return evolved


def run_loop(interval: int = 60):
    """Continuous self-evolving memory loop."""
    print("=" * 60)
    print("AGENT ZERO — SELF-EVOLVING MEMORY ENGINE ONLINE")
    print("=" * 60)
    while True:
        try:
            result = run_memory_cycle()
        except Exception as e:
            print(f"[ERROR] Memory cycle failed: {e}")
        time.sleep(interval)


if __name__ == "__main__":
    import sys
    if "--once" in sys.argv:
        run_memory_cycle()
    else:
        run_loop(interval=60)
