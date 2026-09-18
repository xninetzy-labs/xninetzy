---
name: evaluate-agent
description: Score a completed agent trajectory against task-completion criteria. Reads harness trace + claim ledger, outputs metric bundle for the optimization loop.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - harness_trace
    - claim_ledger_record
    - observability_summary
  produces:
    - evaluation_report
  tier: 0
---

# evaluate-agent

Workflow for grading a finished agent trajectory. Produces a metric bundle
that downstream `optimize-*` skills consume.

## When to invoke

- A plan finished (status=`verified` or `failed`) and you want to learn
  from it
- Before calling `optimize-prompt` / `optimize-rag` / `optimize-agent-policy`
- Whenever `lightning_episode_finish` would record an outcome

## Inputs

```yaml
plan_id: "<harness plan id>"
trace_from: harness_trace
metrics_required:
  - task_completion
  - tool_selection_accuracy
  - evidence_grade_distribution
  - hallucination_rate
```

## Workflow

```yaml
steps:
  - id: gather_trace
    tool: harness_trace
    args:
      plan_id: "<id>"
      include_actions: true
      include_verifications: true
    tier: 0
  - id: gather_claims
    tool: observability_query
    args:
      event_kind: claim_recorded
      subject_contains: "<plan_id>"
    tier: 0
  - id: score
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [gather_trace, gather_claims]
```

## Output structure

```yaml
evaluation_report:
  plan_id: "<id>"
  task_completion: 0.0-1.0
  tool_selection_accuracy: 0.0-1.0
  evidence_grade_distribution:
    strong: <int>
    moderate: <int>
    weak: <int>
    uncertain: <int>
  hallucination_rate: 0.0-1.0
  retry_count: <int>
  failed_step_ids: ["..."]
  recommended_followup:
    - skill: optimize-prompt | optimize-rag | optimize-tool-routing | optimize-agent-policy
      rationale: "<short>"
```

## Constraints

- Always read `harness_trace` first; never evaluate from memory alone.
- Score `hallucination_rate` against `claim_ledger_record` entries whose
  source URL was never actually fetched in the trace.
- Do not skip `tool_selection_accuracy` even when a run succeeded — that
  metric catches over-broad tool use.
