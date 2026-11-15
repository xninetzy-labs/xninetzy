# hebat-assignment — §13–19

Contents: 13. Phase 04 - EVIDENCE MAPPING; 14. Claim Contract; 15. Evidence Rule; 16. Source Priority; 17. Citation Integrity; 18. Research Boundary; 19. Research Workflow

## 13. Phase 04 - EVIDENCE MAPPING

Separate:

```text
CLAIM
EVIDENCE
INTERPRETATION
ASSUMPTION
RECOMMENDATION
LIMITATION
```

Never collapse these into one category.

For important claims:

```text
Claim
→ Source
→ Evidence
→ Interpretation
→ Artifact location
```

---

## 14. Claim Contract

Each important claim should have:

```yaml
claim:
  claim_id:
  text:
  type:
  source_refs: []
  evidence:
  interpretation:
  target_section:
  verification_status:
```

Claim types:

```text
FACT
INTERPRETATION
ASSUMPTION
RECOMMENDATION
LIMITATION
```

---

## 15. Evidence Rule

Evidence must actually support the attached claim.

Reject:

```text
citation exists
but source does not support the statement
```

Likewise reject:

```text
"research shows..."
```

without an identifiable source and relevant evidence.

---

## 16. Source Priority

Typical source priority:

```text
official institutional / government source
primary research
peer-reviewed literature
official dataset
official organizational documentation
professional organization
credible secondary analysis
reputable reference source
```

Authority is context-dependent.

A course brief may outrank an academic paper for determining what the assignment
requires.

An academic paper may outrank a blog for supporting an empirical claim.

---

## 17. Citation Integrity

For substantive citations:

```text
source exists
author/title/year are verified where required
claim is actually supported
citation style is correct
reference entry exists
reference entry maps to citation
```

Never fabricate:

```text
authors
papers
DOIs
URLs
publication dates
page numbers
datasets
statistics
quotes
```

If a source cannot be verified:

```text
UNVERIFIED_SOURCE
```

and do not present it as authoritative evidence.

---

## 18. Research Boundary

Research only what materially contributes to:

```text
assignment requirements
claims
analysis
decision
methodology
context
validation
```

Avoid:

```text
source accumulation
citation padding
irrelevant literature
search-snippet dependence
```

A source should have a purpose.

---

## 19. Research Workflow

When research is required:

```text
QUESTION
   ↓
SEARCH
   ↓
SOURCE EVALUATION
   ↓
EVIDENCE EXTRACTION
   ↓
SYNTHESIS
   ↓
CLAIM SUPPORT
   ↓
CITATION
```

Route complex research methodology to:

```text
xninetzy-deep-research
```

This skill consumes verified research outputs.

---
