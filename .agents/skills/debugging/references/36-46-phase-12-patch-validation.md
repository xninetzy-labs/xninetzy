# debugging — §36–46

Contents: 36. Phase 12 — PATCH VALIDATION; 37. Blast-Radius Testing; 38. Diff Safety; 39. Dependency / Environment Failures; 40. Distributed / Async Debugging; 41. Database Debugging; 42. Concurrency / Race Debugging; 43. Time / Ordering Bugs; 44. Observability Gaps; 45. Safe Instrumentation; 46. Security Boundary

## 36. Phase 12 — PATCH VALIDATION

After applying the fix:

```text
1. rerun reproduction
2. run regression test
3. run affected package/module tests
4. inspect diff
5. run relevant integration tests
6. run broader tests according to blast radius
```

Do not stop at the first passing test.

---

## 37. Blast-Radius Testing

Use the affected dependency graph to determine test depth.

Typical escalation:

```text
symbol
 ↓
module
 ↓
package
 ↓
service
 ↓
integration
 ↓
system
```

Cross-module failures should route through:

```text
architecture-analysis
```

when architectural coupling is part of the causal path.

---

## 38. Diff Safety

Before finalizing the patch:

```text
repo_diff
```

must verify:

```text
scope is expected
no unrelated files changed
no debug artifacts remain
no secrets introduced
no tests weakened
no error handling silently suppressed
no temporary bypass remains
```

---

## 39. Dependency / Environment Failures

When evidence points outside the application code, inspect:

```text
runtime version
dependency version
lockfile
container image
environment variables
configuration
network
database schema
migration state
feature flags
build artifacts
deployment version
```

Do not edit application logic to compensate for an unverified environment mismatch.

---

## 40. Distributed / Async Debugging

For multi-service systems, trace:

```text
request_id
trace_id
job_id
event_id
message_id
transaction_id
```

across:

```text
client
API
worker
queue
database
external service
```

Establish:

```text
producer state
→ transport state
→ consumer state
→ persistence state
```

Do not assume the service reporting the error caused the failure.

---

## 41. Database Debugging

Separate:

```text
query generation
query transmission
database execution
transaction visibility
commit
rollback
replication
read-after-write visibility
```

Check:

```text
schema version
migration state
transaction boundary
isolation behavior
constraints
deadlocks
timeouts
connection pool
```

Do not label a failure "database-related" until the failing boundary is localized.

---

## 42. Concurrency / Race Debugging

For concurrency issues, record:

```text
thread/task identity
ordering
timestamps
shared resource
lock state
transaction state
interleaving
retry behavior
```

A race-condition claim requires evidence of an ordering or synchronization defect.

Intermittence alone is insufficient.

---

## 43. Time / Ordering Bugs

Use explicit timelines.

```text
T0 producer starts
T1 producer writes
T2 consumer starts
T3 consumer reads
T4 producer commits
```

Then identify:

```text
expected ordering
actual ordering
missing synchronization
```

Time-sensitive debugging should avoid ambiguous wall-clock interpretation when
monotonic timestamps or trace ordering is available.

---

## 44. Observability Gaps

If evidence cannot establish the causal path because telemetry is missing:

```text
OBSERVABILITY_GAP
```

Do not manufacture certainty.

Instead identify the smallest useful instrumentation needed:

```yaml
instrumentation_gap:
  missing_signal:
  insertion_point:
  expected_observation:
  privacy_risk:
  cleanup_required:
```

Instrumentation must not leak credentials or sensitive data.

---

## 45. Safe Instrumentation

Temporary debugging instrumentation must:

```text
have bounded scope
avoid secrets
avoid sensitive payload logging
carry a cleanup path
not materially alter timing when timing is under investigation
```

For timing/race bugs, instrumentation itself can perturb the failure.

When that risk exists, prefer tracing, sampling, counters, or existing telemetry.

---

## 46. Security Boundary

When a debugging signal indicates:

```text
authentication
authorization
secret leakage
SSRF
injection
unsafe deserialization
sandbox escape
MCP/tool boundary failure
```

route to:

```text
xninetzy-security-testing
```

or:

```text
api-security
```

as appropriate.

Do not weaken security controls merely to reproduce a bug.

---
