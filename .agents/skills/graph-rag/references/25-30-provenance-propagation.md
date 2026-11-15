# graph-rag — §25–30

Contents: 25. Provenance Propagation; 26. Temporal Validity; 27. Temporal Queries; 28. Contradiction Model; 29. Contradiction Resolution; 30. Contradiction Output

## 25. Provenance Propagation

Derived reasoning should not inherit the strongest evidence level automatically.

Example:

```text id="m7x2q9"
Edge A:
STRONG

Edge B:
MODERATE

Path A → B:
derived confidence cannot simply become STRONG.
```

Path confidence must account for:

```text id="w4n8p2"
weakest edge
identity confidence
evidence freshness
relation semantics
path length
contradictions
```

---

## 26. Temporal Validity

Relationships may change over time.

Represent:

```yaml id="s9q3m7"
validity:
  valid_from:
  valid_until:
  observed_at:
```

Examples:

```text id="q4x8m1"
Course A prerequisite_of Course B
valid in curriculum 2026

Project depends_on Service X
valid before migration
```

Never treat a historical relationship as current without checking temporal scope.

---

## 27. Temporal Queries

When the question is time-sensitive:

```text id="n2m7x5"
"What currently depends on X?"
```

prefer currently valid edges.

For:

```text id="c8q4r1"
"What depended on X in 2024?"
```

filter by historical validity.

Temporal state must not be silently collapsed.

---

## 28. Contradiction Model

The graph should support contradictory evidence.

Example:

```text id="v5x1m8"
A ── PREREQUISITE_OF ──> B

Source 1:
supports

Source 2:
contradicts
```

Do not overwrite one source merely because another source is newer unless the
domain's authority policy explicitly requires replacement.

Represent:

```text id="k2q7n4"
SUPPORTED
CONTRADICTED
CONTESTED
UNKNOWN
```

---

## 29. Contradiction Resolution

Compare:

```text id="m6r3p8"
source authority
temporal validity
specificity
directness
independent confirmation
domain ownership
```

A current authoritative source may supersede an older weaker source.

This must be expressed as provenance/state, not silent deletion of history.

---

## 30. Contradiction Output

When contradiction materially affects the answer:

```text id="x9n4c2"
Relationship:
Course A → prerequisite_of → Course B

Evidence:
Source A supports it.
Source B conflicts with it.

Current authoritative status:
[verified / contested / unresolved]
```

Do not hide contradictory evidence to produce a cleaner answer.

---
