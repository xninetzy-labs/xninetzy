---
name: run-dpo
description: Direct Preference Optimization fine-tuning run on a generated DPO dataset. Requires GPU. CPU-only environments block execution.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - generate-training-data
  produces:
    - dpo_run_manifest
  tier: 0
---

# run-dpo

DPO runner. Reads `training_dataset_manifest` (DPO format) and produces
an adapter checkpoint. Skips on CPU-only hosts.

## When to invoke

- After `generate-training-data` produced a DPO manifest
- Owner asks "DPO-train on the preference pairs"

## Inputs

```yaml
manifest_path: "<from generate-training-data>"
framework: trl
base_model: "<hf_model_id or local path>"
epochs: int
beta: float (default 0.1)
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
dpo_run_manifest:
  status: queued | running | succeeded | failed | blocked-cpu-only
  framework: trl
  base_model: "<hf_model_id>"
  adapter_checkpoint_path: "<path or null>"
  metrics:
    reward_curve: [...]
    eval_accuracy: <float | null>
```

## Constraints

- **CPU-only environments MUST short-circuit with `blocked-cpu-only`
  status.**
- Never write outside `RESEARCH_OUTPUT_DIR` / `GENERATED_DOCUMENTS_DIR`.
- Apply path = `improvement_approve` (FINAL).
- Promote path = `promote-model`.
