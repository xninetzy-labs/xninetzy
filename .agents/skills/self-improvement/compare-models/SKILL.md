---
name: compare-models
description: Side-by-side comparison of two or more models or adapters on the same task set. Outputs ranked table with per-metric deltas.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - benchmark-model
  produces:
    - comparison_report
  tier: 0
---

# compare-models

Head-to-head comparison. Reads multiple `benchmark_report` outputs and
emits a ranked table.

## When to invoke

- After running `benchmark-model` on ≥ 2 candidates
- Owner asks "which adapter is better for X task?"

## Inputs

```yaml
benchmark_reports: ["<path>", "..."]
primary_task: "<task name>"
```

## Workflow

```yaml
steps:
  - id: gather
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: rank
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: report
    tool: improvement_propose
    args:
      target_kind: comparison
      risk_level: low
    tier: 0
```

## Output structure

```yaml
comparison_report:
  primary_task: "<task>"
  ranked:
    - rank: 1
      model: "<id>"
      primary_accuracy: 0.0-1.0
      p95_latency_ms: <int>
      recommendation_strength: strong | moderate | weak
    - rank: 2
      model: "<id>"
      ...
  statistical_note: "<paired t-test p-value or n/a>"
```

## Constraints

- Always cite the benchmark source for each row.
- Never recommend a model without at least one paired comparison metric.
- Apply path = owner approval.
