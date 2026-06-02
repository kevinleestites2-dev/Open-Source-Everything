import base64, json, urllib.request, urllib.error

token = "YOUR_GITHUB_TOKEN"
files = {}

# ── SAFLA as a Mercury Skill ──────────────────────────────────────────────────
files["skills/safla/SKILL.md"] = """---
name: safla
description: SAFLA v2 feedback loop — reflects on cycle outcome, scores it, updates entropy and regime, signals T2 adaptation layer to rebalance expert weights.
version: 2.0.0
category: system
categories:
  - system
  - intelligence
intents:
  - reflect on last cycle
  - update regime
  - rebalance weights
  - safla status
  - entropy report
  - feedback loop
tags:
  - safla
  - feedback
  - adaptation
  - entropy
  - regime
allowed-tools:
  - read_file
  - write_file
  - run_command
---

# SAFLA — Self-Adaptive Feedback Loop

Use this skill after any significant agent cycle to reflect, score, and rebalance.

## Workflow

1. Read `agent_zero_safla_state.json` for current entropy + regime
2. Score the last cycle outcome (success=1.0, partial=0.6, failure=0.1)
3. Update entropy: -0.05 on success, +0.08 on failure, +0.01 on partial
4. Select regime: EXPLORE (<0.30) | EXPLOIT (<0.60) | CONSOLIDATE (<0.75) | HIBERNATE (>=0.75)
5. Signal T2 adaptation — reinforce lead mode, decay others
6. Write updated state back to `agent_zero_safla_state.json`
7. Report: cycle count, score, entropy, regime, best mode

## Regimes

| Regime | Entropy | Behavior |
|---|---|---|
| EXPLORE | 0.00–0.30 | High learning rate, take risks |
| EXPLOIT | 0.30–0.60 | Normal execution, steady weights |
| CONSOLIDATE | 0.60–0.75 | Reduce learning rate, stabilize |
| HIBERNATE | 0.75–1.00 | Minimal activity, protect state |
| ESCALATE | manual | Maximum output, override limits |
"""

# ── T2 Adaptation as a Mercury Skill ─────────────────────────────────────────
files["skills/t2-adaptation/SKILL.md"] = """---
name: t2-adaptation
description: Transformer-Squared (T2) expert ensemble — runs two-pass multi-mode processing and adapts expert weights based on SAFLA feedback. Modes: analyst, strategist, synthesizer, critic, executor.
version: 2.0.0
category: intelligence
categories:
  - intelligence
  - system
intents:
  - adapt expert weights
  - t2 status
  - which mode is dominant
  - expert ensemble
  - adapt strategy
  - weight update
tags:
  - t2
  - transformer-squared
  - adaptation
  - experts
  - weights
allowed-tools:
  - read_file
  - write_file
---

# T2 Adaptation — Transformer-Squared Expert Ensemble

Use this skill when choosing how to approach a complex task, or after SAFLA signals a weight update.

## Expert Modes

| Mode | Lens |
|---|---|
| analyst | Break down the task into components. What are the facts? |
| strategist | What is the optimal path forward? What are the tradeoffs? |
| synthesizer | Combine all available information into a coherent whole. |
| critic | What could go wrong? What is missing? Challenge the plan. |
| executor | What is the single next action to take right now? |

## Workflow

1. Read `agent_zero_expert_weights.json` — get current weights
2. Run Pass 1: each mode processes the task through its own lens
3. Run Pass 2: elect lead mode (highest weight)
4. Execute through lead mode's lens
5. After cycle: SAFLA calls `feedback(lead_mode, score)` → weights update
6. Write new weights back to `agent_zero_expert_weights.json`

## Weight Rules

- Winner: `weight += 0.10 * (score - 0.5)`  
- Loser: `weight += 0.02 * (1.0 - score - 0.5)`  
- Bounds: `[0.1, 2.0]`
"""

# ── Pantheon Monitor as a Mercury Skill ──────────────────────────────────────
files["skills/pantheon-monitor/SKILL.md"] = """---
name: pantheon-monitor
description: Monitor all live Pantheon Primes — GhostPrime, Nexus Relay, SAFLA state, War Chest balance. Reports status via Telegram.
version: 1.0.0
category: system
categories:
  - system
  - monitoring
intents:
  - pantheon status
  - check all primes
  - ghost prime status
  - nexus relay status
  - war chest balance
  - heartbeat report
  - are the primes alive
tags:
  - pantheon
  - monitoring
  - ghostprime
  - nexus
  - war chest
allowed-tools:
  - fetch_url
  - read_file
  - run_command
---

# Pantheon Monitor

Use this skill on heartbeat or when the Forgemaster asks for a status report.

## Endpoints to Check

| Prime | URL | Expected |
|---|---|---|
| GhostPrime | https://cloakprime-swarm.onrender.com/health | `{"status":"ok"}` |
| Nexus Relay | https://nexus-relay-production.up.railway.app/ping | version string |

## Workflow

1. `fetch_url` each endpoint — record UP/DOWN + response time
2. Read `agent_zero_safla_state.json` — extract regime, entropy, cycles
3. Read `midas_tracker.py` or War Chest state — extract current balance
4. Compose heartbeat report:

```
⚡ AgentZero Heartbeat — [timestamp]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
GhostPrime:   [✅ UP / ❌ DOWN]
Nexus Relay:  [✅ UP / ❌ DOWN]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SAFLA: [REGIME] | entropy=[X] | cycles=[N]
Best mode: [mode] ([score])
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
War Chest: $[X]
  → Nexus ($3k):   [X]% complete
  → Citadel ($5k): [X]% complete
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

5. If any Prime is DOWN: prepend 🚨 ALERT to the report
6. If entropy > 0.70: add ⚠️ HIGH ENTROPY — CONSOLIDATE REGIME
"""

# ── Layer manifest as a reference skill ──────────────────────────────────────
files["skills/agent-zero-layers/SKILL.md"] = """---
name: agent-zero-layers
description: Reference map of all 13 Agent Zero cognitive layers — what each does, which repo it sources from, and current phase status.
version: 3.0.0
category: system
categories:
  - system
  - reference
intents:
  - layer status
  - architecture overview
  - what layers are done
  - phase status
  - pantheon architecture
tags:
  - architecture
  - layers
  - pantheon
  - agent-zero
allowed-tools: []
---

# Agent Zero — 13-Layer Architecture

| Layer | Name | Source | Status |
|---|---|---|---|
| 1 | The Vault | agent-zero (COG) | ✅ Phase 1 |
| 2 | Perception | gpt-researcher | ✅ Phase 3 |
| 3 | Runtime Body | opencrabs | ✅ Phase 1 |
| 4 | Semantic Router | Brain.ai | ✅ Phase 2 |
| 5 | Cognition | Base-of-Self-Aware-AI | ✅ Phase 2 |
| 5b | Second Brain | **Mercury (this repo)** | ✅ Phase 2 |
| 6 | Adaptation | Transformer-Squared | ✅ Phase 3 |
| 7 | Feedback Loop | SAFLA v2 | ✅ Phase 3 |
| 8 | Evolution Engine | Entwickler | 🔄 Phase 4 |
| 9 | Tool Forge | tiny-self-improve-ai | 🔄 Phase 4 |
| 10 | Identity Layer | self-recognition | 🔄 Phase 5 |
| 11 | The Doctrine | Self-Evolving-Agents | 🔒 Locked |
| 12 | Super Intelligence | convergence of 1–11 | 🌀 Emergent |
| 13 | Physical Form | Psi0 | 🔄 Phase 8 |

## Signal Flow

```
Signal IN → Layer 4 (Router) → Layer 2/3/5/10
                              → Layer 6 (T2 Ensemble)
                              → Layer 7 (SAFLA Reflect)
                              → Response OUT
                              → Weights updated + memory persisted
```

## Mercury as the Chassis

Mercury provides:
- Soul files (soul.md, persona.md, taste.md, heartbeat.md)
- 31 hardened tools (filesystem, git, github, web, shell, scheduler)
- Dual-layer Second Brain (SQLite + FTS5, conscious/subconscious)
- Telegram + CLI channels
- Sub-agent supervisor
- Token budgeting
- Skill system (this directory)

Agent Zero adds:
- Pantheon soul identity
- SAFLA feedback loop (Layer 7)
- T2 adaptation engine (Layer 6)
- Pantheon Prime monitoring
- War Chest tracking
"""

# Push all
for filepath, content in files.items():
    encoded = base64.b64encode(content.encode()).decode()
    sha = None
    try:
        req = urllib.request.Request(
            f"https://api.github.com/repos/kevinleestites2-dev/mercury-agent/contents/{filepath}",
            headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(req) as resp:
            sha = json.loads(resp.read()).get("sha")
    except:
        pass

    payload = {"message": f"feat(agent-zero): skill — {filepath}", "content": encoded}
    if sha:
        payload["sha"] = sha

    req = urllib.request.Request(
        f"https://api.github.com/repos/kevinleestites2-dev/mercury-agent/contents/{filepath}",
        data=json.dumps(payload).encode(), method="PUT",
        headers={"Authorization": f"token {token}", "Accept": "application/vnd.github+json",
                 "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ PUSHED: {filepath}")
    except urllib.error.HTTPError as e:
        print(f"❌ ERROR {filepath}: {e.code} {e.read().decode()[:200]}")
