# pdf — §14–21

Contents: 14. Visual QA Checklist; 15. Content QA; 16. Automated Validation; 17. Regression Testing; 18. Failure Handling; 19. Temporary Files; 20. Security and Robustness; 21. Performance

## 14. Visual QA Checklist

Every rendered page must be checked for:

#### Geometry

* correct page dimensions
* correct orientation
* correct margins
* no clipping
* no overflow

#### Typography

* readable text
* correct font
* correct weights
* no missing glyphs
* no black squares
* no unexpected substitution

#### Layout

* correct alignment
* consistent spacing
* clean page breaks
* no overlapping objects
* no orphaned headings
* no excessive whitespace

#### Tables

* correct borders
* readable cells
* correct wrapping
* correct column alignment
* repeated headers where needed

#### Images

* sharp enough
* correctly scaled
* correctly positioned
* no distortion

#### Navigation

* page numbers correct
* headings consistent
* references readable
* links functional when applicable

---

## 15. Content QA

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

## 16. Automated Validation

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

## 17. Regression Testing

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

## 18. Failure Handling

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

## 19. Temporary Files

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

## 20. Security and Robustness

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

## 21. Performance

For large PDFs:

* avoid rendering every page at unnecessarily high resolution
* extract only relevant pages when possible
* use page ranges for inspection
* process images lazily
* avoid loading huge documents into memory unnecessarily

However, do not optimize away required validation.

Correctness takes priority over speed for final deliverables.

---
