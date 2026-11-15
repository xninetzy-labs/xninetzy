# dependency-audit — §66–69

Contents: 66. Failure Memory; 67. Self-Improvement Boundary; 68. Anti-Patterns; 69. Mandatory Distinctions

## 66. Failure Memory

A reusable finding fingerprint may include:

```text id="p4x7n2"
ecosystem
package
advisory
resolved version family
finding type
```

Avoid volatile identifiers.

Memory should improve:

```text id="c8m5w1"
triage
deduplication
reachability search
remediation discovery
```

It must not suppress a current finding without current evidence.

---

## 67. Self-Improvement Boundary

The audit system may learn:

```text id="q2r6m8"
better package identity normalization
better advisory matching
better reachability queries
better license normalization
better transitive-path resolution
better false-positive patterns
better remediation validation
```

It must not automatically learn:

```text id="n7x3p5"
ignore a vulnerability permanently
disable security scanners
expand network authorization
publish disclosure
bypass approval
suppress findings without evidence
```

Learning improves analysis quality, not authority.

---

## 68. Anti-Patterns

Never report:

```text id="f3m8q1"
"This dependency looks shady."

"This version is old, so it is vulnerable."

"It has a CVE, therefore exploitation is confirmed."

"It is transitive, so we don't care."

"The scanner found it, so it is definitely reachable."

"The package has no recent releases, therefore it is malicious."

"Upgrade to latest" without compatibility analysis.

"Downgrade to version X" without checking policy and security.

"The application is safe because the lockfile scanner is clean."
```

Each conclusion requires evidence appropriate to the claim.

---

## 69. Mandatory Distinctions

Always preserve:

```text id="k5p2r8"
OUTDATED
≠
VULNERABLE

VULNERABLE
≠
REACHABLE

REACHABLE
≠
EXPLOITABLE

PACKAGE INSTALLED
≠
RUNTIME USED

LICENSE UNKNOWN
≠
LICENSE INCOMPATIBLE

MAINTENANCE SIGNAL
≠
MALICIOUSNESS

UPGRADE AVAILABLE
≠
UPGRADE REQUIRED
```

These distinctions prevent overclaiming.

---
