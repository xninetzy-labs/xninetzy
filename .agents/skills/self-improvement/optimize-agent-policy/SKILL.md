---
name: optimize-agent-policy
description: Recommend changes to tier gates, idempotency rules, and confirmation flow based on harness + HITL feedback. Surfaces policy diffs; never applies without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - hitl_list_pending
    - hitl_review (proposed)
    - harness_trace
    - reflect-trajectory
  produces:
    - policy_candidates
  tier: 0
---

# optimize-agent-policy

Policy-variant generator. Reads HITL pending queue + harness trace +
reflection and surfaces candidate policy edits. Application always
requires `improvement_approve` (FINAL).

## When to invoke

- HITL approval queue shows recurring patterns
- `harness_recover` invoked more than N times in a window
- Owner asks "why are users approving the same thing repeatedly?"

## Inputs

```yaml
target: tier_gates | idempotency | approval_flow | harness_drift
evidence_refs: ["<plan_id>", "..."]
```

## Workflow

```yaml
steps:
  - id: pending
    tool: hitl_list_pending
    tier: 0
  - id: traces
    tool: harness_trace
    args: { plan_id: "<id>" }
    tier: 0
  - id: propose
    tool: improvement_propose
    args:
      target_kind: policy
      risk_level: high
    tier: 0
```

## Output structure

```yaml
policy_candidates:
  target: approval_flow
  baseline: { tier_3_halt: true, batch_approval_id_per_plan: false }
  candidates:
    - params: { tier_3_halt: true, batch_approval_id_per_plan: true }
      rationale: "<cite HITL queue size + recovery count>"
      risk_delta: "+low"
      proposed_change_id: "<id>"
```

## Constraints

- Never propose lowering tier for FINAL-class tools.
- Never propose removing CAPTCHA lockout threshold.
- Never propose removing idempotency key requirement for WRITE/FINAL.
- Apply path = `improvement_approve` (FINAL).
