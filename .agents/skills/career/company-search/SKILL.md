---
name: company-search
description: Find companies hiring across legal public job-board APIs. Groups postings by employer, surfaces hiring signal.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_companies
    - career_search_jobs
  produces:
    - company_search_report
  tier: 0
---

# company-search

Aggregate company hiring signal. Calls `career_search_companies` and
optionally `career_search_jobs` to confirm open count.

## When to invoke

- Owner asks "which companies are hiring for X?"
- Before targeted application push

## Inputs

```yaml
query: "<company or industry keyword>"
limit: int (default 25)
```

## Workflow

```yaml
steps:
  - id: companies
    tool: career_search_companies
    args: { query: "<query>", limit: <limit> }
    tier: 0
```

## Output structure

```yaml
company_search_report:
  query: "<echo>"
  companies:
    - company: "<name>"
      source: <adapter>
      open_postings: <int>
      url: "<source URL>"
  total: <int>
```

## Constraints

- Only legal sources (RemoteOK, ArbeitNow).
- Always surface source per company.
- Never fabricate company facts beyond what's in posting snippets.

## Anti-patterns

- Do NOT include companies from sources not in the registry.
- Do NOT dedupe by fuzzy match across very different names.
