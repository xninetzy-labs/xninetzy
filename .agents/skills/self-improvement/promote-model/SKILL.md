---
name: promote-model
description: Promote a benchmarked adapter to the live role. Records provenance, replaces live reference, emits audit receipt. Never executes without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - benchmark-model
    - compare-models
  produces:
    - promotion_receipt
  tier: 0
---

# promote-model

Adapter-promotion runner. Swaps the live adapter reference for a new
checkpoint that has cleared `benchmark-model` and (optionally)
`compare-models`. Emits an audit receipt. Gated by `improvement_approve`
(FINAL).

## When to invoke

- Benchmark report says `recommendation: promote`
- Owner asks "deploy this adapter"

## Inputs

```yaml
adapter_path: "<absolute path under RESEARCH_OUTPUT_DIR>"
role: "<e.g. xninetzy-default-reasoning>"
replace_existing: <bool, default true>
```

## Workflow

```yaml
steps:
  - id: preflight
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: propose
    tool: improvement_propose
    args:
      target_kind: promotion
      risk_level: high
    tier: 0
  - id: swap
    tool: agent_synthesis (LLM-side, gated on approval)
    depends_on: [propose]
```

## Output structure

```yaml
promotion_receipt:
  role: "<role>"
  previous_adapter_path: "<path | null>"
  new_adapter_path: "<path>"
  promoted_at: "<iso>"
  benchmark_source: "<benchmark_report path>"
  rollback_token: "<rollback-model>"
```

## Constraints

- Never auto-promote. Apply path = `improvement_approve` (FINAL).
- Always preserve `previous_adapter_path` so `rollback-model` can revert.
- Never write outside `RESEARCH_OUTPUT_DIR` / `GENERATED_DOCUMENTS_DIR`.
