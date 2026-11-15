---
name: pdf
description: Reads, extracts, edits, fills, validates or transforms existing PDFs where content, tables, forms or layout matter (pypdf, pdfplumber). Use for work on a PDF you already have; to build a new report or deck from content use document-studio.
metadata:
  keywords: and any appropriate creates creating editing extracting extraction fidelity files generation images inspection manipulation page prefer programmatic reading rendered reportlab reviewing structure task transforming typography understanding validating visual when
---

# PDF Skill

## Purpose

Handle PDF workflows with two independent quality dimensions:

1. Content correctness
   - Text
   - Tables
   - Metadata
   - Page order
   - References
   - Numerical values
   - Links
   - Embedded assets

2. Visual correctness
   - Typography
   - Alignment
   - Spacing
   - Margins
   - Tables
   - Images
   - Headers/footers
   - Page breaks
   - Clipping
   - Overflow
   - Glyph rendering

Never assume that a PDF is correct merely because text extraction succeeds.

---

# 1. When to Use

Use this skill when the task involves:

- Reading or summarizing PDF documents
- Extracting text, tables, metadata, or images
- Reviewing PDF formatting or layout
- Creating a PDF from structured or unstructured content
- Converting content into a polished PDF
- Editing or restructuring an existing PDF
- Validating generated PDFs
- Comparing PDF versions
- Checking page-level rendering
- Preparing reports, proposals, academic documents, invoices, forms, or presentations as PDF

For purely textual tasks where PDF layout is irrelevant, use normal text processing instead.

---

# 2. Core Principle

PDF processing must follow:

    Extract -> Understand -> Generate/Edit -> Render -> Inspect -> Validate -> Deliver

Do not skip rendering when layout matters.

Text extraction validates content.

Rendering validates appearance.

Both are required for production-quality output.

---

# 3. Tool Selection

Use the smallest reliable tool for the job.

### Text extraction

Prefer:

- `pdfplumber` for text and table inspection
- `pypdf` for PDF structure, metadata, merging, splitting, and basic manipulation

### PDF generation

Prefer:

- `reportlab`

### Rendering

Prefer:

- `pdftoppm`
- Poppler utilities

### Programmatic inspection

Use Python when useful for:

- page dimensions
- text extraction
- bounding boxes
- metadata
- page counts
- image dimensions
- table detection
- repeated headers/footers
- content validation

### Visual inspection

Always render pages when:

- creating a PDF
- modifying layout
- reviewing visual quality
- generating tables
- adding images/charts
- changing fonts
- changing page size
- changing margins
- changing headers/footers

---

# 4. Input Assessment

Before processing, determine:

- Is the PDF text-based or scanned?
- Is OCR required?
- Does the document contain tables?
- Does the document contain charts/images?
- Is layout preservation important?
- Is the PDF password protected?
- Is the document malformed?
- Is the requested operation destructive or non-destructive?

For scanned PDFs:

1. Attempt text extraction.
2. Detect insufficient/empty extraction.
3. Inspect rendered pages.
4. Use OCR only when necessary.
5. Clearly distinguish OCR-derived text from native PDF text.

Never silently treat failed extraction as an empty document.

---

# 22. Quality Gates

A PDF is NOT ready for delivery until:

### Content

* [ ] Required content exists
* [ ] Text extraction succeeds
* [ ] Tables contain expected data
* [ ] Numbers are correct
* [ ] References are readable
* [ ] No accidental placeholder text exists

### Visual

* [ ] Pages render successfully
* [ ] No clipping
* [ ] No overlap
* [ ] No broken tables
* [ ] No missing glyphs
* [ ] No black squares
* [ ] No distorted images
* [ ] Typography is consistent
* [ ] Margins are consistent
* [ ] Headers/footers are correct
* [ ] Page numbering is correct

### Technical

* [ ] PDF opens successfully
* [ ] Page dimensions are correct
* [ ] No malformed output
* [ ] Temporary artifacts are separated from final output
* [ ] Final filename is stable and descriptive

If any critical gate fails:

```
DO NOT DELIVER.
```

Fix -> regenerate -> render -> inspect -> validate again.

---

# 23. Final Delivery

Before responding:

1. Confirm the final PDF exists.
2. Confirm it opens.
3. Confirm extraction succeeds.
4. Confirm rendering succeeds.
5. Confirm latest rendered pages were inspected.
6. Confirm no critical visual defects remain.
7. Deliver only the final artifact.
8. Do not expose temporary/debug files unless requested.

Never claim:

* "visually verified"
* "rendered successfully"
* "no layout issues"

unless the corresponding validation was actually performed.

---

# 24. Operating Principle

For every PDF task, optimize in this order:

```
Correctness
-> Readability
-> Layout fidelity
-> Consistency
-> Accessibility
-> Performance
```

Never trade correctness for visual polish.

Never trade readability for compactness.

Never consider a generated PDF complete until both its CONTENT and RENDERED APPEARANCE have passed validation.

```

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/05-13-reading-workflow.md` — §5–13: Reading Workflow, PDF Generation Workflow, Typography, Character Safety, Layout Rules, Tables, Images and Charts, Headers and Footers, Rendering QA
- `references/14-21-visual-qa-checklist.md` — §14–21: Visual QA Checklist, Content QA, Automated Validation, Regression Testing, Failure Handling, Temporary Files, Security and Robustness, Performance
