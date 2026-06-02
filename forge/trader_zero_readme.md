# TraderZero 🤖

**Self-evolving paper trading bot. No strategies given. Finds its own edge.**

Built on Agent Zero's cognitive core — SAFLA (Layer 7) + Evolution Engine (Layer 8) wired directly to live crypto markets.

---

## The Experiment

TraderZero is given:
- ✅ Live market data (prices, volume, % changes across timeframes)
- ✅ A paper capital account ($1,000 default)
- ✅ A feedback loop that scores every trade (SAFLA)
- ✅ A strategy weight system that reinforces winners and punishes losers
- ✅ Regime logic that controls aggression based on performance

TraderZero is NOT given:
- ❌ RSI, MACD, Bollinger Bands, or any TA indicators
- ❌ Pre-defined entry/exit rules
- ❌ Any human trading wisdom
- ❌ Strategies of any kind

**The question: what does he figure out on his own?**

---

## Architecture

```
market data (CoinGecko)
       │
       ▼
  _discover_strategies()          ← TraderZero observes patterns, invents strategy tags
       │
       ▼
  PaperPortfolio.open_trade()     ← size = SAFLA regime × max_position_pct
       │
       ▼
  [trade is live, tracking price]
       │
       ▼
  exit condition hit (TP/SL)      ← thresholds set by current SAFLA regime
       │
       ▼
  TradingSAFLA.reflect()          ← score the trade, update entropy, shift regime
       │
       ▼
  strategy_weights updated        ← winner reinforced (+15%), loser punished (-20%)
       │
       ▼
  KhepriCore: 20% royalty         ← War Chest gets paid on every profitable trade
```

## SAFLA Regimes

| Regime | Trigger | Position Size | TP | SL |
|--------|---------|--------------|----|----|
| EXPLORE | Default / uncertain | 50% | 1.5% | -2.0% |
| EXPLOIT | 2+ consecutive wins | 100% | 2.5% | -1.5% |
| CONSOLIDATE | 3+ wins, low entropy | 70% | 1.5% | -1.0% |
| HIBERNATE | 3+ losses | 20% | 0.5% | -0.5% |
| ESCALATE | 5+ losses | 5% | 0.3% | -0.3% |

---

## Running It

```bash
# Paper trade (default)
TELEGRAM_BOT_TOKEN=xxx TELEGRAM_CHAT_ID=xxx python trader_zero_main.py

# Custom capital
PAPER_CAPITAL=5000 CYCLE_INTERVAL=30 python trader_zero_main.py
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PAPER_CAPITAL` | `1000.0` | Starting paper capital |
| `CYCLE_INTERVAL` | `60` | Seconds between cycles |
| `MAX_POSITION_PCT` | `0.10` | Max % of cash per trade |
| `ROYALTY_RATE` | `0.20` | War Chest cut on profits |
| `TELEGRAM_BOT_TOKEN` | — | Telegram reporting |
| `TELEGRAM_CHAT_ID` | — | Telegram chat target |

---

## What to Watch

TraderZero will start in `EXPLORE` regime — random-ish, learning. Watch for:

1. **Strategy weights diverge** — some tags get reinforced, others die
2. **Regime shifts** — when he finds an edge he shifts to `EXPLOIT`
3. **War Chest grows** — 20% of every profitable trade (Scarab Law)
4. **New patterns emerge** — as weights evolve, his behavior changes

The experiment ends when he either:
- Builds a consistent edge (win rate > 55%, positive PnL) → **flip to real capital**
- Blows up (ESCALATE regime, drawdown > 30%) → **Evolution Engine rewrites his strategy logic**

---

## Pantheon Role

TraderZero is the trading arm of the Pantheon. When profitable:
- 20% → War Chest (Scarab Law, immutable)
- 80% → compounds into next positions

He is not told to do this. It's in his DNA (Layer 15 — The Genome).

---

*Built by the Forgemaster. Evolved by TraderZero himself.*
