# hebat-assignment — §20–25

Contents: 20. Phase 05 - ARGUMENT FORMULATION; 21. Section Purpose; 22. Argument Quality; 23. Phase 06 - ARTIFACT SPECIFICATION; 24. Structure Before Styling; 25. Artifact Types

## 20. Phase 05 - ARGUMENT FORMULATION

Before writing polished prose, determine the argument architecture.

Typical structure:

```text
Problem
  ↓
Context
  ↓
Evidence
  ↓
Analysis
  ↓
Implication
  ↓
Response / Proposal
  ↓
Limitation
  ↓
Conclusion
```

Adapt the structure to the actual assignment.

Do not force every assignment into a generic academic-paper structure.

---

## 21. Section Purpose

Every major section should have a purpose:

```yaml
section:
  id:
  title:
  purpose:
  requirements:
  claims:
  evidence_refs:
  expected_artifact:
```

Reject sections that exist only because they "look academic" when they add no
assignment value.

---

## 22. Argument Quality

A strong section generally follows:

```text
CLAIM
→ EXPLANATION
→ EVIDENCE
→ INTERPRETATION
→ RELEVANCE
```

Do not stack quotations without analysis.

The assignment should demonstrate:

```text
understanding
reasoning
application
connection to course concepts
evidence-backed interpretation
```

---

## 23. Phase 06 - ARTIFACT SPECIFICATION

Before generation, define an artifact specification.

Minimum:

```yaml
artifact_spec:
  type:
  audience:
  purpose:
  required_sections: []
  required_evidence: []
  required_visuals: []
  format:
  page_or_word_constraints:
  citation_style:
  typography:
  layout:
  filename:
  submission_format:
  submission_channel:
```

The artifact specification must trace back to the requirement matrix.

---

## 24. Structure Before Styling

Determine:

```text
information architecture
content hierarchy
section order
evidence placement
figure/table placement
navigation
```

before:

```text
colors
typography
decorative elements
```

Content structure is upstream of visual design.

---

## 25. Artifact Types

### Document

Typical pattern:

```text
Cover
→ Context / Introduction
→ Main Analysis
→ Evidence
→ Discussion
→ Conclusion
→ References
→ Appendix
```

Only include required or materially useful sections.

### Presentation

Typical pattern:

```text
Context
→ Problem
→ Evidence
→ Analysis
→ Response
→ Validation
→ Conclusion
```

### Poster / Infographic

Typical pattern:

```text
Headline
→ Problem
→ Evidence
→ Key Insight
→ Response
→ Impact
→ Sources
```

### Prototype Documentation

Typical pattern:

```text
Problem
→ User / Context
→ Requirements
→ Design
→ Prototype
→ Validation
→ Limitations
→ Link / Artifact
```

Adapt to the brief.

---
