"""
StripeConduit — MidasPrime's Payment Integration Layer
Every dollar that flows through PropPilot AI hits the War Chest in real time.

Revenue Streams:
  - Bird Dogging finder's fees ($500-$2,000/lead)
  - Wholesaling assignment fees ($5,000-$20,000/deal)
  - Agent Content subscriptions ($197/$347/$497/mo recurring)

Usage:
    from stripe_conduit import StripeConduit
    conduit = StripeConduit(api_key="sk_live_...")
    conduit.sync_to_war_chest()
"""

import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

try:
    import stripe
except ImportError:
    raise ImportError("stripe required: pip install stripe")

# ── CONFIG ────────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).parent.resolve()
WAR_CHEST_FILE = BASE_DIR / "logs" / "war_chest.json"
WAR_CHEST_FILE.parent.mkdir(exist_ok=True)

# Subscription tier mapping
AGENT_TIERS = {
    197: "Starter",
    347: "Pro",
    497: "Elite"
}

# PropPilot revenue categories (Fair Scale Protocol)
REVENUE_CATEGORIES = {
    "bird_dog":    {"label": "Bird Dogging",        "range": (500, 2000)},
    "wholesale":   {"label": "Wholesaling",         "range": (5000, 20000)},
    "agent_sub":   {"label": "Agent Subscription",  "range": (197, 497)},
}

logging.basicConfig(level=logging.INFO, format="%(asctime)s [STRIPE-CONDUIT] %(message)s")
log = logging.getLogger("StripeConduit")


# ── STRIPE CONDUIT ────────────────────────────────────────────────────────────
class StripeConduit:
    """
    MidasPrime's direct link to Stripe.
    Monitors payments, auto-logs to War Chest, fires MidasPrime updates.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("STRIPE_SECRET_KEY")
        if not self.api_key:
            raise ValueError(
                "Stripe API key required.\n"
                "Set STRIPE_SECRET_KEY in your environment or pass api_key= directly.\n"
                "Get your key at: https://dashboard.stripe.com/apikeys"
            )
        stripe.api_key = self.api_key
        self.war_chest = self._load_war_chest()
        log.info("StripeConduit online. War Chest loaded.")

    # ── WAR CHEST ──────────────────────────────────────────────────────────────
    def _load_war_chest(self) -> dict:
        if WAR_CHEST_FILE.exists():
            with open(WAR_CHEST_FILE) as f:
                return json.load(f)
        return {
            "total_earned": 0.0,
            "total_pending": 0.0,
            "transactions": [],
            "subscriptions": [],
            "last_sync": None
        }

    def _save_war_chest(self):
        with open(WAR_CHEST_FILE, "w") as f:
            json.dump(self.war_chest, f, indent=2)
        log.info(f"War Chest saved. Total earned: ${self.war_chest['total_earned']:.2f}")

    # ── SYNC ALL PAYMENTS ──────────────────────────────────────────────────────
    def sync_to_war_chest(self, limit: int = 100):
        """Pull all recent payments from Stripe → log to War Chest."""
        log.info("Syncing Stripe payments to War Chest...")

        try:
            payments = stripe.PaymentIntent.list(limit=limit)
        except stripe.error.AuthenticationError:
            log.error("❌ Invalid Stripe API key. Check STRIPE_SECRET_KEY.")
            return
        except stripe.error.StripeError as e:
            log.error(f"❌ Stripe error: {e}")
            return

        new_count = 0
        existing_ids = {t["stripe_id"] for t in self.war_chest["transactions"]}

        for payment in payments.auto_paging_iter():
            if payment.id in existing_ids:
                continue
            if payment.status != "succeeded":
                continue

            amount = payment.amount / 100  # cents → dollars
            category = self._categorize_payment(payment, amount)
            timestamp = datetime.fromtimestamp(payment.created, tz=timezone.utc).isoformat()

            entry = {
                "stripe_id":   payment.id,
                "amount":      amount,
                "category":    category,
                "description": payment.description or payment.metadata.get("description", "PropPilot Payment"),
                "customer":    payment.customer,
                "timestamp":   timestamp,
                "status":      "collected"
            }

            self.war_chest["transactions"].append(entry)
            self.war_chest["total_earned"] += amount
            new_count += 1
            log.info(f"  ✅ +${amount:.2f} [{category}] {entry['description']}")

        self.war_chest["last_sync"] = datetime.now(tz=timezone.utc).isoformat()
        self._save_war_chest()
        log.info(f"Sync complete. {new_count} new transactions. Total: ${self.war_chest['total_earned']:.2f}")
        return new_count

    # ── SUBSCRIPTIONS ──────────────────────────────────────────────────────────
    def sync_subscriptions(self):
        """Pull active agent subscriptions → log MRR to War Chest."""
        log.info("Syncing agent subscriptions...")

        try:
            subs = stripe.Subscription.list(status="active", limit=100)
        except stripe.error.StripeError as e:
            log.error(f"❌ Stripe error: {e}")
            return

        active_subs = []
        mrr = 0.0

        for sub in subs.auto_paging_iter():
            amount = sub["items"]["data"][0]["price"]["unit_amount"] / 100
            tier = AGENT_TIERS.get(int(amount), "Custom")
            customer_id = sub.customer

            # Try to get customer email
            try:
                customer = stripe.Customer.retrieve(customer_id)
                customer_name = customer.get("name") or customer.get("email") or customer_id
            except Exception:
                customer_name = customer_id

            entry = {
                "stripe_sub_id": sub.id,
                "customer":      customer_name,
                "tier":          tier,
                "amount":        amount,
                "status":        sub.status,
                "started":       datetime.fromtimestamp(sub.start_date, tz=timezone.utc).isoformat()
            }
            active_subs.append(entry)
            mrr += amount
            log.info(f"  📋 {customer_name} | {tier} | ${amount:.2f}/mo")

        self.war_chest["subscriptions"] = active_subs
        self.war_chest["mrr"] = mrr
        self._save_war_chest()
        log.info(f"Subscriptions synced. Active: {len(active_subs)} | MRR: ${mrr:.2f}")
        return active_subs

    # ── CREATE PAYMENT LINKS ───────────────────────────────────────────────────
    def create_bird_dog_invoice(self, investor_email: str, amount: float, property_address: str) -> str:
        """Create a Stripe invoice for a bird dog finder's fee."""
        try:
            # Find or create customer
            customers = stripe.Customer.list(email=investor_email, limit=1)
            if customers.data:
                customer = customers.data[0]
            else:
                customer = stripe.Customer.create(email=investor_email)

            # Create invoice item
            stripe.InvoiceItem.create(
                customer=customer.id,
                amount=int(amount * 100),
                currency="usd",
                description=f"Bird Dog Finder's Fee — {property_address}"
            )

            # Create and finalize invoice
            invoice = stripe.Invoice.create(
                customer=customer.id,
                auto_advance=True,
                metadata={"category": "bird_dog", "property": property_address}
            )
            invoice = stripe.Invoice.finalize_invoice(invoice.id)

            log.info(f"✅ Invoice created: ${amount:.2f} → {investor_email} | {invoice.hosted_invoice_url}")
            return invoice.hosted_invoice_url

        except stripe.error.StripeError as e:
            log.error(f"❌ Invoice creation failed: {e}")
            return ""

    def create_agent_subscription_link(self, tier: str = "Pro") -> str:
        """Get or create a Stripe payment link for agent subscriptions."""
        tier_prices = {"Starter": 19700, "Pro": 34700, "Elite": 49700}
        price_amount = tier_prices.get(tier, 34700)

        try:
            # Create a price for the subscription
            price = stripe.Price.create(
                unit_amount=price_amount,
                currency="usd",
                recurring={"interval": "month"},
                product_data={"name": f"PropPilot AI — Agent Content {tier}"}
            )

            # Create payment link
            link = stripe.PaymentLink.create(
                line_items=[{"price": price.id, "quantity": 1}]
            )

            log.info(f"✅ Subscription link ({tier}): {link.url}")
            return link.url

        except stripe.error.StripeError as e:
            log.error(f"❌ Payment link creation failed: {e}")
            return ""

    # ── WAR CHEST REPORT ───────────────────────────────────────────────────────
    def war_chest_report(self) -> str:
        """Generate a MidasPrime-style War Chest status report."""
        wc = self.war_chest
        mrr = wc.get("mrr", 0.0)
        total = wc.get("total_earned", 0.0)
        subs = wc.get("subscriptions", [])
        txns = wc.get("transactions", [])

        # Category breakdown
        by_category = {}
        for t in txns:
            cat = t.get("category", "other")
            by_category[cat] = by_category.get(cat, 0) + t["amount"]

        report = f"""
╔══════════════════════════════════════════════╗
║         MIDASPRME — WAR CHEST STATUS         ║
╠══════════════════════════════════════════════╣
║  Total Earned:    ${total:>10,.2f}             ║
║  MRR (Subs):      ${mrr:>10,.2f}/mo           ║
║  Active Clients:  {len(subs):>10}               ║
║  Transactions:    {len(txns):>10}               ║
╠══════════════════════════════════════════════╣
║  REVENUE BREAKDOWN                           ║"""

        for cat, amount in by_category.items():
            label = REVENUE_CATEGORIES.get(cat, {}).get("label", cat)
            report += f"\n║  {label:<25} ${amount:>10,.2f}  ║"

        report += f"""
╠══════════════════════════════════════════════╣
║  Last Sync: {wc.get('last_sync', 'Never')[:19]:<33}║
╚══════════════════════════════════════════════╝
"""
        return report

    # ── HELPERS ────────────────────────────────────────────────────────────────
    def _categorize_payment(self, payment, amount: float) -> str:
        desc = (payment.description or "").lower()
        meta = payment.metadata or {}

        if meta.get("category"):
            return meta["category"]
        if "bird" in desc or "finder" in desc or "lead" in desc:
            return "bird_dog"
        if "wholesale" in desc or "assignment" in desc:
            return "wholesale"
        if "agent" in desc or "content" in desc or "subscription" in desc:
            return "agent_sub"
        if 197 <= amount <= 497:
            return "agent_sub"
        if 500 <= amount <= 2000:
            return "bird_dog"
        if amount >= 5000:
            return "wholesale"
        return "other"


# ── ENTRY POINT ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    api_key = os.environ.get("STRIPE_SECRET_KEY") or (sys.argv[1] if len(sys.argv) > 1 else None)

    if not api_key:
        print("Usage: python stripe_conduit.py <sk_live_...>")
        print("   or: STRIPE_SECRET_KEY=sk_live_... python stripe_conduit.py")
        sys.exit(1)

    conduit = StripeConduit(api_key)

    print("\n🔱 StripeConduit — Full Sync")
    conduit.sync_to_war_chest()
    conduit.sync_subscriptions()
    print(conduit.war_chest_report())
