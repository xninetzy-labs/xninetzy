---
name: reflect-trajectory
description: Reflect on a completed trajectory and surface lessons learned. Outputs a set of lessons, each tagged with applicability (prompt, plan, memory, tool).
metadata:
  type: workflow
  layer: self-improvement
  consumes:
    - harness_trace
    - evaluate-agent
  produces:
    - reflection
  tier: 0
---

# reflect-trajectory

Post-trajectory reflection. Surfaces actionable lessons without rewriting
anything. Lessons feed `experience-mining` and `memory-consolidation`.

## When to invoke

- After `evaluate-agent` produces a report
- Before `optimize-prompt` to seed candidate rewrites
- Whenever `lightning_episode_finish` is called

## Inputs

```yaml
plan_id: "<id>"
evaluation_report: <from evaluate-agent>
```

## Workflow

```yaml
steps:
  - id: read_eval
    tool: agent_synthesis (LLM-side, not an MCP tool)
    input: { evaluation_report: <ref> }
  - id: trace
    tool: harness_trace
    args: { plan_id: "<id>" }
    tier: 0
  - id: extract_lessons
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [trace]
```

## Output structure

```yaml
reflection:
  plan_id: "<id>"
  lessons:
    - text: "<single-sentence lesson>"
      applicability: prompt | plan | memory | tool
      confidence: 0.0-1.0
      evidence_step_ids: ["..."]
      suggested_skill:
        - optimize-prompt
        - optimize-tool-routing
```

## Constraints

- Each lesson must cite at least one `evidence_step_id`.
- Cap lessons at 5 per trajectory to keep downstream filtering cheap.
- Do not produce a lesson that contradicts `analyze-failure` without
  cross-citing the relevant step.
