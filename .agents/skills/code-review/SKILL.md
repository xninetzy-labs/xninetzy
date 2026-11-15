---
name: code-review
description: 'Pre-merge review of a branch, commit range or PR against the repository''s own rules: regressions, error propagation, idempotency, API drift, layering, security, tests and scope creep, with severity-tiered findings. Use before merging.'
metadata:
  keywords: about anchored architecture asks behavior boundaries change changes code comments contract contracts declared defects dependency detects diff driven engineering evidence expansion file fixes gaps invariants layer level merged misleading missing naming observability operator per problems produces project pull ready request retries retry reviews risk rule sensitive silent suggested symbol this unnecessary violations whenever
---

# code-review

Pre-merge verification layer for Xninetzy.

This skill reviews **the change**, not merely the changed lines.

Core principle:

> **A diff is safe only when its changed behavior is understood in the context of the repository's rules, architecture, contracts, dependencies, and tests.**

Second principle:

> **Every important review conclusion must be traceable to evidence.**

---

# 1. Review Objective

The review must answer:

```text
What changed?

Why did it change?

What behavior changed?

Which contracts changed?

Which modules are affected?

Which project rules apply?

Which security boundaries moved?

Which tests validate the new behavior?

What could regress?

What remains unknown?

Is the patch ready under the project's own rules?
```

---

# 2. Core Pipeline

```text
TARGET
  ↓
DIFF
  ↓
RULEBOOK
  ↓
REPOSITORY CONTEXT
  ↓
CHANGE CLASSIFICATION
  ↓
PER-FILE ANALYSIS
  ↓
SYMBOL / CALL IMPACT
  ↓
ARCHITECTURE CHECK
  ↓
API / CONTRACT CHECK
  ↓
SECURITY CHECK
  ↓
ERROR / RETRY / IDEMPOTENCY CHECK
  ↓
TEST CHECK
  ↓
DEPENDENCY / CONFIG CHECK
  ↓
REGRESSION ANALYSIS
  ↓
FINDING CORRELATION
  ↓
REVIEW REPORT
  ↓
VERDICT
```

---

# 54. Review Severity

Use:

```text
BLOCKER
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

## BLOCKER

Must not merge because it violates an explicit hard project rule or introduces
an unacceptable correctness/security condition under project policy.

## CRITICAL

Severe correctness/security issue with strong evidence.

## HIGH

Material correctness/security/reliability regression.

## MEDIUM

Meaningful issue that should normally be fixed before merge.

## LOW

Limited issue or maintainability risk.

## INFO

Observation with no immediate blocking impact.

Do not inflate severity merely because a tool labels something severe.

---

# 60. Review Verdict

Possible verdicts:

```text
APPROVE
REQUEST_CHANGES
COMMENT_ONLY
BLOCKED
```

## APPROVE

No unresolved blocker/critical/high findings and required review gates pass.

## REQUEST_CHANGES

One or more merge-blocking findings remain.

## COMMENT_ONLY

Findings exist but none violate merge gates.

## BLOCKED

Required review evidence is missing or the comparison target/rule context is
ambiguous.

---

# 61. Merge Gate

The default project policy is:

```text
BLOCKER
CRITICAL
HIGH
```

unresolved:

```text
REQUEST_CHANGES
```

However, if the repository explicitly defines a different merge gate, use the
repository rule.

Do not override an explicit project gate with generic conventions.

---

# 75. Review Report

Standard structure:

```text
# Code Review

## Target
base:
head:
merge_base:

## Summary
change type:
files:
risk:

## Merge Gate
status:

## Findings
...

## Architecture
...

## API / Contract
...

## Security
...

## Reliability
...

## Dependencies / Config
...

## Test Coverage
...

## Regression Risk
...

## Positive Observations
...

## Uncertainties
...

## Required Actions
...

## Verdict
...
```

---

# 79. Completion Contract

A code review is complete only when:

```text
[ ] base identified
[ ] head identified
[ ] merge base identified
[ ] diff integrity verified
[ ] project rules loaded
[ ] applicable local rules resolved
[ ] change classified
[ ] per-file review performed
[ ] changed symbols analyzed
[ ] behavior delta understood
[ ] naming checked
[ ] comments checked
[ ] error propagation checked
[ ] retry behavior checked
[ ] idempotency checked
[ ] concurrency checked where relevant
[ ] architecture checked
[ ] API contract checked where relevant
[ ] security boundaries checked where relevant
[ ] dependencies/config checked
[ ] tests checked
[ ] coverage measured or marked unknown
[ ] regression risk assessed
[ ] findings correlated
[ ] pre-existing issues separated
[ ] limitations recorded
[ ] verdict produced
```

---

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/03-10-review-target.md` — §3–10: Review Target, Diff Integrity, Rulebook Loading, Rule Scope, Rule Conflict, Change Classification, Change Surface, Behavior Delta
- `references/11-20-per-file-review.md` — §11–20: Per-File Review, Diff Anchoring, Deleted-Code Analysis, Added-Code Analysis, Modified-Code Analysis, Naming, Naming Semantics, No-Comment Rules, Error Propagation, Error Contract
- `references/21-29-silent-retry-detection.md` — §21–29: Silent Retry Detection, Retry Safety, Idempotency, Transaction Boundaries, Concurrency / Race Analysis, Layer Boundary, Architecture Drift, Dependency Direction, API Contract
- `references/30-38-api-compatibility.md` — §30–38: API Compatibility, Public API Expansion, Authentication Review, Authorization Review, Input Validation, Security-Sensitive Sinks, Secrets, Dependencies, Configuration Changes
- `references/39-48-observability.md` — §39–48: Observability, Test Analysis, Coverage Delta, Test Adequacy, Missing Tests, Regression Risk, Blast Radius, Backward Compatibility, Database Changes, Background Jobs
- `references/49-53-caching.md` — §49–53: Caching, External Integrations, Scope Creep, Generated Files, Dependency Lockfile Integrity
- `references/55-59-confidence.md` — §55–59: Confidence, Finding Schema, Finding Categories, Review Comments, Suggested Fixes
- `references/62-71-unknown-state.md` — §62–71: Unknown State, Review Coverage, Diff Coverage, Review Completeness, Tool Correlation, Security Handoff, Architecture Handoff, API Handoff, Review Order, Priority Ordering
- `references/72-74-review-noise-control.md` — §72–74: Review Noise Control, Existing Problems, Fix Validation
- `references/76-78-per-file-summary.md` — §76–78: Per-File Summary, Positive Evidence, Final Review Example
- `references/80-final-principle.md` — §80: Final Principle
