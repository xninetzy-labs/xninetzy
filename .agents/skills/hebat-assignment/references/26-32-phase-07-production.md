# hebat-assignment — §26–32

Contents: 26. Phase 07 - PRODUCTION; 27. Team Assignment Model; 28. Team Source of Truth; 29. Phase 08 - CONTENT VALIDATION; 30. Structural Validation; 31. Phase 09 - DOCUMENT CONVERSION; 32. Visual Design Principles

## 26. Phase 07 - PRODUCTION

Build using the appropriate specialized skill.

This skill determines:

```text
what to produce
required content
required evidence
required validation
```

Specialized artifact skills determine:

```text
how the file is technically generated
```

Do not duplicate specialized file-generation logic here.

---

## 27. Team Assignment Model

For team work, establish:

```yaml
team_contract:
  members: []
  owners:
    requirements:
    research:
    writing:
    design:
    implementation:
    final_integration:
  source_of_truth:
  merge_rule:
  final_reviewer:
```

Every member should know which artifact/section they own.

The final integration owner validates the complete assignment against the current
requirement contract.

---

## 28. Team Source of Truth

Team members should work from:

```text
one authoritative requirement matrix
one evidence ledger
one artifact specification
one final integration state
```

Do not let separate copies silently diverge.

---

## 29. Phase 08 - CONTENT VALIDATION

Verify:

```text
requirement coverage
claim support
argument coherence
course concept correctness
methodology alignment
numerical consistency
terminology consistency
citation integrity
reference completeness
conclusion alignment
```

The validator must use the current assignment contract.

---

## 30. Structural Validation

Check:

```text
required sections
required headings
required tables
required figures
required links
required appendices
page/word limits
filename
file format
```

Structural validation is distinct from content validation.

---

## 31. Phase 09 - DOCUMENT CONVERSION

For document workflows:

```text
content
→ source document
→ converted PDF
→ structural validation
→ rendered visual validation
→ final package
```

Conversion can introduce:

```text
font substitution
page-break changes
table overflow
image displacement
missing glyphs
spacing changes
link corruption
```

Therefore the final PDF must be validated independently.

---

## 32. Visual Design Principles

Unless overridden by the assignment:

```text
clarity > decoration
consistency > novelty
readability > density
hierarchy > ornament
meaningful visuals > decorative visuals
```

Use:

```text
page grid
consistent margins
clear heading hierarchy
consistent spacing
consistent table/figure treatment
sufficient whitespace
```

Avoid:

```text
excessive colors
decorative clutter
tiny text
inconsistent typography
arbitrary spacing
unnecessary graphics
```

Detailed document defaults belong to:

```text
references/doc-standard.md
```

---
