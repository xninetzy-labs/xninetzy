---
name: analyze-failure
description: Diagnose why a specific plan or agent trajectory failed. Maps failures to root-cause classes (tool, data, reasoning, plan) and emits a fix recommendation per class.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - harness_trace
    - observability_query
  produces:
    - failure_diagnosis
  tier: 0
---

# analyze-failure

Per-failure root-cause classifier. Consumes the plan trace + claim ledger
and emits a structured diagnosis with one fix recommendation per
identified root cause.

## When to invoke

- `harness_review` surfaces a `status=failed` plan
- A specific step inside a verified plan was marked `outcome != ok`
- Owner asks "why did this fail?"

## Inputs

```yaml
plan_id: "<id>"
focus_step_id: "<optional step id, else whole plan>"
```

## Workflow

```yaml
steps:
  - id: trace
    tool: harness_trace
    args: { plan_id: "<id>" }
    tier: 0
  - id: failures
    tool: observability_query
    args: { event_kind: harness_action, severity: error }
    tier: 0
  - id: classify
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [trace, failures]
```

## Failure classes

| Class | Signal | Typical fix |
|---|---|---|
| `tool` | `outcome="unknown_tool"` or repeated 4xx/5xx from one tool | rewrite routing; widen tool set |
| `data` | source adapter returned `[]` or breaker open | switch adapter; widen fallback chain |
| `reasoning` | tool returned data but synthesis skipped/contradicted | tighten prompt; lower temperature |
| `plan` | dependency cycle or skipped cascade | re-plan; cap max_steps |
| `rate_limit` | adapter 429 spikes | lower RPM; add jitter |
| `auth` | 401/403 from adapter | rotate key; check env var |

## Output structure

```yaml
failure_diagnosis:
  plan_id: "<id>"
  scope: step | plan
  classes:
    - class: tool
      evidence_step_ids: ["..."]
      confidence: 0.0-1.0
      fix_skill: optimize-tool-routing
      fix_summary: "<short>"
  primary_recommendation: optimize-tool-routing
```

## Constraints

- Always map at least one class, even if confidence is low.
- Never blame `data` without first checking adapter `health()`.
- Never recommend a FINAL-class fix (e.g. improvement_approve) from this skill.
