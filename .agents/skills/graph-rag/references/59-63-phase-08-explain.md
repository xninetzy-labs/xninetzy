# graph-rag — §59–63

Contents: 59. Phase 08 — EXPLAIN; 60. Answer Structure; 61. Fact / Derivation / Inference Labels; 62. Phase 09 — VERIFY; 63. Projection Verification

## 59. Phase 08 — EXPLAIN

Important graph reasoning should be path-transparent.

Preferred rendering:

```text id="q3m8x1"
Goal
  └─ requires → Skill
       Evidence: source A

Skill
  └─ taught_by → Course
       Evidence: source B

Therefore:
the course provides a supported learning path toward the goal.
```

Each meaningful edge must be inspectable.

---

## 60. Answer Structure

For relational questions:

```text id="x7q2m5"
Answer
↓
Relevant Path / Neighborhood
↓
Evidence
↓
Confidence
↓
Contradictions / Gaps
↓
Implication
```

Do not expose the entire graph unless requested.

---

## 61. Fact / Derivation / Inference Labels

Use explicit labels when useful:

```text id="m8x4p1"
FACT
directly represented by validated graph evidence

DERIVED
computed from validated graph relationships

INFERRED
plausible interpretation requiring assumptions

UNKNOWN
not established
```

This prevents graph reasoning from appearing more certain than its evidence.

---

## 62. Phase 09 — VERIFY

Before returning a consequential graph conclusion:

```text id="r5m7q3"
entity identity
edge validity
evidence
temporal validity
projection state
contradiction status
```

must be considered.

For graph writes:

```text id="c8x2n6"
canonical state
→ projection state
```

must be verified separately.

---

## 63. Projection Verification

After a write:

```text id="p2m9x4"
canonical graph
    ↓
projection refresh
    ↓
projection read-back
```

Possible result:

```text id="v7q3k1"
SYNCED
PENDING
FAILED
UNKNOWN
```

Never report:

```text id="a5x8m2"
"graph updated everywhere"
```

merely because the canonical transaction succeeded.

---
