# FILE: references/doc-standard.md

# HEBAT Assignment — Document Standard

This reference defines default document formatting and visual structure.

Read it when designing document-based HEBAT deliverables.

Explicit lecturer or assignment requirements always override this reference.

---

## 1. Default Document Baseline

Unless the assignment specifies another standard:

```text
Paper: A4
Body font: Times New Roman
Body size: 12 pt
Body color: #000000
Alignment: justified
Line spacing: 1.5
Margins:
  top: 2.3 cm
  bottom: 2.3 cm
  left: 2.5 cm
  right: 2.5 cm
```

Maintain consistent paragraph spacing.

Enable widow/orphan control where supported.

Avoid decorative elements that do not improve comprehension.

Do not use em dashes in academic document prose when normal punctuation is
sufficient.

---

## 2. Heading Hierarchy

Default:

```text
H1: 24 pt, bold
H2: 16 pt, bold
H3: 13 pt, bold
```

Use informative headings.

Prefer:

```text
2.5 Feasibility Analysis in the Surabaya Context
```

over:

```text
2.5 Why This Is Easy
```

Do not insert decorative heading prefixes unless required.

---

## 3. Heading Semantics

Heading levels must reflect structure:

```text
H1
  H2
    H3
```

Do not skip levels merely for visual size.

Heading numbering must remain consistent.

---

## 4. Cover Page

When required, the cover should normally include:

```text
assignment/project title
subtitle when useful
university identity
student/group identity
lecturer when required
study program
faculty
university
city
year
```

Do not invent lecturer information.

---

## 5. Cover Composition

A professional default composition is:

```text
Title
↓
Logo when required
↓
Student / Team Identity
↓
Lecturer
↓
Academic Metadata
```

The cover should fit on one page.

No header/footer should appear on the cover unless the assignment explicitly
requires one.

---

## 6. Student / Team Identity

For group assignments:

```text
Kelompok N
```

Use a numbered member list only when required.

Preferred:

```text
NIM Name
NIM Name
NIM Name
```

For individual work:

```text
Nama | NIM
```

Avoid decorative icons for mandatory academic identity information.

---

## 7. University Logo

When a logo is required:

```text
use the official asset
preserve aspect ratio
do not stretch
maintain sufficient contrast
verify placement visually
```

Do not invent or substitute institutional branding.

---

## 8. Table of Contents

A TOC should:

```text
match actual headings
use correct numbering
show correct page numbers
reflect heading hierarchy
```

Do not include placeholder text.

---

## 9. Tables

Default:

```text
fixed or controlled layout
readable column widths
consistent borders
clear header treatment
black text
restrained decoration
```

A table should be used when it improves comparison or organization.

Do not compress tables until they become unreadable.

---

## 10. Figures

Important figures should have:

```text
figure number
informative caption
source when applicable
adequate resolution
```

Captions should remain visually associated with the figure.

---

## 11. Links

Required external artifacts should remain clearly identifiable.

Preferred:

```text
Figma Prototype: [link]
Project Spreadsheet: [link]
Repository: [link]
Prototype: [link]
```

Do not surround useful links with unnecessary technical metadata.

---

## 12. References

Use the citation style required by the assignment.

Do not impose a generic citation style when the course specifies another one.

---

## 13. Typography Consistency

Maintain consistency in:

```text
font family
heading sizes
paragraph spacing
caption treatment
table styling
page numbering
```

Avoid unnecessary font changes.

---

## 14. Visual Principle

For academic documents:

```text
clarity > decoration
readability > density
consistency > novelty
```

The visual system should support the argument.

---

# FILE: references/qa-and-submission.md

# HEBAT Assignment — QA and Submission Readiness

This reference defines final validation, artifact packaging, and submission
readiness.

Read it when auditing a deliverable before handoff or submission.

---

## 1. QA Model

Run distinct passes:

```text
CONTENT QA
     ↓
STRUCTURAL QA
     ↓
CITATION QA
     ↓
VISUAL QA
     ↓
TECHNICAL QA
     ↓
SUBMISSION QA
```

A pass may trigger another pass.

---

## 2. Content QA

Verify:

```text
[ ] every mandatory requirement is addressed
[ ] rubric criteria are mapped
[ ] concepts are correctly understood
[ ] important claims are supported
[ ] evidence matches claims
[ ] argument is coherent
[ ] methodology is appropriate
[ ] conclusion follows the analysis
[ ] limitations are acknowledged where needed
[ ] terminology is consistent
```

---

## 3. Structural QA

Verify:

```text
[ ] required sections exist
[ ] heading hierarchy is correct
[ ] required tables exist
[ ] required figures exist
[ ] required appendices exist
[ ] page/word limits are satisfied
[ ] filename follows instructions
[ ] file format is correct
```

---

## 4. Citation QA

Verify:

```text
[ ] every substantive citation maps to a real source
[ ] the source supports the attached claim
[ ] author/title/year are correct where required
[ ] citation style is consistent
[ ] references are complete
[ ] references are not fabricated
[ ] unused references are removed where appropriate
```

---

## 5. Visual QA

For documents inspect:

```text
cover
page breaks
headings
margins
body text
tables
figures
captions
references
page numbers
headers/footers
links
whitespace
alignment
overflow
clipping
image quality
```

For presentations inspect:

```text
slide hierarchy
readability
content density
alignment
charts
images
speaker-visible text
references
```

For posters/infographics inspect:

```text
hierarchy
legibility
visual flow
evidence placement
source visibility
alignment
spacing
print/readability constraints
```

---

## 6. Rendered Output Rule

For generated documents:

```text
source file
→ converted output
→ rendered output
→ visual inspection
```

Do not trust the editable source alone.

For PDFs, inspect the rendered PDF pages.

Successful file generation is not equivalent to successful visual QA.

---

## 7. Conversion Regression

After PDF conversion check for:

```text
font substitution
layout shifts
table overflow
figure movement
missing glyphs
broken links
unexpected page count
blank pages
caption displacement
```

If conversion changes layout:

```text
FIX
→ REGENERATE
→ RECONVERT
→ REVALIDATE
```

---

## 8. QA Severity

### Critical

Blocks readiness.

Examples:

```text
missing mandatory requirement
fabricated citation
wrong assignment type
corrupted file
unreadable page
missing required evidence
broken required artifact
incorrect identity information
```

### Major

May materially affect grading or correctness.

Examples:

```text
unsupported central claim
missing rubric criterion
incorrect analysis
serious layout failure
broken required link
important figure/table failure
wrong conclusion
```

### Minor

Does not materially block submission.

Examples:

```text
small spacing inconsistency
minor alignment issue
non-critical typography inconsistency
```

---

## 9. Readiness Gate

Default:

```text
Critical = 0
Major = 0
Minor = acceptable when non-material
```

A deliverable with unresolved critical or major defects is:

```text
REWORK_REQUIRED
```

not:

```text
READY_TO_SUBMIT
```

---

## 10. Requirement Coverage Gate

Before readiness:

```text
mandatory requirements = 100% verified
```

Every mandatory requirement must map to:

```text
artifact location
+
evidence
+
validator
```

---

## 11. Submission Package

Use a package manifest:

```yaml
submission_manifest:
  primary_artifact:
  supplementary_artifacts: []
  required_links: []
  required_data: []
  required_identity_metadata: []
```

Verify the manifest against the current assignment instructions.

Do not include:

```text
temporary files
debug output
unused drafts
internal notes
test artifacts
```

unless explicitly required.

---

## 12. Submission Route

The submission destination must come from the current assignment context.

Do not assume:

```text
all assignments use the same LMS
all assignments use HEBAT
all team assignments use one channel
all individual assignments use one channel
```

Current instructions determine the route.

---

## 13. Handoff Boundary

This skill may produce:

```text
READY_TO_SUBMIT
```

The actual LMS action belongs to:

```text
hebat-academic
```

The handoff should include:

```yaml
handoff:
  assignment_context:
  final_artifacts:
  submission_manifest:
  requirement_coverage:
  qa_summary:
  unresolved:
```

---

## 14. Submission Confirmation

Do not infer:

```text
SUBMITTED
```

from:

```text
file generated
file uploaded locally
browser page opened
upload button clicked
```

Use:

```text
actual LMS / submission-system confirmation
```

for the submitted state.

---

## 15. Final Submission Checklist

```text
CONTENT
[ ] requirements satisfied
[ ] rubric covered
[ ] claims supported
[ ] citations verified
[ ] references complete
[ ] conclusion consistent

ARTIFACT
[ ] correct format
[ ] correct filename
[ ] page/word constraints satisfied
[ ] identity correct
[ ] lecturer information correct
[ ] tables readable
[ ] figures intact
[ ] links verified
[ ] PDF visually validated when applicable

PACKAGE
[ ] all required files included
[ ] no unnecessary files included
[ ] required links included

SUBMISSION
[ ] correct destination identified
[ ] correct deadline identified
[ ] correct group/individual route identified
```

---

## 16. Final Readiness States

```text
NOT_READY
REWORK_REQUIRED
READY_TO_SUBMIT
SUBMITTED
CONFIRMED
BLOCKED
UNKNOWN
```

Meaning:

```text
NOT_READY
Required validation is incomplete.

REWORK_REQUIRED
Defects exist that must be corrected.

READY_TO_SUBMIT
All required readiness gates pass.

SUBMITTED
External submission has been verified.

CONFIRMED
The destination system confirms the expected submission state.

BLOCKED
A required condition prevents progress.

UNKNOWN
The actual external state cannot be established.
```

---

## 17. Final QA Principle

> **A generated artifact is not automatically a valid artifact, and a valid artifact is not automatically a submitted artifact. Each state requires its own evidence and verification.**
