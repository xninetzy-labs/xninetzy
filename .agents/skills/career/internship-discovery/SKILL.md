---
name: internship-discovery
description: Discover internship postings via legal public APIs. Filters by role keywords, location, and internship duration.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
  produces:
    - internship_discovery_report
  tier: 0
---

# internship-discovery

Find internship postings matching role + location. Uses legal public
job-board APIs only. Always filter for `internship` keyword and short
duration.

## When to invoke

- Owner asks "find me internships for X"
- University student job hunt

## Inputs

```yaml
query: "<role keywords>"
country: "<ISO>"
work_mode: remote | hybrid | onsite | any
duration_months_max: int (default 6)
limit: int (default 25)
```

## Workflow

```yaml
steps:
  - id: search_jobs
    tool: career_search_jobs
    args:
      query: "<query> intern OR internship"
      country: "<country>"
      work_mode: "<work_mode>"
      limit: <limit>
    tier: 0
  - id: filter_duration
    tool: agent_synthesis (LLM-side, not an MCP tool)
```

## Output structure

```yaml
internship_discovery_report:
  query: "<echo>"
  total_unique: <int>
  postings:
    - id: "<id>"
      source: <name>
      title: "<title>"
      company: "<company>"
      duration_months: <int | null>
      url: "<apply URL>"
      posted_at: "<iso | null>"
```

## Constraints

- Only legal public APIs.
- Filter by `intern` keyword in title.
- Discard postings without clear duration signal if `duration_months_max` set.

## Anti-patterns

- Do NOT confuse full-time roles with internships when title lacks `intern`.
- Do NOT scrape LinkedIn/Indeed/Glints.
