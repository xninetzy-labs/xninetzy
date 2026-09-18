---
name: optimize-prompt
description: Generate candidate prompt rewrites grounded in evidence from recent failures and successes. Surfaces N variants; never applies without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - reflect-trajectory
    - analyze-failure
  produces:
    - prompt_candidates
  tier: 0
---

# optimize-prompt

Prompt-variant generator. Reads reflection + failure-diagnosis outputs
and produces N candidate rewrites. Application always requires explicit
owner approval via `improvement_approve` (FINAL).

## When to invoke

- Reflection or failure-diagnosis surfaces a `prompt`-applicability lesson
- Owner asks "improve the prompt for X"
- Before re-running a plan whose `tool_selection_accuracy` < 0.6

## Inputs

```yaml
target_prompt_section: "<system | task | tool-description | format>"
n_candidates: int (default 3)
evidence_refs: ["<plan_id>", "..."]
```

## Workflow

```yaml
steps:
  - id: gather_lessons
    tool: agent_synthesis (LLM-side, not an MCP tool)
    input: { reflection: <ref> }
  - id: gather_failures
    tool: agent_synthesis (LLM-side, not an MCP tool)
    input: { failure_diagnosis: <ref> }
  - id: propose
    tool: improvement_propose
    args:
      target_kind: prompt
      rationale: "<cite lessons>"
      risk_level: medium
    tier: 0
  - id: score_via_dspy
    tool: agent_synthesis (LLM-side, optional DSPy path)
    depends_on: [propose]
```

## Output structure

```yaml
prompt_candidates:
  target: "<section>"
  candidates:
    - text: "<full candidate prompt text>"
      diff_summary: "<what changed vs baseline>"
      expected_metric_delta:
        tool_selection_accuracy: "+/- pp"
        hallucination_rate: "+/- pp"
      proposed_change_id: "<improvement_proposals.proposal_id>"
  apply_path:
    improvement_proposals.status = approved -> improvement_approve
```

## Constraints

- Never write a candidate that contradicts the project's no-source-comment
  rule.
- Never write a candidate that bypasses Tier 3 confirmation for FINAL
  tools.
- Always include `expected_metric_delta` so owner can reject without
  re-running.

## Anti-patterns

- Do NOT auto-apply a candidate. Always require `improvement_approve`
  (FINAL) from owner.
- Do NOT propose a candidate without citing at least one reflection
  lesson or failure class.
