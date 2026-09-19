---
name: similar-jobs
description: Find postings similar to a seed posting (same company or title-overlap).
metadata:
  type: workflow
  layer: career
  consumes:
    - career_find_similar_jobs
  produces:
    - similar_jobs_report
  tier: 0
---

# similar-jobs

Surface postings similar to a seed posting. Uses posting text +
company name as signals; never re-scrapes the source.

## When to invoke

- Owner likes a posting and wants more like it
- After CV tailoring, to expand application pool

## Inputs

```yaml
posting_id: "<seed posting id>"
limit: int (default 15)
```

## Workflow

```yaml
steps:
  - id: similar
    tool: career_find_similar_jobs
    args: { posting_id: "<id>", limit: <limit> }
    tier: 0
```

## Output structure

```yaml
similar_jobs_report:
  seed_posting_id: "<id>"
  results:
    - posting: <record_dict>
      reason: same_company | similar_title
  total: <int>
```

## Constraints

- Always show reason per match (same_company vs similar_title).
- Never return the seed posting itself.
- Cap output at `limit`.

## Anti-patterns

- Do NOT match across postings from sources without explicit API access.
- Do NOT surface "similar" postings from a different role family.
