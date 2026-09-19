---
layout: ../../layouts/DocsLayout.astro
title: Introduction to Xninetzy
description: Xninetzy as a local-first, MCP-only Personal Intelligence and Learning system.
section: Start
---

Xninetzy is a **local-first, MCP-native Personal Intelligence and Learning
system**. It exposes one MCP interface that connects a host (Claude,
Claude Code, Cursor, any other MCP-compatible client) to a shared engine:
router, planner, source registry, cache, deduplication, entity-resolution,
evidence, citation, and security.

There is no second product surface. No REST API, no GraphQL, no CLI as a
parallel client, no web dashboard. The MCP server (stdio primary, Streamable
HTTP secondary, loopback-bound by default) is the only external interface.

> **What Xninetzy is NOT:** not an internet-ready multi-tenant SaaS, not an
> autonomous server-side agent that acts on its own, not a replacement for
> vault backups or an LMS, not a scraped-data aggregator of walled-garden
> job boards. Reasoning, planning, and orchestration belong to the host.

## Domains shipped in v2.2.0

| Domain | Source adapters / tools | Notes |
|---|---|---|
| Research | OpenAlex, arXiv, Crossref, PubMed, Europe PMC, DBLP, Semantic Scholar, Wikipedia, Wikidata, DBpedia, HackerNews, Reddit, RSS, GitHub, Open LLM Leaderboard, PapersWithCode, HuggingFace, Kaggle, Zenodo, NVD, PatentsView, OSM, World Bank, FRED, BPS, StackOverflow, Wayback | 27 adapters + 4 MCP tools (`research_search`, `research_fetch`, `research_compare_sources`, `research_grade_evidence`) |
| Career | RemoteOK, ArbeitNow | 17 MCP tools (`career_*`); legal free public APIs only; 19 skill bodies under `.agents/skills/career/` |
| Knowledge | FAISS retrieval, SQLite, Obsidian vault | 4 MCP tools (`knowledge_*`) |
| Learning | Roadmaps, concept graph, mastery formula, SM-2 spaced repetition | 8 MCP tools (`learning_*`) |
| OS kernel | Capture, inbox, triage, tasks, goals, reminders | 5 MCP tools (`task_*`, `goal_*`, etc.) |
| Lightning | CPU-only contextual bandit, episodes, rewards, regression checks | 15 MCP tools (`lightning_*`) |
| Security | HITL approvals, scope tokens, SSRF guards, secret redaction | 9 MCP tools (`security_*`) |
| External MCP gateway | Untrusted-by-default registry, allowlist, risk classification | 5 MCP tools (`external_mcp_*`) |
| Tasks extension | Long-running task handles (SEP-2663) | 4 MCP tools (`tasks_*`) |
| Self-improvement | Memory lifecycle, episodic recall, proposals | 7 MCP tools (`improvement_*`) + 7 (`memory_*`) |

## Design principles

### Local-first and single-owner

The default configuration targets one owner on a local machine or private
network. SQLite, FAISS, HEBAT browser profiles, media, and Obsidian vault
stay local. There is no Xninetzy-operated service anywhere in the default
path.

### MCP is the only public interface

Clients connect via `stdio` (primary) or Streamable HTTP (opt-in, loopback
by default). The MCP server injects trusted identity context. Client-supplied
`sender_id`, `sender_name`, and `chat_id` values are never authorization
evidence.

### No server-side agent loop

Xninetzy exposes capabilities. It does not decide what to do next, does not
chain its own tool calls autonomously, and does not act as a second brain.
Reasoning and orchestration belong to the host (Claude / Claude Code /
Cursor / etc.).

### Human in the loop

`FINAL`-class tools (e.g. `improvement_approve`, `portal_krs_final_submit`)
require HITL approval server-side. Orchestrator tier gate
(`_effective_tier`) rejects owner-supplied tier downgrade of FINAL tools.

### Capture before commitment

The OS Inbox holds ambiguous input until its next action is clear. Promotion
to a task or archive runs in one transaction (task + entity link + state
transition + event). Reusing an idempotency key never creates a second row.

### Provider freedom

LLM providers are pluggable. Flaz is the default, not a lock-in. Optional
backends (Neo4j, Graphiti, Ollama) are opt-in via a `ProviderAdapter`
interface, never a hard dependency.

## Main components

| Component | Technology | Responsibility |
|---|---|---|
| MCP server | Python, FastMCP (`mcp>=1.28.1,<2`) | stdio + Streamable HTTP, canonical tool registry, MCP tool exposure |
| AI service / app core | Python, FastAPI, Pydantic v2 | Routing, prompts, provider registry, persistence, knowledge, research, HEBAT, Obsidian, approvals, Lightning |
| Documentation | Astro Starlight | Static operator and contributor documentation |

There is no WhatsApp engine, no LangGraph agent runtime, no terminal CLI.
The repository contains exactly three trees: `xninetzy/`, `apps/docs/`,
`.agents/skills/`.

## Choose your next path

- New installation: open [Quick start](/docs/getting-started/).
- Choose a model: open [LLM providers](/docs/providers/).
- Connect a vault: open [Obsidian](/docs/obsidian/).
- Understand capture and daily focus: open [OS kernel](/docs/os-kernel/).
- Use coding clients from any directory: open [Global MCP](/docs/mcp/).
- Review safety boundaries: open [Security](/docs/security/).
- Release-gate status: `uv run python -m xninetzy.cli.supervisor release-check`.
