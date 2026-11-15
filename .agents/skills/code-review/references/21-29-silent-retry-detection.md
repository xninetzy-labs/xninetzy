# code-review — §21–29

Contents: 21. Silent Retry Detection; 22. Retry Safety; 23. Idempotency; 24. Transaction Boundaries; 25. Concurrency / Race Analysis; 26. Layer Boundary; 27. Architecture Drift; 28. Dependency Direction; 29. API Contract

## 21. Silent Retry Detection

Flag retries that are:

```text
implicit
unbounded
non-deterministic
hidden from callers
```

Check:

```text
max attempts
backoff
timeout
retryable error classification
idempotency
observability
```

Never approve:

```text
while true:
    request()
```

without explicit project-approved semantics.

---

## 22. Retry Safety

A retry is only safe when:

```text
operation is idempotent
OR
idempotency key exists
OR
duplicate side effects are explicitly prevented
```

Examples of dangerous retries:

```text
payment
create resource
send notification
publish event
charge account
enqueue job
```

---

## 23. Idempotency

For every changed write operation ask:

```text
Can the same request execute twice?
```

Check:

```text
PUT
PATCH
POST
DELETE
queue operations
background jobs
webhooks
scheduled jobs
```

Evidence:

```text
idempotency key
unique constraint
transaction boundary
deduplication key
upsert
state check
```

A function named `create` is not automatically non-idempotent or idempotent;
inspect implementation.

---

## 24. Transaction Boundaries

Where state changes are introduced, inspect:

```text
database write
+
external side effect
```

Potential issue:

```text
database commit
    ↓
external API fails
```

or:

```text
external side effect
    ↓
database rollback
```

Check whether the architecture provides:

```text
transaction
outbox
saga
compensation
retry policy
idempotency
```

Do not demand distributed transactions where the project architecture intentionally
uses another consistency model.

---

## 25. Concurrency / Race Analysis

When changes involve shared state, inspect:

```text
parallel requests
async tasks
workers
queues
locks
caches
transactions
```

Potential classes:

```text
TOCTOU
duplicate creation
lost update
double processing
race on authorization
race on cache state
```

Evidence should cite:

```text
shared resource
read
write
synchronization boundary
```

---

## 26. Layer Boundary

Use:

```text
repo_architecture
```

and companion:

```text
architecture-analysis
```

Check:

```text
presentation
application
domain
infrastructure
data
integration
```

for direction violations.

Every violation should identify:

```text
source module
target module
import/call
expected direction
```

---

## 27. Architecture Drift

A diff may introduce:

```text
new cycle
new cross-layer edge
new cross-feature dependency
new framework leak
new direct DB access
new shared-module dependency
```

Compare:

```text
before graph
vs
after graph
```

Flag only newly introduced or materially worsened drift unless the review explicitly
requests legacy architecture analysis.

---

## 28. Dependency Direction

Check:

```text
consumer
producer
dependency type
layer
```

Potential issue:

```text
domain
  -> infrastructure
```

or:

```text
core
  -> feature-specific implementation
```

Do not propose an abstraction until the actual dependency is understood.

---

## 29. API Contract

For API changes inspect:

```text
route
method
request schema
response schema
authentication
authorization
status codes
error shape
pagination
headers
rate limits
```

Use:

```text
api-security
```

when the change materially affects API security.

---
