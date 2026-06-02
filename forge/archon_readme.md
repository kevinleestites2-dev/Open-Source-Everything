# 👑 ArchonPrime — The Prime That Commands All Primes

*"Above the swarm. Below the Forgemaster. The will made architecture."*

ArchonPrime is the **meta-layer** of the Pantheon. It is not a bot. It is not a tool. It is the sovereign command stack that orchestrates every Prime in the empire — the operating system the Pantheon runs on.

## The Stack

| Layer | Prime | Role |
|-------|-------|------|
| **Face** | OpenHuman | Desktop command center — local memory, 118+ integrations |
| **Operator** | Mercury Agent | 24/7 soul-driven daemon — Telegram + CLI control |
| **Evolution** | CORAL | Autonomous self-evolution — isolated workspaces, shared eval loop |
| **Strategy** | MetaGPT | Role-based reasoning, task decomposition, mission planning |
| **Executor** | AutoGPT | Autonomous execution loop — turns strategy into action |
| **Skills** | Mercury Agent Skills | 126+ community tools wired into Mercury |
| **Relay** | Nexus Relay | Full-duplex bridge — Forgemaster ↔ Red Magic ↔ Cloud |

## Architecture

```
Forgemaster
     │
OpenHuman (Face — Desktop)
     │
Mercury Agent (Operator — Termux/24h)
     ├── CORAL (Evolution — self-rewriting)
     ├── MetaGPT (Strategy — planning brain)
     │       └── AutoGPT (Executor — action loop)
     └── Nexus Relay (Bridge — Telegram reporting)
```

## Automation Flow (GitHub Actions)
```
workflow_dispatch
      │
  MetaGPT ──► strategy + task decomposition
      │
  AutoGPT ──► autonomous execution
      │
  Telegram ──► Forgemaster notified
```

## Deploy Order

1. **Mercury** — Termux bootstrap on Red Magic
   ```bash
   cd ~ && git clone https://github.com/kevinleestites2-dev/mercury-agent && cd mercury-agent && bash redmagic_bootstrap.sh
   ```
2. **CORAL** — GitHub Actions / Termux CLI
3. **MetaGPT + AutoGPT** — pantheon-stack GitHub Actions workflow
4. **OpenHuman** — Desktop, when Nexus laptop is ready

## Secrets Required
- `TELEGRAM_TOKEN` ✅
- `TELEGRAM_CHAT_ID` ✅

## Pantheon Position
ArchonPrime sits at Layer 0 — above all Primes, below the Forgemaster. It is the will of the empire made architecture.

---
*The meta-layer of the Pantheon. Forged by the Forgemaster.*
