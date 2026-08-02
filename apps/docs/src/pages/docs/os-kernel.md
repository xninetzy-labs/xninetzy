---
layout: ../../layouts/DocsLayout.astro
title: OS Inbox and attention kernel
description: Capture input without losing context, turn it into a commitment, and choose focus from real Xninetzy state.
section: Integrations
---

The OS kernel closes the gap between “I just thought of something” and “what
should I work on now?” It is not a new transport. WhatsApp, internal LangGraph,
Codex, Claude Code, and OpenCode use the same services and tables.

## Supported closed loop

```text
Capture → Understand → Plan → Execute → Review → Adapt
   │          │          │
OS Inbox   Triage     Attention queue
```

OS Inbox accepts important input without forcing it into a task. Triage turns a
capture into an explicit commitment or archives it. The attention queue combines
tasks, deadlines, priorities, learning state, and unprocessed captures.

## WhatsApp commands

```text
/capture build a small event-sourcing project
/capture study classification next week
/inbox
/triage 12 task
/triage 13 archive
/today
```

`/today` shows the top focus, its priority reason, the next action, and the
remaining queue. Overdue and due-today tasks receive more weight. Active
learning plans appear unless they duplicate an existing task.

## Shared tools

| Tool | Purpose |
|---|---|
| `os_capture` | Persist and classify a capture deterministically |
| `os_inbox` | List captures by state |
| `os_triage` | Turn a capture into a task or archive it |
| `os_today` | Build an attention queue across OS state |

Example from Codex, Claude Code, or OpenCode:

```text
Use MCP xninetzy to call os_capture with "study CQRS".
Then show os_inbox and os_today.
```

Transport identity fields such as `chat_id` are not exposed in the MCP schema.
The MCP server injects a trusted local-owner principal.

## Replay safety

`os_capture` accepts an `idempotency_key`. The same key and content return the
original capture; reusing the key with different content is rejected. A capture
can be triaged only once.

Promotion to a task writes four changes in one SQLite transaction:

1. the shared task;
2. an entity link from capture to task;
3. the capture's `processed` state;
4. an ecosystem event for reducers.

A repeated call returns the existing target and creates no second task, link, or
event.

## Context and automation

Personal Context includes the top three attention items and the unprocessed
inbox count. Morning briefings use the same source, so WhatsApp, LangGraph, and
MCP clients see consistent focus.

## Current boundaries

- Explicit triage supports `task` and `archive`.
- Capture classification is deterministic and intentionally conservative.
- The attention queue does not yet include external calendars or capacity estimates.
- Future note, knowledge, or goal promotion must preserve the same transaction and idempotency invariants.
