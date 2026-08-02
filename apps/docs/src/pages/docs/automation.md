---
layout: ../../layouts/DocsLayout.astro
title: Automation and scheduled jobs
description: Morning briefings, evening check-ins, weekly reviews, periodic HEBAT sync, leases, retries, and delivery state.
section: Operations
---

Xninetzy automation closes the
`Capture → Understand → Plan → Execute → Review → Adapt` loop. Scheduled
messages are built from current tasks, deadlines, roadmaps, habits, goals,
workouts, events, and freshness state rather than an unsupported LLM template.

## Configuration

```dotenv
OS_SCHEDULER_ENABLED=true
OS_SCHEDULER_STARTUP_DELAY_SECONDS=30
OS_SCHEDULER_POLL_SECONDS=60
OS_JOB_LEASE_SECONDS=900
OS_JOB_RETRY_DELAY_SECONDS=300
OS_NOTIFY_CHAT_ID=628xxxxxxxxxx@s.whatsapp.net

MORNING_BRIEFING_ENABLED=true
MORNING_BRIEFING_HOUR=7
EVENING_CHECKIN_ENABLED=true
EVENING_CHECKIN_HOUR=20
WEEKLY_REVIEW_ENABLED=true
WEEKLY_REVIEW_WEEKDAY=6
WEEKLY_REVIEW_HOUR=20

HEBAT_PERIODIC_SYNC_ENABLED=false
HEBAT_SYNC_INTERVAL_MINUTES=60
```

Hours follow `APP_TIMEZONE`. Weekdays use Python numbering: Monday is `0`
and Sunday is `6`. Delivery targets are resolved from
`OS_NOTIFY_CHAT_ID`, then `HEBAT_NOTIFY_CHAT_ID`, then `ADMIN_JID`.

Periodic HEBAT sync is disabled by default because it opens an authenticated
Moodle session. Enable it only after login is stable, the owner target is
correct, and rate limits have been reviewed.

## Job types

| Job | Idempotency key | Content |
|---|---|---|
| Morning briefing | owner + date | Tasks, deadlines, roadmap, and HEBAT freshness |
| Evening check-in | owner + date | Completed tasks, habits, and review prompt |
| Weekly review | owner + ISO week | Real events, goals, and roadmap progress |
| HEBAT sync | interval bucket | Assignments, shared tasks, and deadline reminders |

## Leases and delivery safety

Each run is persisted in SQLite before work begins. An interrupted internal job
can be reclaimed after its lease expires. Failed HEBAT syncs use persisted
backoff and attempt counts.

Before calling the WhatsApp engine, Xninetzy stores `delivery_started` with the
message content. This prevents a blind retry after restart. If the socket
response is lost, the state becomes `delivery_uncertain`: WhatsApp may already
have received the message, so an operator must inspect the chat before deciding
what to do.

At AI startup, stale `delivery_started` runs are reconciled to
`delivery_uncertain` before the scheduler claims new work.

## Inspecting status

Call this tool from natural chat or any MCP client:

```text
os_job_status
```

It reports the target, HEBAT freshness, state, attempt count, and last error.
Important states are:

- `running`: active with a lease;
- `delivery_started`: delivery has started;
- `delivered`: the WhatsApp engine accepted delivery;
- `succeeded`: an internal job completed;
- `failed`: failed and may have a retry schedule;
- `delivery_uncertain`: delivery is ambiguous and requires manual inspection.

## Freshness

HEBAT is stale when the last sync is older than twice
`HEBAT_SYNC_INTERVAL_MINUTES`. The morning briefing always discloses this
state; stale data is never presented as a guaranteed current deadline.
