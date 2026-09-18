---
name: generate-training-data
description: Convert ranked trajectory rows into SFT/DPO/GRPO dataset format. Outputs JSONL file path + manifest. Never writes dataset without owner approval.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - experience-mining
    - harness_trace
  produces:
    - training_dataset_manifest
  tier: 0
---

# generate-training-data

Row → dataset converter. Reads candidate rows from `experience-mining`
and emits JSONL in SFT / DPO / GRPO format. Writes under
`RESEARCH_OUTPUT_DIR` or `GENERATED_DOCUMENTS_DIR` per artifact
allowlist. Never writes without owner approval.

## When to invoke

- After `experience-mining` returns candidates
- Owner asks "build me a SFT dataset from the last 100 plans"
- Before `run-sft` / `run-dpo` / `run-grpo`

## Inputs

```yaml
source: experience-mining | harness_plan_id_list
format: sft | dpo | grpo
output_dir: <RESEARCH_OUTPUT_DIR | GENERATED_DOCUMENTS_DIR>
```

## Workflow

```yaml
steps:
  - id: gather_rows
    tool: agent_synthesis (LLM-side, not an MCP tool)
    input: { candidates: <ref> }
  - id: format_jsonl
    tool: agent_synthesis (LLM-side, not an MCP tool)
  - id: write_manifest
    tool: improvement_propose
    args:
      target_kind: training_data
      risk_level: high
    tier: 0
```

## Output structure

```yaml
training_dataset_manifest:
  format: sft | dpo | grpo
  path: "<absolute path under RESEARCH_OUTPUT_DIR>"
  row_count: <int>
  schema_version: 1
  provenance:
    source_plan_ids: ["..."]
    generated_at: "<iso>"
  next_skill: run-sft | run-dpo | run-grpo
```

## Constraints

- Always write under `RESEARCH_OUTPUT_DIR` or `GENERATED_DOCUMENTS_DIR`
  (per AGENTS.md artifact allowlist).
- Never include PII or secrets in the dataset.
- Never include trajectories that triggered FINAL tools without owner
  sign-off.
- Apply path = owner approval of `improvement_propose` result.
