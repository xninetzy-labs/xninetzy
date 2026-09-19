---
name: job-search
description: Broad job search across legal sources with structured filters. Outputs ranked postings by query relevance.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - source-selector
  produces:
    - job_search_report
  tier: 0
---

# job-search

Broader search than `job-discovery`. Includes multi-source fan-out,
keyword expansion, and basic ranking.

## When to invoke

- Owner asks "search for X jobs"
- Building a market view of role availability

## Inputs

```yaml
keywords:
  - "<kw1>"
  - "<kw2>"
country: "<ISO>"
work_mode: any
posted_within_days: int (default 30)
limit: int (default 50)
```

## Workflow

```yaml
steps:
  - id: expand_keywords
    tool: source-selector
    args: { intent: job }
    tier: 0
  - id: search
    tool: career_search_jobs
    args:
      keywords: <list>
      country: "<ISO>"
      work_mode: "<work_mode>"
      posted_within_days: <int>
      limit: <limit>
    tier: 0
  - id: rank
    tool: agent_synthesis (LLM-side, not an MCP tool)
    depends_on: [search]
```

## Output structure

```yaml
job_search_report:
  keywords: [...]
  postings:
    - id: "<id>"
      source: <name>
      title: "<title>"
      company: "<company>"
      url: "<url>"
      posted_at: "<iso>"
      match_score: 0.0-1.0
      match_reasons: ["..."]
  total: <int>
```

## Constraints

- Always include multiple keywords (not just one).
- Always rank by `match_score` descending.
- Always cite source per posting.

## Anti-patterns

- Do NOT score on location bias. Score by keyword match + recency.
- Do NOT include postings outside the requested `posted_within_days`.
