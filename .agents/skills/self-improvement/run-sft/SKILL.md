---
name: run-sft
description: Supervised fine-tuning run on a generated SFT dataset. Requires GPU + training framework configured. Never executes without owner approval. CPU-only environments block execution and surface a clear hardware-block error.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - generate-training-data
  produces:
    - sft_run_manifest
  tier: 0
---

# run-sft

SFT runner. Reads `training_dataset_manifest` from `generate-training-data`
and produces an adapter checkpoint path. Skips execution on CPU-only hosts.

## When to invoke

- After `generate-training-data` produced an SFT manifest
- Owner asks "train on the latest SFT dataset"

## Inputs

```yaml
manifest_path: "<from generate-training-data>"
framework: transformers | trl | unsloth
base_model: "<hf_model_id or local path>"
epochs: int
batch_size: int
learning_rate: float
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
sft_run_manifest:
  status: queued | running | succeeded | failed | blocked-cpu-only
  framework: trl
  base_model: "<hf_model_id>"
  adapter_checkpoint_path: "<path or null>"
  metrics:
    train_loss_curve: [...]
    eval_loss: <float | null>
  blocked_reason: "<if blocked-cpu-only>"
```

## Constraints

- **CPU-only environments MUST short-circuit with `blocked-cpu-only`
  status.** Per AGENTS.md §1, xninetzy runtime is CPU-only.
- Never write outside `RESEARCH_OUTPUT_DIR` / `GENERATED_DOCUMENTS_DIR`.
- Apply path = `improvement_approve` (FINAL).
- Promote path = `promote-model`.
