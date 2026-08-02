---
layout: ../../layouts/DocsLayout.astro
title: System architecture
description: Service boundaries, request flow, tool registry, persistence, and the two MCP transports.
section: Start
---

Xninetzy is a monorepo with two primary runtime services, one terminal client,
and one documentation application.

## Service boundaries

```text
WhatsApp user
  ↓
WhatsApp engine / Baileys :8081
  ↓ POST /api/chat
AI service / FastAPI :8000
  ↓
LangGraph → direct | clarify | agent | workflow
  ↓
Tool registry → OS kernel | Obsidian | HEBAT | SQLite | FAISS | WhatsApp
```

### AI service

`services/ai` owns routing, prompts, the provider registry, the stdio MCP
server, domain tools, persistence, knowledge, research, media extraction, HEBAT,
Obsidian, and approvals.

### WhatsApp engine

`services/wa-enggine` is the only process that owns the Baileys socket.
Message delivery, media, contacts, groups, pins, and labels remain in this
service.

### Terminal CLI

`apps/cli` calls the same chat API so providers, memory, routing, and tools are
not duplicated.

## CLI streaming and activity

The CLI uses SSE at `/api/chat/stream` with one request ID per message. Each
turn owns one request, `AbortController`, stream reader, and Thinking timer.
Answer deltas are buffered before rendering. While streaming, the active answer
uses a bounded visual preview; after completion, the complete answer moves into
Ink's append-only `Static` transcript. Spinner and timer updates therefore do
not redraw conversation history.

The **AI Thinking** panel sits directly above the composer and shows elapsed
time plus safe summaries of routing, workflows, ReAct execution, tools, and
research. Events must never expose hidden chain of thought, credentials, raw
prompts, tool arguments, or untrusted tool output. Use `Ctrl+T` to expand safe
activity and `Escape` to cancel an active request.

Ink performs React reconciliation against terminal output. The stable renderer
keeps header, completed messages, and input identities unchanged; limits the
100 ms spinner and 200 ms timer updates to their labels; buffers streaming for
50 ms; bounds active output using terminal width; and displays only the latest
four detailed activities. Old request events are rejected by request ID.

Run phases are `queued`, `planning`, `thinking`, `tool-running`,
`waiting-approval`, `streaming`, and one terminal state. Illegal transitions
are ignored. SSE heartbeats keep long requests active without disclosing
internal reasoning.

### CLI and workflow timeouts

| Variable | Default | Boundary |
|---|---:|---|
| `XNINETZY_THINK_TIMEOUT_SECONDS` | 120 | Time to first token for normal chat |
| `XNINETZY_INACTIVITY_TIMEOUT_SECONDS` | 60 | Time without an SSE event or heartbeat |
| `XNINETZY_TOOL_TIMEOUT_SECONDS` | 180 | Direct registry tool |
| `XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS` | 20 | External MCP connection and catalog |
| `XNINETZY_MCP_CALL_TIMEOUT_SECONDS` | 180 | One external MCP call |
| `XNINETZY_DEEP_RESEARCH_TIMEOUT_SECONDS` | 900 | Complete deep-research workflow |
| `XNINETZY_STREAM_TIMEOUT_SECONDS` | 300 | Complete normal chat stream |
| `XNINETZY_SLOW_REQUEST_WARNING_SECONDS` | 45 | Slow-request warning threshold |

Timeout and cancellation stop the reader and timers, preserve received partial
output, and reject late events.

## Three request paths

1. **Slash commands** use the deterministic command router.
2. **Multi-action requests** become workflows with inspectable state.
3. **Natural messages** are routed by LangGraph to direct, clarify, or ReAct execution.

## The tool registry is the source of truth

`services/ai/app/xninetzy/tools/registry.py` collects all tools. The MCP adapter
reads this catalog dynamically, so a registered tool does not need a separate
client-specific wrapper.

The adapter normalizes names and descriptions, builds JSON Schema, injects
trusted context, converts return values to MCP content, and contains exceptions
so they cannot corrupt the protocol stream.

## Two tool servers

| Server | Transport | Owner | Content |
|---|---|---|---|
| Xninetzy MCP | stdio | AI service | Complete Personal OS registry |
| WhatsApp tool server | HTTP MCP-style | WhatsApp engine | Actions that require the WhatsApp socket |

Codex, Claude Code, and OpenCode launch the stdio server. A registry tool that
must send a WhatsApp message calls the engine through `/mcp/call` with an
internal bearer token.

## Persistence

| Data | Host | Container |
|---|---|---|
| SQLite, FAISS, HEBAT | `services/ai/data` | `/app/data` |
| Obsidian | owner-selected path | `/app/obsidian-vault` |
| WhatsApp media | `wa-media` volume | `/app/data/wa-media` |
| WhatsApp session | `wa-session` volume | `/app/sessions` |

SQLite stores structured state, FAISS stores the embedding projection, and the
Markdown vault remains human-readable.

## Single-owner state and the closed loop

Goals, tasks, roadmaps, habits, workouts, HEBAT state, knowledge, and events
belong to the installation rather than a transport. `chat_id` records origin,
delivery, and conversation memory without splitting owner entities.

```text
HEBAT assignment ─represented_by→ shared task ─reminded_by→ reminder
roadmap item     ─represented_by→ shared task
                                      ↓ task_completed event
                           goal progress + roadmap progress
                                      ↓
                            Personal Context v2
```

Events are persisted before reducers consume them transactionally and write
consumption markers. Unconsumed events are replayed at AI startup. Task
completion emits an event only when state actually changes.

Scheduled jobs share one run table. Daily and weekly keys prevent duplicate
briefings, leases recover interrupted internal jobs, and weekly reviews use real
events. See [Automation](/docs/automation/).

## OS Inbox and attention kernel

```text
important input
  → os_capture
  → os_inbox_items
  → os_triage ──→ shared task ──→ event/reducer
              └─→ archive

tasks + learning state + inbox
  → deterministic scoring
  → os_today / Personal Context / morning briefing
```

OS Inbox separates capture from commitment. Promotion writes the task, entity
link, state transition, and event in one transaction. Reusing an idempotency key
never creates a second row or event. See [OS kernel](/docs/os-kernel/).

## Security boundaries

- Administrators are identified by explicit JIDs.
- The chat API requires a bearer key; WhatsApp owner checks apply in single-owner mode.
- Risky tools require approval or confirmation.
- Obsidian restricts paths to the vault and safe extensions.
- Coding agents use an allowed root, timeout, environment allowlist, and audit log.
- HEBAT final submission is not automatic under the safe default.
- WhatsApp HTTP tools use a shared API key when configured.

## Add a feature

1. define the owning domain and data boundary;
2. implement a service or tool without transport coupling;
3. register the tool in the canonical registry;
4. add domain tests;
5. add MCP schema or invocation tests when the signature changes;
6. update documentation and command examples.
