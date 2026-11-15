# code-review — §72–74

## 72. Review Noise Control

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

## 73. Existing Problems

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

## 74. Fix Validation

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
