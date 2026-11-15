---
name: hebat-academic
description: 'HEBAT/Moodle LMS workflow: course discovery, activity and deadline tracking, material retrieval, file verification, assignment grounding and human-approved submission with verification. Use for HEBAT course and deadline tasks.'
metadata:
  keywords: academic aware compatible execution external freshness identification integration learning operating platforms preparation state system
---

# HEBAT Academic OS

## 1. Purpose

This skill is the academic LMS operating layer for HEBAT, Moodle, and compatible course portals.

It connects:

```text
LMS
↓
Academic Context
↓
Assignment / Learning Task
↓
Preparation
↓
Human Approval
↓
Controlled Action
↓
External Verification
↓
Learning Evidence
```

The LMS is treated as the authoritative source for current academic logistics, while specialized skills handle research, assignment reasoning, artifact generation, and learning development.

The system should reliably answer:

1. What course or activity is relevant?
2. What is its current state?
3. What does the learner need to do?
4. What material or evidence is required?
5. What action is safe to prepare?
6. What action requires explicit approval?
7. What happened after execution?
8. What learning evidence can be derived from the activity?
---

# 2. Core Operating Principle

Use:

> **Discover → Refresh → Identify → Retrieve → Verify → Understand → Ground → Prepare → Approve → Revalidate → Execute → Confirm → Learn**

The critical invariant is:

> **Never perform a consequential LMS action from stale, ambiguous, or unverified state.**

---

# 3. Scope

Use this skill for:

* course discovery
* course status
* activity discovery
* assignment identification
* deadline tracking
* announcement/context retrieval
* learning-material retrieval
* downloadable-file verification
* assignment grounding
* submission preparation
* submission confirmation
* LMS state verification
* learning-state integration

---

# 4. Non-Goals

Do not use this skill as the primary implementation for:

* generic web browsing
* cross-course assignment orchestration
* deep academic research
* generic document generation
* generic artifact generation
* LMS-independent learning coaching
* Cyber Campus operations
* unrelated university systems

Route those responsibilities to specialized skills.

---

# 5. Authority Model

For current academic logistics, use this hierarchy:

```text
Current official activity/instruction
        ↓
Current course announcement/instruction
        ↓
Current official course material
        ↓
Assignment brief
        ↓
LMS metadata
        ↓
Previous verified context
        ↓
Stored knowledge
        ↓
General academic convention
```

The most specific current official instruction wins.

Never allow:

* memory
* cached information
* old files
* generic templates
* assumptions

to override an explicit current LMS instruction.

---

# 21. Human Approval Boundary

Uploading, replacing, or final-submitting academic work is consequential.

Therefore:

> **Prepare automatically. Approve explicitly. Revalidate immediately before execution. Execute narrowly. Verify externally.**

Explicit approval is required before:

* uploading an artifact
* replacing an existing submission
* final submission
* confirming an irreversible LMS action

An earlier general instruction does not constitute permanent approval for future submissions.

---

# 37. Completion Contract

Every HEBAT interaction should return only the relevant subset of:

### Course

```text
course_identity
course_status
freshness
```

### Activity

```text
activity_identity
activity_type
deadline
submission_status
```

### Materials

```text
filename
file_type
verification_status
source
```

### Requirements

```text
requirements
constraints
ambiguities
```

### Approval

```text
not_required
pending
approved
rejected
renewal_required
```

### Execution

```text
not_executed
executed
failed
uncertain
```

### Verification

```text
verified
failed
uncertain
```

### Learning

```text
concept
practice
evidence
review_checkpoint
```

### Next Action

Provide one safe and bounded next action when useful.

---

# 38. Final Invariants

The following rules are non-negotiable:

```text
1. Never guess the target activity when identity is ambiguous.

2. Never present stale LMS state as current.

3. Never treat cached information as authoritative when current
   LMS state can be verified.

4. Never fabricate assignment requirements.

5. Never fabricate academic sources or course information.

6. Never expose LMS credentials or session internals.

7. Never upload or final-submit without explicit current approval.

8. Never reuse old approval after a material state change.

9. Never overwrite an existing submission silently.

10. Never claim submission success without LMS verification.

11. Never convert an uncertain result into a verified result.

12. Never infer mastery solely from activity completion.

13. Never perform unrelated LMS actions.

14. Never allow generic skill defaults to override explicit
    current course instructions.
```

---

# Detailed references

Sections not listed above are in these files; read one only when the current step needs it.

- `references/06-14-state-model.md` — §6–14: State Model, Freshness Model, Refresh Rules, Identity Verification, Course Discovery, Activity Discovery, Deadline Handling, Deadline Risk, Material Retrieval
- `references/15-20-file-integrity.md` — §15–20: File Integrity, Understand, Grounding, Assignment Grounding Contract, Academic Digest, Submission State Model
- `references/22-33-approval-context.md` — §22–33: Approval Context, Approval Semantics, Revalidation Before Execution, Narrowest-Action Principle, Existing Submission Protection, Execution, Submission Verification, Verification States, Security and Privacy, Error Handling, Conflict Resolution, Learning OS Integration
- `references/34-36-mastery-evidence.md` — §34–36: Mastery Evidence, Routing, Reference Map
- `references/39-operating-objective.md` — §39: Operating Objective
