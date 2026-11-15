---
name: dependency-audit
description: Audits direct and transitive dependencies for vulnerabilities, licenses, provenance, integrity, maintainership and reachability within authorized scope. Use when dependencies or lockfiles change or an advisory appears.
metadata:
  keywords: added advisories affect are audit chain context dependency downgraded driven evidence explicitly exploitability graphs known license manifests operator package packages policy remediation removed requests review reviews risk signals software supply surface upgraded used
---

# dependency-audit

Evidence-driven dependency and software supply-chain audit.

The purpose is not merely to answer:

```text id="8u0f7e"
"Does this package have a CVE?"
```

It must establish:

```text id="u0qv1s"
what dependencies exist
what versions are actually resolved
why each package exists
where each package came from
which advisories apply
whether affected functionality is reachable
what the actual execution context is
what license obligations apply
what supply-chain risks are observable
what remediation is available
what regression risk remediation introduces
```

The central principle is:

> **A dependency advisory identifies exposure. Reachability and execution context determine relevance. Evidence determines confidence.**
---

# 1. Authority Model

For dependency resolution, prefer:

```text id="f8j3k1"
lockfile / resolved dependency graph
    >
manifest declaration
    >
package-manager metadata
    >
build artifact metadata
    >
historical dependency state
    >
memory
    >
assumption
```

The lockfile is authoritative for the exact resolved dependency versions when the
ecosystem uses a lockfile.

The manifest remains authoritative for direct dependency intent.

Do not infer resolved versions from package names alone.

---

# 3. Pipeline

```text id="k5m8r2"
SCOPE
   ↓
MANIFEST
   ↓
LOCKFILE
   ↓
RESOLVED_GRAPH
   ↓
BASELINE_DIFF
   ↓
ADVISORY_CORRELATION
   ↓
LICENSE_CORRELATION
   ↓
PROVENANCE / INTEGRITY
   ↓
REACHABILITY
   ↓
EXPLOITABILITY_CONTEXT
   ↓
FINDING_VALIDATION
   ↓
REMEDIATION_ANALYSIS
   ↓
REGRESSION
   ↓
REPORT
```

The pipeline separates:

```text id="b2w7n1"
PACKAGE IS VULNERABLE
```

from:

```text id="j8q4m6"
OUR APPLICATION REACHES THE VULNERABLE FUNCTIONALITY
```

and from:

```text id="p1s9c5"
THE VULNERABILITY IS ACTUALLY EXPLOITABLE IN OUR DEPLOYMENT CONTEXT
```

These are distinct claims.

---

# 4. Scope Gate

Before external security or advisory queries:

```text id="r5x8k2"
security_scope
```

must establish:

```yaml id="n3m7q1"
scope:
  repository:
  environment:
  package_ecosystems:
  allowed_external_queries:
  allowed_network_targets:
  exclusions:
```

No external advisory/package query should occur outside authorized scope.

---

# 5. Read-Only Default

Dependency audit is read-only by default.

It may inspect:

```text id="a2h6m9"
manifests
lockfiles
package metadata
dependency graphs
source call sites
license metadata
advisory feeds
provenance metadata
build artifacts
configuration
```

It must not automatically:

```text id="g8k1q4"
upgrade dependencies
downgrade dependencies
rewrite lockfiles
remove packages
publish advisories
change production configuration
```

Remediation is a separate controlled action.

---

# 70. Audit Completion Contract

A dependency audit is:

```text id="x8m3q6"
AUDIT_COMPLETE
```

only when the required scope was inspected and each required category has one of:

```text id="v2n7p4"
VERIFIED
NOT_APPLICABLE
UNKNOWN_WITH_REASON
BLOCKED_WITH_REASON
```

Required categories:

```text id="m4q8x1"
inventory
resolution
graph
advisory
license
provenance
reachability
remediation
```

A scanner failure must not silently become a clean result.

---

# 73. Golden Audit Workflow

```text id="m5r8q2"
AUTHORIZE SCOPE
      ↓
READ MANIFEST
      ↓
READ LOCKFILE
      ↓
NORMALIZE PACKAGES
      ↓
BUILD RESOLVED GRAPH
      ↓
COMPARE BASELINE
      ↓
MATCH ADVISORIES
      ↓
ANALYZE LICENSES
      ↓
CHECK PROVENANCE / INTEGRITY
      ↓
TRACE REACHABILITY
      ↓
EVALUATE EXPLOITABILITY CONTEXT
      ↓
VALIDATE FINDINGS
      ↓
CLASSIFY REMEDIATION
      ↓
RUN REGRESSION
      ↓
RECHECK DEPENDENCY SURFACE
      ↓
AUDIT COMPLETE
```

---

# 76. Non-Negotiable Operating Rules

The system must:

```text id="g7n3p6"
establish explicit security scope before external queries
treat the lockfile as authoritative for resolved versions
distinguish direct from transitive dependencies
preserve parent chains for transitive findings
compare against an explicit baseline
match exact resolved versions against authoritative advisories
record canonical advisory identifiers
distinguish vulnerability from reachability
distinguish reachability from exploitability
identify call sites when technically possible
never equate scanner output with confirmed exploitability
maintain separate license and security findings
use explicit license policy for compatibility conclusions
never infer a license
inspect provenance and integrity when available
use evidence for maintainer/supply-chain claims
never call a package malicious from subjective signals alone
never equate outdated with vulnerable
never recommend upgrades merely because a newer release exists
never recommend downgrades without policy and compatibility analysis
keep audit read-only by default
validate findings before reporting them
record false-positive dispositions
preserve uncertainty
re-audit after remediation
run regression validation after security changes
never publish disclosures without explicit authorization
never store package or registry secrets in findings or audit logs
use security memory as historical evidence, not current authority
allow learning to improve triage without expanding authority
```

---

# 77. Central Supply-Chain Principle

> **A dependency audit must trace the complete chain from declared dependency to resolved artifact, advisory, vulnerable behavior, application reachability, and deployment context. A package being present is exposure; evidence determines whether that exposure is relevant, reachable, exploitable, and actionable.**

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/02-audit-state-machine.md` — §2: Audit State Machine
- `references/06-10-phase-01-inventory.md` — §6–10: Phase 01 — INVENTORY, Manifest vs Lockfile, Dependency Normalization, Phase 02 — BASELINE, Dependency Diff
- `references/11-20-phase-03-transitive-graph.md` — §11–20: Phase 03 — TRANSITIVE GRAPH, Parent Chain, Multiple Parent Paths, Dependency Reachability Layers, Reachability Analysis, Call-Site Requirement, Exploitability Context, Advisory Matching, Advisory Freshness, CVE and Advisory Identity
- `references/21-31-finding-deduplication.md` — §21–31: Finding Deduplication, Vulnerability Severity vs Context, License Inventory, License Policy, License Evidence, License Obligations, Provenance Analysis, Integrity, Maintainer / Supply-Chain Signals, Abandoned / Low-Maintenance Packages, Outdated Dependency Analysis
- `references/32-42-downgrade-policy.md` — §32–42: Downgrade Policy, Remediation Options, Fixed-Version Analysis, Remediation Risk, Dependency Diff Risk, SecurityFinding Contract, Finding Confidence, Reachability Matrix, Vulnerability Finding Validation, False Positive Handling, False Negative Awareness
- `references/43-54-runtime-inventory.md` — §43–54: Runtime Inventory, Generated / Vendored Dependencies, Dependency Security Boundary, License / Security Correlation, Findings Summary, Dependency Surface Report, Exception Management, No Permanent Silent Suppression, Regression After Remediation, Remediation Verification, Lockfile Integrity After Remediation, Advisory Recheck
- `references/55-65-new-vulnerability-detection.md` — §55–65: New Vulnerability Detection, Dependency Audit and Code Review, Architecture Escalation, Security Escalation, External Disclosure Boundary, Operator Question: "Is X Safe?", Required Outputs, Evidence Contract, Audit Log, Security Privacy, Memory Integration
- `references/66-69-failure-memory.md` — §66–69: Failure Memory, Self-Improvement Boundary, Anti-Patterns, Mandatory Distinctions
- `references/71-72-final-audit-result.md` — §71–72: Final Audit Result, Completion States
- `references/74-75-golden-finding-workflow.md` — §74–75: Golden Finding Workflow, Golden Remediation Workflow
