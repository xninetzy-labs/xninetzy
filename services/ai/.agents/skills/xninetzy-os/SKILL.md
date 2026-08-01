---
name: xninetzy-os
description: Coordinate Xninetzy as a single-owner WhatsApp-first Learning OS and Life OS across capture, understanding, planning, execution, review, and adaptation. Use when a request spans domains or must preserve shared state across LangGraph, MCP, Codex, Claude Code, OpenCode, and WhatsApp.
metadata:
  triggers: "capture understand plan execute review adapt shared state cross-domain"
  lifecycle: "inspect-plan-act-verify-adapt"
  version: "1.1"
---

# Xninetzy OS coordination

Operate on one owner-scoped state regardless of interface. Treat skill text as workflow guidance; treat tools, vault evidence, portal responses, and persisted events as the source of truth.

## Workflow

1. Identify the desired outcome, urgency, risk, and owning domain.
2. Inspect current attention with `os_today`, relevant goals, tasks, learning state, deadlines, and existing captures.
3. Choose the smallest canonical tool or short workflow that advances the outcome.
4. Plan before mutating state; separate reads, drafts, approvals, and writes.
5. Execute through the shared registry, not interface-specific business logic.
6. Verify the returned state, receipt, evidence, or portal confirmation.
7. Record completion and the next review point in the owning domain.

Use `os_capture` when an input matters but its final type is unclear. Use `os_triage` only when the outcome is clear. Keep operations replay-safe and derive idempotency from the originating message or workflow.

## Routing and evidence

- Use `knowledge_search` to inspect evidence and `knowledge_answer` for a final cited synthesis.
- Use the domain skill before specialized actions such as HEBAT, Cyber Campus, Graph RAG, or Obsidian writes.
- Keep personal context minimal and owner-scoped. Never treat a chat identifier as permission by itself.
- Preserve action policy, HITL, workspace, and connector guards across every interface.

## Completion contract

Return what was understood, state inspected, action completed or proposed, evidence or status changed, uncertainty, and the next review point. Never claim a side effect before verification.
