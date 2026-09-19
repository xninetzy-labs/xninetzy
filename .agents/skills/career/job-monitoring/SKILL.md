---
name: job-monitoring
description: Watch for new postings matching owner preferences. Schedules a periodic `career_search_jobs` check and notifies on new matches.
metadata:
  type: workflow
  layer: career
  consumes:
    - os_scheduler
    - career_search_jobs
    - admin_notify_progress
  produces:
    - monitoring_subscription
  tier: 0
---

# job-monitoring

Periodic job-posting watch. Uses `os_scheduler` for cadence. Owner-scoped.

## When to invoke

- Owner wants passive new-posting alerts
- Active job hunt underway

## Inputs

```yaml
query: "<role keywords>"
country: "<ISO>"
work_mode: any
interval_minutes: int (default 240)
owner: "<owner principal>"
```

## Workflow

```yaml
steps:
  - id: schedule
    tool: os_job_create
    args:
      name: career_monitor_<query>
      interval_minutes: <int>
      handler: career_search_jobs
      args: { query, country, work_mode }
    tier: 0
```

## Output structure

```yaml
monitoring_subscription:
  id: "<os_job_id>"
  query: "<echo>"
  interval_minutes: <int>
  notify_via: admin_notify_progress
  owner: "<principal>"
```

## Constraints

- Always owner-scoped.
- Always use `os_scheduler` (no cron injection).
- Always emit notification via `admin_notify_progress` not direct message.

## Anti-patterns

- Do NOT poll external APIs more often than every 60 minutes.
- Do NOT notify on every match; dedupe across runs.
