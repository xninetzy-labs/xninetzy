# hebat-assignment — §33–39

Contents: 33. Phase 10 - QA; 34. QA Severity; 35. QA Loop; 36. Evidence Freshness; 37. Assumption Policy; 38. Scope Drift; 39. Requirement Drift

## 33. Phase 10 - QA

Use separate QA passes.

```text
CONTENT QA
STRUCTURAL QA
VISUAL QA
TECHNICAL QA
CITATION QA
SUBMISSION QA
```

Do not collapse all checks into "looks good."

---

## 34. QA Severity

### Critical

Blocks submission.

Examples:

```text
missing mandatory requirement
fabricated source
wrong assignment format
corrupted file
unreadable pages
missing required evidence
broken required artifact
```

### Major

Potentially affects grading or materially reduces validity.

Examples:

```text
unsupported central claim
missing rubric criterion
serious table/figure failure
incorrect analysis
broken required link
major page overflow
inconsistent conclusion
```

### Minor

Non-material defect.

Examples:

```text
small spacing issue
minor alignment inconsistency
non-critical typography issue
```

Readiness rule:

```text
Critical = 0
Major = 0
Minor = acceptable when non-material
```

---

## 35. QA Loop

After meaningful corrections:

```text
FIX
→ REBUILD
→ REVALIDATE
→ RECHECK
```

Do not assume a correction is isolated.

A content change may affect:

```text
page count
figure references
conclusion
citations
table numbering
visual layout
```

A layout change may affect:

```text
readability
pagination
caption placement
page count
```

---

## 36. Evidence Freshness

Completion evidence must belong to the intended:

```text
assignment version
artifact version
dataset
environment
source set
```

Do not use old evidence after materially changing the artifact unless the evidence
remains valid.

---

## 37. Assumption Policy

Classify assumptions:

```text
LOW_IMPACT
MATERIAL
UNSAFE
```

Low-impact assumptions may be stated and used consistently.

Material assumptions require:

```text
validation
explicit acceptance
or clarification
```

Unsafe assumptions must not be operationalized.

Never fabricate evidence to satisfy an assumption.

---

## 38. Scope Drift

Detect when production expands beyond:

```text
target
assignment scope
required artifact
deadline
approved constraints
```

When scope expands materially:

```text
STOP
→ REPORT SCOPE DELTA
→ RECONCILE REQUIREMENTS
→ UPDATE ARTIFACT SPECIFICATION
```

Do not silently broaden the assignment.

---

## 39. Requirement Drift

If current work no longer matches the current requirement contract:

```text
REQUIREMENT_DRIFT
```

Re-check:

```text
brief
rubric
lecturer instructions
artifact specification
current work
```

Do not optimize the artifact against an obsolete interpretation.

---
