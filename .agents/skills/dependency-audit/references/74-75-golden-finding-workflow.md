# dependency-audit — §74–75

## 74. Golden Finding Workflow

```text id="u2n7p5"
PACKAGE
  ↓
EXACT VERSION
  ↓
ADVISORY
  ↓
AFFECTED RANGE
  ↓
PARENT CHAIN
  ↓
VULNERABLE SYMBOL
  ↓
CALL SITE
  ↓
ENTRY POINT
  ↓
ATTACKER CONTROL
  ↓
CONTEXT
  ↓
VALIDATED FINDING
```

Stop at the highest evidence-supported level.

Do not invent deeper reachability.

---

## 75. Golden Remediation Workflow

```text id="x4m8q1"
FINDING
  ↓
FIXED VERSION / PATCH
  ↓
COMPATIBILITY CHECK
  ↓
PLAN REMEDIATION
  ↓
APPLY THROUGH APPROVED WORKFLOW
  ↓
LOCKFILE REGENERATE
  ↓
DEPENDENCY RECHECK
  ↓
TARGETED TESTS
  ↓
REGRESSION TESTS
  ↓
SECURITY RECHECK
  ↓
VERIFY RESOLUTION
```

A remediation is not complete until the post-change dependency graph is audited
again.

---
