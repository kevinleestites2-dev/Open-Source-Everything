#!/usr/bin/env python3
"""
War Chest Bridge — MidasPrime Integration Layer
Pipes earnings from ALL sources into the central War Chest.

Sources:
  - OmegaPrime (job earnings)
  - trade_meta / ZeusPrimeBot (Polymarket PnL)
  - Bird Dog Engine (lead fees)
  - Stripe (direct payments)

All roads lead to war_chest.json.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

BASE_DIR       = Path(__file__).parent.resolve()
WAR_CHEST_FILE = BASE_DIR / "logs" / "war_chest.json"
WAR_CHEST_FILE.parent.mkdir(exist_ok=True)

log = logging.getLogger("WarChestBridge")


def _load():
    if WAR_CHEST_FILE.exists():
        with open(WAR_CHEST_FILE) as f:
            return json.load(f)
    return {"total_earned": 0.0, "total_pending": 0.0,
            "transactions": [], "subscriptions": [], "mrr": 0.0,
            "last_sync": None}


def _save(data):
    with open(WAR_CHEST_FILE, "w") as f:
        json.dump(data, f, indent=2)


def record_earning(amount: float, source: str, description: str = "", meta: dict = None):
    """
    Record any earning into the War Chest.
    Call this from OmegaPrime, trade_meta, bird_dog, anywhere.

    Args:
        amount:      Dollar amount earned (positive only)
        source:      "omega_prime" | "trade_meta" | "bird_dog" | "stripe" | "manual"
        description: Human-readable note
        meta:        Any extra context (job_id, market_id, etc.)
    """
    if amount <= 0:
        return

    data = _load()
    txn = {
        "id":          f"{source}_{int(datetime.now(tz=timezone.utc).timestamp())}",
        "amount":      round(amount, 2),
        "source":      source,
        "description": description,
        "meta":        meta or {},
        "timestamp":   datetime.now(tz=timezone.utc).isoformat(),
        "status":      "completed"
    }
    data["transactions"].append(txn)
    data["total_earned"] = round(data.get("total_earned", 0.0) + amount, 2)
    data["last_sync"] = datetime.now(tz=timezone.utc).isoformat()
    _save(data)
    log.info(f"💰 War Chest +${amount:.2f} [{source}] {description}")
    return txn


def sync_omega_prime_earnings(db_path: str):
    """Pull closed trade earnings from OmegaPrime's SQLite DB."""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get jobs not yet synced to war chest
        cur.execute("""
            SELECT job_id, earnings, outcome, timestamp
            FROM job_outcomes
            WHERE earnings > 0 AND outcome = 'success'
        """)
        rows = cur.fetchall()
        conn.close()

        chest = _load()
        synced_ids = {t.get("meta", {}).get("job_id") for t in chest.get("transactions", [])}

        new_count = 0
        for row in rows:
            if row["job_id"] not in synced_ids:
                record_earning(
                    amount=float(row["earnings"]),
                    source="omega_prime",
                    description=f"Job {row['job_id']} — {row['outcome']}",
                    meta={"job_id": row["job_id"], "timestamp": row["timestamp"]}
                )
                new_count += 1

        if new_count:
            log.info(f"OmegaPrime sync: +{new_count} new earnings")
        return new_count

    except Exception as e:
        log.error(f"OmegaPrime sync failed: {e}")
        return 0


def sync_trade_meta_pnl(db_path: str):
    """Pull closed trade PnL from trade_meta / ZeusPrimeBot's SQLite DB."""
    try:
        import sqlite3
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        cur.execute("""
            SELECT id, strategy, pnl, timestamp
            FROM trades
            WHERE status = 'closed' AND pnl > 0
        """)
        rows = cur.fetchall()
        conn.close()

        chest = _load()
        synced_ids = {t.get("meta", {}).get("trade_id") for t in chest.get("transactions", [])}

        new_count = 0
        for row in rows:
            trade_id = str(row["id"])
            if trade_id not in synced_ids:
                record_earning(
                    amount=float(row["pnl"]),
                    source="trade_meta",
                    description=f"Polymarket trade — strategy: {row['strategy']}",
                    meta={"trade_id": trade_id, "strategy": row["strategy"],
                          "timestamp": row["timestamp"]}
                )
                new_count += 1

        if new_count:
            log.info(f"TradeMeta sync: +{new_count} profitable trades")
        return new_count

    except Exception as e:
        log.error(f"TradeMeta sync failed: {e}")
        return 0


def get_balance() -> float:
    return _load().get("total_earned", 0.0)


def full_report() -> str:
    data = _load()
    balance  = data.get("total_earned", 0.0)
    txns     = data.get("transactions", [])
    by_source = {}
    for t in txns:
        s = t.get("source", "unknown")
        by_source[s] = by_source.get(s, 0.0) + t.get("amount", 0.0)

    lines = [
        "╔══════════════════════════════════════════════╗",
        "║        WAR CHEST — FULL REPORT               ║",
        f"║  TOTAL: ${balance:>10,.2f}                       ║",
        "╠══════════════════════════════════════════════╣",
    ]
    for src, amt in by_source.items():
        lines.append(f"║  {src:<20} ${amt:>10,.2f}             ║")
    lines.append(f"║  Transactions: {len(txns):>5}                        ║")
    lines.append("╚══════════════════════════════════════════════╝")
    return "\n".join(lines)


# ── FULL SYNC — call this from midas_tracker or cron ─────────────────────────
def sync_all():
    log.info("🔱 War Chest Bridge — Full Sync Starting...")

    # Sync OmegaPrime job earnings
    omega_db = BASE_DIR / "omega_prime_v2.db"
    if omega_db.exists():
        sync_omega_prime_earnings(str(omega_db))
    else:
        log.info("OmegaPrime DB not found — skipping")

    # Sync Polymarket trade PnL
    trade_db = BASE_DIR / "midas_prime.db"
    if trade_db.exists():
        sync_trade_meta_pnl(str(trade_db))
    else:
        log.info("TradeMeta DB not found — skipping")

    # Sync Stripe
    import os
    stripe_key = os.environ.get("STRIPE_SECRET_KEY")
    if stripe_key:
        try:
            from stripe_conduit import StripeConduit
            conduit = StripeConduit(api_key=stripe_key)
            conduit.sync_to_war_chest()
            conduit.sync_subscriptions()
            log.info("Stripe sync complete")
        except Exception as e:
            log.error(f"Stripe sync error: {e}")

    log.info(f"🔱 Sync complete. Balance: ${get_balance():,.2f}")
    return get_balance()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [WAR-CHEST] %(message)s")
    balance = sync_all()
    print(full_report())
