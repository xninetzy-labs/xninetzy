---
name: debugging
description: 'Evidence-first debugging of wrong outputs, failed requests, regressions, flaky tests, race conditions and incidents: reproduce, isolate the root cause, falsify, apply the smallest fix, add a regression test. Use when the cause of a failure is unknown.'
metadata:
  keywords: before behavior closes collects contributing controlled driven emits factors falsification for from hypotheses incorrect learning loop malformed memory narrows primary production reproducible requires results runtime separates symptom tool unexpected validation verifiable with workflow
---

# debugging

Evidence-first debugging control plane.

The system must explain **why the behavior occurred**, not merely produce a patch that makes the symptom disappear.

Debugging is complete only when the failure has been:

```text
reproduced or bounded
→ observed
→ localized
→ falsifiably tested
→ causally explained
→ minimally fixed
→ regression-protected
→ verified
→ recorded
```
---

# 1. Core Invariant

Never confuse:

```text
SYMPTOM
≠
FAILURE MECHANISM
≠
ROOT CAUSE
≠
FIX
≠
REGRESSION TEST
```

Example:

```text
Symptom:
request returns 500

Mechanism:
undefined value reaches database serializer

Root cause:
request normalization skipped for one code path

Fix:
normalize input at the shared boundary

Regression:
test exercises the previously failing code path and asserts the expected result
```

A successful patch without causal proof is not a complete debugging result.

---

# 3. Pipeline

```text
SYMPTOM
   ↓
SCOPE
   ↓
REPRODUCE
   ↓
OBSERVED_STATE
   ↓
EVIDENCE_TABLE
   ↓
BOUNDARY_LOCALIZATION
   ↓
HYPOTHESES
   ↓
RANK_BY_EVIDENCE
   ↓
CONTROLLED_TEST
   ↓
FALSIFY
   ↓
ROOT_CAUSE
   ↓
MINIMAL_FIX
   ↓
TARGETED_TEST
   ↓
FULL_REGRESSION
   ↓
VERIFY_NO_REGRESSION
   ↓
RECORD_LEARNING
```

The sequence before `HYPOTHESES` is mandatory unless the system is explicitly in
an incident mode where evidence is continuously collected while containment is
being performed.

---

# 56. Debugging Output Contract

Every completed debugging operation should produce:

```yaml
debug_result:
  state:

  symptom:
    expected:
    observed:

  reproduction:
    status:
    recipe:

  scope:
    environment:
    commit:
    component:

  evidence:
    refs: []
    table: []

  localization:
    boundary:
    first_incorrect_state:
    source_location:

  hypotheses:
    - id:
      statement:
      status:
      confidence:
      supporting_evidence: []
      refuting_evidence: []

  root_cause:
    primary:
    contributing_factors: []
    mechanism:

  fix:
    summary:
    files: []
    diff_ref:

  regression:
    reproduces_before_fix:
    passes_after_fix:
    tests: []

  verification:
    result:
    blast_radius_tests: []

  learning:
    failure_fingerprint:
    memory_recorded:

  next_action:
    type:
    reason:
```

---

# 62. Final Golden Workflow

```text
CAPTURE SYMPTOM
      ↓
SCOPE
      ↓
REPRODUCE
      ↓
COLLECT OBSERVATIONS
      ↓
BUILD EVIDENCE TABLE
      ↓
TRACE EXECUTION BOUNDARIES
      ↓
LOCALIZE FIRST INCORRECT STATE
      ↓
GENERATE MULTIPLE HYPOTHESES
      ↓
RANK BY EVIDENCE
      ↓
DESIGN CONTROLLED TEST
      ↓
FALSIFY / SUPPORT
      ↓
ESTABLISH PRIMARY ROOT CAUSE
      ↓
DESIGN MINIMAL FIX
      ↓
INSPECT DIFF
      ↓
RUN REGRESSION
      ↓
RUN BLAST-RADIUS TESTS
      ↓
RERUN ORIGINAL REPRODUCTION
      ↓
VERIFY NO REGRESSION
      ↓
STORE FAILURE MEMORY
      ↓
CLOSE
```

---

# 63. Non-Negotiable Operating Rules

The system must:

```text
collect evidence before forming causal hypotheses
preserve the exact symptom
define debugging scope
reproduce before modifying code when feasible
distinguish observation from interpretation
identify the first incorrect state
trace boundaries instead of guessing from the final exception
maintain multiple hypotheses
record evidence for and against each hypothesis
use controlled tests to distinguish hypotheses
require falsifiable predictions
avoid unsupported probability claims
distinguish root cause from contributing factors
prefer invariant restoration over symptom suppression
produce the smallest justified patch
inspect the resulting diff
require regression protection
test before and after the fix when practical
expand testing according to blast radius
treat intermittent behavior as evidence of intermittence, not proof of race
treat restart/retry/cache clearing as observations, not root-cause explanations
preserve security boundaries
never log secrets
record uncertainty explicitly
use historical memory as a hypothesis source, never as current proof
learn routing and diagnosis patterns without expanding authority
stop when causal evidence is insufficient
```

---

# 64. Central Debugging Principle

> **Do not debug toward a patch. Debug toward a causal explanation. The patch is only the final intervention that proves the explanation by removing the observed failure without violating the system's intended invariants.**

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/02-debugging-state-machine.md` — §2: Debugging State Machine
- `references/04-09-phase-01-capture-symptom.md` — §4–9: Phase 01 — CAPTURE SYMPTOM, Phase 02 — SCOPE, Scope Integrity, Phase 03 — REPRODUCE, Reproduction Quality, Flaky / Intermittent Debugging
- `references/10-15-phase-04-observed-state.md` — §10–15: Phase 04 — OBSERVED STATE, Evidence Table, Evidence Hierarchy, Evidence Quality, Phase 05 — BOUNDARY LOCALIZATION, First Incorrect State
- `references/16-21-phase-06-localize.md` — §16–21: Phase 06 — LOCALIZE, Phase 07 — HYPOTHESIS GENERATION, Hypothesis Contract, Evidence-For / Evidence-Against Rule, Hypothesis Ranking, Bayesian Language Policy
- `references/22-28-phase-08-controlled-test.md` — §22–28: Phase 08 — CONTROLLED TEST, Controlled-Test Contract, Falsification, Negative Evidence, Phase 09 — ROOT CAUSE, Primary Root Cause vs Contributing Factors, Root-Cause Quality Gate
- `references/29-35-phase-10-minimal-fix.md` — §29–35: Phase 10 — MINIMAL FIX, Fix Design Contract, Minimality Rule, Patch Evidence, Phase 11 — REGRESSION TEST, Regression Quality, Manual Verification
- `references/36-46-phase-12-patch-validation.md` — §36–46: Phase 12 — PATCH VALIDATION, Blast-Radius Testing, Diff Safety, Dependency / Environment Failures, Distributed / Async Debugging, Database Debugging, Concurrency / Race Debugging, Time / Ordering Bugs, Observability Gaps, Safe Instrumentation, Security Boundary
- `references/47-55-memory-learning-loop.md` — §47–55: Memory / Learning Loop, Failure Fingerprint, Reuse of Historical Failures, Self-Improvement Boundary, Incident Mode, Rollback Rule, Multiple Simultaneous Failures, Anti-Patterns, Common Symptom-Fixing Traps
- `references/57-61-completion-states.md` — §57–61: Completion States, Required Artifacts, Compact Hypothesis Matrix, Root-Cause Statement Contract, Patch Contract
