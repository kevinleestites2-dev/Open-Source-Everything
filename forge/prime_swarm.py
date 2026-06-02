"""
PRIME-Swarm v1.0 — The Hive Mind
Orchestrator for IgnisPrime (Execution) and SAFLA 2.0 (Intelligence).
"""
import asyncio
import os
import sys
import time
from pathlib import Path

# ── Integration Paths ────────────────────────────────────────────────────────
sys.path.append(os.path.abspath("ignis_prime"))
sys.path.append(os.path.abspath("safla-v2"))

try:
    from strike import IgnisStrike
    from bridge import SAFLABridge
    HAS_COMPONENTS = True
except ImportError as e:
    print(f"❌ Error loading components: {e}")
    HAS_COMPONENTS = False

class PrimeSwarm:
    def __init__(self):
        print("🔱 PRIME-Swarm v1.0 — The Hive Mind Online")
        self.ignis = IgnisStrike(intensity=1.2)
        self.safla = SAFLABridge("PRIME-Swarm")
        self.cycle_count = 0

    async def run_cycle(self):
        """
        One Hive Mind cycle:
        1. Sync intelligence from SAFLA.
        2. Assign task to Ignis.
        3. Reflect on outcome through SAFLA.
        """
        self.cycle_count += 1
        print(f"\n🌀 PRIME-Swarm Cycle {self.cycle_count} starting...")

        # 1. Intelligence Phase
        weights = self.safla.get_weights()
        conviction = weights.get("conviction", 0.75)
        print(f"🧠 Intelligence: SAFLA Conviction at {conviction:.2f}")

        # 2. Execution Phase (Ignis Strike)
        strike_count = int(5 * conviction)
        results = await self.ignis.swarm_strike(count=strike_count)

        # 3. Reflection Phase
        total_pnl = sum(r["pnl"] for r in results)
        success_count = sum(1 for r in results if r["success"])
        
        print(f"📊 Reflection: {success_count}/{len(results)} strikes successful. Total PnL: ${total_pnl:.2f}")

        # Report to SAFLA for evolution
        self.safla.report_event(
            event_id=f"swarm_cycle_{self.cycle_count}",
            outcome_value=total_pnl,
            metadata={
                "success_rate": success_count / len(results) if results else 0,
                "cycle": self.cycle_count,
                "pnl": total_pnl
            }
        )
        
        return total_pnl

    async def heartbeat(self):
        """
        Continuous Hive Mind execution.
        """
        print("💓 Hive Mind Heartbeat active.")
        while True:
            await self.run_cycle()
            wait_time = 30 # Metabolic rate
            print(f"💤 Sleeping {wait_time}s for neural cooldown...")
            await asyncio.sleep(wait_time)

async def main():
    if not HAS_COMPONENTS:
        print("❌ Cannot start PRIME-Swarm: Missing Ignis or SAFLA components.")
        return

    swarm = PrimeSwarm()
    await swarm.heartbeat()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 PRIME-Swarm Offline.")
