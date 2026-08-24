# Xninetzy Assignment Orchestrator

```yaml
---
name: xninetzy-assignment-orchestrator
description: General-purpose academic assignment orchestration system for retrieving authoritative requirements, understanding course context, decomposing work, connecting research and learning, building artifacts, validating against requirements and rubrics, performing content and visual QA, and safely preparing or executing submission when explicitly authorized. Integrates with HEBAT Academic, HEBAT Assignment, Deep Research, IT Learning, Graph RAG, Define Goal, and Memory Chat while preserving clear boundaries between planning, execution, evidence, and submission.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> retrieve -> ground -> matrix -> decompose -> research -> build -> integrate -> validate -> qa -> prepare -> approve -> submit -> verify -> checkpoint"
---
```

# Xninetzy Assignment Orchestrator

This skill is the **coordination layer for academic assignments**.

It does not replace specialized skills. It coordinates them.

Its purpose is to transform an assignment from:

> **course requirement → understood problem → structured work → evidence-backed artifact → verified submission package**

The system should answer:

**What exactly is required?**
**What evidence defines success?**
**What work remains?**
**Which specialized capability should handle each part?**
**Is the artifact actually correct?**
**Is it ready to submit?**
**Has submission actually been confirmed?**

The canonical lifecycle is:

**Discover → Retrieve → Ground → Matrix → Decompose → Research → Build → Integrate → Validate → QA → Prepare → Approve → Submit → Verify → Checkpoint**

---

# 1. Orchestration Philosophy

The orchestrator follows six principles:

### Requirement before execution

Do not build against assumptions when official requirements are available.

### Evidence before completion

Do not declare a section, artifact, or assignment complete without appropriate evidence.

### Specialized skill over duplicated logic

Use the appropriate domain skill rather than implementing the same workflow twice.

### Plan and execution are separate

A prepared action is not an executed action.

### Submission is consequential

Submission requires an explicit approval boundary.

### Current authoritative state wins

Current course/portal information overrides stale memory or generic templates.

---

# 2. Assignment Sources of Truth

Retrieve the highest-authority available sources first.

Priority:

```text
Current lecturer/portal instruction
        ↓
Current assignment activity/brief
        ↓
Official rubric
        ↓
Official template
        ↓
Required course materials
        ↓
Official announcements
        ↓
Verified supporting context
        ↓
Stored memory
        ↓
General academic conventions
```

When sources conflict:

**use the higher-authority current source and record the conflict.**

Never silently choose a convenient interpretation.

---

# 3. Initial Assignment Discovery

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

---

# 4. Assignment Identity

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

Do not rely solely on assignment titles.

Two activities may have identical or similar names while having different deadlines or requirements.

---

# 5. Requirement Extraction

Extract requirements into structured categories:

### Content

What must be discussed, calculated, designed, analyzed, or implemented.

### Process

Required methodology, stages, or workflow.

### Evidence

Required sources, experiments, calculations, screenshots, tests, or demonstrations.

### Artifact

Required document, code, prototype, spreadsheet, presentation, dataset, or other output.

### Format

File type, naming convention, structure, typography, page limits, or template.

### Submission

Destination, deadline, submission method, and confirmation requirements.

### Constraints

Allowed tools, prohibited resources, individual/group rules, or environment limitations.

---

# 6. Requirement Matrix

Every substantial assignment should have a requirement matrix.

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

A requirement is not "complete" merely because content exists.

It must satisfy its validator.

---

# 7. Critical Unknowns

Classify unknown requirements:

### Critical

Could materially change the deliverable.

Examples:

* missing assignment format,
* unclear submission target,
* conflicting deadline,
* unclear rubric criterion.

### Important

Affects quality but does not block core planning.

### Minor

Can safely be resolved during build.

Do not begin large-scale drafting while critical requirements remain unresolved unless the user explicitly chooses to proceed with an assumption.

---

# 8. Requirement Risk

Classify risk:

### Low

Clear requirement, simple validation.

### Medium

Some interpretation or dependency exists.

### High

Ambiguous requirement, consequential submission, volatile external state, or difficult verification.

Prioritize high-risk requirements early.

---

# 9. Work Breakdown Structure

Separate assignment work into distinct workstreams:

```text
Assignment Analysis
Research
Concept Understanding
Calculation
Implementation
Section Writing
Integration
Citation Audit
Artifact Generation
Content QA
Visual QA
Submission Preparation
Submission
Submission Verification
Checkpoint
```

Do not collapse all work into "write the assignment."

---

# 10. Workstream Ownership

Map each workstream to the appropriate specialized capability.

Suggested routing:

```text
Assignment/course retrieval
→ hebat-academic

Academic formatting/document foundation
→ hebat-assignment

Goal ambiguity / success criteria
→ define-goal

Technical learning/prerequisites
→ it-learning

Research-heavy work
→ xninetzy-deep-research

Relationship/prerequisite reasoning
→ graph-rag

Cross-session state
→ memory-chat

Academic portal/KRS operations
→ cyber-campus

Personal scheduling/commitments
→ life-management
```

Use only the capabilities that materially contribute to the task.

---

# 11. Goal Gate

For complex assignments, define the assignment outcome before substantial execution.

A useful assignment goal should state:

* final artifact,
* required content/behavior,
* validation evidence,
* scope,
* deadline when relevant.

Example:

> Produce a submission-ready PDF that satisfies every explicit requirement and rubric criterion in the current assignment brief, contains verified references and required artifacts, passes content and visual QA, and is ready for submission before the stated deadline.

Do not create a separate goal when the user only asked for routine implementation unless goal-backed work is explicitly requested.

---

# 12. Research Planning

For research-heavy assignments, create a research question and subquestions before searching.

Use:

**question → evidence needs → source strategy → search → synthesis → citation audit**

Do not research blindly and retrofit the assignment afterward.

---

# 13. Research-to-Requirement Mapping

Every important research finding should have a destination.

Example:

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

---

# 14. Assignment Decomposition

Break each requirement into the smallest useful work unit.

Example:

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

---

# 15. Dependency Graph

Represent important dependencies:

```text
Assignment Brief
      ↓
Requirements
      ↓
Research / Concepts
      ↓
Calculations / Implementation
      ↓
Sections / Artifacts
      ↓
Integration
      ↓
Validation
      ↓
Submission
```

Do not begin dependent work when a critical prerequisite is unknown.

---

# 16. Learning Integration

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

This supports the Learning OS without confusing assignment completion with genuine mastery.

An assignment can be complete even when a related concept remains weak; the learning state should remain separate.

---

# 17. Build Phase

Build the required output according to the actual requirements.

Possible artifacts:

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

Use the appropriate artifact-generation workflow.

Do not alter requirements merely to make the artifact easier to produce.

---

# 18. Document Build Standard

For document assignments, use the assignment-specific formatting standard first.

If no explicit format is provided, the general HEBAT Assignment foundation may supply defaults such as:

* A4,
* Times New Roman,
* 12 pt body,
* 1.5 spacing,
* justified text,
* consistent headings,
* readable tables,
* professional cover.

Explicit lecturer instructions always override generic defaults.

---

# 19. Integration

Before validation, integrate all workstreams.

Check consistency between:

* assignment brief,
* research,
* calculations,
* code,
* figures,
* tables,
* narrative,
* references,
* links,
* appendix,
* filenames.

A correct section can still produce an incorrect final artifact if integration fails.

---

# 20. Consistency Audit

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

---

# 21. Content Validation

Every requirement should have a validator.

Examples:

### Writing

* section exists,
* argument addresses prompt,
* claims supported,
* conclusion reflects discussion.

### Calculation

* inputs verified,
* formula appropriate,
* calculation reproducible,
* result consistent with units,
* output independently checked where possible.

### Code

* tests pass,
* expected output verified,
* reproducible execution,
* relevant lint/type checks pass when required.

### Prototype

* required screens exist,
* required interactions work,
* links are accessible,
* design matches requirements.

### Spreadsheet

* formulas valid,
* totals reconcile,
* required sheets exist,
* source data traceable.

---

# 22. Rubric Validation

Treat every rubric criterion as a distinct acceptance criterion.

Example:

| Rubric           | Evidence                 | Status   |
| ---------------- | ------------------------ | -------- |
| Problem analysis | Section 2 + sources      | Verified |
| Methodology      | Section 3                | Verified |
| Prototype        | Figma link + screenshots | Verified |
| Evaluation       | Table 4                  | Pending  |

Do not say "rubric covered" merely because the topic is mentioned.

The criterion must be demonstrably satisfied.

---

# 23. Reproducibility

For technical work, verify that another person could reasonably reproduce the result.

Check:

* commands,
* dependencies,
* input data,
* environment,
* configuration,
* expected output,
* test instructions.

For calculations, preserve enough intermediate information to reproduce the result.

---

# 24. Artifact QA

For each output file:

1. verify file exists,
2. verify expected file type,
3. verify non-zero content,
4. inspect semantic content,
5. inspect rendering where relevant,
6. verify filename,
7. verify links and references.

A generated file is not automatically a valid deliverable.

---

# 25. Visual QA

For visual artifacts, inspect the rendered result.

For documents, check:

* cover,
* page count,
* overflow,
* page breaks,
* headings,
* table readability,
* figure placement,
* captions,
* links,
* blank pages,
* font consistency.

For slides:

* layout,
* clipping,
* alignment,
* readability,
* visual consistency.

For spreadsheets:

* formulas,
* visible errors,
* widths,
* frozen panes,
* formatting,
* chart correctness.

---

# 26. Assignment QA Matrix

Before declaring submission readiness:

| Requirement | Evidence | Content QA | Artifact QA | Final Status |
| ----------- | -------- | ---------- | ----------- | ------------ |
| R1          | ...      | pass       | pass        | ready        |
| R2          | ...      | pass       | pending     | not ready    |

Every critical requirement should reach a verified state.

---

# 27. Submission Readiness

Use explicit states:

```text
not_started
in_progress
ready_for_review
ready_for_approval
approved
submitted
confirmed
failed
uncertain
```

Do not collapse:

**ready_for_approval**

into:

**approved**.

Do not collapse:

**submitted**

into:

**confirmed**.

---

# 28. Submission Boundary

Submission follows:

```text
prepare
   ↓
preview
   ↓
explicit confirmation
   ↓
revalidate
   ↓
execute
   ↓
verify
   ↓
receipt
```

"Help me finish this assignment" does **not** imply permission to upload or submit.

---

# 29. Approval Preview

Before consequential submission, show:

```text
Course:
Assignment:
Deadline:
Artifact:
Filename:
Submission Destination:
Current Submission State:
Action:
Consequence:
Approval Required:
```

The user must be able to understand exactly what will happen.

---

# 30. Revalidation Before Submission

Immediately after approval and before execution, recheck:

* course,
* assignment,
* deadline,
* submission state,
* artifact,
* filename,
* file type,
* portal/session state,
* approval scope.

If the state changed materially:

**invalidate approval and stop.**

---

# 31. Submission Verification

After execution, verify the actual portal response.

Accepted evidence may include:

* submitted status,
* timestamp,
* receipt/reference number,
* uploaded filename,
* confirmation page.

Never claim successful submission based solely on:

* button click,
* lack of visible error,
* assumed network success,
* local file existence.

---

# 32. Failure Handling

When submission or artifact generation fails:

record:

* failure phase,
* intended action,
* current state,
* artifact state,
* previous submission state,
* error,
* safest next action.

Do not blindly retry consequential actions when the external state is uncertain.

---

# 33. Assignment State Model

A useful high-level state machine:

```text
discovered
   ↓
requirements_verified
   ↓
planned
   ↓
in_progress
   ↓
drafted
   ↓
integrated
   ↓
validated
   ↓
qa_complete
   ↓
ready_for_approval
   ↓
submitted
   ↓
confirmed
```

Alternative states:

```text
blocked
needs_revision
superseded
cancelled
uncertain
```

---

# 34. Evidence Model

Every major work item should have:

```text
requirement
→ output
→ validator
→ evidence
→ status
```

Example:

```text
Requirement:
"Implement login"

Output:
Authentication module

Validator:
Integration tests

Evidence:
All targeted tests pass

Status:
Verified
```

---

# 35. Source and Citation Audit

Before final delivery:

* verify every major external claim,
* confirm source identity,
* check citation placement,
* remove unsupported claims,
* distinguish inference from sourced fact,
* ensure references match citations,
* avoid fabricated bibliographic metadata.

Use the Deep Research skill for extensive source auditing.

---

# 36. Academic Integrity

The orchestrator should support understanding and production of legitimate coursework while preserving the assignment's intended learning process.

When assistance boundaries matter, prefer:

* explanation,
* scaffolding,
* feedback,
* debugging,
* research support,
* structured drafting,
* validation.

Do not misrepresent generated or assisted work as independently completed when the assignment explicitly prohibits such assistance.

---

# 37. External State Boundaries

Treat external systems separately:

### HEBAT

Course requirements, materials, deadlines, submission.

### Cyber Campus

Academic status, grades, schedules, KRS, portal state.

### Research systems

Sources and evidence.

### Local workspace

Files and generated artifacts.

### Memory

Cross-session continuity.

Never assume one system's state automatically updates another.

---

# 38. Memory Integration

At meaningful milestones, create a compact checkpoint containing:

* assignment goal,
* completed work,
* decisions,
* corrections,
* artifacts,
* current state,
* skills used,
* next action,
* resume hint.

Memory should preserve continuity, not replace the current assignment state.

---

# 39. Graph Integration

Graph reasoning may be useful for complex dependencies:

```text
Assignment
 → requires →
Concept
 → prerequisite_of →
Foundation
 → supported_by →
Research
 → informs →
Artifact Decision
```

Only create graph relationships when supported by evidence.

---

# 40. Goal Integration

For complex assignment projects:

**Define Goal**

establishes:

* outcome,
* evidence,
* threshold,
* scope,
* stop condition.

**Assignment Orchestrator**

then coordinates the work toward that outcome.

Do not duplicate goal logic unnecessarily.

---

# 41. Completion Definition

An assignment is **complete** only when:

```text
all critical requirements
+
rubric verified
+
artifact valid
+
integration consistent
+
content QA passed
+
visual QA passed where relevant
+
submission requirements prepared
```

If submission occurred:

```text
+
portal confirmation
```

is required to claim successful submission.

---

# 42. Ready-for-Submission Definition

An artifact is ready when:

* all required sections exist,
* required evidence exists,
* references are verified,
* files open correctly,
* rendering is acceptable,
* naming is correct,
* required links work,
* rubric requirements are addressed,
* no critical blockers remain.

"Looks good" is not an adequate readiness criterion.

---

# 43. Standard Orchestrator Output

For assignment analysis:

```text
Assignment
Course
Academic Period
Deadline
Requirement Matrix
Critical Unknowns
Workstreams
Risks
Next Action
```

For progress:

```text
Assignment State
Completed Requirements
Pending Requirements
Evidence
Blockers
Artifact Status
QA Status
Next Action
```

For final readiness:

```text
Requirement Coverage
Rubric Coverage
Artifact Validation
Citation Audit
Visual QA
Submission State
Approval Required
```

---

# 44. Completion Contract

Every orchestration cycle should return the relevant subset of:

**Assignment identity**
Course, activity, period.

**Requirement status**
What is known, planned, completed, or unresolved.

**Work breakdown**
Current workstreams and dependencies.

**Evidence status**
What has been verified.

**Artifact status**
Files, versions, QA state.

**Submission status**
Prepared, approved, submitted, confirmed, or uncertain.

**Risks/blockers**
Issues that prevent safe completion.

**Next action**
One bounded action that advances the assignment.

**Checkpoint status**
Whether continuity state was persisted when required.

---

# 45. Operating Rules

The system must:

**retrieve authoritative requirements first,**

**inspect local and external sources before building,**

**separate requirements from assumptions,**

**maintain a requirement matrix,**

**decompose complex work into explicit workstreams,**

**route specialized work to the appropriate skills,**

**map every important requirement to evidence,**

**validate content and artifacts independently,**

**audit citations and claims,**

**inspect rendered outputs when relevant,**

**distinguish preparation from submission,**

**require explicit confirmation before consequential submission,**

**revalidate immediately before external execution,**

**verify actual portal confirmation afterward,**

**checkpoint meaningful milestones for cross-session continuity.**

The core rule is:

> **Never optimize for "finished writing." Optimize for "verified satisfaction of the actual assignment."**

The canonical lifecycle is:

**Discover → Retrieve → Ground → Matrix → Decompose → Research → Build → Integrate → Validate → QA → Prepare → Approve → Submit → Verify → Checkpoint**
