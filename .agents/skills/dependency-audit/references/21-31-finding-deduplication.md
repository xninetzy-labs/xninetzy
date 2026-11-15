# dependency-audit — §21–31

Contents: 21. Finding Deduplication; 22. Vulnerability Severity vs Context; 23. License Inventory; 24. License Policy; 25. License Evidence; 26. License Obligations; 27. Provenance Analysis; 28. Integrity; 29. Maintainer / Supply-Chain Signals; 30. Abandoned / Low-Maintenance Packages; 31. Outdated Dependency Analysis

## 21. Finding Deduplication

Deduplicate using stable dimensions:

```text id="r6w1n4"
ecosystem
package
affected_version
underlying_advisory
```

Then preserve all relevant advisory aliases.

Do not merge genuinely different vulnerabilities merely because they affect the
same package.

---

## 22. Vulnerability Severity vs Context

Keep separate:

```text id="m3q7x1"
ADVISORY SEVERITY
APPLICATION RELEVANCE
REACHABILITY
EXPLOITABILITY CONTEXT
REMEDIATION RISK
```

An upstream advisory's severity must not automatically become the application's
final contextual risk classification.

Likewise, lack of observed reachability does not invalidate the upstream
vulnerability.

---

## 23. License Inventory

For each resolved package, collect when available:

```yaml id="b8n2m5"
license:
  package:
  version:
  declared_license:
  normalized_spdx:
  source:
  confidence:
```

Group inventory by:

```text id="q5h9x3"
SPDX identifier
```

and separately track:

```text id="z2m6r8"
UNKNOWN
CUSTOM
MULTIPLE
LICENSE_FILE_ONLY
NO_DECLARED_LICENSE
```

Do not infer a license from package popularity or ecosystem convention.

---

## 24. License Policy

License risk is policy-dependent.

Separate:

```text id="e7w3n2"
FACT
```

from:

```text id="p9q4m6"
POLICY
```

Example:

```text id="a8x2k5"
Fact:
package declares license X.

Policy:
repository permits licenses X and Y.

Result:
policy-compliant.
```

Do not label a license "unsafe" without a defined policy basis.

---

## 25. License Evidence

Use, when available:

```text id="c2v7m9"
package metadata
LICENSE file
NOTICE file
registry metadata
repository metadata
declared SPDX expression
```

If licensing cannot be established:

```text id="f6p1k8"
LICENSE_UNKNOWN
```

Do not guess.

---

## 26. License Obligations

Where the policy system supports it, identify obligations such as:

```text id="n4w8q2"
notice requirements
attribution
source-distribution requirements
copyleft implications
license compatibility
redistribution conditions
```

This is an obligations analysis, not legal advice.

Escalate ambiguous legal interpretation to the appropriate owner.

---

## 27. Provenance Analysis

Inspect package provenance where metadata is available:

```text id="u7r3m1"
registry
repository
source archive
maintainer identity
publisher identity
package namespace
release metadata
signature/attestation
integrity metadata
```

Possible states:

```text id="x9p2k6"
VERIFIED
EXPECTED
MISMATCH
UNKNOWN
UNAVAILABLE
```

---

## 28. Integrity

When package integrity metadata is available, compare:

```text id="h5m1q7"
expected artifact integrity
vs
resolved artifact integrity
```

Examples of useful evidence:

```text id="j8r4n3"
lockfile checksum
package manager integrity field
registry checksum
signed provenance
build attestation
```

An integrity mismatch should be treated as a distinct supply-chain finding.

---

## 29. Maintainer / Supply-Chain Signals

Evaluate observable signals only.

Useful evidence may include:

```text id="s6p3w8"
package ownership changes
unexpected maintainer changes
repository transfer
release provenance anomalies
sudden publishing pattern changes
unusual dependency expansion
package-to-repository mismatch
registry/source mismatch
known compromise advisory
```

Do not use subjective labels such as:

```text id="x2m7k4"
"shady maintainer"
"untrustworthy developer"
```

without concrete evidence.

Observed maintainer signals are risk indicators, not proof of maliciousness.

---

## 30. Abandoned / Low-Maintenance Packages

Age alone is not proof of insecurity.

Consider:

```text id="d7q3m9"
security advisories
release activity
issue responsiveness
repository activity
dependency health
maintainer continuity
ecosystem maturity
```

A package may be old but stable and unaffected.

"Outdated" and "vulnerable" are different findings.

---

## 31. Outdated Dependency Analysis

Only report outdated status when comparing against a defined source.

Capture:

```yaml id="v2k8p5"
outdated:
  package:
  current_version:
  latest_version:
  source:
  retrieved_at:
```

Do not automatically recommend upgrading merely because a newer version exists.

The appropriate action may be:

```text id="m4q7n1"
upgrade
stay pinned
replace
accept exception
```

depending on compatibility, security, and repository policy.

---
