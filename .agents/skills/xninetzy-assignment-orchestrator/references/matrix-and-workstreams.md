# Xninetzy Assignment Orchestrator — Matrix, Workstreams, and Integration

This reference expands the requirement matrix, workstream ownership, critical unknowns, requirement risk, dependency graph, learning integration, build phase, document build standard, integration, and consistency audit. Read it when decomposing a complex assignment.

## Requirement matrix

Every substantial assignment should have a requirement matrix:

| Requirement | Official Source | Planned Output   | Evidence  | Status       | Risk            |
| ----------- | --------------- | ---------------- | --------- | ------------ | --------------- |
| Requirement | source          | artifact/section | validator | pending/done | low/medium/high |

Recommended statuses:

```text
unknown
identified
planned
in_progress
blocked
validated
complete
```

A requirement is not "complete" merely because content exists. It must satisfy its validator.

## Initial assignment discovery

Before substantial work begins, identify:

* course,
* course code,
* assignment/activity,
* assignment wording,
* deadline,
* rubric,
* required format,
* required template,
* required materials,
* allowed/prohibited resources,
* individual/group status,
* required artifacts,
* submission destination,
* current submission state.

Also determine whether the assignment has multiple deliverables.

## Assignment identity

Create an internal assignment identity from:

```text
course
+
assignment/activity
+
academic period
+
assignment identifier
```

Do not rely solely on assignment titles. Two activities may have identical or similar names while having different deadlines or requirements.

## Goal gate

For complex assignments, define the assignment outcome before substantial execution. A useful assignment goal should state:

* final artifact,
* required content/behavior,
* validation evidence,
* scope,
* deadline when relevant.

Example: `Produce a submission-ready PDF that satisfies every explicit requirement and rubric criterion in the current assignment brief, contains verified references and required artifacts, passes content and visual QA, and is ready for submission before the stated deadline.`

Do not create a separate goal when the user only asked for routine implementation unless goal-backed work is explicitly requested.

## Research planning

For research-heavy assignments, create a research question and subquestions before searching:

**question → evidence needs → source strategy → search → synthesis → citation audit**

Do not research blindly and retrofit the assignment afterward.

## Research-to-requirement mapping

Every important research finding should have a destination:

```text
Research Source
    ↓
Finding
    ↓
Assignment Requirement
    ↓
Section / Decision / Artifact
```

This prevents irrelevant citations and disconnected research.

## Assignment decomposition

Break each requirement into the smallest useful work unit:

```text
Requirement:
Analyze the proposed system.

↓
Task A:
Understand required architecture.

↓
Task B:
Research supporting evidence.

↓
Task C:
Create architecture diagram.

↓
Task D:
Write analysis.

↓
Task E:
Verify diagram and narrative agree.
```

The work breakdown should expose dependencies.

## Learning integration

For assignments that are also learning activities:

```text
Assignment Requirement
        ↓
Required Concept
        ↓
Prerequisite
        ↓
Practice
        ↓
Evidence
        ↓
Assignment Artifact
```

This supports the Learning OS without confusing assignment completion with genuine mastery. An assignment can be complete even when a related concept remains weak; the learning state should remain separate.

## Build phase

Build the required output according to the actual requirements. Possible artifacts:

* DOCX,
* PDF,
* spreadsheet,
* code,
* notebook,
* prototype,
* presentation,
* diagram,
* dataset,
* archive.

Use the appropriate artifact-generation workflow. Do not alter requirements merely to make the artifact easier to produce.

## Document build standard

For document assignments, use the assignment-specific formatting standard first. If no explicit format is provided, the general HEBAT Assignment foundation may supply defaults such as A4, Times New Roman, 12 pt body, 1.5 spacing, justified text, consistent headings, readable tables, and professional cover. Explicit lecturer instructions always override generic defaults.

## Integration

Before validation, integrate all workstreams. Check consistency between assignment brief, research, calculations, code, figures, tables, narrative, references, links, appendix, and filenames. A correct section can still produce an incorrect final artifact if integration fails.

## Consistency audit

Check for contradictions such as:

```text
text says 12 credits
table says 15 credits

diagram shows 3 modules
text discusses 4 modules

reference says 2025
citation says 2024

prototype link points to wrong version
```

The final artifact should have one coherent state.

## Goal integration

For complex assignment projects, **Define Goal** establishes outcome, evidence, threshold, scope, and stop condition. **Assignment Orchestrator** then coordinates the work toward that outcome. Do not duplicate goal logic unnecessarily.