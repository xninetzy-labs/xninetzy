# pdf — §5–13

Contents: 5. Reading Workflow; 6. PDF Generation Workflow; 7. Typography; 8. Character Safety; 9. Layout Rules; 10. Tables; 11. Images and Charts; 12. Headers and Footers; 13. Rendering QA

## 5. Reading Workflow

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

## 6. PDF Generation Workflow

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

## 7. Typography

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

## 8. Character Safety

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

## 9. Layout Rules

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

## 10. Tables

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

## 11. Images and Charts

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

## 12. Headers and Footers

Verify:

- consistent placement
- consistent typography
- correct page numbers
- correct total-page references if used
- no collision with body content
- no accidental appearance on intentionally blank pages

For multi-section documents, verify section transitions independently.

---

## 13. Rendering QA

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
