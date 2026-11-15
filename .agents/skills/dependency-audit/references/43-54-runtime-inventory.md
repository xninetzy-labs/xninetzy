# dependency-audit — §43–54

Contents: 43. Runtime Inventory; 44. Generated / Vendored Dependencies; 45. Dependency Security Boundary; 46. License / Security Correlation; 47. Findings Summary; 48. Dependency Surface Report; 49. Exception Management; 50. No Permanent Silent Suppression; 51. Regression After Remediation; 52. Remediation Verification; 53. Lockfile Integrity After Remediation; 54. Advisory Recheck

## 43. Runtime Inventory

When the target requires stronger assurance, correlate declared dependencies with
runtime artifacts:

```text id="m6p2r9"
lockfile
→ build
→ artifact
→ container
→ deployed runtime
```

Possible discrepancy:

```text id="a7w3k1"
declared dependency absent from runtime
```

or:

```text id="q2x8m5"
undeclared runtime package present
```

Treat unmanaged runtime dependencies as a separate supply-chain/configuration
finding.

---

## 44. Generated / Vendored Dependencies

Inspect when applicable:

```text id="s4n9q6"
vendor directories
generated clients
embedded archives
bundled JS
copied source trees
container-installed packages
```

Do not assume that everything executable appears in the primary package manager
lockfile.

---

## 45. Dependency Security Boundary

A dependency audit should distinguish:

```text id="p9k2m7"
direct application exposure
build-time exposure
test-only exposure
developer tooling exposure
runtime exposure
container exposure
```

A test-only vulnerability may require different handling from a runtime-exposed
vulnerability.

Do not collapse all package types into one risk category.

---

## 46. License / Security Correlation

Security and license issues must remain separate.

One package may have:

```text id="h1m5q8"
security finding
+
license finding
```

These should not be merged into one finding merely because the package is the same.

---

## 47. Findings Summary

Required summary:

```yaml id="x6r3n8"
summary:
  total_dependencies:
  direct:
  transitive:

  added:
  removed:
  upgraded:
  downgraded:

  advisories:
  vulnerable_packages:
  reachable_vulnerabilities:
  unknown_reachability:

  licenses:
  license_policy_violations:
  unknown_licenses:

  provenance_anomalies:
  integrity_mismatches:

  unresolved_findings:
```

---

## 48. Dependency Surface Report

Human-readable summary:

```text id="m7q2x9"
Dependency Surface
------------------
Direct:
Transitive:
Runtime:
Development:
Build:

Changes
-------
Added:
Removed:
Upgraded:
Downgraded:

Security
--------
Advisories:
Affected packages:
Reachable vulnerable paths:
Unknown reachability:

License
-------
SPDX distribution:
Policy violations:
Unknown licenses:

Supply Chain
------------
Integrity anomalies:
Provenance anomalies:
Other evidence-backed signals:

Remediation
-----------
Required:
Optional:
Blocked:
```

---

## 49. Exception Management

A temporary exception should contain:

```yaml id="n8p4r1"
exception:
  finding_id:
  reason:
  owner:
  compensating_control:
  created_at:
  expires_at:
  review_date:
```

Exceptions should be:

```text id="g3m7q5"
explicit
time-bounded
auditable
reviewable
```

Do not convert unresolved findings into "accepted" without an explicit owner and
policy-supported exception.

---

## 50. No Permanent Silent Suppression

Avoid configurations such as:

```text id="j7x2m4"
ignore vulnerability forever
```

without:

```text id="w9q5k1"
reason
scope
owner
expiration
review condition
```

A suppression is a governance decision, not evidence that the vulnerability
disappeared.

---

## 51. Regression After Remediation

When remediation is applied, verify:

```text id="c8m2q7"
resolved dependency version
lockfile consistency
build
unit tests
integration tests
affected runtime paths
security scanner
dependency graph
```

For security remediation:

```text id="h4p7n1"
old vulnerable resolution
→ remediation
→ new resolution
→ advisory no longer matches
→ targeted behavior preserved
```

---

## 52. Remediation Verification

A remediation is `VERIFIED` only when:

```text id="x2k8m5"
vulnerable version no longer resolves
+
expected fix version resolves
+
affected functionality still works
+
new critical regressions are absent
```

"Dependency upgraded successfully" is not sufficient.

---

## 53. Lockfile Integrity After Remediation

After changes:

```text id="s7q3w9"
manifest
↔
lockfile
↔
resolved graph
```

must remain consistent.

Unexpected lockfile changes should trigger another dependency diff.

---

## 54. Advisory Recheck

After remediation, re-query the relevant authoritative advisory source when
necessary.

Result:

```text id="p4m9x6"
RESOLVED
STILL_AFFECTED
NEW_ADVISORY
UNKNOWN
```

Do not mark a finding resolved solely because the version number changed.

---
