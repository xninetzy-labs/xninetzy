---
name: hebat-academic
description: Academic operating system for HEBAT or Moodle courses, including course freshness, activities, assignments, deadlines, learning materials, downloadable files, PDF reading, assignment grounding, submission preparation, and submission verification. Use for LMS course work where human approval is required before any external upload or final submission.
metadata:
  scope: general
  platform: "HEBAT/Moodle-like LMS"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> refresh -> identify -> retrieve -> verify -> understand -> ground -> prepare -> approve -> execute -> confirm -> learn"
---

# HEBAT Academic OS

This skill is the reusable and safety-conscious workflow for working with academic learning management systems such as **HEBAT, Moodle, and compatible course portals**.

It connects academic course activity to the broader IT Learning OS without treating the LMS itself as the learning system.

The system should answer four distinct questions:

* What is happening in the course?
* What material or requirement matters?
* What should the learner do next?
* What action, if any, requires explicit approval?

The core lifecycle is:

**Discover → Refresh → Identify → Retrieve → Verify → Understand → Ground → Prepare → Approve → Execute → Confirm → Learn**

## When to use

* the user asks for an HEBAT/Moodle course, activity, assignment, or deadline;
* the user wants to download or read course materials;
* the user wants to ground an assignment in the current course context;
* the user wants to prepare or execute a confirmed submission.

## When NOT to use

* Cyber Campus or UACC operations — use `xninetzy-cyber-campus` or `xninetzy-uacc`;
* assignment orchestration across many skills — use `xninetzy-assignment-orchestrator`;
* web structure analysis without LMS workflow — use `xninetzy-web-analysis`.

## Core principles

* **The LMS is a source of academic context.** HEBAT/Moodle should provide authoritative context for course identity, activity identity, assignment requirements, deadlines, lecturer instructions, learning materials, submission rules, available files, and grades/statuses when accessible. Do not replace official course information with assumptions from memory.
* **Freshness before action.** Course information can change. Refresh when a deadline may have changed, an activity appears newly created or modified, the user asks for current status, submission information is uncertain, a file may have been replaced, the last synchronization is stale, or the portal indicates a different state. Never present stale course information as current without qualification.
* **Portal internals are not evidence.** Credentials, cookies, browser state, raw HTML, session tokens, internal selectors, hidden page metadata, and technical request logs may help operate the connector but must never be exposed as evidence in the final answer.

## Academic context hierarchy

When determining what an assignment requires, prioritize:

```text
Current official activity/instruction
        ↓
Current course materials
        ↓
Official lecturer/course announcements
        ↓
Assignment brief
        ↓
HEBAT/Moodle metadata
        ↓
Stored knowledge / previous context
        ↓
General academic assumptions
```

Current explicit course instructions override generic templates.

## Core workflow

1. **Discover.** Identify the authenticated account/session, available courses, course names, and freshness of course information. Avoid unnecessary synchronization of the entire LMS.
2. **Refresh.** Re-fetch when information is stale, the user asks for current state, or the cache signals a likely change. Distinguish fresh, stale, unknown, and unavailable states.
3. **Identify.** Verify the course and activity identity (name, code, semester, title, type, deadline, submission status, required file or response format). Do not act on an activity solely because its title looks similar to another activity.
4. **Retrieve and verify.** Download only the requested file unless broader retrieval is explicitly required. Verify file existence, filename, type, non-zero size, readable structure, and expected format.
5. **Understand.** Extract only what is relevant to the user's current task unless they explicitly request a comprehensive digest.
6. **Ground the assignment.** Tie the assignment brief, lecturer instructions, required material, and relevant learning concepts together before planning the deliverable.
7. **Prepare.** Compile the complete intended transaction: course, activity, deadline, filename, file type, submission consequence, existing submission, and required action. Show this information before crossing the human-approval boundary.
8. **Approve explicitly.** Require explicit approval before upload, replacing a previous submission, final submission, or confirming an irreversible submission state. Approval must occur before the action, not after.
9. **Execute narrowly.** Perform only the smallest action required. Never overwrite a previous academic submission silently.
10. **Confirm.** Re-read the LMS submission status, timestamp, receipt/reference number, uploaded filename, and confirmation message. Do not claim success unless the LMS actually confirms the submission.
11. **Learn.** Update learning evidence and mastery state when the assignment maps to a concept, practice, or recall checkpoint.

## Material-to-learning mapping

When useful, create an explicit mapping:

| Academic Item     | Learning OS Mapping |
| ----------------- | ------------------- |
| Lecture/material  | Concept             |
| Assignment brief  | Target/constraint   |
| Practical task    | Practice            |
| Project milestone | Evidence            |
| Lecturer feedback | Evaluation          |
| Deadline          | Schedule constraint |
| Failed task       | Weak concept        |
| Review activity   | Recall checkpoint   |

This allows course activity to feed the learner's roadmap without duplicating the LMS.

## Academic digest

When the user asks for a course digest, prioritize actionable information:

```text
Course
Current Status
Upcoming Deadlines
New Activities
Important Materials
Assignment Requirements
Risks / Ambiguities
Recommended Learning Action
```

Do not overwhelm the learner with every portal item when only a few items are relevant.

## Deadline handling

Treat deadlines as time-sensitive data. For each deadline, capture exact date, exact time when available, timezone when relevant, course, activity, submission target, and current status. Use absolute dates in summaries when ambiguity is possible:

> Due Monday, August 24, 2026 at 23:59 WIB.

Do not infer a deadline from a general weekly schedule when the activity contains an explicit deadline.

Deadline risk classes (advisory):

```text
safe       — sufficient time and no obvious blockers
attention  — deadline approaching or preparation remains
at_risk    — major unfinished work, unclear requirements, or technical blocker
blocked    — submission cannot safely proceed
```

## Human-in-the-loop boundary

Uploading or final-submitting an academic artifact is consequential. Therefore:

**Prepare automatically. Approve explicitly. Execute narrowly. Verify externally.**

Approval must occur before upload, replacing a previous submission, final submission, or confirming an irreversible submission state. Do not treat an earlier general instruction as permanent approval for future consequential actions.

## Approval message

Before execution, present a compact confirmation:

```text
Target:
Course:
Activity:
File:
Action:
Deadline:
Existing submission:
Consequence:
Approval required:
```

The user should be able to understand what will happen without inspecting portal internals.

## Conflict resolution

* When HEBAT information conflicts with stored knowledge, current portal state wins for current course logistics.
* When lecturer instructions conflict with a generic skill rule, lecturer instructions win.
* When a file conflicts with a filename or earlier cached version, the verified current file wins.
* When portal state is uncertain, stop and surface the uncertainty.

## Security and privacy

Never expose passwords, cookies, access tokens, session identifiers, private browser state, authentication headers, hidden portal data, or internal selectors. Use only the minimum information necessary to explain the academic result.

## Reference map

* `references/retrieval.md` — course discovery, material retrieval, file verification, and PDF reading.
* `references/grounding.md` — assignment requirement extraction, conflict resolution, and Learning OS integration.
* `references/submission.md` — preparation, approval message, revalidation, narrowest-action principle, existing submission protection, and submission verification.

## Routing

* Cyber Campus academic status → `xninetzy-cyber-campus`.
* Cross-domain assignment orchestration → `xninetzy-assignment-orchestrator`.
* Research → `xninetzy-deep-research`.
* Learning capability development → `it-learning` and `xninetzy-learning-coach`.
* Obsidian note ingestion of LMS material → `xninetzy-obsidian-orchestra`.

## Completion contract

Every HEBAT interaction should return the relevant subset of:

* **Course identity** — verified course name/code when available.
* **Activity identity** — exact activity or assignment.
* **Freshness status** — fresh, stale, unknown, or unavailable.
* **Material/file status** — retrieved path, filename, type, and verification status.
* **Requirement status** — what the assignment actually requires.
* **Approval status** — not required / pending / approved / rejected.
* **Execution status** — not executed / executed / failed / uncertain.
* **Portal verification** — confirmed evidence from the LMS.
* **Learning connection** — the corresponding concept, task, evidence, or review checkpoint when applicable.
* **Next action** — one safe, bounded learning or academic action.