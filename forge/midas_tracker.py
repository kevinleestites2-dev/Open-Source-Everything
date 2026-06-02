#!/usr/bin/env python3
"""
MidasPrime: Treasury Tracker v2.0
Warden of the War Chest. Purpose: ACCUMULATION.

Targets:
  🎯 Nexus    — $3,000  → 1TB Laptop (The Throne)
  🎯 Citadel  — $5,000  → The Apartment

Tracks: Stripe payments + Bird Dog pipeline + threshold signals.
"""

import os
import json
import logging
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR       = Path(__file__).parent.resolve()
WAR_CHEST_FILE = BASE_DIR / "logs" / "war_chest.json"
LEADS_FILE     = BASE_DIR / "logs" / "bird_dog_leads.json"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [MIDAS-TRACKER] %(message)s")
log = logging.getLogger("MidasTracker")


class MidasPrime:
    NEXUS_TARGET   = 3_000.0   # 1TB Laptop
    CITADEL_TARGET = 5_000.0   # The Apartment

    def __init__(self):
        self.war_chest   = self._load_war_chest()
        self.leads       = self._load_leads()
        self.stripe_key  = os.environ.get("STRIPE_SECRET_KEY")

    def _load_war_chest(self):
        if WAR_CHEST_FILE.exists():
            with open(WAR_CHEST_FILE) as f:
                return json.load(f)
        return {"total_earned": 0.0, "transactions": [], "subscriptions": [], "mrr": 0.0}

    def _load_leads(self):
        if LEADS_FILE.exists():
            with open(LEADS_FILE) as f:
                return json.load(f)
        return []

    def sync_stripe(self):
        """Pull latest payments from Stripe into War Chest."""
        if not self.stripe_key:
            log.warning("No STRIPE_SECRET_KEY. Skipping Stripe sync.")
            return
        try:
            from stripe_conduit import StripeConduit
            conduit = StripeConduit(api_key=self.stripe_key)
            conduit.sync_to_war_chest()
            conduit.sync_subscriptions()
            self.war_chest = conduit.war_chest  # refresh
            log.info("Stripe sync complete.")
        except Exception as e:
            log.error(f"Stripe sync failed: {e}")

    def get_balance(self) -> float:
        """Total capital accumulated."""
        return self.war_chest.get("total_earned", 0.0)

    def get_pending(self) -> float:
        """Value of invoiced but unpaid bird dog leads."""
        return sum(l["fee"] for l in self.leads if l.get("status") == "invoiced")

    def get_mrr(self) -> float:
        return self.war_chest.get("mrr", 0.0)

    def check_thresholds(self) -> str:
        balance = self.get_balance()
        if balance >= self.CITADEL_TARGET:
            return "🏰 SIGNAL: CITADEL SECURED. THE APARTMENT IS YOURS."
        elif balance >= self.NEXUS_TARGET:
            return "💻 SIGNAL: NEXUS ACQUISITION AUTHORIZED. BUY THE THRONE."
        else:
            pct = (balance / self.NEXUS_TARGET) * 100
            remaining = self.NEXUS_TARGET - balance
            return (f"⚔️  ACCUMULATING — ${balance:,.2f} / ${self.NEXUS_TARGET:,.2f} "
                    f"({pct:.1f}%) | ${remaining:,.2f} to NEXUS")

    def progress_bar(self, current, target, width=20) -> str:
        filled = int((min(current, target) / target) * width)
        bar    = "█" * filled + "░" * (width - filled)
        return f"[{bar}] {(current/target*100):.1f}%"

    def full_report(self) -> str:
        balance  = self.get_balance()
        pending  = self.get_pending()
        mrr      = self.get_mrr()
        txns     = self.war_chest.get("transactions", [])
        subs     = self.war_chest.get("subscriptions", [])
        paid_leads   = [l for l in self.leads if l.get("status") == "paid"]
        active_leads = [l for l in self.leads if l.get("status") in ("new","submitted","invoiced")]

        nexus_bar   = self.progress_bar(balance, self.NEXUS_TARGET)
        citadel_bar = self.progress_bar(balance, self.CITADEL_TARGET)

        report = f"""
╔══════════════════════════════════════════════════════╗
║           MIDASPRME — WAR CHEST REPORT               ║
║           {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC'):<43}║
╠══════════════════════════════════════════════════════╣
║  💰 BALANCE:      ${balance:>10,.2f}                       ║
║  ⏳ PENDING:      ${pending:>10,.2f}  (invoiced, not paid)   ║
║  📈 MRR:          ${mrr:>10,.2f}/mo                      ║
╠══════════════════════════════════════════════════════╣
║  🎯 NEXUS    $3,000  {nexus_bar:<30} ║
║  🏰 CITADEL  $5,000  {citadel_bar:<30} ║
╠══════════════════════════════════════════════════════╣
║  BIRD DOG PIPELINE                                   ║
║  Active Leads:    {len(active_leads):>5}                              ║
║  Paid Leads:      {len(paid_leads):>5}                              ║
║  Stripe Txns:     {len(txns):>5}                              ║
║  Active Subs:     {len(subs):>5}                              ║
╠══════════════════════════════════════════════════════╣
║  {self.check_thresholds():<52} ║
╚══════════════════════════════════════════════════════╝
"""
        return report


if __name__ == "__main__":
    midas = MidasPrime()
    midas.sync_stripe()
    print(midas.full_report())
