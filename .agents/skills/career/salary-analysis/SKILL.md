---
name: salary-analysis
description: Aggregate salary signals from legal public job postings + owner profile. Surfaces median + range for a target role.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - memory_get_context
  produces:
    - salary_analysis_report
  tier: 0
---

# salary-analysis

Aggregate salary from postings that explicitly state pay. Many postings
omit pay; signal is therefore partial. Always surface sample size.

## When to invoke

- Owner asks "what salary should I expect for X?"
- Before salary negotiation prep

## Inputs

```yaml
target_role: "<role>"
country: "<ISO>"
work_mode: any
sample_min: int (default 5)
```

## Workflow

```yaml
steps:
  - id: search
    tool: career_search_jobs
    args:
      query: "<role>"
      country: "<country>"
      limit: 50
    tier: 0
  - id: aggregate
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [search]
```

## Output structure

```yaml
salary_analysis_report:
  target_role: "<echo>"
  sample_size: <int>
  postings_with_pay: <int>
  median_usd: <int | null>
  range_p25_usd: <int | null>
  range_p75_usd: <int | null>
  caveat: "Salary data only available from postings that disclose pay."
```

## Constraints

- Always surface `caveat` about sample bias.
- Never invent numbers from postings that don't disclose pay.
- Always include `sample_size`.

## Anti-patterns

- Do NOT extrapolate from <5 postings without a warning.
- Do NOT include pay in non-disclosed currencies without conversion note.
