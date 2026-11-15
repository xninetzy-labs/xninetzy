# hebat-assignment — §6–12

Contents: 6. Phase 01 - DISCOVER; 7. Phase 02 - CONTEXT BINDING; 8. Phase 03 - REQUIREMENTS LOCK; 9. Requirement Traceability Matrix; 10. Requirement Coverage; 11. Requirement Types; 12. Requirement Ambiguity

## 6. Phase 01 - DISCOVER

Determine:

```text
assignment identity
course
semester/period
lecturer
student/team context
assignment type
deadline
submission channel
current authoritative sources
```

Collect candidate sources:

```text
assignment brief
course contract
rubric
lecturer instructions
HEBAT material
weekly instruction
official template
official example
verified project context
```

Do not start drafting before the relevant authoritative context is identified.

---

## 7. Phase 02 - CONTEXT BINDING

Bind the assignment to:

```yaml
assignment_context:
  assignment_id:
  course:
  academic_period:
  lecturer:
  team_mode:
  title:
  type:
  deadline:
  submission_channel:
  authoritative_sources: []
```

When an institutional identifier is unavailable, preserve:

```text
UNKNOWN
```

rather than guessing.

---

## 8. Phase 03 - REQUIREMENTS LOCK

Build the requirement contract before substantial production.

Each requirement should be represented conceptually as:

```yaml
requirement:
  requirement_id:
  statement:
  source:
  authority:
  interpretation:
  mandatory:
  artifact_location:
  evidence_required:
  validator:
  status:
```

Possible status:

```text
MISSING
PLANNED
IN_PROGRESS
SATISFIED
VERIFIED
BLOCKED
CONFLICTING
NOT_APPLICABLE
```

---

## 9. Requirement Traceability Matrix

Canonical structure:

| ID | Requirement | Authority | Source | Interpretation | Artifact Location | Evidence | Validator | Status   |
| -- | ----------- | --------- | ------ | -------------- | ----------------- | -------- | --------- | -------- |
| R1 | ...         | Brief     | B1     | ...            | Section 2         | S3       | QA-01     | VERIFIED |

Every material requirement must map to:

```text
artifact location
+
evidence
+
validator
```

A requirement that exists only in notes is not considered covered.

---

## 10. Requirement Coverage

Coverage should be computed from mandatory requirements.

Conceptually:

```text
requirement_coverage =
verified_mandatory_requirements
/
total_mandatory_requirements
```

For submission readiness:

```text
mandatory requirement coverage = 100%
```

unless the user explicitly accepts an incomplete submission.

Do not inflate coverage by marking unclear requirements as satisfied.

---

## 11. Requirement Types

Classify requirements when useful:

```text
CONTENT
STRUCTURE
EVIDENCE
METHOD
FORMAT
VISUAL
FILE
LINK
CITATION
TEAM
DEADLINE
SUBMISSION
```

This prevents content compliance from masking structural or submission failures.

---

## 12. Requirement Ambiguity

Use:

```text
UNAMBIGUOUS
PARTIALLY_AMBIGUOUS
MATERIALLY_AMBIGUOUS
CONFLICTING
UNKNOWN
```

A materially ambiguous requirement must be clarified before finalization when it
could change:

```text
graded content
artifact type
scope
methodology
required evidence
format
submission route
deadline interpretation
```

---
