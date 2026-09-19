---
name: market-skill-trend
description: Aggregate skill frequency from legal public job postings for a target role. Surfaces frequency-ranked skill list with recency weighting.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
  produces:
    - market_skill_trend_report
  tier: 0
---

# market-skill-trend

Skill frequency analysis. Reads postings from `career_search_jobs`,
extracts skill mentions via LLM, ranks by frequency.

## When to invoke

- Owner asks "what skills do X roles want?"
- Before `skill-gap`

## Inputs

```yaml
target_role: "<role>"
country: "<ISO>"
posted_within_days: int (default 60)
limit: int (default 50)
```

## Workflow

```yaml
steps:
  - id: search
    tool: career_search_jobs
    args:
      query: "<role>"
      country: "<country>"
      limit: <limit>
    tier: 0
  - id: extract_skills
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [search]
  - id: rank
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [extract_skills]
```

## Output structure

```yaml
market_skill_trend_report:
  target_role: "<echo>"
  postings_analyzed: <int>
  skills:
    - skill: "<name>"
      frequency_pct: 0-100
      postings_with_skill: <int>
  caveat: "Skill extraction is LLM-derived from posting text; results may include false positives."
```

## Constraints

- Always report `caveat`.
- Always cite `postings_analyzed`.
- Always surface top N skills (default 20).

## Anti-patterns

- Do NOT include skills mentioned only once.
- Do NOT bias toward trendy frameworks absent from multiple postings.
