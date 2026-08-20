---
name: xninetzy-mcp-lightning
description: Apply Xninetzy MCP tools, Lightning contextual decision learning, and Deep Research evidence workflow across LangGraph, MCP, WhatsApp, Codex, Claude Code, and OpenCode. Use whenever an agent selects tools, skills, providers, models, research profiles, or reviews outcomes.
metadata:
  triggers: "mcp lightning rl contextual bandit reward provider skill deep research optimization"
  lifecycle: "inspect-decide-act-verify-measure-propose"
  version: "1.0"
---

# Xninetzy MCP and Lightning

Use the shared Xninetzy tool registry and owner-scoped storage for every interface. This skill is workflow guidance, not evidence and not authorization.

## Mandatory workflow

1. Inspect action risk, owner scope, available providers, relevant skills, and state.
2. Choose canonical registered tools; never implement client-specific domain logic.
3. For eligible read work, record bounded context and the selected strategy.
4. Record material route, tool, provider, and skill actions with idempotency when available.
5. Verify state or evidence before treating execution as task success.

## Context and strategy

Record only interface, domain, intent, modality, risk class, task type, evidence requirement, provider availability, and budget/latency bucket. Never log credentials, raw private prompts, cookies, or high-cardinality identifiers.

## Reward and safety

- `task_success` is terminal task execution, not merely a tool return.
- `evidence_quality` requires inspected relevant evidence and valid citations.
- Missing components remain neutral with low confidence; never normalize them to perfect reward.
- Never explore or auto-select write, final, destructive, upload, submission, or cross-contact actions.

## Deep Research

1. Start with local knowledge when relevant, DDGS, arXiv, and Crossref.
2. Add Tavily, Serper, and YouTube only when configured and within policy/budget.
3. Keep provider provenance, raw rank, canonical URL, evidence level, and relevance score.
4. Deduplicate and rank before evidence-only synthesis; disclose insufficient evidence.

## Completion contract

Return the selected strategy, result, evidence status, reward coverage, uncertainty, and any required owner approval.
