---
name: xninetzy-academic-safety
description: Applies authorization, confirmation, idempotency, current-state revalidation and receipt rules to academic workflows. Use before any academic write or submission.
metadata:
  keywords: apply
---

# Academic Safety

## Required server-side controls

Consequential actions require:

* trusted owner identity;
* capability check;
* current-state read;
* exact action preview;
* scoped confirmation token;
* expiry;
* idempotency key;
* one-time execution;
* post-action read;
* audit record;
* receipt.

## Confirmation token scope

Bind token to:

```yaml
owner:
action:
target:
payload_hash:
current_state_hash:
expires_at:
single_use:
```

## Prohibited

* OTP bypass;
* grade modification;
* attendance fabrication;
* impersonation;
* silent retry of non-idempotent action.