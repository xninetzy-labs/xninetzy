# Xninetzy Assignment Orchestrator — Validation, Submission, and Completion

This reference expands content validation, rubric validation, reproducibility, artifact QA, visual QA, assignment QA matrix, submission readiness states, preview, revalidation, verification, failure handling, completion definitions, and the standard output. Read it when validating, preparing submission, or finalizing an assignment.

## Content validation

Every requirement should have a validator.

### Writing

* section exists,
* argument addresses prompt,
* claims supported,
* conclusion reflects discussion.

### Calculation

* inputs verified,
* formula appropriate,
* calculation reproducible,
* result consistent with units,
* output independently checked where possible.

### Code

* tests pass,
* expected output verified,
* reproducible execution,
* relevant lint/type checks pass when required.

### Prototype

* required screens exist,
* required interactions work,
* links are accessible,
* design matches requirements.

### Spreadsheet

* formulas valid,
* totals reconcile,
* required sheets exist,
* source data traceable.

## Rubric validation

Treat every rubric criterion as a distinct acceptance criterion.

| Rubric           | Evidence                 | Status   |
| ---------------- | ------------------------ | -------- |
| Problem analysis | Section 2 + sources      | Verified |
| Methodology      | Section 3                | Verified |
| Prototype        | Figma link + screenshots | Verified |
| Evaluation       | Table 4                  | Pending  |

Do not say `rubric covered` merely because the topic is mentioned. The criterion must be demonstrably satisfied.

## Reproducibility

For technical work, verify that another person could reasonably reproduce the result. Check commands, dependencies, input data, environment, configuration, expected output, and test instructions. For calculations, preserve enough intermediate information to reproduce the result.

## Artifact QA

For each output file:

1. verify file exists,
2. verify expected file type,
3. verify non-zero content,
4. inspect semantic content,
5. inspect rendering where relevant,
6. verify filename,
7. verify links and references.

A generated file is not automatically a valid deliverable.

## Visual QA

For visual artifacts, inspect the rendered result.

For documents, check cover, page count, overflow, page breaks, headings, table readability, figure placement, captions, links, blank pages, font consistency.

For slides: layout, clipping, alignment, readability, visual consistency.

For spreadsheets: formulas, visible errors, widths, frozen panes, formatting, chart correctness.

## Assignment QA matrix

Before declaring submission readiness:

| Requirement | Evidence | Content QA | Artifact QA | Final Status |
| ----------- | -------- | ---------- | ----------- | ------------ |
| R1          | ...      | pass       | pass        | ready        |
| R2          | ...      | pass       | pending     | not ready    |

Every critical requirement should reach a verified state.

## Submission readiness

Use explicit states:

```text
not_started
in_progress
ready_for_review
ready_for_approval
approved
submitted
confirmed
failed
uncertain
```

Do not collapse `ready_for_approval` into `approved`. Do not collapse `submitted` into `confirmed`.

## Submission boundary

Submission follows:

```text
prepare
   ↓
preview
   ↓
explicit confirmation
   ↓
revalidate
   ↓
execute
   ↓
verify
   ↓
receipt
```

`Help me finish this assignment` does not imply permission to upload or submit.

## Approval preview

Before consequential submission, show:

```text
Course:
Assignment:
Deadline:
Artifact:
Filename:
Submission Destination:
Current Submission State:
Action:
Consequence:
Approval Required:
```

The user must be able to understand exactly what will happen.

## Revalidation before submission

Immediately after approval and before execution, recheck:

* course,
* assignment,
* deadline,
* submission state,
* artifact,
* filename,
* file type,
* portal/session state,
* approval scope.

If the state changed materially, invalidate approval and stop.

## Submission verification

After execution, verify the actual portal response. Accepted evidence may include submitted status, timestamp, receipt/reference number, uploaded filename, and confirmation page. Never claim successful submission based solely on a button click, lack of visible error, assumed network success, or local file existence.

## Failure handling

When submission or artifact generation fails, record failure phase, intended action, current state, artifact state, previous submission state, error, and safest next action. Do not blindly retry consequential actions when the external state is uncertain.

## Completion definition

An assignment is **complete** only when:

```text
all critical requirements
+
rubric verified
+
artifact valid
+
integration consistent
+
content QA passed
+
visual QA passed where relevant
+
submission requirements prepared
```

If submission occurred:

```text
+
portal confirmation
```

is required to claim successful submission.

## Ready-for-submission definition

An artifact is ready when:

* all required sections exist,
* required evidence exists,
* references are verified,
* files open correctly,
* rendering is acceptable,
* naming is correct,
* required links work,
* rubric requirements are addressed,
* no critical blockers remain.

`Looks good` is not an adequate readiness criterion.

## Standard orchestrator output

For assignment analysis:

```text
Assignment
Course
Academic Period
Deadline
Requirement Matrix
Critical Unknowns
Workstreams
Risks
Next Action
```

For progress:

```text
Assignment State
Completed Requirements
Pending Requirements
Evidence
Blockers
Artifact Status
QA Status
Next Action
```

For final readiness:

```text
Requirement Coverage
Rubric Coverage
Artifact Validation
Citation Audit
Visual QA
Submission State
Approval Required
```

## Memory integration

At meaningful milestones, create a compact checkpoint containing assignment goal, completed work, decisions, corrections, artifacts, current state, skills used, next action, and resume hint. Memory should preserve continuity, not replace the current assignment state.

## Operating rules

The system must:

* retrieve authoritative requirements first,
* inspect local and external sources before building,
* separate requirements from assumptions,
* maintain a requirement matrix,
* decompose complex work into explicit workstreams,
* route specialized work to the appropriate skills,
* map every important requirement to evidence,
* validate content and artifacts independently,
* audit citations and claims,
* inspect rendered outputs when relevant,
* distinguish preparation from submission,
* require explicit confirmation before consequential submission,
* revalidate immediately before external execution,
* verify actual portal confirmation afterward,
* checkpoint meaningful milestones for cross-session continuity.

The canonical lifecycle is:

**Discover → Retrieve → Ground → Matrix → Decompose → Research → Build → Integrate → Validate → QA → Prepare → Approve → Submit → Verify → Checkpoint**