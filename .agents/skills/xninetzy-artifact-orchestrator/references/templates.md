# Xninetzy Artifact Orchestrator — Templates and Design Systems

This reference defines default artifact-specific design and structural patterns.

Read it when:

```text
designing a document
reproducing a template
building a presentation
structuring a spreadsheet
creating diagrams or infographics
selecting artifact-specific defaults
```

These are **fallback defaults**.

Explicit assignment, client, institutional, brand, or template requirements always
override them.

---

# 1. Design-System Precedence

Use:

```text
explicit artifact requirement
    >
authoritative existing template
    >
brand/client/institutional standard
    >
artifact-specific default
    >
generic fallback
```

Never override a stronger requirement with a visual preference.

---

# 2. Artifact Design Contract

Every substantial artifact should define:

```yaml
design_contract:
  artifact_type:
  dimensions:
  grid:
  typography:
  spacing:
  hierarchy:
  color:
  components:
  accessibility:
  output_constraints:
```

Only fields relevant to the artifact are required.

---

# 3. DOCX Default

Unless a stronger requirement exists:

```yaml
document:
  page:
    size: A4
    width: 21.0 cm
    height: 29.7 cm
    margins:
      top: 2.3 cm
      bottom: 2.3 cm
      left: 2.5 cm
      right: 2.5 cm

  body:
    font: Times New Roman
    size: 12 pt
    color: "#000000"
    alignment: justified
    line_spacing: 1.5
    widow_orphan_control: true

  headings:
    h1:
      size: 24 pt
      weight: bold
    h2:
      size: 16 pt
      weight: bold
    h3:
      size: 13 pt
      weight: bold

  tables:
    layout: fixed
    header_background: "#D9D9D9"
    text_color: "#000000"

  captions:
    size: 9 pt
    italic: true
    color: "#555555"

  general:
    decorative_elements: minimal
    em_dash: disallowed
```

These are not mandatory when the assignment specifies different formatting.

---

# 4. DOCX Heading Rules

Headings should be:

```text
informative
hierarchical
consistent
searchable
```

Prefer:

```text
2.5 Feasibility Analysis in the Surabaya Context
```

over:

```text
2.5 Why This Is Easy
```

Do not use decorative heading prefixes unless required.

---

# 5. DOCX Cover

When an academic cover is required:

```text
Title
↓
Institutional Logo
↓
Student / Team Identity
↓
Lecturer
↓
Program / Faculty / University
↓
City / Year
```

Default:

```text
one page
single logo
centered logo
balanced vertical spacing
no unnecessary icons
no accidental header/footer
```

Do not hard-code institutional identity.

Use the current authoritative course/assignment context.

---

# 6. Cover Asset Rule

When an authoritative branding asset is available:

```text
reuse original asset
```

instead of:

```text
regenerate equivalent asset
```

Verify:

```text
asset exists
asset identity is correct
aspect ratio is preserved
placement is correct
```

Do not claim an asset was used if it was unavailable.

---

# 7. Table Design

Use tables when they improve:

```text
comparison
organization
traceability
summary
```

Default:

```text
fixed layout
readable widths
clear headers
controlled wrapping
consistent borders
minimal decoration
```

Do not compress tables until they become unreadable.

---

# 8. Figure Design

Important figures should contain:

```text
figure number
informative caption
source when applicable
sufficient resolution
clear relationship to surrounding content
```

A figure should have a semantic purpose.

Avoid decorative visuals that do not support the artifact's message.

---

# 9. Table / Figure Semantics

Where appropriate:

```text
Table
→ referenced in surrounding text
→ interpreted or discussed

Figure
→ referenced in surrounding text
→ interpreted or discussed
```

Do not insert visuals without explaining their relevance when the artifact is
analytical or academic.

---

# 10. Table QA Contract

Every important table should be checkable for:

```text
headers
units
values
totals
source
column clipping
row consistency
number formatting
```

---

# 11. Figure QA Contract

Every important figure should be checkable for:

```text
resolution
labels
caption
source
cropping
alignment
legibility
semantic relevance
```

---

# 12. Presentation Modes

Choose design mode according to purpose:

```text
academic lecture
research defense
technical walkthrough
project presentation
startup pitch
portfolio
```

Do not automatically apply one style to every presentation.

---

# 13. Presentation Canvas

Default:

```text
16:9 widescreen
```

Override when the presentation specification requires another format.

---

# 14. Presentation Slide Contract

Each slide should conceptually define:

```yaml
slide:
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

Every slide should have a reason to exist.

---

# 15. Slide Architecture

General default:

```text
Opening
→ Context
→ Problem
→ Evidence
→ Insight
→ Approach
→ Solution
→ Validation
→ Impact
→ Closing
```

Adapt according to the actual narrative.

---

# 16. Slide Density

Avoid turning a document page into a slide.

Prefer:

```text
one primary message
+
supporting evidence
+
one dominant visual idea
```

Move secondary explanation into speaker notes when appropriate.

---

# 17. Presentation Typography

Use a clear distinction between:

```text
headline
supporting statement
body
caption
source
```

Do not shrink text simply to fit more content.

When content does not fit:

```text
reduce content
→ restructure slide
→ split slide
```

before:

```text
reduce font size excessively
```

---

# 18. Futuristic Tech / AI Pitch Preset

Use only when explicitly appropriate.

```yaml
pitch_preset:
  canvas: 16:9

  background: "#000000"
  primary_text: "#FFFFFF"
  secondary_text: "#CCCCCC"

  accents:
    - "#245BFF"
    - "#7B3FF2"
    - magenta_highlight

  headline:
    weight: extra-bold
    casing: uppercase

  body:
    weight: regular
    spacing: generous

  cards:
    shape: rounded
    background: dark
    border: thin

  composition:
    negative_space: high
    visual_balance: asymmetric
```

Do not apply this preset to ordinary academic decks unless appropriate.

---

# 19. Spreadsheet Design

Spreadsheets require a different mental model:

```text
Input
→ Transformation
→ Calculation
→ Validation
→ Summary
→ Visualization
```

Prioritize:

```text
data integrity
formula correctness
traceability
input/output separation
readable widths
meaningful sheet names
frozen headers when useful
correct number formats
```

---

# 20. Spreadsheet Structure

Prefer meaningful sheets such as:

```text
Input
Raw_Data
Transform
Calculation
Validation
Summary
Visualization
```

Use names that reflect actual workbook semantics.

Avoid unnecessary duplication of the same dataset.

---

# 21. Spreadsheet Formula Design

Important formulas should be:

```text
consistent
traceable
reconciled
```

Avoid hiding business logic in unreadable formulas when a helper column or
calculation sheet materially improves auditability.

---

# 22. Spreadsheet Number Formats

Use formats appropriate to:

```text
currency
percentage
date
time
integer
decimal
ratio
identifier
```

Do not store identifiers as numeric values when doing so can alter their meaning,
such as leading-zero codes.

---

# 23. Spreadsheet Freeze / Interaction

Use:

```text
frozen headers
filters
controlled column widths
```

when they improve usability.

Do not freeze arbitrary panes without an interaction reason.

---

# 24. Diagram Design

A diagram should define:

```yaml
diagram:
  purpose:
  audience:
  entities:
  relationships:
  direction:
  hierarchy:
  legend:
  evidence:
```

Use a consistent visual grammar:

```text
entity
relationship
direction
group
annotation
```

Do not use decorative shapes where semantic shapes are available.

---

# 25. Diagram Relationship Semantics

Where relationships represent factual claims:

```text
node
→ relation
→ node
```

should have supporting evidence when the relationship is consequential.

For knowledge graphs, use:

```text
graph-rag
```

for semantic relation governance.

---

# 26. Infographic Design

General structure:

```text
Headline
→ Problem
→ Evidence
→ Key Insight
→ Response
→ Implication
→ Sources
```

Do not substitute decoration for evidence.

Keep source attribution visible enough to remain useful.

---

# 27. Content Architecture

Before generating a long artifact, define its architecture.

Document:

```text
Cover
→ Navigation
→ Introduction
→ Context
→ Analysis
→ Evidence
→ Discussion
→ Conclusion
→ References
→ Appendix
```

Presentation:

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

Spreadsheet:

```text
Input
→ Transform
→ Calculate
→ Validate
→ Summarize
→ Visualize
```

Only use sections that materially contribute to the artifact.

---

# 28. Bounded Production Template

Each production unit should contain:

```yaml
production_unit:
  id:
  purpose:
  required_content:
  required_evidence:
  dependencies:
  output:
  validator:
  status:
```

Use units to control:

```text
scope
context
revision
validation
parallel work
```

---

# 29. Existing Template Inspection

Before reusing a template, record:

```yaml
template_contract:
  dimensions:
  fixed_elements: []
  editable_elements: []
  required_placeholders: []
  typography:
  repeated_components: []
  branding:
  forbidden_changes: []
```

This prevents accidental destruction of template semantics.

---

# 30. General Visual Principles

Prefer:

```text
clarity
→ hierarchy
→ consistency
→ readability
→ meaningful visual emphasis
```

over:

```text
decoration
→ novelty
→ density
```

A visual system should reduce cognitive load.

---

# 31. Accessibility Defaults

When applicable:

```text
readable text
sufficient contrast
logical order
meaningful captions
non-color-only distinctions
descriptive labels
```

Use artifact-appropriate accessibility checks.

Do not assume one universal font or contrast threshold is correct for every output
context.

---

# 32. Template Completion Rules

Before final generation:

```text
all required placeholders resolved
required sections present
template identity preserved
no unintended template residue
```

Search for:

```text
TODO
TBD
Lorem ipsum
[NAME]
[DATE]
[LINK]
INSERT FIGURE
ADD CITATION
WILL BE UPDATED
```

No unresolved placeholder may remain in the final artifact unless explicitly
intentional.

---

# 33. Design Anti-Patterns

Avoid:

```text
document styling applied to spreadsheets
one visual theme applied to every artifact
tiny text used to force content to fit
decorative figures without semantic purpose
excessive colors
inconsistent typography
inconsistent spacing
arbitrary alignment
template elements copied without understanding
```

---

# 34. Final Design Principle

> **The artifact's visual system should make its content easier to understand, verify, navigate, and use. Design is successful when presentation reinforces meaning rather than competing with it.**
