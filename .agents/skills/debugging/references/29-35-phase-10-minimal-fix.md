# debugging — §29–35

Contents: 29. Phase 10 — MINIMAL FIX; 30. Fix Design Contract; 31. Minimality Rule; 32. Patch Evidence; 33. Phase 11 — REGRESSION TEST; 34. Regression Quality; 35. Manual Verification

## 29. Phase 10 — MINIMAL FIX

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

## 30. Fix Design Contract

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

## 31. Minimality Rule

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

## 32. Patch Evidence

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

## 33. Phase 11 — REGRESSION TEST

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

## 34. Regression Quality

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

## 35. Manual Verification

Manual verification is useful for exploratory debugging.

It is not sufficient as the only regression protection for a software defect.

Required sequence:

```text
manual observation
+
automated regression where feasible
```

---
