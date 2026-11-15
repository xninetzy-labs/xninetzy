# context-engineering — §34–39

Contents: 34. Compaction Record; 35. Context Debt; 36. Context Recompute Threshold; 37. Recompute Levels; 38. Context Invalidation; 39. Risk-Adaptive Context

## 34. Compaction Record

Create:

```yaml
context_compaction:
  before_tokens:
  after_tokens:
  removed:
  preserved:
  summary:
  references:
```

Compaction must be traceable.

Never silently delete important context.

---

## 35. Context Debt

Track repeated retrieval caused by poor context.

Example:

```text
same endpoint rediscovered 4 times
same architecture file retrieved 3 times
same memory repeated across turns
```

Create:

```text
CONTEXT_DEBT
```

Possible improvements:

```text
better cache key
better memory
better skill reference
better repository context package
better resolve command
```

---

## 36. Context Recompute Threshold

Do not rebuild every layer every turn.

Recompute only when:

```text
intent changed materially
target changed
scope changed
branch changed
major error occurred
new evidence contradicts active context
execution phase changed
tool capability changed
freshness expired
context confidence dropped
```

Default:

```text
L0 + L1
```

are recomputed every turn.

Other layers are reused until invalidated.

---

## 37. Recompute Levels

#### L0 Recompute

When user intent changes.

#### L1 Recompute

When immediate execution state changes.

#### L2 Recompute

When task/domain/tool requirements change.

#### L3 Recompute

When memory materially affects the current task or memory becomes stale.

#### L4 Recompute

When repository state/branch/diff changes.

#### L5 Recompute

When current task benefits from precedent or a new failure occurred.

#### L6 Recompute

When evidence is missing, stale, contradicted, or explicitly requested.

---

## 38. Context Invalidation

Invalidate context when:

```text
repository commit changes
branch changes
environment changes
target changes
authorization expires
user changes requirements
new dependency introduced
tool availability changes
```

Do not partially reuse invalid context without marking it.

---

## 39. Risk-Adaptive Context

Risk affects evidence requirements.

#### LOW

Use:

```text
L0
L1
L2
```

#### MEDIUM

Typically:

```text
L0-L4
```

#### HIGH

Typically:

```text
L0-L6
```

with stronger verification.

#### CRITICAL

Require:

```text
explicit evidence sufficiency
source-of-truth verification
contradiction resolution
approval when applicable
```

Do not let risk level increase tool authority.

---
