---
name: run-grpo
description: Group Relative Policy Optimization fine-tuning run on a generated GRPO dataset. Requires GPU. CPU-only environments block execution.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - generate-training-data
  produces:
    - grpo_run_manifest
  tier: 0
---

# run-grpo

GRPO runner. Reads `training_dataset_manifest` (GRPO format) and produces
an adapter checkpoint. Skips on CPU-only hosts.

## When to invoke

- After `generate-training-data` produced a GRPO manifest
- Owner asks "GRPO-train on the preference groups"

## Inputs

```yaml
manifest_path: "<from generate-training-data>"
framework: trl
base_model: "<hf_model_id or local path>"
group_size: int (default 4)
epochs: int
```

## Workflow

```yaml
steps:
  - id: preflight_cpu
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: propose
    tool: improvement_propose
    args:
      target_kind: training_run
      risk_level: high
    tier: 0
  - id: run_trainer
    tool: agent_synthesis (LLM-side, gated on approval)
    depends_on: [propose]
```

## Output structure

```yaml
grpo_run_manifest:
  status: queued | running | succeeded | failed | blocked-cpu-only
  framework: trl
  base_model: "<hf_model_id>"
  adapter_checkpoint_path: "<path or null>"
  metrics:
    group_reward_curve: [...]
    eval_win_rate: <float | null>
```

## Constraints

- **CPU-only environments MUST short-circuit with `blocked-cpu-only`
  status.**
- Never write outside `RESEARCH_OUTPUT_DIR` / `GENERATED_DOCUMENTS_DIR`.
- Apply path = `improvement_approve` (FINAL).
- Promote path = `promote-model`.
