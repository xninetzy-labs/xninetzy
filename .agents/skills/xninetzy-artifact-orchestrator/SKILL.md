---
name: xninetzy-artifact-orchestrator
description: Artifact production operating system for long-form DOCX, PDF, PPTX, spreadsheet, diagram, and related deliverables. Use for coordinating requirements, template analysis, source management, content architecture, bounded production, integration, evidence auditing, artifact generation, rendering, structural QA, visual QA, accessibility, versioning, and checkpointing.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> specify -> inspect-template -> source -> architect -> produce -> integrate -> audit -> generate -> render -> qa -> revise -> freeze -> checkpoint -> deliver"
---

# Xninetzy Artifact Orchestrator

This skill is the **artifact-production layer** for academic, professional, technical, and project deliverables.

It coordinates the creation of:

* DOCX,
* PDF,
* PPTX,
* XLSX/spreadsheets,
* diagrams,
* structured reports,
* research documents,
* presentation decks,
* supporting artifact packages.

The objective is not merely to create a file. The objective is to create an artifact that is:

**requirement-aligned, evidence-backed, internally consistent, physically valid, visually verified, and ready for its intended use.**

The canonical lifecycle is:

**Discover → Specify → Inspect Template → Source → Architect → Produce → Integrate → Audit → Generate → Render → QA → Revise → Freeze → Checkpoint → Deliver**

## When to use

* producing a long document, deck, spreadsheet, or diagram package;
* coordinating multi-section or multi-format deliverables;
* integrating sections produced by different workers;
* running content, structural, and visual QA on a generated artifact.

## When NOT to use

* HEBAT-specific assignment workflow — use `hebat-academic` and `xninetzy-assignment-orchestrator`;
* repository code changes without artifact output — use the standard coding workflow;
* a single short document with no integration or visual QA needs.

## Core principles

* **Requirements before formatting.** Do not begin styling before understanding intended output, audience, required content, format, template, rubric, page/slide limits, citation requirements, required figures/tables, and submission constraints.
* **Artifact type determines the design system.** Do not force the DOCX standard onto presentations, spreadsheets, diagrams, dashboards, or technical reports. Each artifact type has its own appropriate design system. Use assignment-specific or client-specific requirements first; use general defaults only when no stronger requirement exists.
* **Content and presentation are separate QA dimensions.** An artifact can be content-correct but visually broken, or visually attractive but factually incorrect. Validate independently.

## Core workflow

1. **Discover.** Identify the artifact type, purpose, audience, and intended use. Determine whether a single worker is sufficient or whether bounded production across sections is required.
2. **Specify.** Extract functional, content, structural, visual, evidence, and delivery requirements into a typed requirement set.
3. **Inspect template.** Before building from an existing template, inspect page/slide dimensions, typography, margins, repeated layout patterns, master/layout behavior, branding elements, mandatory placeholders, and elements that must not be changed.
4. **Source.** Maintain a source ledger for substantial artifacts distinguishing provided sources, discovered sources, user-provided context, generated content, and derived calculations.
5. **Architect.** Create the document architecture (cover → TOC → body → references → appendix, or slide arc, or workbook structure) before writing a long artifact.
6. **Produce.** Long artifacts should be produced in bounded units: section, chapter, slide group, sheet, analysis module, appendix, or figure/table package. Each unit should have purpose, required evidence, output, status, and validator.
7. **Integrate.** Resolve duplicated arguments, inconsistent terminology, conflicting numbers, inconsistent dates, citation numbering, uneven depth, broken cross-references, repeated conclusions, incompatible visuals, and missing requirements. Do not simply concatenate independently generated sections.
8. **Audit.** Before final generation, inspect claim-source alignment, source metadata, coverage, inference vs finding, freshness, and consistency between prose and tables/figures.
9. **Generate.** Use artifact-appropriate tooling: structured DOCX generation, controlled PDF generation, `python-pptx` for decks, `openpyxl` for spreadsheets, dedicated diagram tools. Do not use a generic document workflow for spreadsheets merely because it is convenient.
10. **Render and inspect.** Always render and inspect the produced artifact before claiming visual quality. Capture screenshots or PDF pages, identify defects, and revise from the responsible source.
11. **QA.** Run content QA, structural QA, evidence QA, delivery QA, and where relevant accessibility QA. Fix critical/high defects before delivery.
12. **Revise.** Detect → classify severity → fix smallest responsible source → regenerate → re-render → reinspect. Do not patch only the generated PDF when the underlying DOCX/source is responsible.
13. **Freeze.** Once QA passes, identify the exact final artifact, freeze the verified version, record the final path, and avoid accidental edits.
14. **Checkpoint.** Persist a continuity checkpoint with artifact goal, completed stages, exact paths, important decisions, version, QA state, unresolved defects, next action, and resume hint.
15. **Deliver.** Provide the final submission-ready files and required links/materials through the appropriate channel.

## Artifact manifest

Every substantial artifact should have a working manifest:

```yaml
artifact:
artifact_type:
purpose:
audience:
source_requirements:
template:
content_scope:
page_or_slide_target:
citation_style:
required_sections:
required_tables:
required_figures:
design_system:
output_formats:
source_ledger:
section_owners:
qa_requirements:
delivery_constraints:
version:
```

Not every field is required for simple artifacts. For long artifacts, avoid starting production without a clear purpose, output type, and scope.

## Source ledger

Maintain a source ledger for substantial artifacts:

```text
source_id
title
type
origin
access_status
date
relevance
used_for
citation
verification_status
```

Distinguish provided sources, discovered sources, user-provided context, generated content, and derived calculations.

## Integration responsibilities

The integration stage resolves:

* duplicated arguments,
* inconsistent terminology,
* conflicting numbers,
* inconsistent dates,
* citation numbering,
* uneven depth,
* broken cross-references,
* repeated conclusions,
* incompatible visuals,
* missing requirements.

Do not simply concatenate independently generated sections.

## Canonical terminology

Establish terminology before integration.

Example:

```text
Canonical:
"retrieval-augmented generation"

Allowed:
"RAG"

Avoid alternating:
"RAG system"
"retrieval system"
"retrieval augmented AI"
"document QA system"
```

Unless they genuinely refer to different concepts. Terminology consistency improves both readability and evidence tracing.

## Numerical consistency

Important numbers should be reconciled across the artifact: totals, percentages, dates, sample sizes, dimensions, credit totals, benchmark results, financial figures, and figure/table values. If the same fact appears in multiple places, it should have one authoritative value.

## Citation integration

During integration: preserve source identity, resolve duplicate citations, normalize citation style, ensure citations support actual claims, update reference numbering, remove orphan references, and remove uncited references when the style requires it. Do not renumber citations manually without checking the entire artifact.

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

Check the generated structure by artifact type:

* **DOCX** — headings, paragraphs, tables, figures, sections, page breaks, TOC, references.
* **PDF** — page count, text presence, page order, links, figures, clipping, metadata when relevant.
* **PPTX** — slide count, layouts, text boxes, images, speaker notes, slide dimensions.
* **Spreadsheet** — sheets, formulas, ranges, values, references, charts, frozen panes, formatting.

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

Inspect for overflow, clipping, broken alignment, whitespace imbalance, inconsistent spacing, unreadable text, malformed tables, missing images, duplicated elements, accidental blank pages, inconsistent typography, and broken hyperlinks where visible. Do not rely solely on source code or document structure.

## Spreadsheet standards

Spreadsheets require a separate design and correctness workflow. Prioritize:

* data integrity,
* formula correctness,
* traceability,
* clean input/output separation,
* readable column widths,
* meaningful sheet names,
* frozen headers where helpful,
* validated calculations,
* appropriate number formats.

Do not apply DOCX typography rules to spreadsheets.

## Spreadsheet formula QA

For important workbooks:

* inspect formulas,
* verify references,
* check for errors,
* reconcile totals,
* test representative rows,
* confirm expected sheet dependencies.

When possible, use actual spreadsheet calculation/rendering workflows rather than treating formulas as plain text.

## Versioning

Long artifacts should have a clear version state:

```text
draft
draft-2
integrated
qa-1
revised
final
submitted
```

Do not label an artifact `final` before required QA is complete. After submission, distinguish **submitted version** from **latest local version**.

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

## Artifact defect taxonomy

Classify QA defects:

* **Critical** — prevents submission or changes meaning.
* **High** — major layout, evidence, or requirement failure.
* **Medium** — noticeable inconsistency or quality issue.
* **Low** — minor cosmetic issue.

Fix critical/high defects before delivery.

## No false QA claims

Never say `The layout is verified.` unless the rendered artifact was actually inspected. Never say `The file is correct.` when only file existence was checked. Use precise status: `File exists and opens; visual QA not yet completed.`

## Routing

* HEBAT academic deliverable → `hebat-academic`, `hebat-assignment`, `xninetzy-assignment-orchestrator`.
* Research document → `xninetzy-deep-research`.
* Persistence → `xninetzy-memory`.

## Reference map

* `references/templates.md` — DOCX, cover, tables, figures, PPTX, and spreadsheet design system defaults.
* `references/qa-and-delivery.md` — physical file QA, structural QA, rendering QA, visual QA, defect taxonomy, revision loop, freeze, output package, and standard QA checklist.

## Operating rules

The system must:

* understand requirements before building,
* analyze templates before reproducing them,
* maintain a source ledger for substantial artifacts,
* produce long artifacts in bounded units,
* integrate rather than concatenate,
* audit claims and citations,
* generate using artifact-appropriate tooling,
* verify the physical file,
* inspect rendered output before claiming visual quality,
* revise from the responsible source when defects appear,
* freeze the exact verified final version,
* never leave placeholders in a final artifact,
* distinguish local final from submitted final,
* checkpoint meaningful milestones.

The canonical artifact pipeline is:

**Requirements → Template Analysis → Source Ledger → Architecture → Bounded Production → Integration → Evidence Audit → Generation → Physical QA → Visual QA → Revision → Freeze → Checkpoint → Delivery**

The central objective is:

> **Do not merely generate a file. Produce a verified artifact whose content, evidence, structure, rendering, and delivery state can all be accounted for.**