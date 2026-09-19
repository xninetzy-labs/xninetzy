

name: "hebat-assignment"

description: "Evidence-driven control plane for producing submission-ready HEBAT academic assignments across courses, disciplines, teams, and artifact types. Establishes authoritative requirements, requirement traceability, evidence and claim integrity, argument structure, artifact specifications, content and visual QA, submission readiness, and controlled handoff to specialized execution skills. Use whenever a HEBAT assignment must be understood, produced, reviewed, validated, or prepared for submission."

metadata:
  owner: "xninetzy"
  version: "4.0.0"
  scope: "general"
  language: "en"
  priority: "P1"
  applies_to: "all HEBAT assignments"

lifecycle: "discover -> bind-context -> lock-requirements -> map-evidence -> formulate -> specify-artifact -> produce -> validate -> qa -> package -> handoff"

required_tools:
- context_retrieve
- repo_search
- ---
ource_search
- evidence_validate

optional_tools:
- file_search
- file_read
- repo_diff
- graph_search
- memory_search
- goal_inspect
- goal_create
- document_create
- pdf_validate
- slide_create
- spreadsheet_create
- image_create
- hitl_request_approval
- lightning_record_action

trigger_conditions:
- HEBAT assignment requirements must be discovered
- an assignment brief or rubric must be interpreted
- an assignment needs research and evidence mapping
- an academic artifact must be produced
- a draft must be audited against requirements
- citation integrity must be checked
- a document/presentation/poster/prototype package must be validated
- an assignment is approaching submission readiness
- a team assignment needs a shared requirement and artifact contract

escalation_routes:
  LMS/course-retrieval: "hebat-academic"
  cross-domain-orchestration: "xninetzy-assignment-orchestrator"
  deep-research: "xninetzy-deep-research"
  learning-goals: "define-goal"
  graph-reasoning: "graph-rag"
  artifact-generation: "xninetzy-artifact-orchestrator"
  document: "docx"
  pdf: "pdf"
  presentation: "slides"
  spreadsheet: "spreadsheets"
-------------------------

# HEBAT Assignment Control Plane

This skill is the reusable foundation for handling HEBAT assignments from
requirement discovery through submission readiness.

Its responsibility is to establish:

```text
WHAT must be produced
WHY it must be produced
WHAT evidence must support it
HOW requirements map to the artifact
HOW completion is verified
```

Specialized skills determine:

```text
HOW research is conducted
HOW files are generated
HOW LMS interaction is executed
HOW complex multi-domain work is orchestrated
```

The core principle is:

> **Requirements before structure. Evidence before claims. Structure before styling. Validation before delivery.**
---

# 1. Scope

Use this skill for:

```text
individual assignments
team assignments
written reports
academic papers
project proposals
case studies
research assignments
presentations
posters
infographics
prototype documentation
reflective assignments
design-oriented deliverables
mixed-format submissions
final submission packages
```

The skill remains course-agnostic.

Current course materials determine the actual assignment contract.

---

# 2. Non-Goals

This skill is not the primary executor for:

```text
LMS navigation or submission
long-running project orchestration
deep research methodology
generic file generation
specialized graphic design
specialized programming implementation
durable project task management
```

Route these responsibilities to the appropriate specialized skills.

---

# 3. Authority Model

When current assignment instructions conflict, use:

```text
CURRENT OFFICIAL LECTURER / COURSE INSTRUCTION
        >
CURRENT ASSIGNMENT BRIEF / RUBRIC
        >
CURRENT OFFICIAL HEBAT MATERIAL
        >
VERIFIED COURSE CONTRACT
        >
VERIFIED PROJECT CONTEXT
        >
ACADEMIC CONVENTION
        >
GENERAL DEFAULT
```

The highest applicable authoritative source wins.

When two authoritative sources conflict:

```text
identify both
→ compare recency
→ compare specificity
→ compare scope
→ determine materiality
→ resolve only when authority is sufficient
→ otherwise ask for clarification
```

Never silently reinterpret a grading requirement.

---

# 4. Current-Context Rule

Current assignment context outranks:

```text
memory
previous submission
previous approved example
old course instructions
generic HEBAT convention
personal preference
```

Historical material may provide context.

It may not silently override the current brief.

---

# 5. Assignment State Machine

Canonical workflow:

```text
DISCOVERED
    ↓
CONTEXT_BOUND
    ↓
REQUIREMENTS_LOCKED
    ↓
EVIDENCE_MAPPED
    ↓
ARGUMENT_READY
    ↓
ARTIFACT_SPECIFIED
    ↓
PRODUCTION_READY
    ↓
BUILDING
    ↓
CONTENT_VALIDATED
    ↓
STRUCTURE_VALIDATED
    ↓
VISUAL_VALIDATED
    ↓
SUBMISSION_PACKAGED
    ↓
READY_TO_SUBMIT
```

Alternative states:

```text
AMBIGUOUS
BLOCKED
CONFLICTING
PARTIAL
INVALIDATED
REWORK_REQUIRED
```

The skill does not claim:

```text
SUBMITTED
```

unless the actual submission system verifies that event.

---

# 6. Phase 01 - DISCOVER

Determine:

```text
assignment identity
course
semester/period
lecturer
student/team context
assignment type
deadline
submission channel
current authoritative sources
```

Collect candidate sources:

```text
assignment brief
course contract
rubric
lecturer instructions
HEBAT material
weekly instruction
official template
official example
verified project context
```

Do not start drafting before the relevant authoritative context is identified.

---

# 7. Phase 02 - CONTEXT BINDING

Bind the assignment to:

```yaml
assignment_context:
  assignment_id:
  course:
  academic_period:
  lecturer:
  team_mode:
  title:
  type:
  deadline:
  submission_channel:
  authoritative_sources: []
```

When an institutional identifier is unavailable, preserve:

```text
UNKNOWN
```

rather than guessing.

---

# 8. Phase 03 - REQUIREMENTS LOCK

Build the requirement contract before substantial production.

Each requirement should be represented conceptually as:

```yaml
requirement:
  requirement_id:
  statement:
  source:
  authority:
  interpretation:
  mandatory:
  artifact_location:
  evidence_required:
  validator:
  status:
```

Possible status:

```text
MISSING
PLANNED
IN_PROGRESS
SATISFIED
VERIFIED
BLOCKED
CONFLICTING
NOT_APPLICABLE
```

---

# 9. Requirement Traceability Matrix

Canonical structure:

| ID | Requirement | Authority | Source | Interpretation | Artifact Location | Evidence | Validator | Status   |
| -- | ----------- | --------- | ------ | -------------- | ----------------- | -------- | --------- | -------- |
| R1 | ...         | Brief     | B1     | ...            | Section 2         | S3       | QA-01     | VERIFIED |

Every material requirement must map to:

```text
artifact location
+
evidence
+
validator
```

A requirement that exists only in notes is not considered covered.

---

# 10. Requirement Coverage

Coverage should be computed from mandatory requirements.

Conceptually:

```text
requirement_coverage =
verified_mandatory_requirements
/
total_mandatory_requirements
```

For submission readiness:

```text
mandatory requirement coverage = 100%
```

unless the user explicitly accepts an incomplete submission.

Do not inflate coverage by marking unclear requirements as satisfied.

---

# 11. Requirement Types

Classify requirements when useful:

```text
CONTENT
STRUCTURE
EVIDENCE
METHOD
FORMAT
VISUAL
FILE
LINK
CITATION
TEAM
DEADLINE
SUBMISSION
```

This prevents content compliance from masking structural or submission failures.

---

# 12. Requirement Ambiguity

Use:

```text
UNAMBIGUOUS
PARTIALLY_AMBIGUOUS
MATERIALLY_AMBIGUOUS
CONFLICTING
UNKNOWN
```

A materially ambiguous requirement must be clarified before finalization when it
could change:

```text
graded content
artifact type
scope
methodology
required evidence
format
submission route
deadline interpretation
```

---

# 13. Phase 04 - EVIDENCE MAPPING

Separate:

```text
CLAIM
EVIDENCE
INTERPRETATION
ASSUMPTION
RECOMMENDATION
LIMITATION
```

Never collapse these into one category.

For important claims:

```text
Claim
→ Source
→ Evidence
→ Interpretation
→ Artifact location
```

---

# 14. Claim Contract

Each important claim should have:

```yaml
claim:
  claim_id:
  text:
  type:
  source_refs: []
  evidence:
  interpretation:
  target_section:
  verification_status:
```

Claim types:

```text
FACT
INTERPRETATION
ASSUMPTION
RECOMMENDATION
LIMITATION
```

---

# 15. Evidence Rule

Evidence must actually support the attached claim.

Reject:

```text
citation exists
but source does not support the statement
```

Likewise reject:

```text
"research shows..."
```

without an identifiable source and relevant evidence.

---

# 16. Source Priority

Typical source priority:

```text
official institutional / government source
primary research
peer-reviewed literature
official dataset
official organizational documentation
professional organization
credible secondary analysis
reputable reference source
```

Authority is context-dependent.

A course brief may outrank an academic paper for determining what the assignment
requires.

An academic paper may outrank a blog for supporting an empirical claim.

---

# 17. Citation Integrity

For substantive citations:

```text
source exists
author/title/year are verified where required
claim is actually supported
citation style is correct
reference entry exists
reference entry maps to citation
```

Never fabricate:

```text
authors
papers
DOIs
URLs
publication dates
page numbers
datasets
statistics
quotes
```

If a source cannot be verified:

```text
UNVERIFIED_SOURCE
```

and do not present it as authoritative evidence.

---

# 18. Research Boundary

Research only what materially contributes to:

```text
assignment requirements
claims
analysis
decision
methodology
context
validation
```

Avoid:

```text
source accumulation
citation padding
irrelevant literature
search-snippet dependence
```

A source should have a purpose.

---

# 19. Research Workflow

When research is required:

```text
QUESTION
   ↓
SEARCH
   ↓
SOURCE EVALUATION
   ↓
EVIDENCE EXTRACTION
   ↓
SYNTHESIS
   ↓
CLAIM SUPPORT
   ↓
CITATION
```

Route complex research methodology to:

```text
xninetzy-deep-research
```

This skill consumes verified research outputs.

---

# 20. Phase 05 - ARGUMENT FORMULATION

Before writing polished prose, determine the argument architecture.

Typical structure:

```text
Problem
  ↓
Context
  ↓
Evidence
  ↓
Analysis
  ↓
Implication
  ↓
Response / Proposal
  ↓
Limitation
  ↓
Conclusion
```

Adapt the structure to the actual assignment.

Do not force every assignment into a generic academic-paper structure.

---

# 21. Section Purpose

Every major section should have a purpose:

```yaml
section:
  id:
  title:
  purpose:
  requirements:
  claims:
  evidence_refs:
  expected_artifact:
```

Reject sections that exist only because they "look academic" when they add no
assignment value.

---

# 22. Argument Quality

A strong section generally follows:

```text
CLAIM
→ EXPLANATION
→ EVIDENCE
→ INTERPRETATION
→ RELEVANCE
```

Do not stack quotations without analysis.

The assignment should demonstrate:

```text
understanding
reasoning
application
connection to course concepts
evidence-backed interpretation
```

---

# 23. Phase 06 - ARTIFACT SPECIFICATION

Before generation, define an artifact specification.

Minimum:

```yaml
artifact_spec:
  type:
  audience:
  purpose:
  required_sections: []
  required_evidence: []
  required_visuals: []
  format:
  page_or_word_constraints:
  citation_style:
  typography:
  layout:
  filename:
  submission_format:
  submission_channel:
```

The artifact specification must trace back to the requirement matrix.

---

# 24. Structure Before Styling

Determine:

```text
information architecture
content hierarchy
section order
evidence placement
figure/table placement
navigation
```

before:

```text
colors
typography
decorative elements
```

Content structure is upstream of visual design.

---

# 25. Artifact Types

## Document

Typical pattern:

```text
Cover
→ Context / Introduction
→ Main Analysis
→ Evidence
→ Discussion
→ Conclusion
→ References
→ Appendix
```

Only include required or materially useful sections.

## Presentation

Typical pattern:

```text
Context
→ Problem
→ Evidence
→ Analysis
→ Response
→ Validation
→ Conclusion
```

## Poster / Infographic

Typical pattern:

```text
Headline
→ Problem
→ Evidence
→ Key Insight
→ Response
→ Impact
→ Sources
```

## Prototype Documentation

Typical pattern:

```text
Problem
→ User / Context
→ Requirements
→ Design
→ Prototype
→ Validation
→ Limitations
→ Link / Artifact
```

Adapt to the brief.

---

# 26. Phase 07 - PRODUCTION

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

# 27. Team Assignment Model

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

# 28. Team Source of Truth

Team members should work from:

```text
one authoritative requirement matrix
one evidence ledger
one artifact specification
one final integration state
```

Do not let separate copies silently diverge.

---

# 29. Phase 08 - CONTENT VALIDATION

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

# 30. Structural Validation

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

# 31. Phase 09 - DOCUMENT CONVERSION

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

# 32. Visual Design Principles

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

# 33. Phase 10 - QA

Use separate QA passes.

```text
CONTENT QA
STRUCTURAL QA
VISUAL QA
TECHNICAL QA
CITATION QA
SUBMISSION QA
```

Do not collapse all checks into "looks good."

---

# 34. QA Severity

## Critical

Blocks submission.

Examples:

```text
missing mandatory requirement
fabricated source
wrong assignment format
corrupted file
unreadable pages
missing required evidence
broken required artifact
```

## Major

Potentially affects grading or materially reduces validity.

Examples:

```text
unsupported central claim
missing rubric criterion
serious table/figure failure
incorrect analysis
broken required link
major page overflow
inconsistent conclusion
```

## Minor

Non-material defect.

Examples:

```text
small spacing issue
minor alignment inconsistency
non-critical typography issue
```

Readiness rule:

```text
Critical = 0
Major = 0
Minor = acceptable when non-material
```

---

# 35. QA Loop

After meaningful corrections:

```text
FIX
→ REBUILD
→ REVALIDATE
→ RECHECK
```

Do not assume a correction is isolated.

A content change may affect:

```text
page count
figure references
conclusion
citations
table numbering
visual layout
```

A layout change may affect:

```text
readability
pagination
caption placement
page count
```

---

# 36. Evidence Freshness

Completion evidence must belong to the intended:

```text
assignment version
artifact version
dataset
environment
source set
```

Do not use old evidence after materially changing the artifact unless the evidence
remains valid.

---

# 37. Assumption Policy

Classify assumptions:

```text
LOW_IMPACT
MATERIAL
UNSAFE
```

Low-impact assumptions may be stated and used consistently.

Material assumptions require:

```text
validation
explicit acceptance
or clarification
```

Unsafe assumptions must not be operationalized.

Never fabricate evidence to satisfy an assumption.

---

# 38. Scope Drift

Detect when production expands beyond:

```text
target
assignment scope
required artifact
deadline
approved constraints
```

When scope expands materially:

```text
STOP
→ REPORT SCOPE DELTA
→ RECONCILE REQUIREMENTS
→ UPDATE ARTIFACT SPECIFICATION
```

Do not silently broaden the assignment.

---

# 39. Requirement Drift

If current work no longer matches the current requirement contract:

```text
REQUIREMENT_DRIFT
```

Re-check:

```text
brief
rubric
lecturer instructions
artifact specification
current work
```

Do not optimize the artifact against an obsolete interpretation.

---

# 40. Completion Contract

A submission artifact is considered:

```text
READY_TO_SUBMIT
```

only when:

```text
mandatory requirements = verified
critical defects = 0
major defects = 0
required evidence = verified
citation integrity = verified
artifact format = correct
structural validation = pass
visual validation = pass when applicable
submission package = complete
```

This is readiness, not proof that an external LMS submission has occurred.

---

# 41. Submission Handoff

When the final assignment is ready for LMS submission:

```text
HEBAT ASSIGNMENT
      ↓
READY_TO_SUBMIT
      ↓
hebat-academic
      ↓
LMS submission workflow
      ↓
portal confirmation
```

Do not perform portal operations here when the owning skill is `hebat-academic`.

---

# 42. Completion States

Use:

```text
NOT_STARTED
IN_PROGRESS
PARTIAL
BLOCKED
REWORK_REQUIRED
READY_TO_SUBMIT
SUBMITTED
CONFIRMED
```

Only use:

```text
SUBMITTED
```

when actual submission evidence exists.

Only use:

```text
CONFIRMED
```

when the submission system verifies the resulting state.

---

# 43. Final Assignment Result

Canonical result:

```yaml
assignment_result:
  assignment_context:
  requirement_coverage:
  evidence_status:
  artifact:
  content_qa:
  structural_qa:
  visual_qa:
  technical_qa:
  citation_qa:
  submission_package:
  readiness_state:
  unresolved:
  next_action:
```

The result must distinguish:

```text
produced
validated
ready
submitted
confirmed
```

---

# 44. Submission Package Manifest

When multiple deliverables are required:

```yaml
submission_manifest:
  primary_artifact:
  supplementary_artifacts: []
  datasets: []
  links: []
  required_metadata: []
```

Verify the package against the assignment brief.

Do not include:

```text
temporary files
debug files
intermediate drafts
unused screenshots
internal notes
```

unless explicitly required.

---

# 45. Academic Integrity

The assignment system must preserve:

```text
source attribution
claim ownership
evidence provenance
student work context
```

Never fabricate:

```text
sources
experiments
field observations
interview participants
survey responses
datasets
results
citations
```

Do not represent generated content as observed evidence.

---

# 46. Claim Calibration

Match language strength to evidence strength.

Prefer:

```text
suggests
indicates
is consistent with
supports
```

when evidence is limited.

Use stronger language only when supported.

Avoid:

```text
proves
always
guarantees
the best
revolutionary
100% effective
```

without appropriate evidence.

---

# 47. Knowledge Integration

Valid sources may include:

```text
HEBAT materials
official course instructions
verified project context
personal knowledge base
academic literature
official institutional sources
datasets
field observations
verified artifacts
```

Use source precedence appropriate to the claim.

Personal knowledge never overrides current assignment requirements.

---

# 48. Graph Integration

When graph relationships materially improve reasoning, `graph-rag` may model:

```text
Requirement
  → requires →
Evidence

Claim
  → supported_by →
Source

Concept
  → applied_in →
Section

Rubric Criterion
  → validated_by →
Evidence

Artifact
  → satisfies →
Requirement
```

Graph edges remain evidence-backed.

Do not create relationships merely from semantic similarity.

---

# 49. Goal Integration

A significant assignment may define a goal first:

```text
define-goal
      ↓
validated assignment outcome
      ↓
hebat-assignment
```

The goal defines:

```text
what success is
```

This skill defines:

```text
how the assignment contract and evidence are organized
```

Do not duplicate long-term goal management here.

---

# 50. Memory Integration

Memory may provide:

```text
previous approved structure
known project context
reusable source mappings
previous QA lessons
```

Memory remains historical context.

Current authoritative assignment requirements win.

---

# 51. Final Optimization Order

Optimize in this order:

```text
1. Requirement compliance
2. Academic correctness
3. Evidence quality
4. Citation integrity
5. Argument quality
6. Structural clarity
7. Readability
8. Visual quality
9. Technical validity
10. Submission readiness
```

Do not optimize visual polish before compliance.

Do not increase citation count merely to appear academic.

Do not reduce readability to satisfy page count through arbitrary compression.

---

# 52. Anti-Patterns

Never:

```text
start writing before reading the brief
treat previous assignments as current requirements
invent missing requirements
use generic academic conventions over explicit instructions
collect citations without claim mapping
use search snippets as primary evidence
fabricate a citation
write "research shows" without evidence
treat a generated artifact as validated
treat DOCX generation as proof of PDF correctness
treat visual polish as requirement compliance
mark requirements complete without validation
silently expand scope
silently resolve authoritative conflicts
claim submission from file generation
claim submission success without external confirmation
```

---

# 53. Golden Workflow

```text
ASSIGNMENT REQUEST
       ↓
DISCOVER AUTHORITATIVE CONTEXT
       ↓
BIND CURRENT COURSE / PERIOD
       ↓
LOCK REQUIREMENTS
       ↓
BUILD TRACEABILITY MATRIX
       ↓
MAP CLAIMS TO EVIDENCE
       ↓
FORMULATE ARGUMENT
       ↓
SPECIFY ARTIFACT
       ↓
PRODUCE
       ↓
CONTENT VALIDATION
       ↓
STRUCTURAL VALIDATION
       ↓
VISUAL VALIDATION
       ↓
TECHNICAL / CITATION QA
       ↓
PACKAGE
       ↓
READY_TO_SUBMIT
       ↓
HANDOFF TO LMS OWNER
```

---

# 54. Non-Negotiable Rules

The system must:

```text
use current authoritative assignment context
bind work to the correct course and academic period
inspect requirements before production
map material requirements to artifact locations
map important claims to evidence
verify citations
preserve fact/interpretation/assumption/recommendation distinctions
use meaningful source hierarchy
research only what materially contributes
define artifact structure before styling
keep specialized generation outside this skill
validate content independently
validate structure independently
validate visuals independently
inspect converted PDF independently
keep team work on a shared requirement contract
detect requirement and scope drift
preserve uncertainty
never fabricate evidence
never fabricate sources
never claim completion without evidence
never claim LMS submission without actual confirmation
hand off specialized operations to owning skills
```

---

# 55. Central Principle

> **A HEBAT assignment is submission-ready only when the current authoritative requirements are explicitly mapped to the final artifact, substantive claims are supported by verifiable evidence, the artifact passes the required content and presentation checks, and every remaining uncertainty is visible rather than silently guessed.**
