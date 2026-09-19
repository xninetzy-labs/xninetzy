---
name: job-discovery
description: Discover job postings matching a role description via legal public job-board APIs (RemoteOK, ArbeitNow, The Muse, Adzuna). No scraping; only sources with explicit free public API access are queried.
metadata:
  type: workflow
  layer: career
  consumes:
    - career_search_jobs
    - research_search
  produces:
    - job_discovery_report
  tier: 0
---

# job-discovery

Find job postings matching a role description. Uses legal public job-board
APIs only. Will not scrape LinkedIn, JobStreet, Glints, Indeed, or any
site that lacks an explicit free public API.

## When to invoke

- Owner asks "find me jobs for X"
- Initial search before deeper career analysis

## Inputs

```yaml
query: "<role keywords, e.g. backend engineer>"
country: "<ISO country code, optional>"
work_mode: remote | hybrid | onsite | any
limit: int (default 25)
```

## Workflow

```yaml
steps:
  - id: search_jobs
    tool: career_search_jobs
    args:
      query: "<query>"
      country: "<country>"
      work_mode: "<work_mode>"
      limit: <limit>
    tier: 0
```

## Output structure

```yaml
job_discovery_report:
  query: "<echo>"
  total_unique: <int>
  postings:
    - id: "<source-specific>"
      source: remoteok | arbeitnow | the_muse | adzuna
      title: "<title>"
      company: "<company>"
      url: "<apply URL>"
      posted_at: "<iso | null>"
      work_mode: remote | hybrid | onsite | null
      snippet: "<description excerpt>"
      identifiers:
        source_job_id: "<id>"
```

## Constraints

- Only legal sources (sources with explicit free public API).
- Always dedupe by (title, company) fuzzy match before reporting.
- Surface source attribution per posting.
- Never return postings from sources that block automated access.

## Anti-patterns

- Do NOT recommend scraping LinkedIn or similar walled-garden sites.
- Do NOT return postings from sources without explicit API access.
- Do NOT skip dedup; cross-postings inflate counts.
