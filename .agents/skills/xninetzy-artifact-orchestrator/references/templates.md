# Xninetzy Artifact Orchestrator — Templates and Design System

This reference expands the DOCX, cover, table, figure, PPTX, and spreadsheet design system defaults. Read it when generating or inspecting an artifact's visual and structural foundation.

## DOCX general standard

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

## Cover standard

When an academic DOCX requires the general HEBAT cover:

```text
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

The lecturer is required when the course instructions require it. Do not hard-code a specific lecturer for a generic artifact. Retrieve the correct lecturer from current course context.

## Cover asset rule

When the official UNAIR branding asset is available at the configured location:

`/home/misbahul45/code/xninetzy/assets/branding/logo-unair.png`

reuse the original asset rather than regenerating it. Verify its existence before use. Do not claim that it was used if the file was unavailable.

## Cover QA

For an academic cover:

* exactly one page,
* logo present once,
* logo visually centered,
* title not clipped,
* metadata visible,
* lecturer present when required,
* no second-page overflow.

Do not verify only by text extraction. Inspect the rendered page.

## Table and figure QA

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

## Presentation standard

PPTX design must adapt to the presentation's purpose. Possible modes:

* academic lecture,
* research defense,
* technical walkthrough,
* project presentation,
* startup pitch,
* portfolio presentation.

Do not automatically apply a futuristic style to every deck.

## Futuristic tech / AI startup pitch preset

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

Electric blue `#245BFF`, violet `#7B3FF2`, magenta highlights.

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

## Slide architecture contract

Every slide should have an explicit semantic role. Recommended schema:

```yaml
purpose:
headline:
key_message:
evidence:
visual:
citation:
speaker_note:
transition:
```

Not every field must contain content. However, every slide should answer: **Why does this slide exist?**

## Slide density

Avoid putting a document page onto a slide. Prefer:

* one primary message,
* supporting evidence,
* one visual idea,
* concise text.

Move elaboration into speaker notes when appropriate.

## Spreadsheet artifact standard

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

## Content architecture

Before writing a long artifact, create its architecture.

For documents:

```text
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

For slides:

```text
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

```text
Input
→ Transformation
→ Calculation
→ Validation
→ Summary
→ Visualization
```

Do not create empty sections just to follow a generic template.

## Bounded production

Long artifacts should be produced in bounded units:

* section,
* chapter,
* slide group,
* sheet,
* analysis module,
* appendix,
* figure/table package.

Each unit should have purpose, required evidence, output, status, and validator. This reduces drift, repetition, and context loss.

## Section ownership

For long collaborative artifacts, assign explicit ownership:

```yaml
section_owners:
  introduction: worker_a
  research: worker_b
  methodology: worker_c
  analysis: worker_d
  conclusion: worker_e
```

Ownership does not remove integration responsibility. Every artifact must undergo a global integration pass.