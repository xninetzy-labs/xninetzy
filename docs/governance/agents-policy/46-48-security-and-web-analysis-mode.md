# AGENTS.md — §46–48

Part of the AGENTS.md policy; binds equally.

## 46. Security and Web Analysis Mode

When the user requests:

```text
analyze this website
```

the agent should determine whether the task is:

```text
PASSIVE ANALYSIS
AUTHORIZED ACTIVE TESTING
```

Passive analysis may proceed automatically.

Active security testing requires an identifiable authorized scope.

Once authorization is established, the security workflow may run autonomously within that scope.

---

## 47. Scope Enforcement

The security engine must maintain:

```text
IN_SCOPE
OUT_OF_SCOPE
UNKNOWN
```

Never treat UNKNOWN as IN_SCOPE.

If a discovered asset appears related but is not explicitly within scope:

```text
record
do not actively test
```

unless authorization covers the broader domain/system.

---

## 48. Security Evidence

Every finding should contain:

```text
finding_id
target
endpoint
parameter
vulnerability
severity
confidence
evidence
reproduction
impact
scope
timestamp
tool
recommendation
```

The report must distinguish:

```text
OBSERVED
INFERRED
POTENTIAL
CONFIRMED
```

---
