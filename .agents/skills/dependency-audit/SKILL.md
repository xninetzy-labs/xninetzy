---

name: dependency-audit

description: Evidence-driven dependency and software supply-chain audit for direct and transitive packages. Reviews manifests, lockfiles, dependency graphs, known vulnerabilities, license policy, provenance, package integrity, maintainership signals, reachability, exploitability context, and remediation risk within explicitly authorized scope. Use when dependencies are added, removed, upgraded, downgraded, lockfiles change, advisories affect used packages, or the operator requests a dependency surface review.

metadata:
   author: xninetzy
   version: "2.0.0"
   scope: domain
   priority: P1

required_tools:
- repo_dependency
- security_dependencies
- security_scope
- security_validate_finding
- lightning_record_action

optional_tools:
- repo_search
- repo_symbol
- repo_diff
- repo_history
- security_assets
- security_supply_chain
- security_license
- security_reachability
- hitl_request_approval
- os_inbox
- memory_security_store

trigger_conditions:
- a dependency is added
- a dependency is upgraded
- a dependency is downgraded
- a dependency is removed
- the lockfile changes
- a package manager configuration changes
- a new security advisory affects a used package
- the operator asks whether a dependency is safe
- the operator requests dependency inventory or supply-chain review
- a package provenance or integrity signal changes

prerequisites:
- local manifest or lockfile is reachable
- dependency scope is known
- explicit security scope exists before external advisory/package queries
- package-manager ecosystem is identifiable

escalation_routes:
   application_security: security-review
   infrastructure: xninetzy-security-testing
   API_surface: api-security
   architecture_impact: architecture-analysis
------------------------------------------

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

# 2. Audit State Machine

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

# 6. Phase 01 — INVENTORY

Inventory direct and transitive dependencies.

Canonical fields:

```yaml id="x4p7n2"
dependency:
  ecosystem:
  package:
  resolved_version:
  requested_range:
  dependency_type:
  direct:
  parent_chain:
  lockfile:
  manifest:
```

Possible `dependency_type`:

```text id="y9c3m1"
runtime
development
optional
peer
build
test
tooling
```

Do not collapse development-only dependencies into runtime exposure.

---

# 7. Manifest vs Lockfile

Compare:

```text id="c6v2j8"
DECLARED
vs
RESOLVED
```

Example:

```text id="m8x1q5"
Manifest:
foo ^4.2

Lockfile:
foo 4.2.7
```

The advisory match must use the resolved version when assessing actual installed
exposure.

A broad manifest range is not itself proof of a vulnerable installed version.

---

# 8. Dependency Normalization

Normalize package identity using:

```text id="q7n2w5"
ecosystem
canonical package name
resolved version
package manager
source registry
lockfile identity
```

Account for ecosystem-specific aliases and package naming semantics when supported.

Do not treat:

```text id="f1r8m4"
same text
```

as:

```text id="p3w9k7"
same package
```

without ecosystem context.

---

# 9. Phase 02 — BASELINE

Establish the comparison point.

Possible baselines:

```text id="d8q2f6"
current branch
merge base
release tag
previous lockfile
previous audit snapshot
operator-specified version
```

Preferred order:

```text id="w1m5c9"
explicit operator baseline
→ repository merge base
→ previous known-good audit
→ previous lockfile
```

Record the baseline identity.

---

# 10. Dependency Diff

Summarize:

```yaml id="u6k9r2"
dependency_diff:
  added: []
  removed: []
  upgraded: []
  downgraded: []
  unchanged: []
  source_changed: []
```

For each changed package capture:

```text id="b5r7x1"
old version
new version
direct/transitive
parent chain
lockfile location
reason when available
```

Do not state that a dependency upgrade caused a regression merely because the
upgrade appears in the diff.

---

# 11. Phase 03 — TRANSITIVE GRAPH

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

# 12. Parent Chain

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

# 13. Multiple Parent Paths

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

# 14. Dependency Reachability Layers

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

# 15. Reachability Analysis

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

# 16. Call-Site Requirement

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

# 17. Exploitability Context

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

# 18. Advisory Matching

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

# 19. Advisory Freshness

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

# 20. CVE and Advisory Identity

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

# 21. Finding Deduplication

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

# 22. Vulnerability Severity vs Context

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

# 23. License Inventory

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

# 24. License Policy

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

# 25. License Evidence

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

# 26. License Obligations

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

# 27. Provenance Analysis

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

# 28. Integrity

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

# 29. Maintainer / Supply-Chain Signals

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

# 30. Abandoned / Low-Maintenance Packages

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

# 31. Outdated Dependency Analysis

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

# 32. Downgrade Policy

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

# 33. Remediation Options

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

# 34. Fixed-Version Analysis

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

# 35. Remediation Risk

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

# 36. Dependency Diff Risk

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

# 37. SecurityFinding Contract

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

# 38. Finding Confidence

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

# 39. Reachability Matrix

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

# 40. Vulnerability Finding Validation

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

# 41. False Positive Handling

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

# 42. False Negative Awareness

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

# 43. Runtime Inventory

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

# 44. Generated / Vendored Dependencies

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

# 45. Dependency Security Boundary

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

# 46. License / Security Correlation

Security and license issues must remain separate.

One package may have:

```text id="h1m5q8"
security finding
+
license finding
```

These should not be merged into one finding merely because the package is the same.

---

# 47. Findings Summary

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

# 48. Dependency Surface Report

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

# 49. Exception Management

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

# 50. No Permanent Silent Suppression

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

# 51. Regression After Remediation

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

# 52. Remediation Verification

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

# 53. Lockfile Integrity After Remediation

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

# 54. Advisory Recheck

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

# 55. New Vulnerability Detection

A security upgrade may introduce new dependencies or new advisories.

Therefore:

```text id="m1q7r4"
REMEDIATION
   ↓
FULL DEPENDENCY RECHECK
```

is preferred over validating only the original package.

---

# 56. Dependency Audit and Code Review

When a dependency changes:

```text id="j8m5p2"
dependency-audit
+
code-review
```

may both be required.

Dependency audit answers:

```text id="r7x2q4"
"What changed in the supply chain?"
```

Code review answers:

```text id="d9m3k8"
"How does the application use the changed dependency?"
```

Do not substitute one for the other.

---

# 57. Architecture Escalation

If dependency changes introduce:

```text id="q3n8m5"
new framework boundary
new database layer
new service coupling
new runtime integration
shared utility coupling
```

route to:

```text id="w6p2k9"
architecture-analysis
```

Dependency security remains separate from architectural impact.

---

# 58. Security Escalation

If a dependency finding provides evidence of:

```text id="g4q7m1"
remote code execution
credential exposure
deserialization
SSRF
sandbox escape
supply-chain compromise
malicious package behavior
```

route to:

```text id="c8m2r5"
xninetzy-security-testing
```

for broader authorized assessment.

Do not expand scope automatically.

---

# 59. External Disclosure Boundary

The dependency-audit skill may:

```text id="u7m3q8"
identify vulnerabilities
document findings
prepare internal remediation information
link to authoritative advisories
```

It must not:

```text id="z5p1n6"
publish public disclosures
contact maintainers
open external security reports
announce compromise
```

without explicit authorized workflow.

---

# 60. Operator Question: "Is X Safe?"

Do not answer with an unqualified:

```text id="r6q2m8"
safe
```

Instead evaluate:

```text id="h3n7p1"
version
advisories
license
provenance
integrity
usage
reachability
configuration
deployment context
```

Then report bounded conclusions such as:

```text id="c4x8m2"
No matching advisory was identified for the resolved version in the checked
sources; application reachability and deployment-specific risk remain separate
considerations.
```

"Safe" is not a property that can usually be established from package metadata
alone.

---

# 61. Required Outputs

A completed audit should produce:

```text id="n2k7w5"
1. dependency inventory
2. manifest/lockfile resolution
3. baseline diff
4. transitive parent chains
5. advisory correlation
6. license inventory
7. provenance/integrity observations
8. reachability matrix
9. validated SecurityFindings
10. remediation analysis
11. regression requirements
12. audit summary
```

Not all outputs need to be user-visible, but each required conclusion must have
supporting evidence.

---

# 62. Evidence Contract

Every consequential finding should reference:

```yaml id="v5m8q2"
evidence:
  source:
  package:
  version:
  locator:
  observation:
  retrieved_at:
```

Possible sources:

```text id="s8q4m1"
manifest
lockfile
repository_source
package_registry
advisory_database
license_file
provenance_metadata
build_artifact
runtime_inventory
```

---

# 63. Audit Log

Record significant audit actions through:

```text id="x7p3m9"
lightning_record_action
```

At minimum:

```yaml id="q4w8k2"
audit_action:
  operation:
  target:
  scope:
  timestamp:
  result:
  finding_refs:
```

Never record:

```text id="r5m1n7"
registry credentials
tokens
private package credentials
authorization headers
```

---

# 64. Security Privacy

Never place secrets into:

```text id="e6q2w8"
dependency reports
audit events
finding descriptions
memory
screenshots
debug logs
lockfile excerpts
```

Redact:

```text id="j1p7x4"
tokens
passwords
private registry credentials
authorization headers
signed URLs
private package credentials
```

---

# 65. Memory Integration

When `memory_security_store` is available, store only durable security knowledge:

```text id="m8q3r6"
recurring vulnerable package
validated false-positive pattern
repository-specific license policy
known dependency ownership
previous remediation outcome
recurring transitive path
```

Historical memory is advisory.

Current lockfile and authoritative advisory data take precedence.

---

# 66. Failure Memory

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

# 67. Self-Improvement Boundary

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

# 68. Anti-Patterns

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

# 69. Mandatory Distinctions

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

# 71. Final Audit Result

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

# 72. Completion States

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

# 74. Golden Finding Workflow

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

# 75. Golden Remediation Workflow

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
