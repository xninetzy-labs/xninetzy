---
name: application-tracking
description: Track job applications in the owner-controlled memory store. Records status (drafted, applied, interviewed, rejected, offer). Always owner-scoped.
metadata:
  type: workflow
  layer: career
  consumes:
    - memory_add
    - memory_search
  produces:
    - application_log
  tier: 0
---

# application-tracking

Track applications in owner-scoped memory. Never posts to external
systems. Never scrapes employer portals.

## When to invoke

- After applying to a posting
- Weekly review

## Inputs

```yaml
posting_id: "<id>"
status: drafted | applied | phone_screen | interviewed | offer | rejected | withdrawn
notes: "<short>"
```

## Workflow

```yaml
steps:
  - id: log
    tool: memory_add
    args:
      scope: career_applications
      key: "<posting_id>"
      value: { status, notes, updated_at: <iso> }
    tier: 0
```

## Output structure

```yaml
application_log:
  posting_id: "<id>"
  status: <echo>
  recorded_at: "<iso>"
  retrieve_via: memory_search(scope="career_applications")
```

## Constraints

- Always owner-scoped (never global).
- Always emit `recorded_at` timestamp.
- Never sync to external ATS systems.

## Anti-patterns

- Do NOT auto-update status without owner confirmation.
- Do NOT expose application log to non-owner tools.
