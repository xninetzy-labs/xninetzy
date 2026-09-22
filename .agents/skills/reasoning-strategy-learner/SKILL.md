---
name: reasoning-strategy-learner
description: Tracks reasoning strategy outcomes per context, exposes history trace,
  and supports replay-safe strategy updates. Used by Lightning to learn which reasoning
  depth + tool budget works for which task class.
metadata:
  type: meta
  layer: learning
  consumes: '[{"tool":"reasoning_record_history"},{"tool":"reasoning_set_strategy"},{"tool":"reasoning_get_strategy"},{"tool":"reasoning_trace"},{"tool":"reasoning_clear_strategy"}]'
  produces: '["strategy_descriptor","reasoning_trace"]'
  tier: '0'
---


# reasoning-strategy-learner

Maintains per-context reasoning strategy state. Provides:

- `reasoning_set_strategy` — register depth + budget for a context
- `reasoning_get_strategy` — read current strategy
- `reasoning_record_history` — append step to history
- `reasoning_trace` — recent history + tool/outcome counters
- `reasoning_clear_strategy` — release state

## State model

```yaml
context_key: <string>
depth: <trivial|routine|complex|high_risk>
min_iterations: <int>
max_iterations: <int>
anti_loop_window: <int>
history:
  - { hypothesis: <str>, tool: <str>, outcome: <str> }
```

## Anti-loop contract

When `reasoning_should_stop` returns `replan` with anti-loop signal,
the strategy learner records the failing fingerprint. Future strategy
choices SHOULD avoid that fingerprint for the same `context_key`.

## Lightning feedback

After every harness execution, the orchestrator SHOULD record:

- `context_key`
- final depth
- total iterations
- stop outcome
- critic verdict
- tool calls used
- evidence pieces used

This is the learning signal for which depth budget works for which
task class.

## When to invoke

- Setting up a new reasoning loop
- Reading the current state before deciding next step
- Cleaning up after a completed run
