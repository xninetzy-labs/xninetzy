---
name: rollback-model
description: Revert a promotion to its previous adapter. Validates the rollback token from the original promotion receipt. Never executes without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - promote-model (receipt)
  produces:
    - rollback_receipt
  tier: 0
---

# rollback-model

Adapter-revert runner. Reads a `promotion_receipt` and swaps the live
adapter back to `previous_adapter_path`. Gated by `improvement_approve`
(FINAL).

## When to invoke

- Owner detects regression after a promotion
- Benchmark after promotion shows degradation
- Owner asks "revert that promotion"

## Inputs

```yaml
rollback_token: "<from promotion_receipt>"
role: "<role>"
reason: "<short>"
```

## Workflow

```yaml
steps:
  - id: validate_token
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: propose
    tool: improvement_propose
    args:
      target_kind: rollback
      risk_level: high
    tier: 0
  - id: revert
    tool: agent_synthesis (LLM-side, gated on approval)
    depends_on: [propose]
```

## Output structure

```yaml
rollback_receipt:
  role: "<role>"
  reverted_from: "<new adapter path>"
  reverted_to: "<previous adapter path>"
  rolled_back_at: "<iso>"
  reason: "<short>"
```

## Constraints

- Never auto-revert. Apply path = `improvement_approve` (FINAL).
- Always validate `rollback_token` against the original
  `promotion_receipt`.
- Never delete the rolled-back-from adapter; archive it.
