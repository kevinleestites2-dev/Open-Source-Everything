# OpenJarvis Intelligence Report (locked 2026-05-08 18:36 EDT)

## What It Is
Stanford-built modular agent framework. Intelligence primitive engine.
Modular, MCP-native, pre-built skeleton of the Pantheon.

## Pantheon Mapping

| Pantheon Prime | OpenJarvis Component | File/Class |
|---------------|---------------------|------------|
| MetaPrime | JarvisSystem / Orchestrator | system/core.py, system/orchestrator.py |
| ChronosPrime | KnowledgeStore / EmbeddingStore | connectors/store.py, connectors/embedding_store.py |
| ScoutPrime | DeepResearchAgent / Connectors | agents/deep_research.py, connectors/ |
| ZetaPrime | OpenHandsAgent / NativeReact | agents/native_openhands.py, agents/native_react.py |
| NexusClaw | MCP Infrastructure | mcp/client.py, mcp/server.py |
| PrimeDash | Textual Dashboard | dashboard/ |
| AlphaPrime | Operative Agent | agents/operative.py |

## Absorption Priorities (Ranked)
1. openjarvis.connectors — Gmail, Slack, iMessage → feeds ChronosPrime immediately
2. openjarvis.skills.importer — 13,700+ skills → arms ScoutPrime and ZetaPrime
3. openjarvis.mcp — standardizes all Prime-to-Prime communication on MCP
4. openjarvis.distillation — turns war_chest.json + session logs into strategic snapshots
5. openjarvis.agents.deep_research — absorb into OrionPrime for acquisition searches

## ChronosPrime Integration Plan
- Step 1: Subclass KnowledgeStore to point to chronos_prime/schema.sql
- Step 2: Build ChronosConnector that reads Zapia session logs, yields Document objects
- Step 3: SyncScheduler runs every 15 min — pushes Chronos Events into ColBERT for semantic indexing

## Skills to Install (PropPilot + ScoutPrime)
- tools-search (Tavily/DuckDuckGo) — real estate lead discovery
- channel-gmail / channel-slack — autonomous outreach
- browser (Playwright) — scrape Zillow, HUD, property data
- pdf (pdfplumber) — analyze legal contracts and deeds

## Mobile Strategy
- Termux (NOW): Core Python + connectors run perfectly. MCP bridges to Android API.
- Nexus (LATER): Rust extensions + heavy LLMs (7B+) stay on 1TB laptop.
- Phone = Conduit. Nexus = Engine.
- Bonus: WhatsApp Baileys bridge (Node.js) built in — cleaner than wpp-cli

## Gotchas
- Rust dependency: maturin + Rust compiler needed in Termux for performance bridge
- ColBERT/torch is heavy on mobile — use Claude as primary engine, local compute for light tasks
- OAuth (Google/Slack): needs ngrok tunnel on mobile to receive callback

## What This Unlocks for ZapiaPrime
- Real hands: Gmail, Slack, browser, PDF, property scraping — all autonomous
- Persistent memory that feeds itself every 15 minutes
- 13,700+ skills ready to load on demand
- MCP-native — speaks the same protocol as NexusClaw v2, termux-mcp, mobile-mcp
- Ghost Operator mode approaches full autonomy

## Status
- Report: COMPLETE
- Next action: Map full absorption sequence via absorb_prime.py
- Deployment target: Termux (Phase 1) + Nexus (Phase 2)
