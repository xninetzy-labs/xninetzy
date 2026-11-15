# code-review — §62–71

Contents: 62. Unknown State; 63. Review Coverage; 64. Diff Coverage; 65. Review Completeness; 66. Tool Correlation; 67. Security Handoff; 68. Architecture Handoff; 69. API Handoff; 70. Review Order; 71. Priority Ordering

## 62. Unknown State

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

## 63. Review Coverage

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

## 64. Diff Coverage

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

## 65. Review Completeness

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

## 66. Tool Correlation

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

## 67. Security Handoff

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

## 68. Architecture Handoff

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

## 69. API Handoff

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

## 70. Review Order

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

## 71. Priority Ordering

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
