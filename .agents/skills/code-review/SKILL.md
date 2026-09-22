---
name: "code-review"

description: "Evidence-driven pre-merge code review against the repository's declared rules, architecture, API contracts, security boundaries, tests, and engineering invariants. Reviews a branch, commit range, or pull request at file and symbol level; detects rule violations, behavior regressions, error-propagation problems, retry/idempotency defects, API contract drift, architecture/layer violations, security-sensitive changes, missing or misleading tests, dependency risk, observability gaps, and unnecessary scope expansion. Produces a diff-anchored, severity-tiered review with evidence, suggested fixes, coverage gaps, regression risks, and a deterministic review verdict. Never silently rewrites the patch."

metadata:
author: "xninetzy"
owner: "misbahul45"
version: "2.0.0"
scope: "domain"
priority: "P1"
domain: "xninetzy.domains.code-review"
lifecycle: >
discover -> diff -> rules -> context -> classify -> analyze ->
correlate -> test -> validate -> report -> verdict -> regress

required_tools:

* repo_diff
* repo_search
* repo_symbol
* repo_architecture

optional_tools:

* repo_test
* repo_dependency
* repo_history
* repo_ownership
* repo_risk
* security_sast
* security_api_inventory
* security_validate_finding
* lightning_record_action
* learning_attach_resource
* hitl_request_approval

trigger_conditions:

* a PR is about to be merged
* the operator asks to review a diff
* a feature branch is ready for QA
* an external contributor submits a patch
* a commit changes shared infrastructure
* an API contract changes
* authentication or authorization changes
* dependency versions change
* a large refactor is proposed
* the operator asks whether a change is ready

prerequisites:

* target diff reachable
* project rulebook loaded
* repository context available
* base and head identifiable
* applicable architecture rules available where possible

references:
architecture:
file: "../architecture-analysis/SKILL.md"
use_when:
- layering
- dependency direction
- module boundaries
- architecture drift
- refactor impact

security:
file: "../xninetzy-security-testing/SKILL.md"
use_when:
- auth/authz changes
- security-sensitive endpoints
- secrets
- SSRF
- injection
- security configuration
- live validation

api:
file: "../api-security/SKILL.md"
use_when:
- HTTP/API/MCP/WebSocket/gRPC changes
- auth contracts
- CORS
- rate limits
- schema changes

non_goals:

* automatic code rewriting
* automatic merge
* automatic architecture migration
* treating passing CI as proof of correctness
* generic style criticism without repository evidence
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

# 3. Review Target

Accept:

```text
PR
branch
commit
commit range
git diff
patch file
```

Normalize to:

```yaml
review_target:
  repository:
  base:
  head:
  merge_base:
  changed_files:
  changed_lines:
  generated_files:
```

Always establish the exact comparison:

```text
base...head
```

Do not accidentally review:

```text
working tree
```

when the user intended:

```text
branch vs main
```

---

# 4. Diff Integrity

Before review verify:

```text
base exists
head exists
merge base exists
diff is non-empty or explicitly expected
renames detected
deleted files detected
binary files detected
generated files classified
submodules classified
```

If the target diff is ambiguous:

```text
REVIEW_BLOCKED
```

Do not invent a comparison.

---

# 5. Rulebook Loading

Load applicable project rules before judging code.

Possible sources:

```text
AGENTS.md
CLAUDE.md
CONTRIBUTING.md
README.md
workspace rules
package-level rules
directory-local rules
CI rules
lint configuration
formatter configuration
architecture contracts
security policies
API contracts
```

Rule precedence:

```text
explicit local project rule
    >
parent project rule
    >
architecture contract
    >
CI/tool configuration
    >
repository conventions
    >
general engineering best practice
```

Where a higher-level repository rule explicitly establishes a stronger requirement,
apply it.

---

# 6. Rule Scope

Rules may be:

```text
repository-wide
workspace-wide
package-specific
directory-specific
file-specific
language-specific
generated-code-specific
test-specific
```

A rule must only apply where its scope is valid.

Do not flag a file using a rule from an unrelated package.

---

# 7. Rule Conflict

If two rules conflict:

```text
identify both
identify scope
identify precedence
report conflict
```

Do not silently choose.

Example:

```text
workspace:
  no comments

generated package:
  generated files may contain comments
```

The more specific applicable rule wins when project policy says so.

---

# 8. Change Classification

Classify the diff:

```text
FEATURE
BUGFIX
REFACTOR
PERFORMANCE
SECURITY
API_CHANGE
CONFIG_CHANGE
DEPENDENCY_CHANGE
DATABASE_CHANGE
INFRASTRUCTURE_CHANGE
TEST_ONLY
DOCUMENTATION
GENERATED_CODE
MIXED
```

A patch may have multiple classifications.

Example:

```text
FEATURE
+
API_CHANGE
+
AUTHORIZATION_CHANGE
```

---

# 9. Change Surface

Determine:

```text
changed files
changed symbols
changed modules
changed packages
changed public APIs
changed dependencies
changed configuration
changed persistence
changed network behavior
changed authentication
changed authorization
```

Output:

```yaml
change_surface:
  files:
  symbols:
  modules:
  packages:
  public_api:
  persistence:
  network:
  security:
  dependencies:
```

---

# 10. Behavior Delta

Do not review only syntax.

Determine:

```text
before
vs
after
```

for:

```text
inputs
outputs
side effects
state transitions
errors
retries
timeouts
authorization
dependencies
resource usage
```

Example:

```text
before:
POST /orders
  -> create one order

after:
POST /orders
  -> create order
  -> enqueue notification
  -> update analytics
```

This is a behavior expansion even if only ten lines changed.

---

# 11. Per-File Review

Every changed source file receives a review record.

```yaml
file_review:
  file:
  change_type:
  changed_lines:
  affected_symbols:
  applicable_rules:
  findings:
  test_evidence:
  risk:
```

Every actionable finding must point to:

```text
file:line
```

or:

```text
file:symbol
```

and include supporting repository evidence when the issue depends on broader context.

---

# 12. Diff Anchoring

Required anchor:

```text
file_path:line_number
```

Preferred:

```text
file_path:line_number
symbol_name
```

For deleted code:

```text
file_path:old_line_number
```

For cross-file findings:

```text
changed_file:line
+
related_file:line
```

Never produce:

```text
"This part seems wrong."
```

without a location.

---

# 13. Deleted-Code Analysis

Deletion deserves independent analysis.

Check whether deleted code represented:

```text
validation
authorization
logging
cleanup
retry
timeout
transaction boundary
security header
test coverage
error handling
```

A removal can be a regression even when the replacement code is clean.

---

# 14. Added-Code Analysis

Added code is checked for:

```text
new state
new dependency
new side effect
new public surface
new external call
new permission
new config
new persistence
new concurrency
```

---

# 15. Modified-Code Analysis

For modified symbols compare:

```text
precondition
postcondition
invariants
error behavior
side effects
call graph
```

Do not assume the function's old behavior remains unchanged merely because
the signature did not change.

---

# 16. Naming

Check repository naming conventions for:

```text
variables
functions
classes
types
files
modules
commands
routes
constants
environment variables
tests
```

Do not flag naming merely because it differs from generic language conventions.

The project convention is authoritative.

---

# 17. Naming Semantics

Check whether names accurately describe behavior.

Potential issue:

```text
getUser()
```

actually:

```text
updates user
```

or:

```text
validate()
```

actually:

```text
normalizes + persists
```

Misleading names are especially important for:

```text
side effects
security
writes
network operations
transactions
```

---

# 18. No-Comment Rules

If the project forbids source comments:

```text
flag newly introduced comments
```

including:

```text
inline comments
block comments
temporary comments
TODO comments
debug comments
```

Do not flag:

```text
LICENSE headers
required generated-code headers
configuration where the project explicitly permits them
```

unless the rulebook says otherwise.

Finding should cite the exact project rule.

---

# 19. Error Propagation

Trace:

```text
error source
   ↓
catch
   ↓
transform
   ↓
return
```

Check for:

```text
swallowed errors
empty catch blocks
incorrect fallback
generic error replacement
lost context
incorrect status mapping
partial failure hidden as success
```

Potential anti-pattern:

```text
try:
   operation()
catch:
   return []
```

if callers interpret:

```text
[]
```

as:

```text
successful empty result
```

---

# 20. Error Contract

For each changed public operation identify:

```text
success state
failure states
retryable errors
non-retryable errors
user-visible errors
internal errors
```

Verify that the patch preserves the contract.

---

# 21. Silent Retry Detection

Flag retries that are:

```text
implicit
unbounded
non-deterministic
hidden from callers
```

Check:

```text
max attempts
backoff
timeout
retryable error classification
idempotency
observability
```

Never approve:

```text
while true:
    request()
```

without explicit project-approved semantics.

---

# 22. Retry Safety

A retry is only safe when:

```text
operation is idempotent
OR
idempotency key exists
OR
duplicate side effects are explicitly prevented
```

Examples of dangerous retries:

```text
payment
create resource
send notification
publish event
charge account
enqueue job
```

---

# 23. Idempotency

For every changed write operation ask:

```text
Can the same request execute twice?
```

Check:

```text
PUT
PATCH
POST
DELETE
queue operations
background jobs
webhooks
scheduled jobs
```

Evidence:

```text
idempotency key
unique constraint
transaction boundary
deduplication key
upsert
state check
```

A function named `create` is not automatically non-idempotent or idempotent;
inspect implementation.

---

# 24. Transaction Boundaries

Where state changes are introduced, inspect:

```text
database write
+
external side effect
```

Potential issue:

```text
database commit
    ↓
external API fails
```

or:

```text
external side effect
    ↓
database rollback
```

Check whether the architecture provides:

```text
transaction
outbox
saga
compensation
retry policy
idempotency
```

Do not demand distributed transactions where the project architecture intentionally
uses another consistency model.

---

# 25. Concurrency / Race Analysis

When changes involve shared state, inspect:

```text
parallel requests
async tasks
workers
queues
locks
caches
transactions
```

Potential classes:

```text
TOCTOU
duplicate creation
lost update
double processing
race on authorization
race on cache state
```

Evidence should cite:

```text
shared resource
read
write
synchronization boundary
```

---

# 26. Layer Boundary

Use:

```text
repo_architecture
```

and companion:

```text
architecture-analysis
```

Check:

```text
presentation
application
domain
infrastructure
data
integration
```

for direction violations.

Every violation should identify:

```text
source module
target module
import/call
expected direction
```

---

# 27. Architecture Drift

A diff may introduce:

```text
new cycle
new cross-layer edge
new cross-feature dependency
new framework leak
new direct DB access
new shared-module dependency
```

Compare:

```text
before graph
vs
after graph
```

Flag only newly introduced or materially worsened drift unless the review explicitly
requests legacy architecture analysis.

---

# 28. Dependency Direction

Check:

```text
consumer
producer
dependency type
layer
```

Potential issue:

```text
domain
  -> infrastructure
```

or:

```text
core
  -> feature-specific implementation
```

Do not propose an abstraction until the actual dependency is understood.

---

# 29. API Contract

For API changes inspect:

```text
route
method
request schema
response schema
authentication
authorization
status codes
error shape
pagination
headers
rate limits
```

Use:

```text
api-security
```

when the change materially affects API security.

---

# 30. API Compatibility

Classify changes:

```text
BACKWARD_COMPATIBLE
POTENTIALLY_BREAKING
BREAKING
UNKNOWN
```

Examples:

```text
new optional response field
  -> usually compatible

remove response field
  -> potentially breaking

make optional field required
  -> potentially breaking

change enum semantics
  -> potentially breaking
```

Do not call a change breaking without consumer evidence or a clearly defined contract.

---

# 31. Public API Expansion

Check whether the patch accidentally exports:

```text
internal symbol
debug endpoint
implementation detail
database type
framework object
credential-bearing object
```

Compare:

```text
before exports
vs
after exports
```

---

# 32. Authentication Review

When auth changes, verify:

```text
authentication mechanism
credential extraction
token validation
issuer
audience
expiration
revocation
session lifecycle
```

Check all callers and affected routes.

Do not consider:

```text
middleware added
```

equivalent to:

```text
authentication enforced correctly
```

---

# 33. Authorization Review

When access control changes, build:

```text
actor
role
resource
action
tenant
```

matrix.

Check for:

```text
BOLA
function-level authorization
property-level authorization
tenant bypass
privilege escalation
```

Use `api-security` where the changed surface is an API endpoint.

---

# 34. Input Validation

Check changed inputs:

```text
path
query
headers
body
files
MCP arguments
WebSocket messages
gRPC fields
```

Trace:

```text
input
 ↓
parser
 ↓
validator
 ↓
business logic
 ↓
sink
```

Potential issues:

```text
missing validation
wrong validator
validation after dangerous sink
validation mismatch
unexpected fields
unsafe defaults
```

---

# 35. Security-Sensitive Sinks

When changed code reaches:

```text
SQL
shell
filesystem
template
HTML
URL fetch
HTTP client
deserialization
command execution
authorization
```

perform deeper analysis.

Where available:

```text
security_sast
```

should corroborate source-to-sink findings.

---

# 36. Secrets

Detect newly introduced:

```text
API key
token
password
private key
cloud credential
database credential
service credential
```

Use:

```text
Gitleaks
Trivy
security_sast
```

Never put secret contents in the review.

Show:

```text
file
line
secret type
redacted evidence
```

---

# 37. Dependencies

When dependency files change:

```text
package.json
package-lock.json
pnpm-lock.yaml
Cargo.lock
Cargo.toml
pyproject.toml
requirements.txt
go.mod
go.sum
```

check:

```text
direct dependency
transitive dependency
version change
license
known vulnerability
runtime/build scope
```

Where available use:

```text
repo_dependency
OSV
Trivy
dep-scan
```

Do not report a dependency as vulnerable without identifying the actual version.

---

# 38. Configuration Changes

Review changes to:

```text
environment variables
feature flags
timeouts
rate limits
CORS
headers
TLS
logging
database
queues
storage
container
deployment
```

Potential issue:

```text
secure default
  ↓
insecure default
```

or:

```text
production-safe configuration
  ↓
developer convenience default
```

---

# 39. Observability

A behavior change should preserve sufficient observability.

Check:

```text
logs
metrics
traces
request IDs
audit events
error context
```

Particularly for:

```text
auth
billing
security
state transitions
background jobs
external integrations
```

Do not request sensitive payloads simply to improve logging.

---

# 40. Test Analysis

Use:

```text
repo_test
```

where available.

Determine:

```text
tests added
tests modified
tests removed
tests covering changed behavior
tests covering failure paths
regression coverage
integration coverage
authorization coverage
```

Passing tests are evidence of tested behavior, not proof of complete correctness.

---

# 41. Coverage Delta

Required:

```yaml
coverage:
  lines_added:
  lines_changed:
  lines_covered:
  coverage_pct:
  baseline_coverage_pct:
  delta:
```

If exact coverage is unavailable:

```text
UNKNOWN
```

Do not invent coverage percentages.

---

# 42. Test Adequacy

A change should have tests proportional to behavioral risk.

Examples:

```text
pure rename
  -> focused static check may suffice

new parser
  -> valid + invalid inputs

new auth rule
  -> allow + deny matrix

new retry
  -> retryable + non-retryable + exhaustion

new API endpoint
  -> success + validation + auth + error

new state transition
  -> valid + invalid transitions
```

---

# 43. Missing Tests

Do not flag:

```text
"no tests"
```

as automatically high severity.

Instead determine:

```text
risk
behavioral change
existing test architecture
testability
criticality
```

Possible severity:

```text
INFO
LOW
MEDIUM
HIGH
```

depending on evidence.

---

# 44. Regression Risk

Identify what can break outside the diff.

Use:

```text
repo_symbol
repo_dependency
repo_architecture
repo_diff
```

Trace:

```text
changed symbol
 ↓
direct callers
 ↓
indirect callers
 ↓
public APIs
 ↓
affected modules
```

Classify:

```text
LOCAL
MODERATE
WIDE
SYSTEMIC
UNKNOWN
```

---

# 45. Blast Radius

For shared code measure:

```text
fan_in
fan_out
affected callers
affected modules
public API count
```

A one-line change in a highly central module may deserve more scrutiny than
a large isolated refactor.

---

# 46. Backward Compatibility

Check:

```text
API
database schema
serialization
configuration
CLI
environment variables
events
queues
file formats
```

Possible change:

```text
compatible
migration_required
breaking
unknown
```

Do not assume all internal code can change freely when a public contract exists.

---

# 47. Database Changes

For migrations inspect:

```text
schema change
existing data
nullability
indexes
foreign keys
rollback
deployment ordering
application compatibility
```

Potential issue:

```text
application deploy
before
schema exists
```

or:

```text
schema removal
before
old application removed
```

Review migration sequencing.

---

# 48. Background Jobs

When queue/worker behavior changes inspect:

```text
job identity
retry
idempotency
visibility timeout
dead-letter behavior
ordering
duplicate execution
serialization
```

A worker may execute the same job more than once even if application code appears
single-shot.

---

# 49. Caching

Changes involving cache must evaluate:

```text
key
TTL
invalidation
scope
tenant
authorization
stale data
race
```

Potential security issue:

```text
tenant A
  ↓
cache key
  ↓
tenant B receives cached response
```

Cache correctness is part of authorization correctness when responses are
tenant-sensitive.

---

# 50. External Integrations

For new/changed calls to external services inspect:

```text
timeout
retry
rate limit
authentication
request size
response validation
error mapping
idempotency
failure mode
```

Do not assume the external API is always available or correct.

---

# 51. Scope Creep

Detect modifications unrelated to the stated change.

Example:

```text
feature:
add login endpoint

diff:
+ login endpoint
+ database migration
+ UI redesign
+ dependency replacement
+ unrelated formatter changes
```

Classify:

```text
SCOPE_EXPANSION
```

The finding should explain why the extra changes increase review uncertainty.

---

# 52. Generated Files

Classify generated files:

```text
generated
derived
manual
unknown
```

Do not repeatedly flag generated content when the repository expects generated
artifacts to be committed.

Instead review:

```text
generator source
```

when available.

---

# 53. Dependency Lockfile Integrity

When package manifest and lockfile both change:

```text
verify they represent the same dependency intent
```

Potential issue:

```text
package version:
A

lockfile:
B
```

or unexpected transitive changes.

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

# 55. Confidence

Every finding also has:

```text
HIGH
MEDIUM
LOW
```

Confidence reflects evidence quality, not severity.

Example:

```text
CRITICAL / LOW CONFIDENCE
```

means the potential impact is high but evidence is incomplete.

---

# 56. Finding Schema

```yaml
finding:
  id:
  file:
  line:
  symbol:
  severity:
  confidence:

  category:
  title:

  rule:
  evidence:
    diff:
    repository:
    history:
    test:

  behavior:
    before:
    after:

  impact:
  affected_modules:
  regression_risk:

  recommendation:
    summary:
    consumer:
    producer:
    boundary:

  validation:
    required:
    command_or_test:

  status:
    open
    accepted
    resolved
    false_positive
    needs_context
```

---

# 57. Finding Categories

Use stable categories:

```text
RULE_VIOLATION
CORRECTNESS
BUG
REGRESSION
ERROR_HANDLING
RETRY
IDEMPOTENCY
CONCURRENCY
API_CONTRACT
AUTHENTICATION
AUTHORIZATION
INPUT_VALIDATION
SECURITY
DEPENDENCY
CONFIGURATION
ARCHITECTURE
LAYERING
PERFORMANCE
OBSERVABILITY
TEST_GAP
COMPATIBILITY
DATABASE
MIGRATION
SCOPE
```

---

# 58. Review Comments

Each finding should be concise:

```text
Problem
Evidence
Why it matters
Suggested direction
Validation
```

Example:

```text
HIGH — Authorization regression

apps/api/projects.ts:84

`projectId` is now accepted without the ownership check previously present
in `projectService.update()`.

Evidence:
- previous branch checked `assertProjectOwner()`
- new path calls repository update directly
- `PATCH /projects/:id` remains user-accessible

Impact:
A user may update another user's project.

Suggested direction:
Restore the authorization check at the application boundary.

Validation:
Add own-project / other-project / admin regression cases.
```

Do not rewrite the function inside the review.

---

# 59. Suggested Fixes

A suggested fix should identify:

```text
where
what
why
```

Prefer:

```text
Consumer:
  src/application/order-service.ts

Boundary:
  application -> repository contract

Issue:
  application imports concrete database implementation

Suggested direction:
  preserve existing repository abstraction
```

Avoid vague:

```text
refactor this
add interface
clean up architecture
```

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

# 62. Unknown State

Use:

```text
UNKNOWN
```

when:

```text
dynamic behavior cannot be resolved
call graph incomplete
tests unavailable
architecture contract missing
runtime evidence unavailable
generated code hides implementation
external dependency behavior unknown
```

Unknown is not:

```text
safe
```

and not:

```text
bug
```

---

# 63. Review Coverage

Required coverage report:

```yaml
review_coverage:
  changed_files:
  files_reviewed:
  changed_symbols:
  symbols_reviewed:

  rules:
    loaded:
    applicable:
    checked:

  architecture:
    checked:

  api:
    checked:

  security:
    checked:

  tests:
    checked:

  dependencies:
    checked:
```

---

# 64. Diff Coverage

Required:

```text
lines_added
lines_deleted
lines_modified
files_added
files_deleted
files_modified
```

If test coverage data exists:

```text
lines_added
lines_covered
coverage_pct
```

Never estimate test coverage from test-file existence.

---

# 65. Review Completeness

A review is not complete merely because:

```text
lint passes
tests pass
typecheck passes
```

Those are evidence sources.

The reviewer must additionally examine:

```text
project rules
behavioral delta
architecture
API contracts
security boundaries
error propagation
retry/idempotency
regression surface
```

---

# 66. Tool Correlation

Preferred evidence combination:

```text
repo_diff
+
repo_symbol
+
repo_architecture
+
repo_dependency
+
repo_test
+
security tooling where applicable
```

Example:

```text
repo_diff:
  middleware removed

repo_symbol:
  endpoint has direct repository call

repo_architecture:
  endpoint bypasses application service

repo_test:
  no authorization regression test

=> correlated HIGH finding
```

One scanner alert should not automatically become a merge blocker.

---

# 67. Security Handoff

Trigger `xninetzy-security-testing` or `api-security` when the diff changes:

```text
authentication
authorization
session handling
API routes
input validation
URL fetching
file uploads
security headers
CORS
rate limits
crypto
secrets
permissions
MCP tools/resources
```

Do not duplicate deep security testing when the dedicated security skill should own it.

The code review should surface the change and route it appropriately.

---

# 68. Architecture Handoff

Trigger `architecture-analysis` when the diff changes:

```text
module boundaries
shared packages
dependency direction
service communication
repository/data layer
framework boundaries
workspace topology
```

The code review should report relevant architectural consequences while leaving
full architecture analysis to the architecture skill.

---

# 69. API Handoff

Trigger `api-security` when the diff changes:

```text
HTTP route
REST endpoint
GraphQL resolver
gRPC method
WebSocket channel
MCP tool/resource
auth middleware
CORS
rate limit
API schema
```

---

# 70. Review Order

Use:

```text
1. scope
2. rules
3. correctness
4. security
5. architecture
6. API/contract
7. reliability
8. dependency/config
9. tests
10. regression
11. report
12. verdict
```

Do not begin by nitpicking formatting while a critical correctness issue remains
unresolved.

---

# 71. Priority Ordering

Within the review:

```text
BLOCKER
CRITICAL
HIGH
MEDIUM
LOW
INFO
```

and within the same severity:

```text
security
correctness
data integrity
authorization
API compatibility
reliability
architecture
maintainability
style
```

---

# 72. Review Noise Control

Do not generate findings for:

```text
unchanged legacy issues
known accepted risks
generated code
irrelevant formatting
personal style preference
```

unless the operator explicitly requested a broader repository audit.

The default review is:

```text
change-focused
```

not:

```text
whole-repository cleanup
```

---

# 73. Existing Problems

If an issue predates the patch:

```text
PRE_EXISTING
```

Do not classify it as introduced by the patch.

If the patch worsens it:

```text
REGRESSION
```

If the patch merely exposes it:

```text
EXPOSED_EXISTING_ISSUE
```

---

# 74. Fix Validation

When a finding is marked fixed:

```text
load original evidence
↓
inspect new diff
↓
run targeted regression
↓
compare behavior
```

Possible results:

```text
FIXED
PARTIALLY_FIXED
UNCHANGED
REGRESSED
UNCERTAIN
```

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

# 76. Per-File Summary

Required table:

```text
| File | Change | Findings | Risk | Test Evidence |
|---|---|---:|---|---|
| src/api/users.ts | modified | 2 | HIGH | partial |
| src/domain/user.ts | modified | 0 | LOW | strong |
| tests/users.test.ts | added | 0 | LOW | strong |
```

---

# 77. Positive Evidence

The review should also record meaningful evidence that supports the change:

```text
existing invariant preserved
regression test added
authorization matrix covered
error handling improved
dependency removed
architecture boundary preserved
idempotency improved
```

Do not let the report become only a list of problems.

---

# 78. Final Review Example

```text
Target:
main...feature/auth-refactor

Summary:
12 files changed
3 modules affected
1 public API changed
1 authentication boundary changed

Findings:

HIGH — AUTHORIZATION
apps/api/projects.ts:84

The new update path bypasses project ownership validation.

MEDIUM — TEST_GAP
tests/projects.test.ts

The changed authorization path has no other-user regression case.

LOW — RULE_VIOLATION
apps/api/projects.ts:91

Introduces an inline source comment, prohibited by project rule §4.

Architecture:
No new layer violation.

API:
PATCH /projects/:id response unchanged.

Coverage:
Added lines: 142
Covered lines: 119
Coverage: 83.8%

Verdict:
REQUEST_CHANGES
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

# 80. Final Principle

The code review engine should behave like:

```text
DIFF ANALYZER
+
RULE ENFORCER
+
BEHAVIOR REVIEWER
+
ARCHITECTURE REVIEWER
+
SECURITY ROUTER
+
TEST / REGRESSION ANALYZER
```

not:

```text
STYLE LINTER
```

The quality bar is:

```text
diff evidence
+
repository context
+
project rules
+
behavioral reasoning
+
architecture evidence
+
security evidence
+
test evidence
+
regression analysis
```

A strong review does not merely say:

```text
"LGTM"
```

or:

```text
"fix this"
```

It explains:

```text
what changed
why it matters
what evidence supports the finding
what boundary is affected
what should change
how the fix can be verified
```

## and gives a deterministic verdict based on the repository's actual merge policy.
