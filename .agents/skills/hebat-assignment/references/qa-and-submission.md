# HEBAT Assignment — Quality Assurance and Submission Readiness

This reference defines the final validation, defect classification, artifact inspection,
submission-package verification, and submission-readiness gates for HEBAT assignments.

Read it when:

```text
auditing a completed assignment
validating an artifact before delivery
checking content and citations
checking document or visual quality
verifying final files
assembling a submission package
preparing an LMS handoff
confirming submission readiness
```

This reference governs **validation and readiness**.

Actual LMS navigation and submission execution belong to:

```text
hebat-academic
```

Explicit assignment instructions always override these defaults.

---

# 1. QA Principle

A generated artifact passes through distinct states:

```text
PRODUCED
   ↓
VALIDATED
   ↓
QA_PASSED
   ↓
PACKAGED
   ↓
READY_TO_SUBMIT
   ↓
SUBMITTED
   ↓
CONFIRMED
```

These states must not be collapsed.

In particular:

```text
file_generated
≠
file_valid
≠
ready_to_submit
≠
submitted
≠
submission_confirmed
```

---

# 2. QA Lifecycle

Canonical QA sequence:

```text
CONTENT QA
    ↓
STRUCTURAL QA
    ↓
CITATION / EVIDENCE QA
    ↓
VISUAL QA
    ↓
TECHNICAL QA
    ↓
SUBMISSION QA
    ↓
PACKAGE VALIDATION
    ↓
READINESS GATE
```

A failed pass returns the artifact to:

```text
REWORK_REQUIRED
```

After correction:

```text
FIX
→ REBUILD
→ REVALIDATE
```

Do not assume a correction is isolated.

---

# 3. Minimum QA Requirement

Before delivery, perform at least:

```text
1. Content / requirement QA
2. Artifact / visual QA
```

For complex assignments, also run:

```text
3. Structural QA
4. Citation / evidence QA
5. Technical QA
6. Submission QA
```

The actual QA depth should match artifact type and assignment consequence.

---

# 4. QA Source of Truth

All QA must use the current:

```text
assignment brief
lecturer instructions
rubric
course contract
HEBAT requirements
artifact specification
requirement traceability matrix
```

Do not validate against memory or an earlier version of the assignment when
current authoritative material is available.

---

# 5. Content QA

Verify:

```text
[ ] every mandatory requirement is addressed
[ ] every mandatory rubric criterion is represented
[ ] concepts are correctly understood
[ ] analysis matches the assignment question
[ ] claims are supported
[ ] evidence is relevant
[ ] methodology matches the requirement
[ ] conclusion follows from the discussion
[ ] limitations are appropriately represented
[ ] required links are present
[ ] required outputs are present
```

---

# 6. Requirement Coverage Gate

Every mandatory requirement should map to:

```text
Requirement
→ Artifact Location
→ Evidence
→ Validator
→ QA Result
```

Canonical statuses:

```text
MISSING
PLANNED
PRESENT
VERIFIED
BLOCKED
CONFLICTING
NOT_APPLICABLE
```

For final readiness:

```text
mandatory requirements = 100% VERIFIED
```

unless the user explicitly accepts an incomplete deliverable.

Do not mark:

```text
PRESENT
```

as equivalent to:

```text
VERIFIED
```

when the requirement needs substantive validation.

---

# 7. Content Correctness

Check:

```text
[ ] central claims are supported
[ ] important numerical values are verified
[ ] terminology is consistent
[ ] analysis does not contradict the evidence
[ ] recommendations are distinguishable from facts
[ ] assumptions are visible
[ ] limitations are not hidden
[ ] conclusion is consistent with the body
```

Do not use visual polish to compensate for unsupported content.

---

# 8. Evidence QA

For every important claim:

```text
Claim
→ Source
→ Evidence
→ Interpretation
→ Final Location
```

Verify:

```text
[ ] source exists
[ ] source is identifiable
[ ] evidence supports the exact claim
[ ] interpretation is not stronger than the evidence
[ ] citation is attached to the appropriate statement
```

Reject:

```text
"research shows..."
```

without traceable supporting evidence.

---

# 9. Citation QA

Verify:

```text
[ ] every substantive citation maps to a real source
[ ] source identity is correct
[ ] author/title/year are correct where required
[ ] DOI/URL is valid when included
[ ] citation style is internally consistent
[ ] cited sources appear in the reference list
[ ] references are not fabricated
[ ] unused references are removed when appropriate
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
quotations
```

Unverified sources must be explicitly marked as unverified or excluded from
authoritative evidence.

---

# 10. Structural QA

Verify:

```text
[ ] required sections exist
[ ] required section order is respected where specified
[ ] heading hierarchy is valid
[ ] required tables exist
[ ] required figures exist
[ ] required appendices exist
[ ] required links exist
[ ] required metadata exists
[ ] page/word limits are satisfied
[ ] filename follows instructions
[ ] file format is correct
```

Structural QA answers:

> Is the required artifact structurally complete?

It does not alone establish content correctness.

---

# 11. Technical QA

Verify the artifact opens and behaves as required.

Examples:

```text
document:
  opens successfully
  no corruption
  links work

PDF:
  renders correctly
  fonts/glyphs are intact
  page count is valid

presentation:
  file opens
  slides render correctly
  embedded media/links work when required

spreadsheet:
  opens
  required sheets exist
  formulas/data are intact

prototype:
  URL resolves
  required screens are accessible
```

Do not mark technical validity based solely on file existence.

---

# 12. Visual QA

Visual QA applies to any artifact where presentation affects usability or grading.

Check:

```text
[ ] cover
[ ] hierarchy
[ ] margins
[ ] spacing
[ ] typography
[ ] page breaks
[ ] tables
[ ] figures
[ ] captions
[ ] references
[ ] page numbering
[ ] headers/footers
[ ] hyperlinks
[ ] alignment
[ ] whitespace
[ ] image quality
[ ] clipping
[ ] overflow
[ ] unexpected blank pages
```

For presentation artifacts also check:

```text
[ ] slide density
[ ] readability at presentation scale
[ ] visual consistency
[ ] chart legibility
[ ] source visibility where required
```

For posters/infographics:

```text
[ ] visual hierarchy
[ ] reading flow
[ ] legibility at target output size
[ ] evidence/source placement
```

---

# 13. Cover QA

When a cover is required:

```text
[ ] exactly one page
[ ] assignment title correct
[ ] student/team identity correct
[ ] lecturer correct
[ ] study program correct
[ ] faculty/university correct
[ ] city/year correct
[ ] required logo correct
[ ] logo aspect ratio preserved
[ ] no unexpected header/footer
[ ] no overflow to page two
```

Institutional information must come from authoritative assignment context.

Never guess lecturer or identity information.

---

# 14. PDF Validation

For generated documents:

```text
source document
→ PDF conversion
→ structural inspection
→ rendered-page inspection
```

Do not trust the editable source alone.

Check for conversion regressions:

```text
font substitution
page-break changes
table overflow
figure displacement
missing glyphs
blank pages
clipping
broken links
unexpected page count
caption displacement
```

A valid DOCX does not guarantee a valid PDF.

---

# 15. Visual Regression Loop

When a visual defect is found:

```text
IDENTIFY
   ↓
FIX
   ↓
REGENERATE
   ↓
RENDER
   ↓
REINSPECT
```

Do not patch the source and assume the rendered output remained unchanged.

---

# 16. QA Severity

Classify each defect.

## CRITICAL

Blocks submission or invalidates a major requirement.

Examples:

```text
missing mandatory section
wrong assignment requirements
fabricated citation
missing required evidence
corrupted artifact
unreadable artifact
wrong required file
incorrect identity information
submission package missing a mandatory file
```

## MAJOR

May materially affect grading, correctness, or usability.

Examples:

```text
unsupported central claim
missing rubric criterion
incorrect analysis
broken required link
serious table/figure defect
major overflow
wrong conclusion
important formatting violation
```

## MINOR

Does not materially affect correctness or submission.

Examples:

```text
small spacing inconsistency
minor alignment issue
minor typography inconsistency
non-critical visual imperfection
```

---

# 17. Readiness Gate

Default readiness policy:

```text
CRITICAL = 0
MAJOR = 0
MINOR = acceptable when non-material
```

Therefore:

```text
Critical > 0
→ NOT_READY

Major > 0
→ REWORK_REQUIRED

Critical = 0
AND Major = 0
AND mandatory requirements verified
→ READY_TO_SUBMIT
```

Do not override a critical or major defect merely because the deadline is near.

An explicit user decision to accept a known defect may change the workflow state,
but must remain visible as an unresolved exception.

---

# 18. Exception Handling

When an issue is intentionally accepted:

```yaml
exception:
  issue_id:
  severity:
  reason:
  accepted_by:
  accepted_at:
  consequence:
```

Never silently suppress a major requirement defect.

The final report should identify accepted exceptions.

---

# 19. QA Recheck Scope

After changes, rerun all affected validations.

Examples:

```text
content change
→ content QA
→ citation QA when affected
→ structural QA when pagination may change

layout change
→ visual QA
→ structural QA when page count changes

source change
→ evidence QA
→ citation QA
→ content QA for affected claims

filename/package change
→ technical QA
→ submission QA
```

Do not rerun every expensive validator unnecessarily, but do not assume unaffected
state without checking dependency.

---

# 20. Dependency-Aware Revalidation

A QA result may become stale after a change.

Conceptually:

```text
artifact change
      ↓
affected validators
      ↓
invalidated evidence
      ↓
revalidation
```

Examples:

```text
changing a figure
→ figure QA invalidated

changing a paragraph with a citation
→ citation/content QA invalidated

changing page layout
→ visual and structural QA invalidated

changing a required section
→ requirement coverage invalidated
```

---

# 21. Submission Manifest

For multi-file submissions create:

```yaml
submission_manifest:
  primary_artifact:
  supplementary_artifacts: []
  required_links: []
  required_datasets: []
  required_metadata: []
```

Every manifest item must be validated.

Do not include:

```text
temporary drafts
debug files
internal notes
unused screenshots
intermediate exports
```

unless explicitly required.

---

# 22. Submission Package QA

Verify:

```text
[ ] all required files exist
[ ] every file uses the correct format
[ ] filenames follow instructions
[ ] links resolve
[ ] supporting artifacts correspond to the final version
[ ] no stale draft is accidentally included
[ ] required metadata is present
[ ] package matches the current brief
```

A complete package is more than a directory containing multiple files.

---

# 23. Submission Route

Determine the submission destination from the current assignment context.

Possible destinations include:

```text
HEBAT
LMS
lecturer-designated channel
team administrator
external project platform
```

Do not hard-code one route.

The actual route must be verified from authoritative current instructions.

---

# 24. Group vs Individual Submission

Do not assume submission behavior from the assignment type alone.

Instead inspect:

```text
team/individual mode
current submission instructions
designated submitter
required copies
required channels
```

The source of truth is the current assignment instruction.

---

# 25. Handoff Contract

When the artifact reaches readiness:

```yaml
handoff:
  assignment_context:
  requirement_coverage:
  final_artifacts: []
  submission_manifest:
  qa_summary:
  exceptions: []
  unresolved: []
  readiness_state:
```

Recommended handoff state:

```text
READY_TO_SUBMIT
```

This means:

```text
the artifact/package has passed the local readiness gates
```

It does not mean:

```text
the external submission already happened
```

---

# 26. LMS Boundary

Actual LMS interaction belongs to:

```text
hebat-academic
```

Handoff:

```text
HEBAT ASSIGNMENT
       ↓
READY_TO_SUBMIT
       ↓
hebat-academic
       ↓
submission workflow
       ↓
portal verification
```

The assignment skill should not duplicate LMS navigation logic.

---

# 27. Submission State

Use distinct states:

```text
NOT_READY
READY_TO_SUBMIT
SUBMISSION_IN_PROGRESS
SUBMITTED
CONFIRMED
UNKNOWN
BLOCKED
```

Definitions:

## READY_TO_SUBMIT

All local readiness gates pass.

## SUBMISSION_IN_PROGRESS

Submission action has started but has not yet been externally confirmed.

## SUBMITTED

The external submission system reports a successful submission event.

## CONFIRMED

The resulting submission state was independently verified.

## UNKNOWN

The external state cannot be reliably established.

## BLOCKED

A required condition prevents submission.

---

# 28. Submission Confirmation

Do not infer submission from:

```text
file generated
file exists
upload dialog opened
upload button clicked
browser navigation occurred
HTTP request returned without obvious error
```

Confirmation requires evidence from the actual submission system.

Possible evidence:

```text
submission receipt
submission ID
portal status
official confirmation message
submission timestamp
verified LMS record
```

---

# 29. Timeout / Unknown Submission

Important case:

```text
submit
 ↓
network timeout
```

Initial state:

```text
SUBMISSION_UNKNOWN
```

Then:

```text
read submission status
→ identify actual portal state
```

Do not blindly submit again.

---

# 30. Final Submission Readiness Checklist

```text
REQUIREMENTS
[ ] current brief verified
[ ] mandatory requirements covered
[ ] rubric mapped
[ ] no unresolved material requirement conflict

CONTENT
[ ] concepts correct
[ ] claims supported
[ ] evidence verified
[ ] analysis coherent
[ ] conclusion consistent
[ ] limitations appropriate

CITATIONS
[ ] sources verified
[ ] claim-source mapping checked
[ ] citation format consistent
[ ] references complete
[ ] no fabricated sources

ARTIFACT
[ ] correct type
[ ] correct filename
[ ] correct format
[ ] page/word limits satisfied
[ ] identity information correct
[ ] required links present
[ ] tables and figures intact

VISUAL
[ ] no overflow
[ ] no clipping
[ ] no unexpected blank pages
[ ] typography consistent
[ ] hierarchy consistent
[ ] rendered output inspected when applicable

PACKAGE
[ ] all required files present
[ ] no stale drafts
[ ] no unnecessary internal files
[ ] links verified

SUBMISSION
[ ] destination verified
[ ] deadline verified
[ ] group/individual route verified
[ ] designated submitter verified
```

---

# 31. Completion Contract

Final QA should return:

```yaml
qa_result:
  state:
  requirement_coverage:
  content:
  structural:
  citation:
  visual:
  technical:
  submission:
  critical_defects: []
  major_defects: []
  minor_defects: []
  accepted_exceptions: []
  final_artifacts: []
  submission_manifest:
  unresolved: []
  next_action:
```

---

# 32. Readiness Formula

Conceptually:

```text
READY_TO_SUBMIT
=
MANDATORY_REQUIREMENTS_VERIFIED
∧
CRITICAL_DEFECTS = 0
∧
MAJOR_DEFECTS = 0
∧
REQUIRED_EVIDENCE_VERIFIED
∧
ARTIFACT_VALID
∧
PACKAGE_VALID
```

For artifact types where visual QA applies:

```text
∧
VISUAL_QA_PASSED
```

---

# 33. General Submission Rule

Submission behavior must be derived from:

```text
current official requirement
→ current assignment brief
→ current course/HEBAT instruction
→ verified project context
```

Do not infer submission behavior from:

```text
previous assignments
another course
another semester
generic HEBAT convention
memory
```

When the assignment explicitly specifies different destinations or submitters,
follow those instructions exactly.

---

# 34. Reusability Rule

Remain course-agnostic.

Do not hard-code:

```text
course code
lecturer
project theme
SDG
methodology
submission channel
team structure
Figma structure
page count
citation style
```

These values must come from the current assignment context.

This reference defines:

```text
HOW TO VERIFY READINESS
```

The current assignment defines:

```text
WHAT MUST BE VERIFIED
```

---

# 35. Final Operating Rules

The system must:

```text
validate against current authoritative requirements
perform separate QA passes
distinguish presence from verification
verify important claims and citations
validate structure independently from content
inspect rendered artifacts when visual correctness matters
revalidate after meaningful changes
classify defects by severity
prevent critical and major defects from silently passing readiness
validate the complete submission package
derive submission route from current instructions
never claim LMS submission from local artifact generation
treat uncertain external submission state as UNKNOWN
never blindly retry an uncertain submission
preserve accepted exceptions explicitly
keep the skill course-agnostic
handoff LMS operations to hebat-academic
```

---

# 36. Central Principle

> **Submission readiness is an evidence-backed state, not an impression. A deliverable is ready only when the current assignment requirements, content, evidence, artifact, package, and applicable QA gates have been verified; actual submission remains a separate externally confirmed state.**
