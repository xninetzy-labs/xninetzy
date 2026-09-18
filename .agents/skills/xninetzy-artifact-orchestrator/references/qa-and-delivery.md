# Xninetzy Artifact Orchestrator — QA and Delivery

This reference defines physical validation, structural validation, evidence QA,
rendering inspection, visual QA, defect handling, revision, freeze, checkpoint,
packaging, and delivery.

Read it when:

```text
finalizing an artifact
auditing a generated file
checking rendered output
assembling a package
preparing delivery
handling defects
freezing a final version
```

---

# 1. QA Principle

A successful generator call is not evidence of artifact correctness.

Use:

```text
GENERATE
→ INSPECT
→ VALIDATE
→ RENDER
→ QA
→ REVISE IF NEEDED
→ FREEZE
→ DELIVER
```

Never skip verification because generation succeeded.

---

# 2. QA Layers

Use separate QA dimensions:

```text
REQUIREMENT QA
CONTENT QA
EVIDENCE / CITATION QA
STRUCTURAL QA
TECHNICAL QA
RENDERING QA
VISUAL QA
ACCESSIBILITY QA
DELIVERY QA
```

Not every artifact requires every dimension.

The applicable dimensions must be determined by artifact type and requirements.

---

# 3. Physical File QA

After generation verify:

```text
file exists
exact path
non-zero size
expected extension
expected MIME/type
file opens
no obvious corruption
```

Where relevant also verify:

```text
page count
slide count
sheet count
archive contents
file permissions
```

A file's existence does not prove its content is correct.

---

# 4. Structural QA

## DOCX

Check:

```text
headings
paragraphs
tables
figures
sections
page breaks
TOC
references
links
```

## PDF

Check:

```text
page count
page order
text presence
links
figures
metadata when relevant
clipping indicators
```

## PPTX

Check:

```text
slide count
slide dimensions
layouts
text boxes
images
notes
links
```

## Spreadsheet

Check:

```text
sheet names
formulas
ranges
values
references
charts
frozen panes
number formats
```

---

# 5. Content QA

Verify:

```text
requirements are addressed
important claims are supported
analysis is coherent
terminology is consistent
numbers are consistent
conclusion follows from the content
required content exists
```

Do not treat:

```text
file generated
```

as:

```text
content verified
```

---

# 6. Evidence / Citation QA

For every important claim:

```text
Claim
→ Source
→ Evidence
→ Artifact location
```

Check:

```text
source exists
source identity is correct
source supports claim
citation is correctly attached
reference exists
```

Reject:

```text
fabricated source
unsupported claim
citation mismatch
unverified empirical result
```

---

# 7. Requirement QA

Build or inspect the requirement matrix:

| Requirement | Artifact Location | Evidence | Validator | Status   |
| ----------- | ----------------- | -------- | --------- | -------- |
| R1          | Section X         | Source Y | QA-01     | VERIFIED |

Final readiness normally requires:

```text
mandatory requirements = 100% VERIFIED
```

unless an explicit exception is recorded.

---

# 8. Rendering QA

Visual quality must be assessed from the rendered representation whenever
layout materially matters.

Pipeline:

```text
Source Artifact
   ↓
Generate
   ↓
Render / Preview
   ↓
Inspect
   ↓
Detect Defects
   ↓
Revise Source
   ↓
Regenerate
   ↓
Render Again
```

Do not claim visual correctness from source structure alone.

---

# 9. PDF Rendering

For PDF-sensitive work:

```text
source document
→ PDF
→ render pages
→ inspect pages
```

Check:

```text
font substitution
missing glyphs
page-break shifts
table overflow
figure displacement
blank pages
cropping
clipping
broken links
unexpected page count
caption displacement
```

---

# 10. Visual QA

Inspect for:

```text
overflow
clipping
misalignment
spacing inconsistency
whitespace imbalance
unreadable text
malformed tables
missing images
duplicate elements
unexpected blank pages
inconsistent typography
broken visible links
```

For documents also inspect:

```text
cover
headings
margins
pagination
references
headers/footers
```

For presentations:

```text
slide density
headline hierarchy
chart legibility
visual consistency
speaker-scale readability
```

For spreadsheets:

```text
column readability
sheet navigation
formula visibility where useful
number formatting
frozen panes
dashboard/chart readability
```

---

# 11. Cover QA

When a cover is required:

```text
exactly one page
correct title
correct identity
correct lecturer when required
correct academic metadata
correct logo
logo appears once
logo aspect ratio preserved
no overflow
no unexpected header/footer
```

Render and inspect the cover visually.

---

# 12. Placeholder Audit

Before delivery, search for unresolved:

```text
TODO
TBD
Lorem ipsum
[NAME]
[DATE]
[LINK]
[PLACEHOLDER]
INSERT FIGURE
ADD CITATION
WILL BE UPDATED
EMPTY TEMPLATE FIELD
```

No unresolved placeholder belongs in a final artifact unless explicitly
intentional.

---

# 13. Link Audit

For important links verify:

```text
URL is complete
target is correct
version is correct
link resolves when verification is possible
access state is appropriate
```

When verification cannot be performed:

```text
LINK_STATUS = UNKNOWN
```

Do not claim that an inaccessible link is verified.

---

# 14. Length Validation

When constraints exist:

```text
actual page count
actual slide count
actual word count when applicable
appendix treatment
cover/TOC treatment
hidden/blank slide treatment
```

Do not estimate page/slide length from word count alone.

---

# 15. Accessibility QA

When applicable:

```text
text readability
contrast
logical reading order
meaningful hierarchy
captions
alternative text where supported
non-color-only distinctions
table readability
slide readability
```

Accessibility should be evaluated against:

```text
artifact type
target audience
assignment requirements
applicable standards
```

---

# 16. Defect Taxonomy

Use four levels:

## CRITICAL

Prevents submission, corrupts the artifact, or changes meaning materially.

Examples:

```text
missing mandatory requirement
wrong artifact
fabricated source
corrupted file
missing required evidence
unreadable output
critical calculation error
wrong identity information
```

## HIGH

Materially affects quality, correctness, grading, or usability.

Examples:

```text
unsupported central claim
missing major requirement
serious layout failure
broken important table
broken required link
major rendering defect
incorrect major calculation
```

## MEDIUM

Noticeable but not normally blocking.

Examples:

```text
inconsistent spacing
minor structural issue
non-critical alignment problem
small evidence gap
```

## LOW

Cosmetic or non-material issue.

Examples:

```text
minor typography mismatch
small whitespace imbalance
cosmetic alignment issue
```

---

# 17. Readiness Gate

Default:

```text
CRITICAL = 0
HIGH = 0
```

Then:

```text
mandatory requirements verified
+
required evidence verified
+
physical file valid
+
structural validation passed
+
applicable visual QA passed
+
critical defects = 0
+
high defects = 0
```

→

```text
READY
```

Otherwise:

```text
REWORK_REQUIRED
```

---

# 18. Defect Handling

For every defect:

```yaml
defect:
  defect_id:
  severity:
  description:
  responsible_layer:
  affected_artifact:
  validator:
  resolution:
  status:
```

Possible status:

```text
OPEN
IN_PROGRESS
FIXED
WONT_FIX
ACCEPTED_EXCEPTION
```

An exception must remain visible.

---

# 19. Revision Loop

Canonical:

```text
DETECT
 ↓
CLASSIFY
 ↓
LOCALIZE RESPONSIBLE SOURCE
 ↓
FIX
 ↓
REGENERATE
 ↓
RENDER
 ↓
REINSPECT
 ↓
REVALIDATE
```

Do not patch only the derived artifact when the root defect is upstream.

---

# 20. Revision Scope

After a change, determine which QA dimensions are invalidated.

Examples:

```text
content edit
→ content/evidence/citation QA

layout edit
→ structural/rendering/visual QA

source substitution
→ evidence/content/citation QA

formula change
→ spreadsheet calculation QA

package change
→ delivery QA
```

When impact cannot be bounded reliably:

```text
perform broader QA
```

---

# 21. Spreadsheet QA

For important workbooks:

```text
inspect formulas
inspect references
inspect representative values
check calculation errors
reconcile totals
verify sheet dependencies
check number formats
inspect charts
```

Use spreadsheet-native calculation/validation where practical.

Do not treat a formula string as proof that the spreadsheet computes correctly.

---

# 22. Presentation QA

For decks, verify:

```text
slide count
dimensions
readability
message hierarchy
visual consistency
chart correctness
image placement
speaker notes where required
citation/source placement
```

Never solve overflow by making all content unreadably small.

---

# 23. Document QA

For documents, verify:

```text
cover
TOC when required
heading hierarchy
page numbering
tables
figures
captions
references
links
pagination
```

Where PDF is the final delivery format, repeat applicable checks on the PDF.

---

# 24. Package QA

For multi-file delivery:

```yaml
submission_package:
  primary_artifact:
  supporting_artifacts: []
  required_links: []
  required_data: []
```

Verify:

```text
all required files exist
all files correspond to the same final state
no stale draft is included
filenames are correct
required links are present
package contains no unintended internal artifacts
```

---

# 25. Version Consistency

All files in the same final package should correspond to compatible versions.

Example:

```text
report.pdf
report.docx
presentation.pptx
spreadsheet.xlsx
```

must not silently mix:

```text
report v5
presentation v3
spreadsheet v2
```

when those versions depend on one another.

---

# 26. Freeze Protocol

Freeze only after readiness gates pass.

Record:

```yaml
freeze:
  artifact_id:
  version:
  final_path:
  checksum:
  frozen_at:
  qa_summary:
```

After freeze:

```text
any content/layout change
→ new version
→ revalidation
```

---

# 27. Checksum / Integrity

When useful, record:

```text
SHA-256
```

or another supported integrity identifier for the frozen file.

Do not treat checksum equality as semantic correctness.

Checksum proves:

```text
same bytes
```

not:

```text
correct artifact
```

---

# 28. Checkpointing

For long-running work preserve:

```text
artifact goal
artifact ID
version
completed stages
exact paths
important decisions
QA state
unresolved defects
next action
resume hint
```

Checkpoints are continuity aids.

They are not substitutes for the final artifact.

---

# 29. Delivery States

Use:

```text
DRAFT
QA_READY
REWORK_REQUIRED
FROZEN
READY
DELIVERED
SUBMITTED
CONFIRMED
BLOCKED
UNKNOWN
```

Definitions:

```text
QA_READY
Required QA has completed but freeze may not yet have occurred.

FROZEN
Verified artifact is immutable unless a new version is created.

READY
Frozen artifact/package has passed delivery readiness.

DELIVERED
Artifact was provided through the intended local/handoff channel.

SUBMITTED
External submission system reports submission.

CONFIRMED
External system verifies the resulting submission state.
```

---

# 30. No False Delivery Claims

Never say:

```text
submitted
uploaded
published
confirmed
```

unless corresponding evidence exists.

Distinguish:

```text
file created
file delivered
file uploaded
submission accepted
submission confirmed
```

---

# 31. Handoff Contract

A delivery handoff should include:

```yaml
handoff:
  artifact_id:
  version:
  artifacts: []
  package_manifest:
  qa_summary:
  exceptions: []
  unresolved: []
  delivery_state:
  next_action:
```

---

# 32. Security / Privacy Check

Before delivery inspect for accidental inclusion of:

```text
passwords
tokens
cookies
private URLs
internal infrastructure
hidden notes
debug logs
personal information
temporary files
```

Redact or remove unauthorized sensitive material.

---

# 33. Final QA Checklist

```text
REQUIREMENTS
[ ] current requirements inspected
[ ] mandatory requirements mapped
[ ] coverage verified

CONTENT
[ ] required content exists
[ ] important claims verified
[ ] numbers reconciled
[ ] terminology consistent

EVIDENCE
[ ] sources verified
[ ] citations verified
[ ] claim/evidence alignment checked
[ ] no fabricated sources

STRUCTURE
[ ] required sections exist
[ ] hierarchy correct
[ ] required tables/figures exist
[ ] length constraints checked

TECHNICAL
[ ] physical file valid
[ ] file opens
[ ] expected counts verified
[ ] formulas/links checked where applicable

RENDERING
[ ] final representation rendered
[ ] rendered output inspected

VISUAL
[ ] no clipping
[ ] no overflow
[ ] no unintended blank pages/slides
[ ] typography consistent
[ ] tables/figures readable

PLACEHOLDERS
[ ] no unresolved placeholders

PACKAGE
[ ] required files present
[ ] versions compatible
[ ] no stale drafts
[ ] required links present

FREEZE
[ ] final version identified
[ ] final path identified
[ ] checksum recorded when useful

DELIVERY
[ ] correct destination
[ ] delivery state explicit
[ ] exceptions documented
```

---

# 34. Completion Contract

Return:

```yaml
qa_result:
  artifact_id:
  version:
  artifact_type:

  requirement_status:
    coverage:
    unresolved: []

  evidence_status:
    verified:
    unresolved: []

  physical_status:
  structural_status:
  technical_status:
  rendering_status:
  visual_status:
  accessibility_status:

  defects:
    critical: []
    high: []
    medium: []
    low: []

  exceptions: []

  freeze_status:
  final_path:
  checksum:

  package_status:
  delivery_status:

  overall_state:
  next_action:
```

Use:

```text
PASS
FAIL
PARTIAL
UNKNOWN
```

for individual validators.

---

# 35. Completion Rule

An artifact is:

```text
READY
```

only when:

```text
mandatory requirements verified
+
required evidence verified
+
physical artifact valid
+
required structural QA passed
+
required rendering/visual QA passed
+
CRITICAL = 0
+
HIGH = 0
```

Then:

```text
FREEZE
→ READY
```

External submission remains a separate state.

---

# 36. Golden QA Workflow

```text
ARTIFACT GENERATED
      ↓
PHYSICAL CHECK
      ↓
STRUCTURAL CHECK
      ↓
CONTENT CHECK
      ↓
EVIDENCE / CITATION CHECK
      ↓
RENDER
      ↓
VISUAL CHECK
      ↓
DEFECT CLASSIFICATION
      ↓
REVISE IF NEEDED
      ↓
REGENERATE
      ↓
REVALIDATE
      ↓
FREEZE
      ↓
PACKAGE
      ↓
DELIVER
```

---

# 37. Central Principle

> **QA is not a final glance. It is a chain of independent checks proving that the artifact satisfies its requirements, contains supported content, remains structurally and technically valid, renders correctly, and corresponds to the exact frozen version that is delivered.**
