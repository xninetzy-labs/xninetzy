---
name: xninetzy-assignment-orchestrator
description: Academic assignment orchestration system for retrieving authoritative requirements, understanding course context, decomposing work, connecting research and learning, building artifacts, validating against requirements and rubrics, performing content and visual QA, and safely preparing or executing submission when explicitly authorized. Use to coordinate academic work end-to-end across HEBAT, Cyber Campus, research, learning, and artifact subsystems.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> retrieve -> ground -> matrix -> decompose -> research -> build -> integrate -> validate -> qa -> prepare -> approve -> submit -> verify -> checkpoint"
---

# Xninetzy Assignment Orchestrator

This skill is the **coordination layer for academic assignments**. It does not replace specialized skills. It coordinates them.

Its purpose is to transform an assignment from:

> **course requirement → understood problem → structured work → evidence-backed artifact → verified submission package**

The system should answer:

* What exactly is required?
* What evidence defines success?
* What work remains?
* Which specialized capability should handle each part?
* Is the artifact actually correct?
* Is it ready to submit?
* Has submission actually been confirmed?

The canonical lifecycle is:

**Discover → Retrieve → Ground → Matrix → Decompose → Research → Build → Integrate → Validate → QA → Prepare → Approve → Submit → Verify → Checkpoint**

## Orchestration philosophy

* **Requirement before execution.** Do not build against assumptions when official requirements are available.
* **Evidence before completion.** Do not declare a section, artifact, or assignment complete without appropriate evidence.
* **Specialized skill over duplicated logic.** Use the appropriate domain skill rather than implementing the same workflow twice.
* **Plan and execution are separate.** A prepared action is not an executed action.
* **Submission is consequential.** Submission requires an explicit approval boundary.
* **Current authoritative state wins.** Current course/portal information overrides stale memory or generic templates.

## When to use

* any academic assignment requiring multi-step coordination across subsystems;
* orchestration that touches HEBAT/Cyber Campus, research, learning, and artifact generation;
* submission preparation that requires careful verification and approval.

## When NOT to use

* simple implementation or single-section tasks;
* non-academic artifact work — use `xninetzy-artifact-orchestrator`;
* generic learning planning — use `it-learning` and `xninetzy-learning-coach`.

## Assignment sources of truth

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

When sources conflict, use the higher-authority current source and record the conflict. Never silently choose a convenient interpretation.

## Core workflow

1. **Discover.** Identify course, course code, assignment/activity, deadline, rubric, format, template, materials, allowed/prohibited resources, individual/group status, required artifacts, submission destination, and current submission state.
2. **Retrieve.** Fetch authoritative context from HEBAT/Moodle, Cyber Campus, the assignment brief, and the rubric.
3. **Ground.** Tie the assignment brief, lecturer instructions, required material, and relevant learning concepts together.
4. **Matrix.** Build a requirement matrix with `requirement | official source | planned output | evidence | status | risk` and statuses `unknown | identified | planned | in_progress | blocked | validated | complete`.
5. **Decompose.** Break each requirement into the smallest useful work unit and surface dependencies.
6. **Research.** Run evidence collection for research-heavy requirements, decompose into subquestions, map findings to specific assignment sections, and audit citations.
7. **Build.** Produce the artifact using the appropriate artifact-generation workflow.
8. **Integrate.** Resolve duplicated arguments, terminology drift, conflicting numbers, inconsistent dates, citation numbering, and visual inconsistencies across sections.
9. **Validate.** Verify every requirement against its validator. Apply rubric validation as a separate acceptance check.
10. **QA.** Run content QA and visual QA independently. Inspect rendered output before claiming visual quality.
11. **Prepare.** Compile the submission package with course, activity, deadline, filename, file hash, submission action, existing submission, and expected state.
12. **Approve.** Require explicit confirmation bound to the exact submission hash. Invalidate approval on material state change.
13. **Submit.** Execute once. Re-read submission state. Capture portal confirmation. Store receipt.
14. **Verify.** Compare intended vs actual outcome; classify as `verified_success | partial_success | unchanged | failed | uncertain`.
15. **Checkpoint.** Persist a continuity checkpoint with assignment goal, completed work, decisions, corrections, artifacts, current state, skills used, next action, and resume hint.

## Workstream ownership

Map each workstream to the appropriate specialized capability:

```text
Assignment/course retrieval        → hebat-academic
Academic formatting/foundation     → hebat-assignment
Goal ambiguity / success criteria  → define-goal
Technical learning/prerequisites   → it-learning
Research-heavy work                → xninetzy-deep-research
Relationship/prerequisite reasoning → graph-rag
Cross-session state                → xninetzy-memory
Academic portal/KRS operations      → xninetzy-cyber-campus
Personal scheduling/commitments     → life-management
Artifact production                → xninetzy-artifact-orchestrator
```

Use only the capabilities that materially contribute to the task.

## Critical unknowns

Classify unknown requirements:

* **Critical** — could materially change the deliverable (missing assignment format, unclear submission target, conflicting deadline, unclear rubric criterion).
* **Important** — affects quality but does not block core planning.
* **Minor** — can safely be resolved during build.

Do not begin large-scale drafting while critical requirements remain unresolved unless the user explicitly chooses to proceed with an assumption.

## Requirement risk

Classify risk:

* **Low** — clear requirement, simple validation.
* **Medium** — some interpretation or dependency exists.
* **High** — ambiguous requirement, consequential submission, volatile external state, or difficult verification.

Prioritize high-risk requirements early.

## Dependency graph

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

## Submission boundary

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

`Help me finish this assignment` does not imply permission to upload or submit.

## Approval preview

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

## Revalidation before submission

Immediately after approval and before execution, recheck course, assignment, deadline, submission state, artifact, filename, file type, portal/session state, and approval scope. If any material state changed, **invalidate approval and stop.**

## Submission verification

After execution, verify the actual portal response. Accepted evidence may include submitted status, timestamp, receipt/reference number, uploaded filename, and confirmation page. Never claim successful submission based solely on a button click, lack of visible error, assumed network success, or local file existence.

## Failure handling

When submission or artifact generation fails, record the failure phase, intended action, current state, artifact state, previous submission state, error, and safest next action. Do not blindly retry consequential actions when the external state is uncertain.

## Assignment state model

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

Alternative states: `blocked`, `needs_revision`, `superseded`, `cancelled`, `uncertain`.

## Evidence model

Every major work item should have `requirement → output → validator → evidence → status`.

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

## Source and citation audit

Before final delivery, verify every major external claim, confirm source identity, check citation placement, remove unsupported claims, distinguish inference from sourced fact, ensure references match citations, and avoid fabricated bibliographic metadata. Use the Deep Research skill for extensive source auditing.

## Academic integrity

The orchestrator should support understanding and production of legitimate coursework while preserving the assignment's intended learning process. When assistance boundaries matter, prefer explanation, scaffolding, feedback, debugging, research support, structured drafting, and validation. Do not misrepresent generated or assisted work as independently completed when the assignment explicitly prohibits such assistance.

## External state boundaries

Treat external systems separately:

* **HEBAT** — course requirements, materials, deadlines, submission.
* **Cyber Campus** — academic status, grades, schedules, KRS, portal state.
* **Research systems** — sources and evidence.
* **Local workspace** — files and generated artifacts.
* **Memory** — cross-session continuity.

Never assume one system's state automatically updates another.

## Routing

* HEBAT workflow → `hebat-academic`, `hebat-assignment`.
* Cyber Campus / KRS → `xninetzy-cyber-campus`.
* Artifact production → `xninetzy-artifact-orchestrator`.
* Research → `xninetzy-deep-research`.
* Learning → `it-learning`, `xninetzy-learning-coach`.
* Memory → `xninetzy-memory`.

## Reference map

* `references/matrix-and-workstreams.md` — requirement matrix, workstream ownership, critical unknowns, risk, dependency graph, learning integration, and build/integration/consistency detail.
* `references/validation-and-submission.md` — content validation, rubric validation, reproducibility, artifact QA, visual QA, assignment QA matrix, submission readiness states, preview, revalidation, verification, failure handling, and completion definitions.

## Operating rules

The system must:

* retrieve authoritative requirements first,
* inspect local and external sources before building,
* separate requirements from assumptions,
* maintain a requirement matrix,
* decompose complex work into explicit workstreams,
* route specialized work to the appropriate skills,
* map every important requirement to evidence,
* validate content and artifacts independently,
* audit citations and claims,
* inspect rendered outputs when relevant,
* distinguish preparation from submission,
* require explicit confirmation before consequential submission,
* revalidate immediately before external execution,
* verify actual portal confirmation afterward,
* checkpoint meaningful milestones for cross-session continuity.

The core rule is:

> **Never optimize for "finished writing." Optimize for "verified satisfaction of the actual assignment."**