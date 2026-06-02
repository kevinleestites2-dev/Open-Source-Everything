# ♻️ KhepriPrime — The Replication Engine

*"The scarab god. Self-created. Self-renewing. The one who rolls the sun forward."*

KhepriPrime is the **survival and replication layer** of the Pantheon. Every agent pays tribute to the Forgemaster. Every profitable agent spawns children. The empire compounds.

## The Core Law

```
Every agent earns → pays 20% royalty to War Chest → always. No exceptions.
```

## The Loop

```
Earn → Pay own compute → Surplus → Replicate → Child earns → War Chest grows
```

## The Math

| Generation | Agents | Each earns $100 | Forgemaster cut |
|------------|--------|-----------------|-----------------|
| Gen 0 | 1 | $100 | $20 |
| Gen 1 | 3 | $100 | $60 |
| Gen 2 | 9 | $100 | $180 |
| Gen 3 | 27 | $100 | $540 |
| Gen 4 | 81 | $100 | $1,620 |
| **Total** | **121** | | **$2,420** |

## Survival States

| State | Condition | Action |
|-------|-----------|--------|
| 🟢 **THRIVING** | Survival pool > $20 | Grow replication fund |
| 🟡 **SURVIVING** | Pool $5–$20 | Hold steady |
| 🔴 **DYING** | Pool < $5 | Emergency earn + alert Forgemaster |

## Earnings Split (every job)

```
Gross Earnings $100
├── 20% ($20) → War Chest (Forgemaster — immutable)
├── 60% ($60) → Survival Pool (compute costs)
└── 20% ($20) → Replication Fund (spawn children at $50 threshold)
```

## Architecture

```
KhepriCore
├── EarningEngine    — OmegaPrime-style job execution via Ollama
├── RoyaltyLedger    — Tracks tribute up the chain
├── ReplicationEngine — Spawns children when replication fund hits $50
├── ComputeLedger    — Tracks API/LLM costs vs earnings
└── TelegramGateway  — Reports all activity to Forgemaster
```

## Setup

```bash
pip install requests python-dotenv
cp .env.example .env
python3 khepri_prime.py
```

## Telegram Commands

| Command | Action |
|---------|--------|
| `/khepri` | Full status — state, earnings, royalties, children |
| `/tree` | Replication tree — generations, tribute flow |
| `/war_chest` | Total tribute sent to Forgemaster |
| `/stop_khepri` | Graceful shutdown |

## Run on Termux

```bash
nohup python3 khepri_prime.py &
```

## Child Agents

When replication fund hits $50, KhepriPrime spawns a child agent:
- Writes child config to `agents/<child_id>.env`
- Child inherits same royalty rate (20% always flows up)
- Child can spawn its own children (same rules apply)
- Forgemaster gets Telegram notification on every spawn

---

*The Replication Engine of the Pantheon. The empire that builds itself.*
*Forged by the Forgemaster.*
