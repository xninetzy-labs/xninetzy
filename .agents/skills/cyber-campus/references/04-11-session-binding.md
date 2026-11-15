# cyber-campus — §4–11

Contents: 4. Session Binding; 5. Session Freshness; 6. Session Invalidation Signals; 7. Portal Context Binding; 8. Semester Identity; 9. Navigation; 10. Read Workflow; 11. Academic Read Identity

## 4. Session Binding

Every protected interaction receives:

```yaml
session:
  session_id:
  authenticated:
  identity_context:
  portal:
  created_at:
  last_verified_at:
  expires_at:
  scope:
```

Before protected reads:

```text
session valid?
identity correct?
portal correct?
```

Before writes:

```text
session valid?
identity correct?
portal correct?
academic period correct?
```

If any is unknown:

```text
STOP
```

---

## 5. Session Freshness

Classify:

```text
LIVE
FRESH
STALE
EXPIRED
UNKNOWN
```

Suggested semantics:

```text
LIVE
  verified immediately before operation

FRESH
  recently verified and no invalidation signal

STALE
  may no longer represent current portal state

EXPIRED
  session no longer valid

UNKNOWN
  validity cannot be established
```

Never treat:

```text
STALE
```

as:

```text
LIVE
```

---

## 6. Session Invalidation Signals

Invalidate session assumptions when:

```text
login page appears
unauthorized response
session timeout
portal switches account
portal switches institution
portal redirects to SSO
unexpected authentication prompt
permission context changes
academic period changes unexpectedly
```

After invalidation:

```text
re-check session
re-bind portal context
```

---

## 7. Portal Context Binding

Every read should record:

```yaml
portal_context:
  institution:
  portal_host:
  page:
  page_identity:
  academic_period:
  record_type:
  retrieved_at:
```

Example:

```text
institution:
  Universitas ...

academic_period:
  2026/2027 Ganjil

record_type:
  KRS
```

A grade with no identifiable academic period should be:

```text
PARTIAL
```

rather than silently assigned to the current semester.

---

## 8. Semester Identity

Treat semester as a first-class key.

```text
student
+
academic_year
+
semester
+
record_type
```

Example:

```text
2026/2027
Ganjil
Grades
```

is different from:

```text
2025/2026
Genap
Grades
```

Never merge them without explicit evidence.

---

## 9. Navigation

Navigation must be deterministic.

Before reading a page verify:

```text
current host
current authenticated identity
current page identity
current academic period
current module
```

Do not assume:

```text
known URL
```

means:

```text
intended academic page
```

---

## 10. Read Workflow

Canonical read:

```text
SESSION
  ↓
PORTAL CONTEXT
  ↓
NAVIGATE
  ↓
VERIFY PAGE
  ↓
READ
  ↓
NORMALIZE
  ↓
FRESHNESS
  ↓
RETURN
```

Reads include:

```text
profile
academic status
grades
schedule
course offerings
prerequisites
quota
eligibility
current KRS
submission state
```

---

## 11. Academic Read Identity

Every result should identify:

```text
portal
academic period
record type
retrieval time
source page
```

Example:

```yaml
grades:
  portal: cyber-campus
  period: "2026/2027 Ganjil"
  source_page: grades
  retrieved_at: ...
```

---
