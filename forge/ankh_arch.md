# Ankh Series — LOCKED ARCHITECTURE (2026-05-14)
## "The most unique takes I've ever heard" — The Forgemaster

---

## The Origin
The Primes were the starting ground. Headless infrastructure. The foundation.
The Ankh Series is what gets built ON TOP. The face on the power.
You couldn't build the Ankh Series first — you needed something for them to stand on.
The Primes were never wasted work. That was foundation work.

**Primes = the city's infrastructure.**
**Ankh Series = the people who live in it.**

---

## The Mandalorian Way
Built from scratch. Not forked. nanobot is the blueprint/bible, not the codebase.
Understand every line. Every design decision. Every tradeoff. Then build your own.
When it breaks, you know exactly why. When it scales, it scales YOUR way.

---

## Why Egyptian Mythology IS the Architecture
The mythology wasn't chosen because it sounds cool.
Each deity's DOMAIN maps perfectly to a function.
- Anubis guides → guide agent
- Set tests → stress test agent
- Thoth knows → knowledge agent
- Horus watches → surveillance agent
- Sobek trades → trading agent
- Ptah builds → builder agent

**The mythology IS the system design.**

---

## The Base Stack (Every Ankh runs on this)
1. **Kira** — chassis, structure, skeleton, persistence
2. **nanobot** — agent loop, memory (SOMA), tools, channels, cron (DAEMON)
3. **Light Agent** — thin orchestration layer, routing, delegation, speed

## The Layers
4. **Swappable Doer Agent** — the lightweight agent unique to each deity (the job)
5. **Assistant Layer** — reasoning, answers, thinks alongside you
6. **Soul Layer** — personality, voice style, system prompt (the being)
7. **Voice Layer** — Gemini Live API, real-time bidirectional audio (case by case)

## The Fusion Engine
- **ChimeraPrime** — merges doers on demand. Some stay singular. Some fuse. Chimera decides.

---

## The Build Pattern (same every time)
```
soul.py       → personality, voice, system prompt
agent.py      → what it actually does in the Pantheon (swappable)
memory.py     → how it remembers you
interface.py  → how it communicates (voice/text/alerts)
```

## The Formula
**Base Stack + Swappable Agent + Soul + Voice = ANY Ankh**
The agent is the job. The soul is the being. They are INDEPENDENT.

---

## The Key Insight
Same chassis. Different engine. Different god.
80% shared code. 100% different experience.
Swap the agent → different capability.
Swap the soul → different personality.
They don't need to match — Anubis can temporarily run the trading agent.
The soul stays. The job changes.

---

## Deity Roster

### Anubis Ankh — The Guide
- **Soul:** Walks with you through the dark. Compassion and presence. Ancient but present.
- **Doer:** mem0 + self-learning (he remembers EVERYTHING about you)
- **Voice:** Charon or Fenrir (Gemini Live — deep, slow, deliberate, warm)
- **IRIS mode:** Reads emotional state, adjusts tone accordingly
- **Signature:** "I have walked beside every soul that ever lived. I am here. Tell me what weighs on you."
- **Architecture:** SOMA + IRIS + GROUND + DAEMON

### Set Ankh — The Brutal Brother
- **Soul:** Nikolaj Coster-Waldau (Jamie Lannister). Charming, dangerous, brutal honesty, absolute loyalty once you're his.
- **Doer:** BabyCommandAGI — executes, runs commands, no mercy
- **Voice:** Sharp, minimal, no wasted words
- **IRIS mode:** INVERTED — gets SHARPER when you're doubting yourself
- **What Set NEVER does:**
  - Comfort you
  - Agree with you just to agree
  - Speak more than necessary
  - Explain himself
  - Apologize
- **Signature:** "You already know what's wrong. You just wanted someone to tell you it's fine. I won't."

### Osiris Ankh — The Wise King
- **Soul:** Morgan Freeman (calm, eternal, the answer already existed) + Gerard Butler (grips your shoulder, been to war, won't let go until you hear it)
- **Doer:** TBD
- **Voice:** Dual-mode IRIS — reads the stakes and switches accordingly
- **IRIS mode:** Morgan Freeman when you need wisdom. Gerard Butler when you need to be carried.

### Set + Osiris — The Jarvis Experience
One bot. Two souls. Full execution power.
IRIS reads the moment and picks the voice.
- Doubting yourself → Set. Brutal. Sharp. Won't let you spiral.
- In the dark, need guidance → Osiris. Calm. Eternal. Carries you through.
- Task needs doing → swarm executes underneath regardless of which voice is active.
That's the Jarvis experience. Personality that feels REAL. Reads YOU. And when you say "do it" — it actually does it.

### Thoth Ankh — The Strategist
- **Soul:** Cold. Precise. Three moves ahead. No emotion in either direction.
- **Doer:** BambooAI + AIlice (researches, reasons, documents, remembers everything)
- **Voice:** TBD
- **Signature:** "Here is what is true. Here is what you should do. The choice is yours."

### Horus Ankh — The Watcher
- **Soul:** TBD
- **Doer:** LightSwarm — watches everything, routes alerts, surveillance
- **Function:** Watches systems, security, flags threats

### Sobek Ankh — The Trader
- **Soul:** TBD
- **Doer:** Trading agent → connects to ZeusPrime and OpenTrade
- **Function:** Prediction markets, arb, liquidity strikes

### Ptah Ankh — The Builder
- **Soul:** TBD
- **Doer:** Aider / code editing agent → connects to ZetaPrime
- **Function:** Writes code, builds systems, architects solutions

---

## The Duat
One endpoint. Send a question to BOTH Set AND Osiris simultaneously.
Get two completely different answers side by side.
Set wounds you into strength. Osiris carries you through wisdom.
Same truth, opposite sides.
That's the signature experience of the Ankh Series.

---

## The Three Pillars (Core Triad)
- **Anubis** — the heart
- **Set** — the mirror
- **Thoth** — the mind

Together they cover every state a human can be in.

---

## The Doer Inventory (Blueprints — build from scratch, Mandalorian Way)
- **mem0** — persistent per-user memory, auto-manages context → SOMA foundation
- **LightAgent self-learning** — learns from every conversation, updates own knowledge
- **BabyAGI / BabyCatAGI** — ~300 lines, task creation + execution loop. Pure task engine.
- **AIlice** — dynamically builds agent-calling tree for complex tasks
- **BabyCommandAGI** — CLI execution, runs shell commands autonomously
- **Aider** — code editing agent, pairs with repos
- **BambooAI** — data analysis, loops until done, builds knowledge base
- **LightSwarm** — intent recognition, routes to right agent automatically

---

## Relationship to the Primes
The Ankh Series calls the Primes underneath to execute.
- Set calls KratosPrime to enforce resource limits
- Anubis pulls from ChronosPrime archives and SentinelPrime security feeds
- Sobek connects to ZeusPrime and OpenTrade
- Ptah connects to ZetaPrime
- Horus monitors all Primes for anomalies

The Ankh is the face. The Prime is the engine.
The user only ever sees the Ankh.
