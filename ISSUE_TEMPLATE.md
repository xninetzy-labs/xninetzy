# Issue Template — Xninetzy

Copy this template into `KNOWN_ISSUES.md` for each new issue.

```markdown
## ISS-YYYYMMDD-NN — <title>

**Severity:** CRITICAL | HIGH | MEDIUM | LOW
**Status:** OPEN | IN_PROGRESS | BLOCKED | RESOLVED | CLOSED
**Owner:** <handle or "TBD">
**Filed:** YYYY-MM-DD
**Resolution pointer:** <commit SHA, PR link, or "n/a">

### Summary
One-paragraph description of the problem.

### Reproduction
Steps to reproduce (or "observed in audit YYYY-MM-DD").

### Verification
How to verify the fix (test name, command, or grep query).

### Blocker (if status = BLOCKED)
What is blocking resolution; who can unblock.

### Resolution
Free-form description of what was done. Cross-reference commit SHAs.
```

## ID convention

- `ISS-YYYYMMDD-NN` — date + zero-padded sequence per day.
- IDs are stable; never reuse even if the issue is closed.
- Reference in commit messages: `Refs ISS-YYYYMMDD-NN`.

## Status flow

```
OPEN → IN_PROGRESS → BLOCKED → IN_PROGRESS → RESOLVED → CLOSED
                  ↘ RESOLVED → CLOSED
```

`CLOSED` issues stay in `KNOWN_ISSUES.md` for history. Do not delete.
