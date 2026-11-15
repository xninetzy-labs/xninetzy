# xninetzy-artifact-orchestrator — §17–21

Contents: 17. Phase 05 — SOURCE; 18. Phase 06 — ARCHITECT; 19. Section Contract; 20. Bounded Production; 21. Section Ownership

## 17. Phase 05 — SOURCE

Establish source/evidence inputs before long-form production.

For each source determine:

```text
identity
authority
relevance
verification
intended usage
```

Do not collect large amounts of source material without mapping it to an actual
artifact need.

---

## 18. Phase 06 — ARCHITECT

Define information architecture before detailed production.

For documents:

```text
Cover
→ Navigation / TOC when required
→ Main Content
→ Evidence
→ Discussion / Analysis
→ Conclusion
→ References
→ Appendix
```

For presentations:

```text
Opening
→ Context
→ Problem
→ Evidence
→ Insight
→ Response
→ Validation
→ Closing
```

For spreadsheets:

```text
Input
→ Transformation
→ Calculation
→ Validation
→ Summary
→ Visualization
```

For diagrams:

```text
Scope
→ Entities
→ Relationships
→ Flow
→ Legend
→ Evidence
```

These are defaults, not mandatory structures.

---

## 19. Section Contract

Every substantial unit should have:

```yaml
unit:
  unit_id:
  purpose:
  requirements: []
  evidence_refs: []
  content_scope:
  output:
  validator:
  status:
```

Units may be:

```text
section
chapter
slide group
sheet
figure
table
appendix
diagram component
```

---

## 20. Bounded Production

Long artifacts should be produced in bounded units.

Benefits:

```text
context control
lower repetition
easier validation
parallelization
smaller revisions
better failure isolation
```

Do not generate a large artifact as one uncontrolled context block when the
artifact naturally decomposes into independent units.

---

## 21. Section Ownership

For collaborative production:

```yaml
section_owners:
  introduction:
  research:
  methodology:
  analysis:
  conclusion:
```

Ownership means:

```text
responsible for local correctness
```

It does not remove:

```text
global integration responsibility
```

---
