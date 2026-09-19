

name: "debugging"

description: "Evidence-driven debugging workflow for unexpected runtime behavior, incorrect outputs, failed requests, regressions, flaky tests, race conditions, malformed tool results, and production incidents. Collects reproducible evidence before hypotheses, separates symptom from cause, narrows to a primary root cause with contributing factors, requires controlled falsification, emits the smallest verifiable fix, and closes the loop with regression validation and failure-memory learning."

metadata:
            author: "xninetzy"
            version: "2.0.0"
            scope: "domain"
            priority: "P1"

required_tools:
- repo_search
- repo_s---
mbol
- repo_diff
- observability_query
- memory_failure_store

optional_tools:
- repo_test
- repo_history
- repo_dependency
- repo_ownership
- lightning_record_action
- hitl_request_approval
- os_inbox
- action_policy_evaluate

trigger_conditions:
- operator reports an unexpected error
- operator reports incorrect or inconsistent behavior
- a tool returns an empty or malformed result
- a metric deviates from baseline
- a test fails unexpectedly
- a previously passing behavior regresses
- behavior is intermittent or flaky
- the operator asks why X is happening
- a production or staging incident requires root-cause analysis

prerequisites:
- failing scenario is reachable by test, command, request, workflow, or observable production event
- sufficient observability exists for the failing scenario
- affected code or execution boundary can be inspected
- execution scope is known

escalation_routes:
            cross_module_boundary: "architecture-analysis"
            api_boundary: "api-security"
            security_signal: "xninetzy-security-testing"
            deployment_or_infrastructure: "infrastructure-analysis"
-----------------------------------------------------

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

# 2. Debugging State Machine

Canonical states:

```text
REPORTED
  ↓
SCOPED
  ↓
REPRODUCIBLE
  ↓
OBSERVED
  ↓
LOCALIZED
  ↓
HYPOTHESES_READY
  ↓
CONTROLLED_TEST
  ↓
ROOT_CAUSE_ESTABLISHED
  ↓
PATCH_PROPOSED
  ↓
PATCH_VALIDATED
  ↓
REGRESSION_PROTECTED
  ↓
CLOSED
```

Failure / blocked states:

```text
NON_REPRODUCIBLE
INSUFFICIENT_EVIDENCE
ENVIRONMENT_MISMATCH
OBSERVABILITY_GAP
AMBIGUOUS_CAUSE
PATCH_UNSAFE
REGRESSION_UNPROVEN
BLOCKED
UNKNOWN
```

Never transition directly from:

```text
REPORTED
→ PATCH_PROPOSED
```

without sufficient evidence.

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

# 4. Phase 01 — CAPTURE SYMPTOM

Capture the operator's statement without prematurely interpreting it.

Required:

```yaml
symptom:
  reported_at:
  reporter:
  system:
  component:
  environment:
  expected_behavior:
  observed_behavior:
  exact_error:
  affected_operation:
  first_known_occurrence:
  recurrence:
  scope:
```

Preserve exact error messages when useful.

Do not rewrite:

```text
"returns 403"
```

into:

```text
"authorization bug"
```

before evidence exists.

---

# 5. Phase 02 — SCOPE

Define the debugging boundary:

```text
repository
service
module
symbol
request
job
database operation
external dependency
environment
deployment
```

Also identify:

```text
branch
commit
build
runtime version
dependency version
configuration source
feature flags
tenant/user scope when relevant
```

Scope must be narrow enough to debug and broad enough to include the actual
execution path.

---

# 6. Scope Integrity

Do not alter the debugging target while investigating.

A changed:

```text
branch
commit
configuration
dependency
environment
request
input
feature flag
```

may invalidate previous evidence.

Record material environment changes explicitly.

---

# 7. Phase 03 — REPRODUCE

The first objective is deterministic reproduction.

Produce:

```text
reproduction_recipe
```

with:

```yaml
reproduction:
  prerequisites: []
  setup: []
  command:
  request:
  input:
  expected:
  actual:
  reproduction_rate:
  attempts:
  environment:
  commit:
```

A reproduction is stronger when it can be run repeatedly with the same result.

---

# 8. Reproduction Quality

Classify:

```text
DETERMINISTIC
REPEATABLE
INTERMITTENT
RARE
NON_REPRODUCIBLE
UNKNOWN
```

Suggested confidence:

```text
DETERMINISTIC
→ failure reproduced consistently

REPEATABLE
→ failure reproduced under controlled repetition

INTERMITTENT
→ failure appears under some executions

RARE
→ failure reproduced only under limited conditions

NON_REPRODUCIBLE
→ available evidence cannot reproduce it
```

Do not fabricate deterministic reproduction from a single observation.

---

# 9. Flaky / Intermittent Debugging

For intermittent failures, collect:

```text
attempt_number
timestamp
input_fingerprint
runtime
environment
concurrency
ordering
latency
result
error
trace_id
```

Estimate the observed failure frequency:

```text
failure_rate =
failed_attempts / total_attempts
```

Do not label a failure:

```text
"race condition"
```

merely because it is intermittent.

Intermittence is evidence about reproducibility, not proof of mechanism.

---

# 10. Phase 04 — OBSERVED STATE

Collect evidence before forming causal hypotheses.

Preferred evidence sources:

```text
stack trace
structured logs
request traces
metrics
runtime state
database state
queue state
tool output
test output
source code
configuration
dependency metadata
recent diff
deployment history
```

Preserve:

```yaml
observation:
  timestamp:
  source:
  value:
  context:
  trace_id:
  interpretation:
```

`interpretation` must remain separate from `value`.

---

# 11. Evidence Table

Canonical format:

| Time | Source | Observation                | Interpretation                      | Confidence |
| ---- | ------ | -------------------------- | ----------------------------------- | ---------- |
| t1   | log    | `foo_id=null`              | unexpected null at boundary         | HIGH       |
| t1   | stack  | serializer line 42         | failure occurs during serialization | HIGH       |
| t2   | source | no normalization in path B | possible missing invariant          | MEDIUM     |

Evidence must describe what was observed.

Interpretations are hypotheses or derived conclusions and must not be presented as
raw facts.

---

# 12. Evidence Hierarchy

When sources disagree, prefer direct runtime evidence over assumption.

Recommended order:

```text
1. current runtime observation
2. deterministic test result
3. current source/configuration
4. trace/log correlation
5. deployment/version metadata
6. recent history
7. documentation
8. memory
9. intuition
```

This ordering can be adjusted for a specific debugging domain when a stronger
source exists.

---

# 13. Evidence Quality

Classify evidence:

```text
DIRECT
DERIVED
INDIRECT
HISTORICAL
UNVERIFIED
```

Examples:

```text
DIRECT:
stack trace points to function X

DERIVED:
latency increased after dependency initialization

INDIRECT:
symptom resembles a known failure

HISTORICAL:
same error occurred six months ago

UNVERIFIED:
operator suspects cache corruption
```

Only direct or strongly corroborated derived evidence should establish a root cause.

---

# 14. Phase 05 — BOUNDARY LOCALIZATION

Map the failure across execution boundaries.

Typical chain:

```text
INPUT
 ↓
VALIDATION
 ↓
TRANSFORMATION
 ↓
BUSINESS LOGIC
 ↓
PERSISTENCE
 ↓
EXTERNAL SERVICE
 ↓
ASYNC/QUEUE
 ↓
RESPONSE
```

For each boundary ask:

```text
entered?
exited?
expected value?
actual value?
state changed?
error introduced?
```

The objective is to identify the **first incorrect state**, not merely the last
place where the system crashed.

---

# 15. First Incorrect State

Prefer:

```text
first divergence
```

over:

```text
last exception
```

Example:

```text
HTTP 500
 ↓
serializer exception
 ↓
missing object field
 ↓
object already malformed before serializer
 ↓
normalization branch omitted field
```

The serializer is the failure location.

The normalization boundary is the likely causal boundary.

---

# 16. Phase 06 — LOCALIZE

Produce a localization record:

```yaml
localization:
  component:
  file:
  symbol:
  line_or_range:
  boundary:
  first_incorrect_state:
  downstream_failure:
  evidence_refs: []
```

Use `repo_symbol` and `repo_search` to establish exact code ownership and call
paths.

Do not guess source locations from filenames alone.

---

# 17. Phase 07 — HYPOTHESIS GENERATION

Create multiple plausible hypotheses.

Recommended categories:

```text
LOGIC
STATE
INPUT
DATA
CONCURRENCY
TIMING
CACHE
DEPENDENCY
CONFIGURATION
ENVIRONMENT
NETWORK
DATABASE
API_CONTRACT
RESOURCE_EXHAUSTION
RACE
ORDERING
OBSERVABILITY
```

Do not limit hypotheses to the first plausible code defect.

---

# 18. Hypothesis Contract

Each hypothesis must contain:

```yaml
hypothesis:
  id:
  statement:
  category:

  supporting_evidence: []
  refuting_evidence: []

  predicted_observations: []
  falsification_test:

  confidence:
  status:
```

Allowed status:

```text
OPEN
SUPPORTED
WEAKENED
FALSIFIED
ESTABLISHED
```

---

# 19. Evidence-For / Evidence-Against Rule

Every meaningful hypothesis must state both:

```text
what would support it
```

and:

```text
what would refute it
```

Bad:

```text
"It looks like a race condition."
```

Good:

```text
Hypothesis:
shared mutable state is accessed concurrently.

Supports:
failures correlate with concurrency > 1.

Refutes:
same failure occurs with concurrency = 1.

Controlled test:
run identical workload at concurrency 1, 2, 4, 8.
```

---

# 20. Hypothesis Ranking

Rank by evidence, not intuition.

Recommended factors:

```text
direct evidence
causal proximity
reproduction coverage
explanatory power
number of assumptions
contradicting evidence
testability
```

Example:

```yaml
ranking:
  hypothesis_id:
  confidence: HIGH | MEDIUM | LOW
  rationale:
  strongest_evidence:
  strongest_refutation:
```

Do not use arbitrary numeric probability unless the system has a validated
probabilistic model.

---

# 21. Bayesian Language Policy

Avoid unsupported claims such as:

```text
"90% likely"
"almost certainly"
"99% race condition"
```

unless those values are produced by an actual validated model or measurement.

Prefer:

```text
HIGH confidence
MEDIUM confidence
LOW confidence
```

with explicit evidence.

---

# 22. Phase 08 — CONTROLLED TEST

The controlled test must distinguish hypotheses.

A good test changes one meaningful variable while preserving the rest.

Conceptually:

```text
CONTROL
vs
EXPERIMENT
```

Examples:

```text
concurrency 1 vs 8
cache enabled vs disabled
dependency version A vs B
feature flag off vs on
normalized input vs raw input
transaction enabled vs disabled
```

The test must have a predicted outcome for each relevant hypothesis.

---

# 23. Controlled-Test Contract

```yaml
controlled_test:
  test_id:
  hypothesis_ids: []
  control:
  experiment:
  changed_variable:
  held_constant: []
  predicted_results: []
  command_or_procedure:
  observed_results: []
  conclusion:
```

Avoid changing multiple unrelated variables at once.

---

# 24. Falsification

After the controlled test:

```text
SUPPORTED
```

when predicted evidence appears.

```text
FALSIFIED
```

when a prediction is contradicted by reliable evidence.

```text
WEAKENED
```

when evidence becomes less consistent with the hypothesis but does not fully
exclude it.

The system must update the hypothesis matrix after each controlled test.

---

# 25. Negative Evidence

Negative evidence matters.

Examples:

```text
database is healthy
→ weakens database-corruption hypothesis

failure persists with cache disabled
→ weakens cache hypothesis

single-thread execution still fails
→ weakens race hypothesis

same binary fails only with production config
→ strengthens configuration hypothesis
```

Do not record only evidence that supports the preferred explanation.

---

# 26. Phase 09 — ROOT CAUSE

A root cause is established only when:

```text
1. the relevant failure can be reproduced or sufficiently bounded
2. the causal path is identified
3. observed evidence matches the causal mechanism
4. competing hypotheses are sufficiently weakened or falsified
5. a controlled intervention changes the failure as predicted
```

Root cause statement:

```text
ROOT CAUSE:
[one precise causal sentence]
```

Example:

```text
ROOT CAUSE:
The request path bypasses shared input normalization, allowing a null identifier
to reach the serializer and trigger the observed exception.
```

---

# 27. Primary Root Cause vs Contributing Factors

Use:

```yaml
root_cause:
  primary:
  contributing_factors: []
  triggering_condition:
  failure_mechanism:
```

Do not force unrelated failures into one root cause.

A single incident may contain:

```text
primary root cause
+
contributing factors
+
environmental trigger
```

The primary root cause should explain the causal path that produced the observed
failure.

---

# 28. Root-Cause Quality Gate

Reject a root-cause statement when it is merely:

```text
the stack trace location
the exception class
the symptom restated
a generic label
a guess
a component name
```

Bad:

```text
"Database issue."
```

Bad:

```text
"NullPointerException."
```

Good:

```text
"The background worker reads the job payload before the producer's transaction
commit is visible, so the worker receives an incomplete record."
```

---

# 29. Phase 10 — MINIMAL FIX

The fix should change the smallest boundary that restores the violated invariant.

Prefer:

```text
restore invariant
```

over:

```text
hide symptom
```

Examples:

```text
bad:
catch exception and return empty result

better:
validate the missing invariant at the correct boundary
```

```text
bad:
increase timeout indefinitely

better:
identify why the operation exceeds the expected latency budget
```

---

# 30. Fix Design Contract

```yaml
fix:
  objective:
  violated_invariant:
  files:
  symbols:
  change:
  expected_effect:
  collateral_risk:
  rollback_strategy:
  verification_plan:
```

The fix must not broaden scope without justification.

---

# 31. Minimality Rule

Prefer, in order:

```text
targeted logic correction
→ invariant enforcement
→ localized configuration correction
→ localized architectural correction
→ broader refactor
```

A broader refactor requires evidence that the narrow fix would preserve the same
failure.

---

# 32. Patch Evidence

A proposed patch must reference:

```text
root cause evidence
affected symbol
causal boundary
expected behavioral change
regression test
```

Do not emit a patch merely because it appears plausible.

---

# 33. Phase 11 — REGRESSION TEST

The regression test must demonstrate:

```text
BEFORE FIX
→ FAIL

AFTER FIX
→ PASS
```

When practical.

Required test contract:

```yaml
regression:
  name:
  reproduces_original_failure:
  expected_before_fix:
  expected_after_fix:
  assertions: []
  scope:
```

---

# 34. Regression Quality

The test should fail for the old behavior because of the actual bug.

Avoid tests that merely validate:

```text
"function no longer throws"
```

when the real contract is:

```text
correct output
correct side effect
correct persistence
correct error semantics
correct authorization
correct ordering
```

The regression must encode the violated invariant.

---

# 35. Manual Verification

Manual verification is useful for exploratory debugging.

It is not sufficient as the only regression protection for a software defect.

Required sequence:

```text
manual observation
+
automated regression where feasible
```

---

# 36. Phase 12 — PATCH VALIDATION

After applying the fix:

```text
1. rerun reproduction
2. run regression test
3. run affected package/module tests
4. inspect diff
5. run relevant integration tests
6. run broader tests according to blast radius
```

Do not stop at the first passing test.

---

# 37. Blast-Radius Testing

Use the affected dependency graph to determine test depth.

Typical escalation:

```text
symbol
 ↓
module
 ↓
package
 ↓
service
 ↓
integration
 ↓
system
```

Cross-module failures should route through:

```text
architecture-analysis
```

when architectural coupling is part of the causal path.

---

# 38. Diff Safety

Before finalizing the patch:

```text
repo_diff
```

must verify:

```text
scope is expected
no unrelated files changed
no debug artifacts remain
no secrets introduced
no tests weakened
no error handling silently suppressed
no temporary bypass remains
```

---

# 39. Dependency / Environment Failures

When evidence points outside the application code, inspect:

```text
runtime version
dependency version
lockfile
container image
environment variables
configuration
network
database schema
migration state
feature flags
build artifacts
deployment version
```

Do not edit application logic to compensate for an unverified environment mismatch.

---

# 40. Distributed / Async Debugging

For multi-service systems, trace:

```text
request_id
trace_id
job_id
event_id
message_id
transaction_id
```

across:

```text
client
API
worker
queue
database
external service
```

Establish:

```text
producer state
→ transport state
→ consumer state
→ persistence state
```

Do not assume the service reporting the error caused the failure.

---

# 41. Database Debugging

Separate:

```text
query generation
query transmission
database execution
transaction visibility
commit
rollback
replication
read-after-write visibility
```

Check:

```text
schema version
migration state
transaction boundary
isolation behavior
constraints
deadlocks
timeouts
connection pool
```

Do not label a failure "database-related" until the failing boundary is localized.

---

# 42. Concurrency / Race Debugging

For concurrency issues, record:

```text
thread/task identity
ordering
timestamps
shared resource
lock state
transaction state
interleaving
retry behavior
```

A race-condition claim requires evidence of an ordering or synchronization defect.

Intermittence alone is insufficient.

---

# 43. Time / Ordering Bugs

Use explicit timelines.

```text
T0 producer starts
T1 producer writes
T2 consumer starts
T3 consumer reads
T4 producer commits
```

Then identify:

```text
expected ordering
actual ordering
missing synchronization
```

Time-sensitive debugging should avoid ambiguous wall-clock interpretation when
monotonic timestamps or trace ordering is available.

---

# 44. Observability Gaps

If evidence cannot establish the causal path because telemetry is missing:

```text
OBSERVABILITY_GAP
```

Do not manufacture certainty.

Instead identify the smallest useful instrumentation needed:

```yaml
instrumentation_gap:
  missing_signal:
  insertion_point:
  expected_observation:
  privacy_risk:
  cleanup_required:
```

Instrumentation must not leak credentials or sensitive data.

---

# 45. Safe Instrumentation

Temporary debugging instrumentation must:

```text
have bounded scope
avoid secrets
avoid sensitive payload logging
carry a cleanup path
not materially alter timing when timing is under investigation
```

For timing/race bugs, instrumentation itself can perturb the failure.

When that risk exists, prefer tracing, sampling, counters, or existing telemetry.

---

# 46. Security Boundary

When a debugging signal indicates:

```text
authentication
authorization
secret leakage
SSRF
injection
unsafe deserialization
sandbox escape
MCP/tool boundary failure
```

route to:

```text
xninetzy-security-testing
```

or:

```text
api-security
```

as appropriate.

Do not weaken security controls merely to reproduce a bug.

---

# 47. Memory / Learning Loop

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

# 48. Failure Fingerprint

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

# 49. Reuse of Historical Failures

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

# 50. Self-Improvement Boundary

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

# 51. Incident Mode

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

# 52. Rollback Rule

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

# 53. Multiple Simultaneous Failures

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

# 54. Anti-Patterns

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

# 55. Common Symptom-Fixing Traps

## Exception suppression

```text
try:
    failing_operation()
except:
    return default
```

This can hide the failure while preserving invalid state.

## Retry inflation

Increasing retries can mask:

```text
deadlocks
race conditions
broken dependencies
bad timeouts
non-idempotent behavior
```

## Timeout inflation

Increasing timeout does not explain why latency exceeded the expected budget.

## Cache deletion

Clearing caches can temporarily remove stale state without identifying why stale
state was produced.

## Restart-driven recovery

Restarting can reset process state while leaving the causal defect untouched.

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

# 57. Completion States

Use one final state:

```text
FIXED_VERIFIED
```

when:

```text
root cause established
+
fix applied
+
regression passes
+
reproduction no longer fails
+
appropriate blast-radius tests pass
```

Use:

```text
ROOT_CAUSE_ESTABLISHED
```

when the cause is proven but no patch was applied in the current workflow.

Use:

```text
PARTIAL
```

when useful diagnosis exists but the entire lifecycle is incomplete.

Use:

```text
NON_REPRODUCIBLE
```

when available evidence cannot reproduce the problem.

Use:

```text
INSUFFICIENT_EVIDENCE
```

when the causal path cannot yet be established.

Use:

```text
BLOCKED
```

when required access, tools, environment, or authorization is unavailable.

Use:

```text
UNKNOWN
```

when the actual system state cannot be reliably established.

---

# 58. Required Artifacts

A normal completed debugging run should produce:

```text
1. reproduction recipe
2. evidence table
3. localization record
4. hypothesis matrix
5. controlled-test result
6. root-cause statement
7. proposed/applied diff
8. regression test
9. validation result
10. failure-memory record
```

Not every artifact must be user-visible, but each must be available for audit or
continuation where relevant.

---

# 59. Compact Hypothesis Matrix

Canonical human-readable form:

| ID | Hypothesis            | Supporting Evidence   | Refuting Evidence      | Controlled Test              | Status    | Confidence |
| -- | --------------------- | --------------------- | ---------------------- | ---------------------------- | --------- | ---------- |
| H1 | missing normalization | null at boundary      | none                   | bypass/restore normalization | SUPPORTED | HIGH       |
| H2 | cache corruption      | stale value observed  | fresh read still fails | cache off/on                 | FALSIFIED | LOW        |
| H3 | race condition        | intermittent failures | fails at concurrency 1 | concurrency sweep            | WEAKENED  | LOW        |

Do not remove falsified hypotheses from the audit trail.

---

# 60. Root-Cause Statement Contract

Final root cause must be one causal sentence:

```text
ROOT CAUSE:
[actor/component] performs [incorrect behavior] under [specific condition],
causing [failure mechanism] and producing [observed symptom].
```

Example:

```text
ROOT CAUSE:
The worker acknowledges the queue message before the database transaction commits,
so a retrying consumer can observe incomplete state and produce the duplicate-result
failure.
```

---

# 61. Patch Contract

Every proposed patch should answer:

```text
What invariant was violated?
Where was it violated?
Why does this change restore the invariant?
Why is this the smallest safe change?
How will the regression test detect recurrence?
What is the blast radius?
How can the change be rolled back?
```

If these cannot be answered, the patch is not ready.

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
