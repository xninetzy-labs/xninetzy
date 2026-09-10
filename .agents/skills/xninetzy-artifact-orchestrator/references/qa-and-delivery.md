# Xninetzy Artifact Orchestrator — QA and Delivery

This reference expands physical file QA, structural QA, rendering QA, visual QA, defect taxonomy, revision loop, freeze protocol, output package, and standard QA checklist. Read it when finalizing or auditing an artifact.

## Physical file QA

After generation, verify:

* file exists,
* path is exact,
* non-zero size,
* expected file type,
* file opens,
* expected page/slide/sheet count,
* no obvious corruption.

A successful tool call is not proof that the artifact is valid.

## Structural QA

Check the generated structure.

### DOCX

* headings,
* paragraphs,
* tables,
* figures,
* sections,
* page breaks,
* TOC,
* references.

### PDF

* page count,
* text presence,
* page order,
* links,
* figures,
* clipping,
* metadata when relevant.

### PPTX

* slide count,
* layouts,
* text boxes,
* images,
* speaker notes,
* slide dimensions.

### Spreadsheet

* sheets,
* formulas,
* ranges,
* values,
* references,
* charts,
* frozen panes,
* formatting.

## Rendering QA

Never claim visual quality without inspecting a rendered representation. Recommended pipeline:

```text
Source Artifact
   ↓
Generate
   ↓
Render / Preview
   ↓
Inspect
   ↓
Identify defects
   ↓
Revise
   ↓
Render again
```

Visual inspection is mandatory when layout materially affects quality.

## Visual QA

Inspect for:

* overflow,
* clipping,
* broken alignment,
* whitespace imbalance,
* inconsistent spacing,
* unreadable text,
* malformed tables,
* missing images,
* duplicated elements,
* accidental blank pages,
* inconsistent typography,
* broken hyperlinks where visible.

Do not rely solely on source code or document structure.

## Evidence audit

Before final generation, inspect:

### Claim-source alignment

Does the source support the claim?

### Metadata

Is the source identity correct?

### Coverage

Are important claims supported?

### Inference

Are interpretations clearly distinguished from source findings?

### Freshness

Are time-sensitive claims current?

### Consistency

Do tables, figures, and prose agree?

## Artifact generator selection

Use the most appropriate generation tool for the artifact:

* **DOCX** — prefer a structured DOCX generation workflow.
* **PDF** — generate from a controlled document or PDF-native workflow as appropriate.
* **PPTX** — use a presentation generation workflow such as `python-pptx` when appropriate.
* **Spreadsheet** — use spreadsheet-native tooling such as `openpyxl` or `artifact_tool`, following the spreadsheet-specific standards.

Do not use a generic document workflow for spreadsheets merely because it is convenient.

## Artifact defect taxonomy

Classify QA defects:

### Critical

Prevents submission or changes meaning.

### High

Major layout, evidence, or requirement failure.

### Medium

Noticeable inconsistency or quality issue.

### Low

Minor cosmetic issue.

Fix critical/high defects before delivery.

## Revision loop

Use:

```text
Detect defect
↓
Classify severity
↓
Fix smallest responsible source
↓
Regenerate
↓
Re-render
↓
Reinspect
```

Do not patch only the generated PDF when the underlying DOCX/source is responsible, unless a final-output-only operation is explicitly intended.

## No false QA claims

Never say: `The layout is verified.` unless the rendered artifact was actually inspected.

Never say: `The file is correct.` when only file existence was checked.

Use precise status: `File exists and opens; visual QA not yet completed.`

## Freeze before delivery

Once QA passes:

1. identify the exact final artifact,
2. freeze the verified version,
3. record the final path,
4. verify checksum/version metadata when useful,
5. avoid accidental edits afterward.

A submission package should correspond to the verified artifact.

## Output package

When multiple artifacts are required, produce a clear package:

```text
deliverable/
├── final_report.docx
├── final_report.pdf
├── presentation.pptx
├── spreadsheet.xlsx
└── sources/
```

Do not include temporary files unless requested.

## Placeholder audit

Before delivery, search for placeholders such as TODO, TBD, lorem ipsum, "insert figure," "add citation," "will be updated," `[NAME]`, `[LINK]`, or empty template fields. No unresolved placeholder should remain in the final artifact unless explicitly intended.

## Link audit

Verify important links: URLs are complete, links point to intended resources, prototype links reference the correct version, and submission-related links are not accidentally private or invalid. When link verification is impossible, label it accordingly.

## Page and slide count

Where a requirement specifies length:

* verify actual page count,
* verify actual slide count,
* check appendix rules,
* distinguish required pages from cover/TOC pages,
* ensure hidden or blank slides do not accidentally count.

Do not estimate length from word count alone.

## Accessibility

When appropriate, check readable font sizes, sufficient contrast, logical reading order, meaningful slide/document hierarchy, descriptive captions, useful alternative text where supported, and non-color-only distinctions. Accessibility requirements should follow the target artifact and assignment context.

## Checkpointing

After substantial artifact milestones, create a continuity checkpoint containing:

* artifact goal,
* completed stages,
* exact artifact paths,
* important decisions,
* version,
* QA state,
* unresolved defects,
* next action,
* resume hint.

Use the Memory Chat system when persistence is required.

## Standard artifact QA checklist

```text
[ ] Requirements verified
[ ] Template analyzed
[ ] Sources recorded
[ ] Architecture defined
[ ] Bounded sections/slides/sheets produced
[ ] Integration completed
[ ] Citation/evidence audit completed
[ ] Artifact generated
[ ] Physical file verified
[ ] Structural QA completed
[ ] Rendered preview inspected
[ ] Visual QA completed
[ ] Placeholders removed
[ ] Links checked
[ ] Length/page/slide constraints checked
[ ] Final version frozen
[ ] Checkpoint saved when required
```

## Completion contract

An artifact is complete only when the relevant checks have passed. Return:

**Artifact identity** — type, name, version, exact path.

**Requirement status** — coverage of required elements.

**Evidence status** — citation/source/validation state.

**Generation status** — whether the physical file was successfully created.

**Structural QA** — whether the artifact opens and contains the expected structure.

**Visual QA** — whether the rendered result was inspected.

**Known defects** — any remaining issues.

**Final state** — draft, QA-ready, final, or submitted.

**Checkpoint status** — whether continuity information was persisted when required.

**Next action** — one bounded action if anything remains.