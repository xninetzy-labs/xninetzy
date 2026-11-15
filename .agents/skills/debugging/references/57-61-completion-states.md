# debugging — §57–61

Contents: 57. Completion States; 58. Required Artifacts; 59. Compact Hypothesis Matrix; 60. Root-Cause Statement Contract; 61. Patch Contract

## 57. Completion States

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

## 58. Required Artifacts

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

## 59. Compact Hypothesis Matrix

Canonical human-readable form:

| ID | Hypothesis            | Supporting Evidence   | Refuting Evidence      | Controlled Test              | Status    | Confidence |
| -- | --------------------- | --------------------- | ---------------------- | ---------------------------- | --------- | ---------- |
| H1 | missing normalization | null at boundary      | none                   | bypass/restore normalization | SUPPORTED | HIGH       |
| H2 | cache corruption      | stale value observed  | fresh read still fails | cache off/on                 | FALSIFIED | LOW        |
| H3 | race condition        | intermittent failures | fails at concurrency 1 | concurrency sweep            | WEAKENED  | LOW        |

Do not remove falsified hypotheses from the audit trail.

---

## 60. Root-Cause Statement Contract

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

## 61. Patch Contract

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
