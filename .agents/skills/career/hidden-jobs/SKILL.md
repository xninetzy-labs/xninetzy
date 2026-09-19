---
name: hidden-jobs
description: Surface postings from long-tail / non-mainstream boards only. Filter out mainstream aggregators.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_find_hidden_jobs
  produces:
    - hidden_jobs_report
  tier: 0
---

# hidden-jobs

Filter out postings from mainstream aggregators (LinkedIn, Indeed,
Glassdoor, JobStreet, Glints). Output = long-tail / small-board only.

## When to invoke

- Owner exhausted mainstream boards
- Owner specifically asks for "less crowded" opportunities

## Inputs

```yaml
role: "<role keywords>"
country: "<ISO>"
limit: int (default 25)
```

## Workflow

```yaml
steps:
  - id: search
    tool: career_find_hidden_jobs
    args: { role: "<role>", country: "<country>", limit: <limit> }
    tier: 0
```

## Output structure

```yaml
hidden_jobs_report:
  role: "<echo>"
  results:
    - <posting>
  total: <int>
  mainstream_filter: ["linkedin", "indeed", ...]
  status: ok
```

## Constraints

- Always emit `mainstream_filter` so owner can audit the filter list.
- Never widen filter beyond the registered set without owner confirmation.
- Never return postings from sources without explicit API access.

## Anti-patterns

- Do NOT add LinkedIn/JobStreet/Glints to "hidden" results.
- Do NOT relax the mainstream filter silently.
