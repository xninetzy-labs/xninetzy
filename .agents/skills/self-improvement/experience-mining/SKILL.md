---
name: experience-mining
description: Mine high-quality trajectories from harness history for use as training data. Filters by task_completion + tool_selection_accuracy thresholds. Outputs ranked candidate dataset rows.
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - harness_review
    - evaluate-agent
  produces:
    - training_dataset_candidates
  tier: 0
---

# experience-mining

Filters harness history to extract successful trajectories suitable for
SFT/DPO/GRPO training data. Never applies — produces candidate rows
that an owner can approve into a dataset.

## When to invoke

- After a batch of plans completes and `evaluate-agent` reports stable
  metrics
- Before `generate-training-data` to scope which trajectories qualify
- Lightning episode count > 500

## Inputs

```yaml
filters:
  min_task_completion: 0.85
  min_tool_selection_accuracy: 0.75
  max_hallucination_rate: 0.10
  recency_days: 30
```

## Workflow

```yaml
steps:
  - id: review
    tool: harness_review
    args:
      owner: "<owner>"
      status_filter: verified
      limit: 200
    tier: 0
  - id: evaluate_each
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [review]
  - id: rank
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [evaluate_each]
```

## Output structure

```yaml
training_dataset_candidates:
  total_plans_considered: <int>
  total_passing: <int>
  rows:
    - plan_id: "<id>"
      task_completion: 0.0-1.0
      tool_selection_accuracy: 0.0-1.0
      hallucination_rate: 0.0-1.0
      row_format: sft | dpo-preferred | dpo-dispreferred
```

## Constraints

- Never include a plan that completed via CAPTCHA bypass.
- Never include a plan that triggered `harness_recover` more than once.
- Apply path = `generate-training-data` (next skill), which itself
  requires owner approval.
