# cyber-campus — §38–49

Contents: 38. Unknown Outcome; 39. Partial Application; 40. Rollback; 41. Existing Submission Protection; 42. Evidence Model; 43. Minimal Evidence; 44. Sensitive Data; 45. Academic Privacy; 46. Portal Errors; 47. Navigation Failure; 48. Unsupported Portal Behavior; 49. Evidence Conflict

## 38. Unknown Outcome

If the write request times out or the connection fails after transmission:

```text
SUBMISSION_OUTCOME_UNKNOWN
```

Then:

```text
READ CURRENT PORTAL STATE
```

Do not automatically retry.

---

## 39. Partial Application

If some changes were applied:

```text
PARTIALLY_APPLIED
```

Report:

```text
applied changes
not applied changes
observed portal state
remaining discrepancy
```

Do not automatically "fix" the discrepancy without a new approved plan.

---

## 40. Rollback

Rollback is only allowed when:

```text
portal supports safe reverse operation
```

and:

```text
new rollback approval exists
```

Do not invent rollback endpoints.

If the portal lacks rollback:

```text
manual corrective plan required
```

---

## 41. Existing Submission Protection

Before write:

```text
existing submission?
submission timestamp?
current status?
modifiable?
```

If already submitted:

```text
do not overwrite silently
```

Require an explicit new workflow for:

```text
edit
replace
resubmit
cancel
```

---

## 42. Evidence Model

Each important academic state gets provenance:

```yaml
evidence:
  source: portal_page
  portal:
  page:
  period:
  record_type:
  retrieved_at:
  freshness:
  value:
```

Distinguish:

```text
CURRENT_PORTAL
HISTORICAL_PORTAL
MEMORY
INFERENCE
```

---

## 43. Minimal Evidence

Do not retain more personal academic data than needed.

For example, to verify quota:

```text
course_code
class
quota
enrolled
remaining
retrieved_at
```

may be sufficient.

Do not unnecessarily retain:

```text
full student profile
full transcript
other unrelated personal records
```

---

## 44. Sensitive Data

Never log:

```text
password
OTP
MFA secret
session cookie
access token
refresh token
CSRF token
SSO credential
browser storage secret
```

Redact before:

```text
audit
error output
debug output
memory
reports
```

---

## 45. Academic Privacy

Treat as sensitive:

```text
student identifier
grades
academic standing
personal schedule
registration history
disciplinary data
advising information
```

Only expose the minimum required for the current task.

---

## 46. Portal Errors

Normalize errors:

```text
SESSION_EXPIRED
UNAUTHORIZED
FORBIDDEN
PAGE_NOT_FOUND
ACADEMIC_PERIOD_UNAVAILABLE
QUOTA_CHANGED
PREREQUISITE_CHANGED
ELIGIBILITY_CHANGED
REGISTRATION_WINDOW_CLOSED
KRS_STATE_CHANGED
SUBMISSION_UNKNOWN
PORTAL_ERROR
NETWORK_ERROR
```

Do not turn generic portal failure into:

```text
success
```

---

## 47. Navigation Failure

If deterministic navigation fails:

```text
NAVIGATION_UNCERTAIN
```

Do not guess:

```text
selector
form field
URL
button
endpoint
```

---

## 48. Unsupported Portal Behavior

When the portal's write behavior is undocumented or unclear:

```text
READ_ONLY_FALLBACK
```

Do not invent:

```text
POST route
field order
hidden endpoint
JavaScript function
request body
```

---

## 49. Evidence Conflict

If:

```text
current portal
```

says one thing and:

```text
memory / historical state
```

says another:

```text
current portal wins
```

If:

```text
two current portal pages
```

contradict:

```text
CONFLICTED_STATE
```

Do not execute consequential action until reconciled.

---
