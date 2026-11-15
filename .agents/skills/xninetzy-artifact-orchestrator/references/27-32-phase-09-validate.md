# xninetzy-artifact-orchestrator — §27–32

Contents: 27. Phase 09 — VALIDATE; 28. Phase 10 — RENDER; 29. Phase 11 — QA; 30. Phase 12 — REVISE; 31. Defect Locality; 32. Revalidation Dependency

## 27. Phase 09 — VALIDATE

Validation should distinguish:

```text
content
structure
evidence
technical state
```

Each validator returns:

```text
PASS
FAIL
PARTIAL
UNKNOWN
```

Do not replace `UNKNOWN` with `PASS`.

---

## 28. Phase 10 — RENDER

Whenever layout materially affects quality:

```text
source
→ generate
→ render
→ inspect
```

Examples:

```text
DOCX
→ PDF / rendered pages

PPTX
→ rendered slides

Spreadsheet
→ rendered sheets / representative previews

Diagram
→ raster/vector preview
```

Rendering is an observation of the produced artifact, not proof of source correctness.

---

## 29. Phase 11 — QA

Run the applicable checks:

```text
content QA
requirement QA
evidence QA
structural QA
technical QA
visual QA
accessibility QA
delivery QA
```

Detailed QA policy belongs to:

```text
references/qa-and-delivery.md
```

---

## 30. Phase 12 — REVISE

Revision loop:

```text
detect defect
→ classify
→ identify responsible source
→ change source
→ regenerate
→ rerender
→ revalidate
```

Prefer correcting:

```text
source
```

over:

```text
derived output
```

when the source caused the defect.

---

## 31. Defect Locality

A defect should be fixed at the smallest responsible layer.

Examples:

```text
wrong content
→ source content

wrong pagination
→ document structure/layout

wrong PDF rendering
→ conversion/source layout

wrong spreadsheet formula
→ workbook logic

wrong visual theme
→ design system
```

Do not hide an upstream defect with downstream patches.

---

## 32. Revalidation Dependency

A change invalidates only the affected evidence/validators when dependency is known.

Examples:

```text
content change
→ content + citation QA

layout change
→ visual + structural QA

source change
→ evidence + citation + affected content QA

package change
→ delivery QA
```

When impact is uncertain:

```text
revalidate broader scope
```

---
