# code-review — §55–59

Contents: 55. Confidence; 56. Finding Schema; 57. Finding Categories; 58. Review Comments; 59. Suggested Fixes

## 55. Confidence

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

## 56. Finding Schema

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

## 57. Finding Categories

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

## 58. Review Comments

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

## 59. Suggested Fixes

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
