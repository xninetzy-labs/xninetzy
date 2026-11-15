# code-review — §76–78

## 76. Per-File Summary

Required table:

```text
| File | Change | Findings | Risk | Test Evidence |
|---|---|---:|---|---|
| src/api/users.ts | modified | 2 | HIGH | partial |
| src/domain/user.ts | modified | 0 | LOW | strong |
| tests/users.test.ts | added | 0 | LOW | strong |
```

---

## 77. Positive Evidence

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

## 78. Final Review Example

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
