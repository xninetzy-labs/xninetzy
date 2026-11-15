# dependency-audit — §11–20

Contents: 11. Phase 03 — TRANSITIVE GRAPH; 12. Parent Chain; 13. Multiple Parent Paths; 14. Dependency Reachability Layers; 15. Reachability Analysis; 16. Call-Site Requirement; 17. Exploitability Context; 18. Advisory Matching; 19. Advisory Freshness; 20. CVE and Advisory Identity

## 11. Phase 03 — TRANSITIVE GRAPH

Build a directed dependency graph:

```text id="c5p2n8"
Application
  ↓
Direct Dependency
  ↓
Transitive Dependency
  ↓
Transitive Dependency
```

Each edge represents:

```text id="z7m1q4"
parent
→
child
```

Record:

```yaml id="h3v8n2"
edge:
  parent:
  child:
  dependency_range:
  resolved_version:
  dependency_type:
  source:
```

---

## 12. Parent Chain

For every transitive finding, expose the chain.

Example:

```text id="y4k8s1"
application
→ framework-a
→ library-b
→ vulnerable-library-c
```

This lets the operator identify which direct dependency introduced the vulnerable
package.

A transitive vulnerability must not be reported without its parent chain when
the chain can be resolved.

---

## 13. Multiple Parent Paths

A transitive package may have multiple parents.

Represent:

```text id="n8j3m5"
library-c
├── parent-a
└── parent-b
```

Do not assume removing one parent removes the vulnerable package.

The lockfile graph must be checked after any proposed remediation.

---

## 14. Dependency Reachability Layers

Separate at least:

```text id="u5p7c2"
PACKAGE_REACHABLE
SYMBOL_REACHABLE
CODE_PATH_REACHABLE
ATTACK_PATH_REACHABLE
```

Definitions:

```text id="s9m2k4"
PACKAGE_REACHABLE
The package is installed/resolved.

SYMBOL_REACHABLE
Application code reaches an affected symbol/API.

CODE_PATH_REACHABLE
The vulnerable behavior can occur through an actual application execution path.

ATTACK_PATH_REACHABLE
A realistic attacker-controlled input can reach the vulnerable behavior.
```

A package being installed does not establish attack-path reachability.

---

## 15. Reachability Analysis

Where source code is available, inspect:

```text id="p4x7m9"
import graph
symbol references
call sites
entry points
data flow
feature flags
configuration
runtime integration
```

Required evidence for a reachability claim:

```yaml id="r2n5k8"
reachability:
  package:
  vulnerable_symbol:
  caller_path:
  source_location:
  entry_point:
  attacker_controlled_input:
  evidence_refs: []
```

If a vulnerable symbol cannot be located:

```text id="m7q1c3"
REACHABILITY_UNKNOWN
```

not:

```text id="v9n4x6"
NOT_REACHABLE
```

---

## 16. Call-Site Requirement

For actionable vulnerability findings, identify application call sites when
source code and symbol mapping make this possible.

Example:

```text id="j5x8q2"
vulnerable symbol:
parseLegacyInput

caller:
src/api/import.ts:84

entry point:
POST /import
```

Call-site evidence increases confidence.

It does not automatically establish exploitability.

---

## 17. Exploitability Context

Evaluate separately:

```text id="g4m8n1"
input controllability
authentication requirements
authorization requirements
exposure
protocol
feature activation
configuration
runtime path
preconditions
mitigations
```

Possible classification:

```text id="c7q2x9"
HIGHLY_RELEVANT
RELEVANT
CONDITIONAL
LOW_RELEVANCE
NOT_REACHABLE
UNKNOWN
```

This is contextual classification, not a vulnerability severity score.

---

## 18. Advisory Matching

Match resolved packages against authoritative advisory identifiers.

For each match record:

```yaml id="y3w6k8"
advisory:
  identifier:
  package:
  affected_versions:
  fixed_versions:
  source:
  published_at:
  modified_at:
  matched_version:
  evidence_ref:
```

Every vulnerability finding should identify:

```text id="k2n7p4"
package
resolved version
advisory ID
advisory source
```

Never use:

```text id="x6q1m9"
"this version looks unsafe"
```

without an evidence-backed advisory or equivalent authoritative security notice.

---

## 19. Advisory Freshness

Security advisories can change.

Record:

```yaml id="u4m8q2"
advisory_metadata:
  retrieved_at:
  published_at:
  modified_at:
  source:
```

When a current advisory status materially affects the conclusion, re-query it
rather than relying on stale cached information.

---

## 20. CVE and Advisory Identity

Prefer the advisory's canonical identifiers.

A single issue may have:

```text id="h8p3r6"
CVE
GHSA
vendor advisory
OSV identifier
ecosystem-specific advisory
```

Do not emit duplicate findings merely because the same vulnerability has multiple
identifiers.

Store aliases under one normalized issue when the advisory sources establish that
they represent the same underlying vulnerability.

---
