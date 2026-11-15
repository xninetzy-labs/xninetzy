# cli-creator — §30–38

Contents: 30. Offline / Fixture Mode; 31. Write Command Design; 32. Write Safety; 33. Write Approval Boundary; 34. Idempotency; 35. Destructive Operations; 36. Write Verification; 37. Polling; 38. Upload Workflow

## 30. Offline / Fixture Mode

If the CLI supports offline mode, expose it explicitly:

```text
doctor --json
```

should report:

```json
{
  "offline_mode": true,
  "fixture_data": true,
  "network_required": false
}
```

This prevents agents from interpreting fixture-backed success as live API success.

---

## 31. Write Command Design

Each write should correspond to one explicit business action.

Examples:

```text
create
update
delete
upload
schedule
retry
comment
draft
publish
cancel
```

Do not hide multiple writes inside:

```text
fix
sync
auto
repair
deploy-all
```

---

## 32. Write Safety

Write commands should support one or more:

```text
--dry-run
--preview
--draft
--confirm
--idempotency-key
```

where supported by the service.

Default:

```text
read-only
```

Write behavior must be obvious from the command name.

---

## 33. Write Approval Boundary

Before live write:

```text
target
resource
action
payload summary
environment
reversibility
```

must be clear.

For interactive workflows:

```text
preview
↓
explicit confirmation
↓
write
↓
verify
```

Do not hide live writes inside a read command.

---

## 34. Idempotency

For write APIs that support idempotency:

```text
--idempotency-key
```

must be exposed.

For create commands:

```text
same request
same idempotency key
```

should not unintentionally create duplicates.

If the API is naturally idempotent:

```text
document it
```

Do not invent fake idempotency guarantees at the CLI layer.

---

## 35. Destructive Operations

Destructive commands should be explicit:

```text
delete
destroy
remove
cancel
overwrite
publish
```

Where feasible:

```text
require --confirm
```

or:

```text
--dry-run
```

Never interpret:

```text
tool resource sync
```

as permission to delete unrelated resources.

---

## 36. Write Verification

A successful HTTP status is not necessarily a completed business action.

After a write, verify when the service supports it:

```text
create
 ↓
returned ID
 ↓
get/status
 ↓
confirmed state
```

For async jobs:

```text
create
 ↓
job ID
 ↓
poll
 ↓
terminal state
 ↓
read result
```

Possible states:

```text
queued
running
succeeded
failed
cancelled
unknown
```

---

## 37. Polling

For asynchronous APIs:

```text
--timeout
--interval
```

should be bounded.

Example:

```text
create
↓
status every 2s
↓
maximum 5 minutes
↓
STOP
```

Never poll forever.

---

## 38. Upload Workflow

For media/artifact uploads:

```text
create upload
↓
receive upload URL
↓
transfer bytes
↓
poll processing
↓
receive resource ID
↓
attach/reference
↓
verify
```

Treat each phase independently.

Never print:

```text
presigned URL
```

when it contains sensitive credentials or signatures.

---
