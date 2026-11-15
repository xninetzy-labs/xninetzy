---
name: hebat-assignment
description: 'Control plane for submission-ready HEBAT assignments: authoritative requirements, traceability, evidence integrity, artifact specs, content and visual QA, submission readiness. Use whenever a HEBAT assignment must be understood, produced, reviewed or submitted.'
metadata:
  keywords: academic across argument claim controlled courses disciplines driven establishes execution handoff prepared producing requirement skills specialized specifications structure teams types validated
---

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

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/04-current-context-rule.md` — §4: Current-Context Rule
- `references/06-12-phase-01-discover.md` — §6–12: Phase 01 - DISCOVER, Phase 02 - CONTEXT BINDING, Phase 03 - REQUIREMENTS LOCK, Requirement Traceability Matrix, Requirement Coverage, Requirement Types, Requirement Ambiguity
- `references/13-19-phase-04-evidence-mapping.md` — §13–19: Phase 04 - EVIDENCE MAPPING, Claim Contract, Evidence Rule, Source Priority, Citation Integrity, Research Boundary, Research Workflow
- `references/20-25-phase-05-argument-formulation.md` — §20–25: Phase 05 - ARGUMENT FORMULATION, Section Purpose, Argument Quality, Phase 06 - ARTIFACT SPECIFICATION, Structure Before Styling, Artifact Types
- `references/26-32-phase-07-production.md` — §26–32: Phase 07 - PRODUCTION, Team Assignment Model, Team Source of Truth, Phase 08 - CONTENT VALIDATION, Structural Validation, Phase 09 - DOCUMENT CONVERSION, Visual Design Principles
- `references/33-39-phase-10-qa.md` — §33–39: Phase 10 - QA, QA Severity, QA Loop, Evidence Freshness, Assumption Policy, Scope Drift, Requirement Drift
- `references/41-51-submission-handoff.md` — §41–51: Submission Handoff, Completion States, Final Assignment Result, Submission Package Manifest, Academic Integrity, Claim Calibration, Knowledge Integration, Graph Integration, Goal Integration, Memory Integration, Final Optimization Order
- `references/52-anti-patterns.md` — §52: Anti-Patterns
