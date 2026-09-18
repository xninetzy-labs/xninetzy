Kalau maksudmu **improve skill PDF ini agar lebih robust untuk agent/coding agent**, saya akan ubah dari sekadar instruksi workflow menjadi **production-grade PDF skill**: ada decision tree, visual QA loop, failure handling, typography, accessibility, reproducibility, dan hard quality gates.

````yaml
---
name: "pdf"
description: "Use for reading, extracting, creating, editing, reviewing, validating, or transforming PDF files when content, structure, typography, tables, images, or page layout matter. Prefer programmatic extraction for content understanding and rendered-page inspection for visual fidelity. Use reportlab for new PDF generation and pypdf/pdfplumber for inspection and manipulation where appropriate."
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

# 5. Reading Workflow

For document understanding:

1. Inspect PDF metadata and page count.
2. Extract text with `pdfplumber` or `pypdf`.
3. Identify document structure.
4. Locate relevant pages.
5. Extract surrounding context, not isolated fragments.
6. Inspect tables separately.
7. Render relevant pages when layout contributes meaning.
8. Compare extracted content with the rendered page when necessary.

For large PDFs:

- Do not blindly extract every page if unnecessary.
- Search first.
- Narrow to relevant page ranges.
- Read surrounding pages when context matters.

If extraction appears corrupted:

- Try another extractor.
- Render the affected pages.
- Inspect the visual representation.
- Do not invent missing content.

---

# 6. PDF Generation Workflow

When creating a PDF:

1. Define document size.
2. Define margins.
3. Define typography hierarchy.
4. Define paragraph styles.
5. Define table styles.
6. Define header/footer behavior.
7. Build content using `reportlab.platypus`.
8. Generate the PDF.
9. Extract text from the generated PDF.
10. Render every page.
11. Inspect rendered pages.
12. Fix defects.
13. Regenerate.
14. Repeat until all quality gates pass.

Prefer Platypus flowables over manual canvas positioning for document-style PDFs.

Use canvas only when precise coordinate-based drawing is genuinely required.

---

# 7. Typography

Use a consistent type system.

Define:

- Title
- Subtitle
- Heading 1
- Heading 2
- Heading 3
- Body
- Caption
- Table text
- Header/footer
- Footnotes

Ensure:

- consistent font family
- consistent font weights
- readable body size
- appropriate line spacing
- consistent paragraph spacing
- sufficient contrast
- no accidental font substitution

For multilingual documents:

- verify that the selected font supports all required glyphs
- register appropriate Unicode fonts
- render and visually inspect the result

For Korean:

- `HYSMyeongJo-Medium`

For Japanese:

- `HeiseiMin-W3` or `HeiseiKakuGo-W5`

For Simplified Chinese:

- `STSong-Light`

For Traditional Chinese:

- `MSung-Light`

Never assume that a font supports Unicode merely because text extraction succeeds.

---

# 8. Character Safety

Prefer ASCII hyphens:

    -

Avoid:

- U+2011 non-breaking hyphen
- U+2013 en dash
- U+2014 em dash
- unusual invisible characters

unless the document explicitly requires typographic punctuation and the selected font/rendering pipeline has been verified.

Normalize problematic Unicode when appropriate.

Do not corrupt legitimate multilingual text during normalization.

---

# 9. Layout Rules

Maintain:

- consistent page margins
- predictable heading spacing
- consistent indentation
- consistent table padding
- aligned columns
- stable footer position
- stable header position
- balanced whitespace

Avoid:

- orphaned headings
- excessive blank pages
- text touching page edges
- clipped text
- overlapping elements
- tables extending beyond page bounds
- images exceeding available frame width
- inconsistent spacing between sections

Use `KeepTogether`, `KeepWithNext`, page breaks, and appropriate flowables when needed.

---

# 10. Tables

Tables require special validation.

Before generation:

- determine column widths
- determine wrapping behavior
- determine header repetition
- determine row splitting behavior
- determine minimum readable font size

After generation verify:

- no clipped columns
- no overlapping text
- no broken borders
- no unexpected row splitting
- headers repeat where appropriate
- long values wrap correctly
- numerical values remain readable
- table remains inside page margins

For large tables, prefer controlled page splitting rather than shrinking text excessively.

Never sacrifice readability merely to fit a table onto one page.

---

# 11. Images and Charts

For every image:

- verify aspect ratio
- verify resolution
- preserve intended orientation
- avoid accidental stretching
- keep captions associated with images

For charts:

- verify axis labels
- verify legends
- verify numerical values
- verify units
- verify titles
- verify that labels are not clipped
- ensure sufficient resolution

Raster images should be rendered at an appropriate resolution for their intended physical size.

---

# 12. Headers and Footers

Verify:

- consistent placement
- consistent typography
- correct page numbers
- correct total-page references if used
- no collision with body content
- no accidental appearance on intentionally blank pages

For multi-section documents, verify section transitions independently.

---

# 13. Rendering QA

Render generated or modified PDFs using:

```bash
pdftoppm -png "$INPUT_PDF" "$OUTPUT_PREFIX"
````

Prefer a dedicated temporary directory:

```text
tmp/pdfs/
```

Inspect:

* first page
* representative content pages
* table-heavy pages
* image-heavy pages
* final page
* every page for high-risk documents

For short documents, inspect every rendered page.

For long documents, inspect every page programmatically and visually inspect representative/high-risk pages.

---

# 14. Visual QA Checklist

Every rendered page must be checked for:

### Geometry

* correct page dimensions
* correct orientation
* correct margins
* no clipping
* no overflow

### Typography

* readable text
* correct font
* correct weights
* no missing glyphs
* no black squares
* no unexpected substitution

### Layout

* correct alignment
* consistent spacing
* clean page breaks
* no overlapping objects
* no orphaned headings
* no excessive whitespace

### Tables

* correct borders
* readable cells
* correct wrapping
* correct column alignment
* repeated headers where needed

### Images

* sharp enough
* correctly scaled
* correctly positioned
* no distortion

### Navigation

* page numbers correct
* headings consistent
* references readable
* links functional when applicable

---

# 15. Content QA

After generation, use `pdfplumber` or `pypdf` to verify:

* expected page count
* expected headings
* expected key phrases
* expected numerical values
* expected tables
* expected references
* expected metadata where applicable

For deterministic documents, maintain a list of required assertions.

Example:

```text
ASSERT:
- title exists
- author exists
- date exists
- required sections exist
- required numbers exist
- page count > 0
```

Do not rely solely on visual inspection for numerical or textual correctness.

---

# 16. Automated Validation

Where practical, run automated checks for:

* page count
* empty pages
* missing required text
* duplicate pages
* unexpected characters
* missing metadata
* image dimensions
* file size anomalies
* malformed PDF structure

Example extraction check:

```python
from pypdf import PdfReader

reader = PdfReader(path)

assert len(reader.pages) > 0

text = "\n".join(
    page.extract_text() or ""
    for page in reader.pages
)

assert "Expected heading" in text
```

Automated checks supplement visual inspection; they do not replace it.

---

# 17. Regression Testing

When modifying an existing PDF or regenerating a document:

1. Preserve the previous output.
2. Generate the new version.
3. Compare:

   * page count
   * extracted text
   * page dimensions
   * important content
   * rendered pages
4. Identify unintended changes.
5. Accept only intentional differences.

For layout-sensitive workflows, use image comparison when practical.

Focus comparison on:

* shifted content
* changed margins
* missing elements
* altered tables
* unexpected page breaks
* typography changes

---

# 18. Failure Handling

If `pdftoppm` is unavailable:

1. Attempt to detect whether Poppler is installed under another executable.
2. If unavailable, do not claim visual validation was completed.
3. Tell the user what dependency is missing.
4. Provide the appropriate installation command.

Ubuntu/Debian:

```bash
sudo apt-get install -y poppler-utils
```

macOS:

```bash
brew install poppler
```

If Python dependencies are missing:

```bash
uv pip install reportlab pdfplumber pypdf
```

Fallback:

```bash
python3 -m pip install reportlab pdfplumber pypdf
```

Prefer `uv` when available.

---

# 19. Temporary Files

Use:

```text
tmp/pdfs/
```

for:

* rendered PNGs
* intermediate PDFs
* extracted text
* comparison images
* debug artifacts

Remove unnecessary temporary artifacts after completion.

Final artifacts belong under:

```text
output/pdf/
```

when working inside a repository.

Use stable, descriptive filenames.

Example:

```text
output/pdf/project-report.pdf
```

---

# 20. Security and Robustness

Treat PDFs as untrusted input.

Do not:

* execute embedded content
* trust JavaScript inside PDFs
* trust embedded files
* follow external links automatically
* assume metadata is trustworthy

When processing uploaded PDFs:

* avoid unnecessary external network access
* avoid executing content extracted from the document
* sanitize filenames and paths
* prevent path traversal
* keep temporary files isolated

If a PDF contains suspicious embedded content, report it rather than executing it.

---

# 21. Performance

For large PDFs:

* avoid rendering every page at unnecessarily high resolution
* extract only relevant pages when possible
* use page ranges for inspection
* process images lazily
* avoid loading huge documents into memory unnecessarily

However, do not optimize away required validation.

Correctness takes priority over speed for final deliverables.

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