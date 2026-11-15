# dependency-audit — §71–72

## 71. Final Audit Result

```yaml id="c6w9p2"
dependency_audit_result:
  state:

  scope:
  baseline:

  inventory:
    direct:
    transitive:
    runtime:
    development:
    build:

  diff:
    added:
    removed:
    upgraded:
    downgraded:

  security:
    findings: []
    unknowns: []

  license:
    inventory: []
    policy_violations: []
    unknowns: []

  supply_chain:
    provenance:
    integrity:
    maintainer_signals:

  reachability:
    matrix: []

  remediation:
    required: []
    optional: []
    blocked: []

  regression:
    required: []

  evidence_refs: []

  next_action:
```

---

## 72. Completion States

Use:

```text id="p7m3x5"
CLEAN
```

only when required checks completed and no unresolved applicable finding remains.

Use:

```text id="y8q2n6"
FINDINGS_PRESENT
```

when validated findings exist.

Use:

```text id="h4w7c1"
PARTIAL
```

when some required audit categories were completed but others were not.

Use:

```text id="r9m5x2"
UNKNOWN
```

when material dependency state could not be established.

Use:

```text id="j3q8v6"
BLOCKED
```

when scope, tooling, credentials, or policy prevents required analysis.

Never use `CLEAN` when an important check was skipped silently.

---
