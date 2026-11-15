# dependency-audit — §32–42

Contents: 32. Downgrade Policy; 33. Remediation Options; 34. Fixed-Version Analysis; 35. Remediation Risk; 36. Dependency Diff Risk; 37. SecurityFinding Contract; 38. Finding Confidence; 39. Reachability Matrix; 40. Vulnerability Finding Validation; 41. False Positive Handling; 42. False Negative Awareness

## 32. Downgrade Policy

Never recommend a downgrade solely because another advisory is worse.

Before suggesting a downgrade, check:

```text id="p8x2m6"
policy on version pinning
security state of target version
compatibility
dependency constraints
lockfile resolution
regression risk
```

A downgrade can itself introduce vulnerabilities or break dependency guarantees.

---

## 33. Remediation Options

Possible remediation classes:

```text id="k3n7q9"
PATCH
UPGRADE
DOWNGRADE
PIN
REPLACE
REMOVE
CONFIGURE
ISOLATE
MITIGATE
ACCEPT_WITH_EXCEPTION
```

Choose only after evidence establishes the problem and the feasible remedy.

Do not auto-apply remediation in an audit-only workflow.

---

## 34. Fixed-Version Analysis

When an advisory provides a fixed version, record:

```yaml id="r6m2w8"
remediation:
  current_version:
  minimum_fixed_version:
  recommended_version:
  compatibility:
  regression_risk:
```

The first fixed version is not automatically the best upgrade target.

Consider the repository's supported version range.

---

## 35. Remediation Risk

Evaluate:

```text id="n1x5q7"
API compatibility
transitive changes
runtime behavior
breaking changes
build impact
test impact
performance
license changes
new advisories
```

A security remediation that introduces a second unresolved critical failure must
not be presented as completed remediation.

---

## 36. Dependency Diff Risk

For changed dependencies, inspect:

```text id="c9p4m6"
API changes
release notes
lockfile graph changes
new transitive dependencies
removed transitive dependencies
license changes
advisory changes
```

Do not assume:

```text id="y2q8n5"
upgrade = safer
```

or:

```text id="m7k1r3"
downgrade = safer
```

without evidence.

---

## 37. SecurityFinding Contract

Each distinct vulnerability/advisory should emit a structured finding:

```yaml id="b4w8n2"
SecurityFinding:
  finding_id:

  package:
  ecosystem:
  resolved_version:
  dependency_type:

  advisory:
    id:
    aliases: []
    source:
    affected_range:
    fixed_versions: []

  dependency_path: []

  reachability:
    level:
    vulnerable_symbol:
    caller_paths: []
    entry_points: []

  exploitability_context:
    classification:
    attacker_control:
    authentication_required:
    relevant_configuration:
    mitigations: []

  license:
    declared:
    normalized_spdx:
    policy_status:

  provenance:
    source:
    integrity_status:
    maintainer_signals: []

  evidence_refs: []

  confidence:
  remediation:
  regression_risk:
```

---

## 38. Finding Confidence

Confidence should be distinct from severity.

Suggested:

```text id="q2r7m8"
HIGH
direct authoritative advisory + exact resolved version + verified package identity

MEDIUM
advisory match established but some contextual detail is incomplete

LOW
partial metadata match or unresolved package identity
```

Do not increase confidence merely because a scanner produced the finding.

---

## 39. Reachability Matrix

Required where source inspection is possible:

| Package   | Vulnerable Symbol  | Caller         | Location           | Entry Point    | Reachability        |
| --------- | ------------------ | -------------- | ------------------ | -------------- | ------------------- |
| package-c | `parseLegacyInput` | `importData()` | `src/import.ts:84` | `POST /import` | CODE_PATH_REACHABLE |

If no symbol-level mapping exists:

```text id="d6m2q9"
PACKAGE_REACHABLE
```

may be the highest defensible classification.

Do not claim `NOT_REACHABLE` solely because search did not find a call site.

---

## 40. Vulnerability Finding Validation

Before emitting a finding:

```text id="w7p3k1"
1. package identity verified
2. resolved version verified
3. advisory identity verified
4. affected version range verified
5. parent chain verified when transitive
6. reachability analyzed when feasible
7. evidence recorded
```

Then:

```text id="x4m8q6"
security_validate_finding
```

should confirm or reject the finding.

---

## 41. False Positive Handling

Possible reasons:

```text id="r3n7w5"
version outside affected range
advisory package mismatch
platform-specific issue not applicable
feature not enabled
symbol absent
mitigation documented
package shadowed by another resolution
duplicate advisory
```

Do not suppress a finding merely because it is inconvenient.

Record the reason for disposition.

---

## 42. False Negative Awareness

Dependency scanners can miss:

```text id="j5q1m8"
private packages
vendored libraries
generated dependencies
unusual package-manager paths
runtime-loaded artifacts
build-time fetches
unlocked dependencies
manual downloads
```

Where relevant, compare:

```text id="q8m4s2"
manifest
lockfile
build artifact
container image
runtime inventory
```

A clean lockfile scan is not automatically proof that the runtime contains no
unmanaged dependency.

---
