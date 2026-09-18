---
name: benchmark-model
description: Run a CPU-friendly benchmark suite against a model or adapter. Surfaces accuracy / latency / cost metrics. Never overwrites live adapter without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - harness_plan
    - reflect-trajectory
  produces:
    - benchmark_report
  tier: 0
---

# benchmark-model

CPU-runnable benchmark for evaluating models or adapters. Uses
`lm-evaluation-harness` or equivalent for accuracy; uses harness trace
for latency / cost signals.

## When to invoke

- Before `promote-model` (always benchmark first)
- After `run-sft` / `run-dpo` / `run-grpo` completes
- Owner asks "is this adapter better than baseline?"

## Inputs

```yaml
target_model: "<hf_model_id | local path | adapter_path>"
baseline_model: "<hf_model_id | local path>"
tasks:
  - name: "<task>"
    fewshot: <int>
    limit: <int>
```

## Workflow

```yaml
steps:
  - id: preflight
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: run_bench
    tool: agent_synthesis (LLM-side, optional lm-eval-harness path)
  - id: report
    tool: improvement_propose
    args:
      target_kind: benchmark
      risk_level: medium
    tier: 0
```

## Output structure

```yaml
benchmark_report:
  target_model: "<id>"
  baseline_model: "<id>"
  tasks:
    - name: "<task>"
      accuracy: 0.0-1.0
      baseline_accuracy: 0.0-1.0
      delta: "+/- pp"
  latency_p50_ms: <int>
  latency_p95_ms: <int>
  recommendation: promote | hold | reject
```

## Constraints

- Never overwrite the live adapter from this skill. Promote is a
  separate skill gated by `improvement_approve` (FINAL).
- Always include baseline comparison when baseline provided.
- Apply path = owner approval of the benchmark recommendation.
