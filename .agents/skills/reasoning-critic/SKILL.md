---
name: reasoning-critic
description: Critic pass for reasoning outputs. Detects expectation mismatch, unsupported
  claims, missing evidence codes, and contradictions. Returns a verdict with severity-tagged
  defects.
metadata:
  type: meta
  layer: cognitive
  consumes: '[{"tool":"reasoning_critique"}]'
  produces: '["critic_verdict"]'
  tier: '0'
---


# reasoning-critic

Counterexample / self-critique step in the reasoning loop.

The critic NEVER re-explains the answer.
The critic ONLY looks for ways the answer could be wrong.

## When to invoke

- After a domain produces a candidate answer
- Before verification
- Before returning any high_risk or complex result

## Inputs

```yaml
expected: <string|None>
actual: <string|None>
claims: [<string>]
evidence_ids: [<string>]
missing_evidence_codes: [<string>]
contradictions: [<string>]
notes: [<string>]
```

## Defect codes

| code | severity | meaning |
|---|---|---|
| `EXPECTATION_MISMATCH` | blocker | expected != actual |
| `EMPTY_CLAIM_<n>` | warning | empty claim at index n |
| `UNSUPPORTED_CLAIM_<n>` | warning | claim contains hedging marker (probably, maybe, i think) |
| `MISSING_EVIDENCE_<code>` | blocker | required evidence code missing |
| `CONTRADICTION` | blocker | explicit contradiction submitted |

## Verdict

- `pass` — no defects
- `warn` — only warnings
- `fail` — at least one blocker

## Severity policy

- `blocker` always escalates to `fail`
- `warning` elevates to `warn`
- pure info → no defect

## Workflow

1. Collect candidate output from domain
2. Submit to `reasoning_critique` with expected + claims + evidence
3. If verdict == `fail`: return to orchestrator with `critic_fail` outcome
4. If verdict == `warn`: proceed with `ok_with_warnings` label
5. If verdict == `pass`: proceed normally
