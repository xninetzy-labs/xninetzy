---
name: skill-gap
description: Diff between owner profile skills and market demand for a target role. Surfaces priority learning recommendations.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_market_skill_trend
    - memory_get_context
  produces:
    - skill_gap_report
  tier: 0
---

# skill-gap

Compute owner vs market skill diff for a target role. Uses
`career_market_skill_trend` for frequency signals and
`memory_get_context` for owner skill list.

## When to invoke

- Owner asks "what should I learn to land X role?"
- After `job-matching` surfaces large gaps

## Inputs

```yaml
target_role: "<role>"
profile_skills: ["..."]
market_source: career_market_skill_trend
```

## Workflow

```yaml
steps:
  - id: market_trend
    tool: career_market_skill_trend
    args: { role: "<target_role>" }
    tier: 0
  - id: profile
    tool: memory_get_context
    args: { chat_id: "<owner>" }
    tier: 0
  - id: diff
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [market_trend, profile]
```

## Output structure

```yaml
skill_gap_report:
  target_role: "<echo>"
  market_top_skills: ["..."]
  owner_has: ["..."]
  owner_missing:
    - skill: "<name>"
      frequency_pct: 0-100
      recommended_learning:
        - skill: optimize-rag
        - skill: research-paper-search
```

## Constraints

- Always cite `frequency_pct` per missing skill.
- Always tie recommendations to existing skill bodies (`research-search`,
  `literature-review`, etc.) — no inventing new tooling.
- Never recommend a skill outside the registered set.

## Anti-patterns

- Do NOT recommend skills absent from `market_top_skills`.
- Do NOT prioritize low-frequency skills.
