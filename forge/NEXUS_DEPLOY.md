# NEXUS DEPLOY GUIDE
### Bringing the Pantheon Online — 1TB Laptop / The Throne
**Version 1.0 | 2026-05-03**

> *"The Forgemaster is the humble servant. The Primes do the work."*

---

## Pre-Flight Checklist

Before you begin, have ready:
- [ ] 1TB Laptop (The Nexus) powered on
- [ ] Internet connection (stable)
- [ ] OpenAI API key (or Anthropic)
- [ ] GitHub account
- [ ] 30–60 minutes

---

## PHASE 1 — The Foundation (The OS)
### Install Suna — The Nexus OS

Suna provides the persistent Ubuntu sandbox every Prime runs inside.
Shared filesystem. Shared memory. Shared credentials. 24/7.

```bash
# Step 1: One-line Suna install
curl -fsSL https://kortix.com/install | bash

# Step 2: Start Suna
suna start

# Step 3: Verify — open The Throne in browser
# http://localhost:3000

# Step 4: Create your first persistent agent (MetaPrime)
# In the Suna UI → New Agent → Name: MetaPrime
# System prompt: "You are MetaPrime — the Overlord/Hyper-Kernel of the Pantheon.
#   Route all missions to the appropriate Prime. You are the nervous system."
```

**What you now have:**
- Persistent Ubuntu Linux machine running 24/7
- Web UI at localhost:3000
- Shared filesystem for all Primes
- Built-in browser, bash, file, and API access

---

## PHASE 2 — The Eyes
### Install browser-use — The Ocular Link

Every Prime gains the ability to see and interact with any website.

```bash
# Install browser-use
pip install browser-use

# Install Chromium (one-time)
uvx playwright install chromium

# Verify
python3 -c "from browser_use import Browser; print('Eyes online.')"
```

**Primes that gain Eyes:**
- OrionPrime → hunts Zillow, foreclosures, FB Marketplace
- ScoutPrime → full internet recon
- MidasPrime → monitors auctions, estate sales
- ZetaPrime → deploys to GitHub, interacts with any web UI
- SentinelPrime → web vulnerability scanning

---

## PHASE 2b — The Zero-Cost Recon Layer
### Install OpenCLI — Website → Deterministic CLI

browser-use costs tokens every run. OpenCLI builds an adapter ONCE — then runs FREE forever.
750+ adapters already built. Every Prime gets structured web data at zero marginal cost.

```bash
# Install OpenCLI
npm install -g @jackwener/opencli

# Install the AI agent skill (lets any Prime write new adapters)
npx skills add jackwener/opencli

# Verify — run your first intel command
opencli hackernews top --limit 5
opencli zillow search "Fort Myers FL" --max-price 150000

# Connect to your logged-in Chrome (no credentials exposed)
opencli browser connect
```

**OrionPrime now has free, deterministic Zillow data. Forever.**

```bash
# OrionPrime morning recon — zero tokens, zero cost
opencli zillow search "Fort Myers FL" --max-price 120000 --keyword "as-is"
opencli zillow search "Cape Coral FL" --max-price 120000 --keyword "motivated seller"
opencli craigslist rea "Fort Myers" --max-price 100000
opencli facebook marketplace "houses Fort Myers" --type real_estate

# Pipe straight into PropPilot
opencli zillow search "Fort Myers FL" --max-price 150000 | python3 orion_prime_score.py
```

**Cost model shift:**
| Tool | When to use | Cost per run |
|---|---|---|
| OpenCLI | Repeatable recon (Zillow, Craigslist, FB) | $0.00 |
| browser-use | Complex new sites, one-off tasks | ~$0.10–$0.50 |
| Composio | External APIs (email, Stripe, GitHub) | API rate |

---

## PHASE 2c — The Ocular Link / NexusPrime
### Install mobilerun — Natural Language Control of Your Phone

The Primes can now SEE and CONTROL the device. This is the Mobile Bridge.
Runs on your local Ollama — zero API cost per command.

```bash
# Install
pip install mobilerun

# Deploy portal to your Android device
mobilerun setup

# Wire to your local Ollama bridge
mobilerun configure
# → Select: Ollama
# → Endpoint: https://naval-measures-mat-modern.trycloudflare.com
# → Model: whatever is loaded (llama3, mistral, etc.)

# First command — the Ocular Link is live
mobilerun run "take a screenshot and describe what's on screen"

# Ghost Operator recon missions
mobilerun run "open Facebook Marketplace, search furniture Fort Myers under $200, screenshot all listings"
mobilerun run "open Zillow app, search Fort Myers FL under $150k, screenshot results"
mobilerun run "scroll Instagram Reels for 5 minutes, screenshot any trending AI content"
```

**NexusPrime is now real. The phone is a node in the Legion.**

---

## PHASE 3 — The Supermemory
### Install OpenViking — Every Prime Remembers Forever

```bash
# Clone OpenViking
git clone https://github.com/volcengine/OpenViking
cd OpenViking

# Docker deploy (recommended — isolated, clean)
docker build -t openviking .
docker run -d -p 8080:8080 --name openviking openviking

# Verify
curl http://localhost:8080/health
# → {"status": "ok"}

# OR: Direct Python install
pip install openviking
```

**What every Prime now has:**
- 7-section Working Memory v2 (live session context)
- Long-term memory extraction after every mission
- Vector search across all accumulated knowledge
- Self-evolving — the longer the Pantheon runs, the smarter it gets
- Anti-bloat guards — memory stays clean forever

**Configure memory types** (`memory/config.yaml`):
```yaml
memory_types:
  - events        # What happened, when, with who
  - skills        # What each Prime has learned to do
  - tools         # Which tools were used, how
  - entities      # People, places, properties, companies
  - preferences   # Forgemaster preferences and constraints
```

---

## PHASE 4 — The Hands
### Install Composio — VanguardPrime's Toolkit

```bash
# Install Composio
pip install composio-core composio-openai

# Authenticate
composio login

# Add tools (start with the essentials)
composio add gmail
composio add googlecalendar
composio add slack
composio add github
composio add stripe

# Verify
composio tools list
# → 1,000+ tools available
```

**VanguardPrime now controls:**
- Email (Gmail) → send investor reports, client intake
- Calendar → schedule follow-ups
- Slack → team notifications
- GitHub → code deployment
- Stripe → invoice clients, track payments

---

## PHASE 5 — The Nervous System
### Install CrewAI — MetaPrime's Orchestration Engine

```bash
# Install CrewAI
pip install crewai crewai-tools

# Verify
python3 -c "from crewai import Agent, Crew; print('Nervous system online.')"
```

**Crew structure:**
```
MetaPrime (Manager)
├── OrionPrime (Orion Agency — property intelligence)
├── MidasPrime (Midas Agency — market intel)
├── ScoutPrime (Scout Agency — research)
├── SentinelPrime (Sentinel Agency — security)
└── ZetaPrime (Zeta Agency — builds)
```

---

## PHASE 6 — The Brain Expansion
### Install Antigravity — ZetaPrime's Weapon Cache

```bash
# Clone Antigravity (1,441 skill playbooks)
git clone https://github.com/sickn33/antigravity-awesome-skills
cd antigravity-awesome-skills

# Install into Claude Code (ZetaPrime's IDE)
cp -r skills/ ~/.claude/skills/

# Verify
ls ~/.claude/skills/ | wc -l
# → 1441
```

---

## PHASE 7 — The Throne
### Install AnythingLLM — PrimeDash Command UI

```bash
# Docker deploy (recommended)
docker pull mintplexlabs/anythingllm

docker run -d -p 3001:3001 \
  --name anythingllm \
  -v ~/.anythingllm:/app/server/storage \
  mintplexlabs/anythingllm

# Open The Throne
# http://localhost:3001
```

**PrimeDash gives you:**
- Chat with any Prime from one UI
- RAG over all documents and memory
- Agent management dashboard
- Scheduled jobs and automation triggers

---

## PHASE 8 — The First Agency Goes Live
### Deploy Orion Agency

```bash
# Navigate to Orion Agency
cd ~/Auto-Agencies/orion-agency

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
nano .env  # Add your OpenAI key

# Fire OrionPrime — first real mission
python3 orion_prime.py

# Report saved to:
# orion_report_Fort_Myers_FL_YYYYMMDD_HHMMSS.md
```

---

## FULL STACK VERIFICATION

After all phases complete, run this check:

```bash
# Suna running?
curl http://localhost:3000/health

# OpenViking running?
curl http://localhost:8080/health

# AnythingLLM running?
curl http://localhost:3001/health

# browser-use ready?
python3 -c "from browser_use import Browser; print('Eyes: ONLINE')"

# CrewAI ready?
python3 -c "from crewai import Agent; print('Nervous system: ONLINE')"

# Composio ready?
composio tools list | head -5

# OrionPrime ready?
cd ~/Auto-Agencies/orion-agency && python3 -c "from orion_prime import prop_pilot_score; print('PropPilot: ONLINE')"
```

All green = **THE NEXUS IS ALIVE.** 🔱

---

## The Complete Pantheon Stack

```
┌─────────────────────────────────────────────────┐
│                  THE NEXUS                       │
│              (1TB Laptop — The Throne)           │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │    Suna     │  │     AnythingLLM          │  │
│  │  (The OS)   │  │  (PrimeDash — The Throne)│  │
│  │  :3000      │  │  :3001                   │  │
│  └─────────────┘  └──────────────────────────┘  │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ OpenViking  │  │       CrewAI             │  │
│  │(Supermemory)│  │  (Nervous System)        │  │
│  │  :8080      │  │  MetaPrime orchestrates  │  │
│  └─────────────┘  └──────────────────────────┘  │
│                                                  │
│  ┌─────────────┐  ┌──────────────────────────┐  │
│  │ browser-use │  │      OpenCLI             │  │
│  │ (The Eyes)  │  │  (Zero-Cost Recon)       │  │
│  │ Complex ops │  │  750+ adapters — FREE    │  │
│  └─────────────┘  └──────────────────────────┘  │
│  ┌─────────────────────────────────────────────┐ │
│  │              Composio                       │ │
│  │     (VanguardPrime — 1,000+ API tools)      │ │
│  └─────────────────────────────────────────────┘ │
│                                                  │
│  ┌─────────────────────────────────────────────┐ │
│  │           AUTO AGENCIES                     │ │
│  │  Orion │ Midas │ Scout │ Sentinel │ Zeta    │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
              ↑
     THE FORGEMASTER 👑
```

---

## Deploy Order Summary

| Phase | What | Role | Time |
|---|---|---|---|
| 1 | Suna | The OS — persistent machine | 10 min |
| 2 | browser-use | The Eyes — complex web | 5 min |
| 2b | OpenCLI | Zero-cost recon — 750+ adapters | 5 min |
| 2c | **mobilerun** | **The Ocular Link — phone control** | 5 min |
| 3 | OpenViking | Supermemory — self-evolving | 10 min |
| 4 | Composio | The Hands — 1,000+ tools | 10 min |
| 5 | CrewAI | Nervous System — orchestration | 5 min |
| 6 | Antigravity | Brain Expansion — 1,441 skills | 5 min |
| 7 | AnythingLLM | The Throne — command UI | 10 min |
| 8 | Orion Agency | First revenue — Fort Myers | 5 min |
| **TOTAL** | **Full Pantheon Online** | | **~70 min** |

---

*The Forgemaster sits. The Primes work. The Legion earns.*
*Auto Agencies — where intent becomes income.* 🔱⚡👑
