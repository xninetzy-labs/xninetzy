---
name: "reasoning-orchestrator"
description: "Cross-cutting reasoning layer for XNINETZY. Decides thinking depth, runs the critic pass, and applies the stopping rule before/after every non-trivial task. Used by research, exam_qa, process_engineering, developer, security, and quant domains."
metadata:
  type: "meta"
  layer: "cognitive"
  consumes:
    - tool: reasoning_classify_depth
    - tool: reasoning_critique
    - tool: reasoning_should_stop
    - tool: reasoning_record_history
    - tool: reasoning_set_strategy
  produces:
    - reasoning_depth
    - critic_verdict
    - stop_decision
  tier: "0"
---

# reasoning-orchestrator

Cross-cutting reasoning layer for XNINETZY. It is NOT a domain.
It is the cognitive wrapper that every domain task should pass through.

The orchestrator decides:

- how much reasoning depth the task deserves (trivial/routine/complex/high_risk)
- which evidence budget is required
- whether to generate alternatives
- whether counterexample search is required
- what verification depth is mandatory

## When to invoke

- Before any non-trivial plan
- After any domain produces a candidate answer
- Before returning high-risk results to the user

## Inputs

```yaml
request:
  intent: <string>
  side_effect: <read_only|non_idempotent_write|external|irreversible>
  trust_tier: <0..4>
  multi_domain: <bool>
  high_value: <bool>
```

## Outputs

```yaml
depth:
  name: <trivial|routine|complex|high_risk>
  rank: <0..3>
  min_tool_budget: <int>
  min_evidence_budget: <int>
  requires_verification: <bool>
  requires_alternatives: <bool>
  requires_counterexample: <bool>
critic:
  verdict: <pass|warn|fail>
  defects: [<code,severity,message>]
stop:
  outcome: <continue|halt|replan>
  reason: <string>
  anti_loop: <fingerprint,repeat_count>
```

## Workflow

1. Run `reasoning_classify_depth` to obtain depth from side-effect + trust
2. Apply depth policy (tool budget, evidence budget, counterexample flag)
3. Execute domain task per depth policy
4. Run `reasoning_critique` against the candidate result
5. Run `reasoning_should_stop` to decide halt/replan/continue
6. Record history step via `reasoning_record_history`
7. If `replan`: re-enter step 2 with adjusted strategy
8. If `halt`: return result with critic + stop descriptors

## Depth policy table

| depth | tool budget | evidence budget | alternatives | counterexample | verification |
|---|---|---|---|---|---|
| trivial | 1 | 0 | no | no | no |
| routine | 2 | 1 | no | no | yes |
| complex | 4 | 3 | yes | yes | yes |
| high_risk | 6 | 5 | yes | yes | yes + HITL |

## Anti-loop rule

If `reasoning_should_stop` returns `replan` because of anti-loop signal,
the orchestrator MUST change strategy (different hypothesis, different
tool, or different evidence source) — never repeat the exact same action.

## Failure modes

- `UNDERTHINKING` — depth classified too low for risk → critic escalates
- `OVERTHINKING` — depth classified too high → tool budget violated → stop.halt
- `REASONING_LOOP` — repeated fingerprint → stop.replan
- `MISSING_EVIDENCE` — required evidence code missing → critic.fail
- `UNSUPPORTED_CLAIM` — claim contains hedging markers → critic.warn

## Integration with Harness

The orchestrator wraps the harness:

```
INTENT
  → classify depth
  → plan (depth budget applied)
  → execute
  → critic
  → stop
  → checkpoint (depth + critic + stop recorded)
  → report
```
