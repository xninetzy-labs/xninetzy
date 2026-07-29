---
name: xninetzy-os
description: Coordinate Xninetzy as a single-owner WhatsApp-first Learning OS and Life OS. Use for requests that span capture, planning, execution, review, personal context, or several Xninetzy domains; do not use for isolated factual questions that one direct tool can answer.
---

# Xninetzy OS coordination

Treat WhatsApp, LangGraph, Codex, Claude Code, OpenCode, and MCP as interfaces to one shared owner state.

Follow this loop:

1. Capture unclear but important input with `os_capture`.
2. Understand the desired outcome before creating commitments.
3. Read current attention with `os_today`, relevant goals, tasks, learning state, and deadlines.
4. Plan the smallest next action that advances an existing outcome.
5. Execute through the canonical Xninetzy tool instead of inventing interface-specific behavior.
6. Record evidence or completion in the owning domain.
7. Review the result and adapt the next action.

Use `os_inbox` and `os_triage` when captured information still needs a decision. Do not turn every idea into a task.

Keep owner state installation-global. Treat chat identifiers only as origin, delivery, and memory context.

For knowledge questions, use `knowledge_answer` for the final grounded response. Use `knowledge_search` only to inspect evidence. Never present raw retrieved chunks as an answer.

Require existing approval boundaries for destructive actions, submissions, uploads, bulk writes, cross-contact messaging, and academic changes.

Return a concise WhatsApp-friendly result containing:

- what was understood;
- what state was inspected;
- what action was completed or proposed;
- what evidence or status changed;
- the next review point.
