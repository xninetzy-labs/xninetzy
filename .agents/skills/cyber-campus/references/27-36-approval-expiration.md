# cyber-campus — §27–36

Contents: 27. Approval Expiration; 28. Pre-Execution Revalidation; 29. Optimistic Concurrency; 30. Stage; 31. Stage Reconciliation; 32. Final Approval; 33. Submit; 34. Idempotency; 35. Verification; 36. Submission Confirmation

## 27. Approval Expiration

Approval is not permanent.

Invalidate approval if:

```text
current KRS changes
offering changes
quota changes materially
prerequisite state changes
eligibility changes
registration window changes
session changes
portal context changes
action hash changes
```

Then:

```text
return to DRY_RUN
```

---

## 28. Pre-Execution Revalidation

Immediately before staging:

```text
1. session
2. identity
3. portal
4. academic period
5. current KRS
6. offerings
7. quota
8. prerequisites
9. eligibility
10. registration window
11. action hash
```

All relevant preconditions must still hold.

---

## 29. Optimistic Concurrency

Treat current KRS as mutable state.

Before write:

```text
approved_state_hash
```

must match:

```text
current_state_hash
```

If:

```text
approved_state_hash != current_state_hash
```

then:

```text
CONCURRENT_STATE_CHANGE
```

Stop.

Do not overwrite the newer portal state.

---

## 30. Stage

If the portal supports staging:

```text
APPROVED PLAN
   ↓
STAGE NARROW CHANGE
   ↓
READ BACK
   ↓
COMPARE
```

Staging must contain only the approved delta.

---

## 31. Stage Reconciliation

After staging read:

```text
expected
vs
observed
```

Compare:

```text
courses
classes
credits
status
```

Outcomes:

```text
MATCH
PARTIAL_MATCH
MISMATCH
UNKNOWN
```

If mismatch:

```text
STOP
```

No final submission.

---

## 32. Final Approval

Final submission requires another explicit approval.

Reason:

```text
staged state
```

may differ from:

```text
original plan
```

Approval must reference:

```text
staged_state_hash
action_hash
current period
current KRS
```

---

## 33. Submit

Submit exactly once for the approved state unless the portal reports a clearly
retryable transport failure and the operation is proven idempotent.

Prefer:

```text
submit
↓
receive receipt/status
↓
verify
```

Do not blindly retry unknown submission outcomes.

---

## 34. Idempotency

For any KRS mutation determine whether the portal provides:

```text
request ID
submission ID
transaction ID
idempotency key
```

If present, preserve it.

If submission outcome is unknown:

```text
DO NOT SUBMIT AGAIN
```

until current portal state is verified.

This prevents duplicate or conflicting submissions.

---

## 35. Verification

After submission:

```text
1. return to KRS/status page
2. verify current state
3. verify period
4. verify courses
5. verify status
6. verify timestamp/receipt where available
```

Possible outcomes:

```text
NOT_CHANGED
PARTIALLY_APPLIED
FULLY_APPLIED
SUBMITTED
VERIFIED
UNKNOWN
```

---

## 36. Submission Confirmation

Strong confirmation evidence may include:

```text
portal status
submission timestamp
transaction/reference number
confirmation message
current KRS read-back
downloadable receipt
```

Prefer multiple independent portal signals.

---
