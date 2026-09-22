---
name: research-planner
description: Decompose a research question into a multi-step plan with source selection,
  evidence strategy, verification, and synthesis stages. Use when a query needs structured
  research rather than single-shot search.
metadata:
  type: meta
  layer: research-orchestration
  consumes: '["source-selector","research_search","research_fetch"]'
  produces: '["research_plan"]'
  tier: '0'
---


# research-planner

Workflow guidance for decomposing a research question into a multi-step plan.
This skill is **not** factual evidence; it tells the agent *how* to plan, not
*what* is true.

## When to invoke

- Query asks for "latest", "best", "compare", "sota", "trend", "gap"
- Query spans multiple domains (paper + code + dataset)
- User wants more than a snippet
- Query is ambiguous and needs decomposition

## Inputs

```yaml
question: "<the user query>"
context:
  intent: paper | code | dataset | news | company | model | benchmark | security | patent | economics | geographic | entity | general
  requires_open_access: bool
  language: en | id | ...
  freshness_days: int | null
  max_steps: int (default 8)
```

## Output schema

```yaml
research_plan:
  id: "<uuid>"
  question: "<echo>"
  steps:
    - id: "<step-id>"
      tool: research_search | research_fetch | research_compare_sources | research_grade_evidence
      intent: paper | code | ...
      query: "<search query>"
      limit: int
      depends_on: ["<step-id>", ...]
      idempotency_key: "<auto>"
      tier: 0
  verification:
    min_independent_sources: int
    require_open_access: bool
  synthesis:
    contradiction_hunt: true
    evidence_grading: true
    final_critic_pass: true
```

## Plan shape rules

1. First step is always `research_search` with the most specific intent.
2. Subsequent steps depend on prior results via `depends_on`.
3. Always end with `research_grade_evidence` over the merged result set.
4. If multiple intents, fan out then merge via `research_compare_sources`.
5. Cap at `max_steps`. Defer deeper dives to follow-up plans.

## Anti-patterns

- Do NOT plan a single-step "search → answer" loop. Use this skill when the
  question warrants depth.
- Do NOT bake in FINAL-class tools. Research never mutates academic sources.
- Do NOT skip the verification step. Even a "quick" plan needs
  `min_independent_sources >= 2` unless user explicitly opts out.

## Composition

After producing `research_plan`, hand it to `xninetzy.cli.orchestrator run`
with `tier: 0` for every step. The CLI enforces idempotency, harness
checkpoints, and per-step receipts.
