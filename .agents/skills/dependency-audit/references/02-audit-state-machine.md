# dependency-audit — §2

## 2. Audit State Machine

Canonical lifecycle:

```text id="v6c1q8"
SCOPE
  ↓
INVENTORY
  ↓
NORMALIZE
  ↓
BASELINE
  ↓
GRAPH
  ↓
ADVISORY_MATCH
  ↓
LICENSE_ANALYSIS
  ↓
PROVENANCE_ANALYSIS
  ↓
REACHABILITY
  ↓
RISK_CORRELATION
  ↓
VALIDATE
  ↓
FINDINGS
  ↓
REMEDIATION
  ↓
REGRESSION
  ↓
AUDIT_COMPLETE
```

Possible terminal/exception states:

```text id="x7p2m5"
BLOCKED
INSUFFICIENT_EVIDENCE
PARTIAL
UNKNOWN
STALE
INVALIDATED
```

Do not report the audit as complete when a critical phase could not be performed
and the missing phase affects the conclusion.

---
