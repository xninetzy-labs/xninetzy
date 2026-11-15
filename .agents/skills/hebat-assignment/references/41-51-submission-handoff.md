# hebat-assignment — §41–51

Contents: 41. Submission Handoff; 42. Completion States; 43. Final Assignment Result; 44. Submission Package Manifest; 45. Academic Integrity; 46. Claim Calibration; 47. Knowledge Integration; 48. Graph Integration; 49. Goal Integration; 50. Memory Integration; 51. Final Optimization Order

## 41. Submission Handoff

When the final assignment is ready for LMS submission:

```text
HEBAT ASSIGNMENT
      ↓
READY_TO_SUBMIT
      ↓
hebat-academic
      ↓
LMS submission workflow
      ↓
portal confirmation
```

Do not perform portal operations here when the owning skill is `hebat-academic`.

---

## 42. Completion States

Use:

```text
NOT_STARTED
IN_PROGRESS
PARTIAL
BLOCKED
REWORK_REQUIRED
READY_TO_SUBMIT
SUBMITTED
CONFIRMED
```

Only use:

```text
SUBMITTED
```

when actual submission evidence exists.

Only use:

```text
CONFIRMED
```

when the submission system verifies the resulting state.

---

## 43. Final Assignment Result

Canonical result:

```yaml
assignment_result:
  assignment_context:
  requirement_coverage:
  evidence_status:
  artifact:
  content_qa:
  structural_qa:
  visual_qa:
  technical_qa:
  citation_qa:
  submission_package:
  readiness_state:
  unresolved:
  next_action:
```

The result must distinguish:

```text
produced
validated
ready
submitted
confirmed
```

---

## 44. Submission Package Manifest

When multiple deliverables are required:

```yaml
submission_manifest:
  primary_artifact:
  supplementary_artifacts: []
  datasets: []
  links: []
  required_metadata: []
```

Verify the package against the assignment brief.

Do not include:

```text
temporary files
debug files
intermediate drafts
unused screenshots
internal notes
```

unless explicitly required.

---

## 45. Academic Integrity

The assignment system must preserve:

```text
source attribution
claim ownership
evidence provenance
student work context
```

Never fabricate:

```text
sources
experiments
field observations
interview participants
survey responses
datasets
results
citations
```

Do not represent generated content as observed evidence.

---

## 46. Claim Calibration

Match language strength to evidence strength.

Prefer:

```text
suggests
indicates
is consistent with
supports
```

when evidence is limited.

Use stronger language only when supported.

Avoid:

```text
proves
always
guarantees
the best
revolutionary
100% effective
```

without appropriate evidence.

---

## 47. Knowledge Integration

Valid sources may include:

```text
HEBAT materials
official course instructions
verified project context
personal knowledge base
academic literature
official institutional sources
datasets
field observations
verified artifacts
```

Use source precedence appropriate to the claim.

Personal knowledge never overrides current assignment requirements.

---

## 48. Graph Integration

When graph relationships materially improve reasoning, `graph-rag` may model:

```text
Requirement
  → requires →
Evidence

Claim
  → supported_by →
Source

Concept
  → applied_in →
Section

Rubric Criterion
  → validated_by →
Evidence

Artifact
  → satisfies →
Requirement
```

Graph edges remain evidence-backed.

Do not create relationships merely from semantic similarity.

---

## 49. Goal Integration

A significant assignment may define a goal first:

```text
define-goal
      ↓
validated assignment outcome
      ↓
hebat-assignment
```

The goal defines:

```text
what success is
```

This skill defines:

```text
how the assignment contract and evidence are organized
```

Do not duplicate long-term goal management here.

---

## 50. Memory Integration

Memory may provide:

```text
previous approved structure
known project context
reusable source mappings
previous QA lessons
```

Memory remains historical context.

Current authoritative assignment requirements win.

---

## 51. Final Optimization Order

Optimize in this order:

```text
1. Requirement compliance
2. Academic correctness
3. Evidence quality
4. Citation integrity
5. Argument quality
6. Structural clarity
7. Readability
8. Visual quality
9. Technical validity
10. Submission readiness
```

Do not optimize visual polish before compliance.

Do not increase citation count merely to appear academic.

Do not reduce readability to satisfy page count through arbitrary compression.

---
