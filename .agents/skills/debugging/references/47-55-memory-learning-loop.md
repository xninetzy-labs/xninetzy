# debugging — §47–55

Contents: 47. Memory / Learning Loop; 48. Failure Fingerprint; 49. Reuse of Historical Failures; 50. Self-Improvement Boundary; 51. Incident Mode; 52. Rollback Rule; 53. Multiple Simultaneous Failures; 54. Anti-Patterns; 55. Common Symptom-Fixing Traps

## 47. Memory / Learning Loop

After closure, store a compact failure record:

```yaml
failure_memory:
  fingerprint:
  symptom:
  environment:
  trigger:
  primary_root_cause:
  contributing_factors: []
  evidence_refs: []
  fix_summary:
  regression:
  affected_components: []
  recurrence_risk:
  resolved_at:
```

Use `memory_failure_store` only for durable learning that improves future
diagnosis.

---

## 48. Failure Fingerprint

Generate a deterministic fingerprint from stable diagnostic dimensions:

```text
component
error family
failure boundary
normalized symptom
relevant operation
```

Do not include:

```text
timestamps
random IDs
secrets
volatile memory addresses
```

unless necessary to distinguish a failure family.

---

## 49. Reuse of Historical Failures

Historical failure memory may:

```text
suggest hypotheses
identify known regressions
suggest useful reproductions
surface previous fixes
```

It must not override current evidence.

Rule:

```text
CURRENT EVIDENCE
    >
HISTORICAL MEMORY
```

A similar previous failure is not proof that the current failure has the same root
cause.

---

## 50. Self-Improvement Boundary

Debugging may learn:

```text
better reproduction commands
better evidence sources
better hypothesis ordering
better observability queries
better regression patterns
better failure fingerprints
```

It must not automatically learn:

```text
new authorization scope
new write permissions
security-control bypasses
automatic approval
broader production mutation rights
```

Learning improves diagnosis, not authority.

---

## 51. Incident Mode

For production-impacting failures, containment and diagnosis may run in parallel.

Allowed:

```text
CONTAIN
+
PRESERVE EVIDENCE
+
INVESTIGATE
```

Containment must be:

```text
bounded
reversible
audited
least-privilege
```

Examples:

```text
disable affected feature flag
stop unhealthy worker
route traffic away from failed instance
pause a failing queue consumer
```

Do not apply broad corrective changes merely to make an incident disappear.

The incident must still receive a root-cause analysis.

---

## 52. Rollback Rule

Rollback is appropriate when:

```text
current change is strongly correlated with failure
rollback is authorized
rollback is safer than speculative repair
rollback is reversible/auditable
```

Rollback reduces impact.

It does not establish root cause.

After rollback:

```text
preserve evidence
compare behavior
continue causal investigation
```

---

## 53. Multiple Simultaneous Failures

When symptoms appear related but evidence indicates independent causes:

```text
INCIDENT
├── FAILURE A
│   └── ROOT CAUSE A
└── FAILURE B
    └── ROOT CAUSE B
```

Do not force them into one explanation.

---

## 54. Anti-Patterns

Never accept:

```text
"I added a print statement and it works now."

"It's a race condition."

"Restarting fixed it, so the bug is gone."

"I wrapped it in try/except."

"The database is probably slow."

"The API returned 200, so it succeeded."

"The test passes manually."

"Changing three files fixed it."

"The previous incident had the same error, so this is identical."
```

without causal evidence.

---

## 55. Common Symptom-Fixing Traps

### Exception suppression

```text
try:
    failing_operation()
except:
    return default
```

This can hide the failure while preserving invalid state.

### Retry inflation

Increasing retries can mask:

```text
deadlocks
race conditions
broken dependencies
bad timeouts
non-idempotent behavior
```

### Timeout inflation

Increasing timeout does not explain why latency exceeded the expected budget.

### Cache deletion

Clearing caches can temporarily remove stale state without identifying why stale
state was produced.

### Restart-driven recovery

Restarting can reset process state while leaving the causal defect untouched.

---
