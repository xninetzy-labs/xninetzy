# Xninetzy Artifact Orchestrator

```yaml id="k3w8pn"
---
name: xninetzy-artifact-orchestrator
description: General-purpose artifact production operating system for long-form DOCX, PDF, PPTX, spreadsheet, diagram, and related deliverables. Coordinates requirements, template analysis, source management, content architecture, bounded production, integration, evidence auditing, artifact generation, rendering, structural QA, visual QA, accessibility checks, versioning, and checkpointing. Adapts formatting to the actual assignment or artifact type instead of forcing course-specific styling.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> specify -> inspect-template -> source -> architect -> produce -> integrate -> audit -> generate -> render -> qa -> revise -> freeze -> checkpoint -> deliver"
---
```

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

The objective is not merely to create a file.

The objective is to create an artifact that is:

**requirement-aligned, evidence-backed, internally consistent, physically valid, visually verified, and ready for its intended use.**

The canonical lifecycle is:

**Discover → Specify → Inspect Template → Source → Architect → Produce → Integrate → Audit → Generate → Render → QA → Revise → Freeze → Checkpoint → Deliver**

---

# 1. Core Principles

## 1.1 Requirements before formatting

Do not begin styling before understanding:

* intended output,
* audience,
* required content,
* required format,
* template,
* rubric,
* page/slide limits,
* citation requirements,
* required figures/tables,
* submission constraints.

Formatting is subordinate to the actual artifact requirement.

---

## 1.2 Artifact type determines the design system

Do not force the DOCX standard onto:

* presentations,
* spreadsheets,
* diagrams,
* dashboards,
* technical reports.

Each artifact type has its own appropriate design system.

Use assignment-specific or client-specific requirements first.

Use general defaults only when no stronger requirement exists.

---

## 1.3 Content and presentation are separate QA dimensions

An artifact can be:

**content-correct but visually broken**

or:

**visually attractive but factually incorrect.**

Therefore validate independently:

```text id="94yg9n"
Content QA
+
Structural QA
+
Visual QA
+
Evidence QA
+
Delivery QA
```

---

# 2. Artifact Manifest

Every substantial artifact should have a working manifest.

```yaml id="d85a9f"
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

Not every field is required for simple artifacts.

For long artifacts, avoid starting production without a clear purpose, output type, and scope.

---

# 3. Requirements Intake

Extract:

### Functional requirements

What the artifact must contain or do.

### Content requirements

What topics, arguments, data, or evidence must appear.

### Structural requirements

Required sections, ordering, page/slide limits, or sheet structure.

### Visual requirements

Typography, branding, dimensions, colors, layout, or template constraints.

### Evidence requirements

Sources, citations, calculations, screenshots, benchmarks, references.

### Delivery requirements

Filename, format, location, submission channel, and version.

---

# 4. Template Analysis

Before building from an existing template:

1. inspect page/slide dimensions,
2. inspect typography,
3. inspect margins and spacing,
4. inspect repeated layout patterns,
5. inspect master/layout behavior,
6. inspect branding elements,
7. identify mandatory placeholders,
8. identify elements that must not be changed.

Do not infer a template rule from one accidental element.

When the template conflicts with explicit instructions, use the authoritative instruction.

---

# 5. Source Ledger

Maintain a source ledger for substantial artifacts.

Conceptually:

```text id="v8ox8w"
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

The ledger should distinguish:

* provided sources,
* discovered sources,
* user-provided context,
* generated content,
* derived calculations.

---

# 6. Content Architecture

Before writing a long artifact, create its architecture.

For documents:

```text id="ib5j0v"
Cover
→ TOC
→ Introduction
→ Context / Problem
→ Analysis
→ Method / Process
→ Findings
→ Discussion
→ Conclusion
→ References
→ Appendix
```

Adapt to actual requirements.

For slides:

```text id="4a4b2s"
Opening
→ Problem
→ Context
→ Insight
→ Approach
→ Evidence
→ Solution
→ Demonstration
→ Impact
→ Closing
```

For spreadsheets:

```text id="x1dbya"
Input
→ Transformation
→ Calculation
→ Validation
→ Summary
→ Visualization
```

Do not create empty sections just to follow a generic template.

---

# 7. Bounded Production

Long artifacts should be produced in bounded units.

Possible units:

* section,
* chapter,
* slide group,
* sheet,
* analysis module,
* appendix,
* figure/table package.

Each unit should have:

```text id="e9r5c4"
purpose
required evidence
output
status
validator
```

This reduces drift, repetition, and context loss.

---

# 8. Section Ownership

For long collaborative artifacts, assign explicit ownership:

```yaml id="y1k9pl"
section_owners:
  introduction: worker_a
  research: worker_b
  methodology: worker_c
  analysis: worker_d
  conclusion: worker_e
```

Ownership does not remove integration responsibility.

Every artifact must undergo a global integration pass.

---

# 9. Integration

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

---

# 10. Canonical Terminology

Establish terminology before integration.

Example:

```text id="5ldg0d"
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

Unless they genuinely refer to different concepts.

Terminology consistency improves both readability and evidence tracing.

---

# 11. Numerical Consistency

Important numbers should be reconciled across the artifact.

Check:

* totals,
* percentages,
* dates,
* sample sizes,
* dimensions,
* credit totals,
* benchmark results,
* financial figures,
* figure/table values.

If the same fact appears in multiple places, it should have one authoritative value.

---

# 12. Citation Integration

During integration:

* preserve source identity,
* resolve duplicate citations,
* normalize citation style,
* ensure citations support actual claims,
* update reference numbering,
* remove orphan references,
* remove uncited references when the style requires it.

Do not renumber citations manually without checking the entire artifact.

---

# 13. Evidence Audit

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

---

# 14. Artifact Generator Selection

Use the most appropriate generation tool for the artifact.

### DOCX

Prefer a structured DOCX generation workflow.

### PDF

Generate from a controlled document or PDF-native workflow as appropriate.

### PPTX

Use a presentation generation workflow such as `python-pptx` when appropriate.

### Spreadsheet

Use spreadsheet-native tooling such as `openpyxl` or `artifact_tool`, following the spreadsheet-specific standards.

Do not use a generic document workflow for spreadsheets merely because it is convenient.

---

# 15. Physical File QA

After generation, verify:

* file exists,
* path is exact,
* non-zero size,
* expected file type,
* file opens,
* expected page/slide/sheet count,
* no obvious corruption.

A successful tool call is not proof that the artifact is valid.

---

# 16. Structural QA

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

---

# 17. Rendering QA

Never claim visual quality without inspecting a rendered representation.

Recommended pipeline:

```text id="n5mz3a"
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

---

# 18. Visual QA

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

---

# 19. DOCX General Standard

Use these as **default fallbacks only when no stronger requirement exists**:

### Page

* A4: 21.0 × 29.7 cm
* top/bottom: 2.3 cm
* left/right: 2.5 cm

### Body

* Times New Roman
* 12 pt
* black `#000000`
* justified
* line spacing 1.5
* widow/orphan control

### Headings

* H1: 24 pt bold
* H2: 16 pt bold
* H3: 13 pt bold
* black

### Tables

* light gray header `#D9D9D9`
* black text
* fixed layout
* readable dimensions
* controlled wrapping

### Captions

* 9 pt
* italic
* gray `#555555`
* centered unless assignment specifies otherwise

### General

* no unnecessary headers/footers
* no em dash
* consistent spacing
* no placeholder text in final output

Explicit assignment/template instructions always override these defaults.

---

# 20. Cover Standard

When an academic DOCX requires the general HEBAT cover:

```text id="ak2qjt"
Title
↓
Centered UNAIR logo
↓
Identity
↓
Lecturer
↓
Academic metadata
```

Default properties:

* one page,
* single logo,
* logo 5.5 cm,
* centered,
* title above,
* metadata below,
* no decorative icons,
* no em dash.

The lecturer is required when the course instructions require it.

Do not hard-code a specific lecturer for a generic artifact.

Retrieve the correct lecturer from current course context.

---

# 21. Cover Asset Rule

When the official UNAIR branding asset is available at the configured location:

`/home/misbahul45/code/xninetzy/assets/branding/logo-unair.png`

reuse the original asset rather than regenerating it.

Verify its existence before use.

Do not claim that it was used if the file was unavailable.

---

# 22. Cover QA

For an academic cover:

* exactly one page,
* logo present once,
* logo visually centered,
* title not clipped,
* metadata visible,
* lecturer present when required,
* no second-page overflow.

Do not verify only by text extraction.

Inspect the rendered page.

---

# 23. Table and Figure QA

For every table:

* title/caption exists when required,
* header is readable,
* columns are not clipped,
* totals are correct,
* units are clear.

For every figure:

* resolution is sufficient,
* labels are readable,
* caption exists,
* source is present when required,
* figure is referenced in the surrounding text when appropriate.

---

# 24. Presentation Standard

PPTX design must adapt to the presentation's purpose.

Possible modes:

* academic lecture,
* research defense,
* technical walkthrough,
* project presentation,
* startup pitch,
* portfolio presentation.

Do not automatically apply a futuristic style to every deck.

---

# 25. Futuristic Tech / AI Startup Pitch Preset

When the assignment explicitly requires this style, use:

### Canvas

16:9 widescreen.

### Base

Pure black `#000000`.

### Primary text

White `#FFFFFF`.

### Secondary text

Light gray `#CCCCCC`.

### Accent

Electric blue `#245BFF`
Violet `#7B3FF2`
Magenta highlights.

### Headline

Extra-bold geometric sans-serif, uppercase, tight spacing.

### Body

Light/regular sans-serif with generous spacing.

### Cards

Dark rounded rectangles with thin borders and minimal shadow.

### Illustration

Neon light trails and abstract technology imagery.

### Composition

Asymmetric, spacious, high negative space.

Approximate visual balance:

**70% black + 20% white/gray + 10% neon accents**

This preset must only be used when the style is appropriate or explicitly requested.

---

# 26. Slide Architecture Contract

Every slide should have an explicit semantic role.

Recommended schema:

```yaml id="d2vqm2"
purpose:
headline:
key_message:
evidence:
visual:
citation:
speaker_note:
transition:
```

Not every field must contain content.

However, every slide should answer:

**Why does this slide exist?**

---

# 27. Slide Density

Avoid putting a document page onto a slide.

Prefer:

* one primary message,
* supporting evidence,
* one visual idea,
* concise text.

Move elaboration into speaker notes when appropriate.

---

# 28. Spreadsheet Artifact Standard

Spreadsheets require a separate design and correctness workflow.

Prioritize:

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

---

# 29. Spreadsheet Formula QA

For important workbooks:

* inspect formulas,
* verify references,
* check for errors,
* reconcile totals,
* test representative rows,
* confirm expected sheet dependencies.

When possible, use actual spreadsheet calculation/rendering workflows rather than treating formulas as plain text.

---

# 30. Versioning

Long artifacts should have a clear version state.

Example:

```text id="vgqzxa"
draft
draft-2
integrated
qa-1
revised
final
submitted
```

Do not label an artifact `final` before required QA is complete.

After submission, distinguish:

**submitted version**

from:

**latest local version**.

---

# 31. Freeze Before Delivery

Once QA passes:

1. identify the exact final artifact,
2. freeze the verified version,
3. record the final path,
4. verify checksum/version metadata when useful,
5. avoid accidental edits afterward.

A submission package should correspond to the verified artifact.

---

# 32. Output Package

When multiple artifacts are required, produce a clear package.

Example:

```text id="9p8z7y"
deliverable/
├── final_report.docx
├── final_report.pdf
├── presentation.pptx
├── spreadsheet.xlsx
└── sources/
```

Do not include temporary files unless requested.

---

# 33. Placeholder Audit

Before delivery, search for placeholders such as:

* TODO,
* TBD,
* lorem ipsum,
* "insert figure",
* "add citation",
* "will be updated",
* "[NAME]",
* "[LINK]",
* empty template fields.

No unresolved placeholder should remain in the final artifact unless explicitly intended.

---

# 34. Link Audit

Verify important links:

* URLs are complete,
* links point to intended resources,
* prototype links reference the correct version,
* submission-related links are not accidentally private or invalid.

When link verification is impossible, label it accordingly.

---

# 35. Page and Slide Count

Where a requirement specifies length:

* verify actual page count,
* verify actual slide count,
* check appendix rules,
* distinguish required pages from cover/TOC pages,
* ensure hidden or blank slides do not accidentally count.

Do not estimate length from word count alone.

---

# 36. Accessibility

When appropriate, check:

* readable font sizes,
* sufficient contrast,
* logical reading order,
* meaningful slide/document hierarchy,
* descriptive captions,
* useful alternative text where supported,
* non-color-only distinctions.

Accessibility requirements should follow the target artifact and assignment context.

---

# 37. Artifact Defect Taxonomy

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

---

# 38. Revision Loop

Use:

```text id="7i5p9y"
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

---

# 39. No False QA Claims

Never say:

> "The layout is verified."

unless the rendered artifact was actually inspected.

Never say:

> "The file is correct."

when only file existence was checked.

Use precise status:

> File exists and opens; visual QA not yet completed.

---

# 40. Checkpointing

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

---

# 41. Completion Contract

An artifact is complete only when the relevant checks have passed.

Return:

**Artifact identity**
Type, name, version, exact path.

**Requirement status**
Coverage of required elements.

**Evidence status**
Citation/source/validation state.

**Generation status**
Whether the physical file was successfully created.

**Structural QA**
Whether the artifact opens and contains the expected structure.

**Visual QA**
Whether the rendered result was inspected.

**Known defects**
Any remaining issues.

**Final state**
Draft, QA-ready, final, or submitted.

**Checkpoint status**
Whether continuity information was persisted when required.

**Next action**
One bounded action if anything remains.

---

# 42. Standard Artifact QA Checklist

```text id="9a5q0q"
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

---

# 43. Operating Rules

The system must:

**understand requirements before building,**

**analyze templates before reproducing them,**

**maintain a source ledger for substantial artifacts,**

**produce long artifacts in bounded units,**

**integrate rather than concatenate,**

**audit claims and citations,**

**generate using artifact-appropriate tooling,**

**verify the physical file,**

**inspect rendered output before claiming visual quality,**

**revise from the responsible source when defects appear,**

**freeze the exact verified final version,**

**never leave placeholders in a final artifact,**

**distinguish local final from submitted final,**

**checkpoint meaningful milestones.**

The canonical artifact pipeline is:

**Requirements → Template Analysis → Source Ledger → Architecture → Bounded Production → Integration → Evidence Audit → Generation → Physical QA → Visual QA → Revision → Freeze → Checkpoint → Delivery**

The central objective is:

> **Do not merely generate a file. Produce a verified artifact whose content, evidence, structure, rendering, and delivery state can all be accounted for.**
