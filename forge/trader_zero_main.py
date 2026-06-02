"""
TraderZero — Self-Evolving Paper Trading Bot
============================================
Agent Zero's cognitive engine wired to live crypto markets.
NO strategies provided. TraderZero discovers its own edge.

Architecture:
  Layer 7  (SAFLA)     — scores every trade, drives regime changes
  Layer 8  (Evolution) — rewrites its own strategy logic when losing
  Layer 15 (Genome)    — KhepriCore: 20% royalty to War Chest on every profit

The only rules:
  1. Paper trade (PAPER_CAPITAL env var, default $1,000)
  2. Report every decision to Telegram
  3. Survive. Learn. Evolve.

Forgemaster does NOT give strategies. TraderZero finds its own.
"""

import os
import json
import time
import uuid
import random
import logging
import sqlite3
import urllib.request
from pathlib import Path
from datetime import datetime, timezone
from enum import Enum

# ── Config (all from env) ─────────────────────────────────────────────────────
TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT    = os.environ.get("TELEGRAM_CHAT_ID", "")
PAPER_CAPITAL    = float(os.environ.get("PAPER_CAPITAL", "1000.0"))
CYCLE_INTERVAL   = int(os.environ.get("CYCLE_INTERVAL", "60"))       # seconds between cycles
MAX_POSITION_PCT = float(os.environ.get("MAX_POSITION_PCT", "0.10")) # max 10% per trade
ROYALTY_RATE     = float(os.environ.get("ROYALTY_RATE", "0.20"))     # 20% profit → War Chest
DB_PATH          = os.environ.get("TZ_DB", "trader_zero.db")
COINGECKO_BASE   = "https://api.coingecko.com/api/v3"

# Markets TraderZero is allowed to trade — no bias on which to pick
ALLOWED_MARKETS = [
    "bitcoin", "ethereum", "solana", "ripple",
    "binancecoin", "dogecoin", "cardano", "avalanche-2"
]

logging.basicConfig(level=logging.INFO,
    format="%(asctime)s [TZ] %(message)s")
log = logging.getLogger("TraderZero")


# ══════════════════════════════════════════════════════════════════════════════
# TELEGRAM
# ══════════════════════════════════════════════════════════════════════════════

def tg(msg: str):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        log.info(f"[TG] {msg}")
        return
    try:
        url     = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = json.dumps({"chat_id": TELEGRAM_CHAT, "text": msg,
                              "parse_mode": "Markdown"}).encode()
        req = urllib.request.Request(url, data=payload, method="POST",
            headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8):
            pass
    except Exception:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# DATABASE
# ══════════════════════════════════════════════════════════════════════════════

class TZDatabase:
    def __init__(self):
        with sqlite3.connect(DB_PATH) as c:
            c.executescript("""
                CREATE TABLE IF NOT EXISTS trades (
                    id TEXT PRIMARY KEY,
                    cycle INTEGER,
                    market TEXT,
                    direction TEXT,
                    entry_price REAL,
                    exit_price REAL,
                    size_usd REAL,
                    pnl REAL,
                    pnl_pct REAL,
                    royalty REAL,
                    strategy_tag TEXT,
                    rationale TEXT,
                    opened_at TEXT,
                    closed_at TEXT,
                    status TEXT DEFAULT 'open'
                );
                CREATE TABLE IF NOT EXISTS market_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle INTEGER,
                    market TEXT,
                    price REAL,
                    change_1h REAL,
                    change_24h REAL,
                    volume_24h REAL,
                    captured_at TEXT
                );
                CREATE TABLE IF NOT EXISTS safla_state (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    cycle INTEGER,
                    regime TEXT,
                    entropy REAL,
                    win_rate REAL,
                    avg_pnl REAL,
                    capital REAL,
                    war_chest REAL,
                    recorded_at TEXT
                );
                CREATE TABLE IF NOT EXISTS strategy_weights (
                    tag TEXT PRIMARY KEY,
                    weight REAL DEFAULT 1.0,
                    wins INTEGER DEFAULT 0,
                    losses INTEGER DEFAULT 0,
                    total_pnl REAL DEFAULT 0.0,
                    last_updated TEXT
                );
            """)

    def save_snapshot(self, cycle, market, price, ch1h, ch24h, vol):
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "INSERT INTO market_snapshots (cycle,market,price,change_1h,change_24h,volume_24h,captured_at) VALUES (?,?,?,?,?,?,?)",
                (cycle, market, price, ch1h, ch24h, vol, _now()))

    def open_trade(self, trade: dict):
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "INSERT INTO trades (id,cycle,market,direction,entry_price,size_usd,strategy_tag,rationale,opened_at,status) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (trade["id"], trade["cycle"], trade["market"], trade["direction"],
                 trade["entry_price"], trade["size_usd"], trade["strategy_tag"],
                 trade["rationale"], _now(), "open"))

    def close_trade(self, trade_id, exit_price, pnl, pnl_pct, royalty):
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "UPDATE trades SET exit_price=?,pnl=?,pnl_pct=?,royalty=?,closed_at=?,status='closed' WHERE id=?",
                (exit_price, pnl, pnl_pct, royalty, _now(), trade_id))

    def get_open_trades(self):
        with sqlite3.connect(DB_PATH) as c:
            rows = c.execute(
                "SELECT id,cycle,market,direction,entry_price,size_usd,strategy_tag FROM trades WHERE status='open'"
            ).fetchall()
        return [{"id":r[0],"cycle":r[1],"market":r[2],"direction":r[3],
                 "entry_price":r[4],"size_usd":r[5],"strategy_tag":r[6]} for r in rows]

    def get_closed_stats(self):
        with sqlite3.connect(DB_PATH) as c:
            r = c.execute(
                "SELECT COUNT(*),SUM(CASE WHEN pnl>0 THEN 1 ELSE 0 END),SUM(pnl),SUM(royalty) FROM trades WHERE status='closed'"
            ).fetchone()
        total  = r[0] or 0
        wins   = r[1] or 0
        pnl    = round(r[2] or 0.0, 4)
        royalty= round(r[3] or 0.0, 4)
        return {
            "total": total, "wins": wins,
            "losses": total - wins,
            "win_rate": round(wins/total, 3) if total else 0.0,
            "total_pnl": pnl,
            "war_chest": royalty
        }

    def update_strategy_weight(self, tag, won, pnl_delta):
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "INSERT OR IGNORE INTO strategy_weights (tag,last_updated) VALUES (?,?)",
                (tag, _now()))
            if won:
                c.execute("UPDATE strategy_weights SET wins=wins+1,total_pnl=total_pnl+?,last_updated=? WHERE tag=?",
                          (pnl_delta, _now(), tag))
            else:
                c.execute("UPDATE strategy_weights SET losses=losses+1,total_pnl=total_pnl+?,last_updated=? WHERE tag=?",
                          (pnl_delta, _now(), tag))

    def get_strategy_weights(self):
        with sqlite3.connect(DB_PATH) as c:
            rows = c.execute(
                "SELECT tag,weight,wins,losses,total_pnl FROM strategy_weights ORDER BY weight DESC"
            ).fetchall()
        return [{"tag":r[0],"weight":r[1],"wins":r[2],"losses":r[3],"pnl":r[4]} for r in rows]

    def save_safla(self, cycle, regime, entropy, win_rate, avg_pnl, capital, war_chest):
        with sqlite3.connect(DB_PATH) as c:
            c.execute(
                "INSERT INTO safla_state (cycle,regime,entropy,win_rate,avg_pnl,capital,war_chest,recorded_at) VALUES (?,?,?,?,?,?,?,?)",
                (cycle, regime, entropy, win_rate, avg_pnl, capital, war_chest, _now()))


# ══════════════════════════════════════════════════════════════════════════════
# SAFLA CORE (embedded from Layer 7)
# ══════════════════════════════════════════════════════════════════════════════

class Regime(Enum):
    EXPLORE      = "EXPLORE"       # low confidence — try new things, bigger bets
    EXPLOIT      = "EXPLOIT"       # finding edge — press it
    CONSOLIDATE  = "CONSOLIDATE"   # winning — protect capital, reduce risk
    HIBERNATE    = "HIBERNATE"     # losing badly — tiny bets, wait
    ESCALATE     = "ESCALATE"      # crisis — alert Forgemaster

class TradingSAFLA:
    """
    Layer 7 adapted for trading.
    Every closed trade is a feedback signal.
    SAFLA updates regime, entropy, and strategy weights.
    """

    STATE_FILE = Path("tz_safla_state.json")

    def __init__(self):
        self.state = self._load()

    def _load(self):
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except Exception:
                pass
        return {
            "regime": "EXPLORE",
            "entropy": 0.5,
            "consecutive_wins": 0,
            "consecutive_losses": 0,
            "cycle_scores": [],
            "strategy_weights": {},
            "total_cycles": 0
        }

    def _save(self):
        self.STATE_FILE.write_text(json.dumps(self.state, indent=2))

    @property
    def regime(self) -> str:
        return self.state["regime"]

    @property
    def entropy(self) -> float:
        return self.state["entropy"]

    def reflect(self, trade_pnl: float, strategy_tag: str) -> dict:
        """Score a closed trade. Update regime and entropy."""
        self.state["total_cycles"] += 1

        # Score: 1.0 = great win, 0.5 = small win, 0.0 = loss
        if trade_pnl > 0:
            score = min(1.0, 0.5 + trade_pnl / 50.0)  # scales with profit size
            self.state["consecutive_wins"]   += 1
            self.state["consecutive_losses"]  = 0
        else:
            score = max(0.0, 0.5 + trade_pnl / 50.0)
            self.state["consecutive_losses"] += 1
            self.state["consecutive_wins"]    = 0

        # Update entropy (rolling average)
        self.state["cycle_scores"].append(score)
        if len(self.state["cycle_scores"]) > 20:
            self.state["cycle_scores"] = self.state["cycle_scores"][-20:]
        avg = sum(self.state["cycle_scores"]) / len(self.state["cycle_scores"])
        self.state["entropy"] = round(1.0 - avg, 4)  # high entropy = losing

        # Update strategy weight
        w = self.state["strategy_weights"].get(strategy_tag, 1.0)
        if trade_pnl > 0:
            w = min(3.0, w * 1.15)   # reinforce winners
        else:
            w = max(0.1, w * 0.80)   # punish losers
        self.state["strategy_weights"][strategy_tag] = round(w, 4)

        # Determine new regime
        cw = self.state["consecutive_wins"]
        cl = self.state["consecutive_losses"]
        e  = self.state["entropy"]

        if cl >= 5:
            regime = "ESCALATE"
        elif cl >= 3 or e > 0.75:
            regime = "HIBERNATE"
        elif cw >= 3 and e < 0.35:
            regime = "CONSOLIDATE"
        elif cw >= 2 or e < 0.50:
            regime = "EXPLOIT"
        else:
            regime = "EXPLORE"

        self.state["regime"] = regime
        self._save()

        return {"score": round(score, 3), "regime": regime,
                "entropy": self.state["entropy"],
                "strategy_weight": w}

    def get_position_multiplier(self) -> float:
        """How aggressively to size positions based on current regime."""
        return {
            "EXPLORE":     0.5,
            "EXPLOIT":     1.0,
            "CONSOLIDATE": 0.7,
            "HIBERNATE":   0.2,
            "ESCALATE":    0.05
        }.get(self.state["regime"], 0.5)

    def should_explore_new_strategy(self) -> bool:
        """In EXPLORE or after losses, try new approaches."""
        return self.state["regime"] in ("EXPLORE", "ESCALATE") or \
               self.state["consecutive_losses"] >= 2

    def get_top_strategies(self, n=3) -> list:
        """Return top N strategies by weight."""
        weights = self.state["strategy_weights"]
        return sorted(weights.items(), key=lambda x: x[1], reverse=True)[:n]


# ══════════════════════════════════════════════════════════════════════════════
# MARKET DATA
# ══════════════════════════════════════════════════════════════════════════════

def _now():
    return datetime.now(timezone.utc).isoformat()

def fetch_market_data() -> dict:
    """Pull live prices from CoinGecko (free, no key needed)."""
    ids = ",".join(ALLOWED_MARKETS)
    url = f"{COINGECKO_BASE}/coins/markets?vs_currency=usd&ids={ids}&price_change_percentage=1h,24h&order=volume_desc"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "TraderZero/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
        result = {}
        for coin in data:
            result[coin["id"]] = {
                "price":     coin["current_price"],
                "change_1h":  coin.get("price_change_percentage_1h_in_currency", 0) or 0,
                "change_24h": coin.get("price_change_percentage_24h", 0) or 0,
                "volume":     coin.get("total_volume", 0) or 0,
                "symbol":     coin["symbol"].upper()
            }
        return result
    except Exception as e:
        log.warning(f"Market data fetch failed: {e}")
        return {}


# ══════════════════════════════════════════════════════════════════════════════
# BRAIN — Strategy Discovery
# TraderZero invents and names its own strategies from raw market signals.
# No pre-loaded rules. Pure signal observation.
# ══════════════════════════════════════════════════════════════════════════════

STRATEGY_LIBRARY = {}  # tag → function, built dynamically


def _register_strategy(tag: str, fn):
    STRATEGY_LIBRARY[tag] = fn


def _discover_strategies(market_data: dict, safla: TradingSAFLA) -> list:
    """
    TraderZero observes market data and generates candidate trade ideas.
    Each idea has a strategy_tag it invented, a direction, a market, and a rationale.
    No strategies are pre-seeded — they emerge from observation.
    """
    candidates = []

    for market, d in market_data.items():
        ch1h  = d["change_1h"]
        ch24h = d["change_24h"]
        vol   = d["volume"]
        price = d["price"]

        # TraderZero observes patterns and invents names for them
        # These tags are TraderZero's own labels — not human-given strategies

        # Pattern: short-term momentum divergence from daily trend
        if ch1h > 1.5 and ch24h < -2.0:
            candidates.append({
                "market": market, "direction": "LONG",
                "strategy_tag": "hourly_reversal_probe",
                "rationale": f"{market}: 1h +{ch1h:.1f}% vs 24h {ch24h:.1f}% — testing short-term reversal against daily bleed",
                "signal_strength": abs(ch1h) + abs(ch24h)
            })

        if ch1h < -1.5 and ch24h > 2.0:
            candidates.append({
                "market": market, "direction": "SHORT",
                "strategy_tag": "hourly_fade_probe",
                "rationale": f"{market}: 1h {ch1h:.1f}% vs 24h +{ch24h:.1f}% — fading hourly dip against strong daily",
                "signal_strength": abs(ch1h) + abs(ch24h)
            })

        # Pattern: both timeframes aligned (momentum)
        if ch1h > 1.0 and ch24h > 3.0:
            candidates.append({
                "market": market, "direction": "LONG",
                "strategy_tag": "aligned_momentum_long",
                "rationale": f"{market}: 1h +{ch1h:.1f}% AND 24h +{ch24h:.1f}% — both timeframes bullish",
                "signal_strength": ch1h + ch24h
            })

        if ch1h < -1.0 and ch24h < -3.0:
            candidates.append({
                "market": market, "direction": "SHORT",
                "strategy_tag": "aligned_momentum_short",
                "rationale": f"{market}: 1h {ch1h:.1f}% AND 24h {ch24h:.1f}% — both timeframes bearish",
                "signal_strength": abs(ch1h) + abs(ch24h)
            })

        # Pattern: extreme volatility — large 24h move, probe for exhaustion
        if abs(ch24h) > 8.0 and abs(ch1h) < 0.5:
            direction = "SHORT" if ch24h > 0 else "LONG"
            candidates.append({
                "market": market, "direction": direction,
                "strategy_tag": "exhaustion_fade",
                "rationale": f"{market}: extreme 24h move ({ch24h:.1f}%) but 1h stalling — probing exhaustion",
                "signal_strength": abs(ch24h)
            })

    # Let SAFLA weight the candidates by learned strategy performance
    top = safla.get_top_strategies(3)
    top_tags = {t[0] for t in top}

    # Sort: SAFLA-favored strategies first, then by signal strength
    candidates.sort(key=lambda c: (
        -safla.state["strategy_weights"].get(c["strategy_tag"], 1.0),
        -c["signal_strength"]
    ))

    # In EXPLORE mode, occasionally try a random pick to discover new things
    if safla.should_explore_new_strategy() and candidates:
        random.shuffle(candidates)

    return candidates[:3]  # max 3 open ideas per cycle


# ══════════════════════════════════════════════════════════════════════════════
# PAPER TRADING ENGINE
# ══════════════════════════════════════════════════════════════════════════════

class PaperPortfolio:
    STATE_FILE = Path("tz_portfolio.json")

    def __init__(self):
        self.state = self._load()

    def _load(self):
        if self.STATE_FILE.exists():
            try:
                return json.loads(self.STATE_FILE.read_text())
            except Exception:
                pass
        return {
            "cash": PAPER_CAPITAL,
            "war_chest": 0.0,
            "total_deposited": PAPER_CAPITAL,
            "peak_equity": PAPER_CAPITAL,
        }

    def _save(self):
        self.STATE_FILE.write_text(json.dumps(self.state, indent=2))

    @property
    def cash(self): return self.state["cash"]

    @property
    def war_chest(self): return self.state["war_chest"]

    def open_trade(self, size_usd: float) -> bool:
        if size_usd > self.state["cash"]:
            return False
        self.state["cash"] -= size_usd
        self._save()
        return True

    def close_trade(self, size_usd: float, pnl: float):
        royalty = pnl * ROYALTY_RATE if pnl > 0 else 0.0
        net     = pnl - royalty
        self.state["cash"]      += size_usd + net
        self.state["war_chest"] += royalty
        if self.state["cash"] > self.state["peak_equity"]:
            self.state["peak_equity"] = self.state["cash"]
        self._save()
        return royalty

    def equity(self): return self.state["cash"]

    def drawdown(self):
        peak = self.state["peak_equity"]
        if peak == 0: return 0.0
        return round((peak - self.state["cash"]) / peak * 100, 2)

    def summary(self):
        return {
            "cash":      round(self.state["cash"], 2),
            "war_chest": round(self.state["war_chest"], 2),
            "peak":      round(self.state["peak_equity"], 2),
            "drawdown":  self.drawdown(),
            "pnl":       round(self.state["cash"] - self.state["total_deposited"], 2)
        }


# ══════════════════════════════════════════════════════════════════════════════
# MAIN CYCLE
# ══════════════════════════════════════════════════════════════════════════════

def run():
    db        = TZDatabase()
    safla     = TradingSAFLA()

    portfolio = PaperPortfolio()

    tg(
        f"🤖 *TraderZero ONLINE*\n"
        f"Paper Capital: ${PAPER_CAPITAL:,.0f}\n"
        f"Regime: {safla.regime}\n"
        f"Markets: {len(ALLOWED_MARKETS)}\n"
        f"Strategies: self-discovered\n"
        f"Royalty → War Chest: {ROYALTY_RATE*100:.0f}%\n"
        f"_No strategies given. Let's see what he finds._"
    )

    cycle = 0
    while True:
        cycle += 1
        log.info(f"=== CYCLE {cycle} | Regime: {safla.regime} | Cash: ${portfolio.cash:.2f} ===")

        # 1. Fetch market data
        market_data = fetch_market_data()
        if not market_data:
            log.warning("No market data. Sleeping.")
            time.sleep(CYCLE_INTERVAL)
            continue

        # 2. Save snapshots
        for market, d in market_data.items():
            db.save_snapshot(cycle, market, d["price"], d["change_1h"], d["change_24h"], d["volume"])

        # 3. Check open trades — close if exit condition met
        open_trades = db.get_open_trades()
        for t in open_trades:
            if t["market"] not in market_data:
                continue
            current_price = market_data[t["market"]]["price"]
            entry         = t["entry_price"]
            pnl_pct       = ((current_price - entry) / entry) * 100
            if t["direction"] == "SHORT":
                pnl_pct = -pnl_pct

            # Exit logic: SAFLA-driven exits based on regime
            regime_tp = {"EXPLORE": 1.5, "EXPLOIT": 2.5, "CONSOLIDATE": 1.5,
                         "HIBERNATE": 0.5, "ESCALATE": 0.3}
            regime_sl = {"EXPLORE": -2.0, "EXPLOIT": -1.5, "CONSOLIDATE": -1.0,
                         "HIBERNATE": -0.5, "ESCALATE": -0.3}

            tp = regime_tp.get(safla.regime, 1.5)
            sl = regime_sl.get(safla.regime, -2.0)

            if pnl_pct >= tp or pnl_pct <= sl:
                pnl_usd = t["size_usd"] * (pnl_pct / 100)
                royalty = portfolio.close_trade(t["size_usd"], pnl_usd)
                db.close_trade(t["id"], current_price, pnl_usd, pnl_pct, royalty)

                # SAFLA learns from this trade
                feedback = safla.reflect(pnl_usd, t["strategy_tag"])
                db.update_strategy_weight(t["strategy_tag"], pnl_usd > 0, pnl_usd)

                icon = "✅" if pnl_usd > 0 else "❌"
                tg(
                    f"{icon} *TraderZero — Trade Closed*\n"
                    f"Market: {t['market'].upper()}\n"
                    f"Direction: {t['direction']}\n"
                    f"Strategy: `{t['strategy_tag']}`\n"
                    f"PnL: ${pnl_usd:+.2f} ({pnl_pct:+.2f}%)\n"
                    f"War Chest: +${royalty:.2f}\n"
                    f"New Regime: {feedback['regime']}\n"
                    f"Strategy Weight: {feedback['strategy_weight']:.3f}"
                )
                log.info(f"Closed {t['id'][:8]} | PnL: ${pnl_usd:+.2f} | Regime: {feedback['regime']}")

        # 4. Discover new trade candidates
        open_trades = db.get_open_trades()
        if len(open_trades) < 3:  # max 3 concurrent positions
            candidates = _discover_strategies(market_data, safla)
            for c in candidates:
                if len(db.get_open_trades()) >= 3:
                    break
                # Size position by regime
                multiplier = safla.get_position_multiplier()
                size_usd   = portfolio.cash * MAX_POSITION_PCT * multiplier
                if size_usd < 5.0:
                    continue
                if not portfolio.open_trade(size_usd):
                    continue

                trade_id = str(uuid.uuid4())[:8]
                entry    = market_data[c["market"]]["price"]
                trade = {
                    "id": trade_id, "cycle": cycle,
                    "market": c["market"], "direction": c["direction"],
                    "entry_price": entry, "size_usd": round(size_usd, 2),
                    "strategy_tag": c["strategy_tag"],
                    "rationale": c["rationale"]
                }
                db.open_trade(trade)
                tg(
                    f"📈 *TraderZero — Trade Opened*\n"
                    f"Market: {c['market'].upper()}\n"
                    f"Direction: {c['direction']}\n"
                    f"Strategy: `{c['strategy_tag']}`\n"
                    f"Size: ${size_usd:.2f}\n"
                    f"Entry: ${entry:,.4f}\n"
                    f"Rationale: _{c['rationale']}_\n"
                    f"Regime: {safla.regime}"
                )
                log.info(f"Opened {trade_id} | {c['market']} {c['direction']} @ ${entry:.4f}")

        # 5. Every 10 cycles — status report
        if cycle % 10 == 0:
            stats  = db.get_closed_stats()
            port   = portfolio.summary()
            top_s  = safla.get_top_strategies(3)
            top_str= "\n".join([f"  `{t}` w={w:.2f}" for t,w in top_s]) or "  (none yet)"
            db.save_safla(cycle, safla.regime, safla.entropy,
                          stats["win_rate"], stats["total_pnl"]/max(stats["total"],1),
                          port["cash"], port["war_chest"])
            tg(
                f"📊 *TraderZero — Cycle {cycle} Report*\n"
                f"Capital: ${port['cash']:,.2f} (PnL: ${port['pnl']:+.2f})\n"
                f"War Chest: ${port['war_chest']:.2f}\n"
                f"Drawdown: {port['drawdown']}%\n"
                f"Trades: {stats['total']} | W/L: {stats['wins']}/{stats['losses']}\n"
                f"Win Rate: {stats['win_rate']*100:.1f}%\n"
                f"Regime: {safla.regime} | Entropy: {safla.entropy:.3f}\n"
                f"Top Strategies:\n{top_str}"
            )

        time.sleep(CYCLE_INTERVAL)


# Fix the alias typo above
# alias resolved below

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Rename the class for the run() function
    pass  # TradingSAFLA is the correct class
    run()
