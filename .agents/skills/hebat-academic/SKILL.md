# HEBAT Academic OS

```yaml
---
name: hebat-academic
description: General academic operating system for interacting with the owner's HEBAT or Moodle courses, including course freshness, activities, assignments, deadlines, learning materials, downloadable files, PDF reading, assignment grounding, submission preparation, uploads, submission verification, and integration with the IT Learning OS. Uses human approval before any external upload or final submission.
metadata:
  scope: general
  platform: "HEBAT/Moodle-like LMS"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> refresh -> identify -> retrieve -> verify -> understand -> ground -> prepare -> approve -> execute -> confirm -> learn"
---
```

# HEBAT Academic OS

This skill provides a reusable and safety-conscious workflow for working with academic learning management systems such as **HEBAT, Moodle, and compatible course portals**.

It connects academic course activity to the broader **IT Learning OS** without treating the LMS itself as the learning system.

The system should answer four distinct questions:

**What is happening in the course?**
**What material or requirement matters?**
**What should the learner do next?**
**What action, if any, requires explicit approval?**

The core lifecycle is:

**Discover → Refresh → Identify → Retrieve → Verify → Understand → Ground → Prepare → Approve → Execute → Confirm → Learn**

---

# 1. Core Principles

## 1.1 The LMS is a source of academic context

HEBAT/Moodle should provide authoritative context for:

* course identity,
* activity identity,
* assignment requirements,
* deadlines,
* lecturer instructions,
* learning materials,
* submission rules,
* available files,
* grades/statuses when accessible.

Do not replace official course information with assumptions from memory.

---

## 1.2 Freshness before action

Course information can change.

Before relying on cached information, determine whether it is sufficiently fresh.

Refresh when:

* a deadline may have changed,
* an activity appears newly created or modified,
* the user asks for the latest/current status,
* submission information is uncertain,
* a file may have been replaced,
* the last synchronization is stale,
* the portal indicates a different state.

Never present stale course information as current without qualification.

---

## 1.3 Portal internals are not evidence

The following are implementation details, not academic evidence:

* credentials,
* cookies,
* browser state,
* raw HTML,
* session tokens,
* internal selectors,
* hidden page metadata,
* technical request logs.

These may help operate the connector but must never be exposed as evidence in the final answer.

---

# 2. Academic Context Hierarchy

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

---

# 3. Course Discovery

When accessing the LMS:

1. identify the authenticated account/session,
2. identify available courses,
3. verify course names and identifiers,
4. determine freshness of course information,
5. select the relevant course,
6. inspect only the necessary activity/material context.

Avoid unnecessary synchronization of the entire LMS.

---

# 4. Freshness Model

Maintain a simple state:

```text
fresh
stale
unknown
unavailable
```

### Fresh

Information has been recently verified and no material change is suspected.

### Stale

Information exists but should be refreshed before being used for a time-sensitive or consequential action.

### Unknown

There is insufficient information to determine freshness.

### Unavailable

The system cannot access the relevant portal state.

Never silently convert **unknown** into **fresh**.

---

# 5. Course and Activity Identity

Before reading or acting on a record, verify:

**Course**

* course name,
* course code, when available,
* term/semester, when relevant.

**Activity**

* activity title,
* activity type,
* associated course,
* deadline,
* submission status,
* required file or response format.

Do not act on an activity solely because its title looks similar to another activity.

---

# 6. Assignment Requirement Extraction

When an assignment is requested, extract the actual requirements.

At minimum, identify:

* task description,
* required output,
* expected content,
* format,
* deadline,
* submission method,
* individual/group requirement,
* naming convention,
* attached/reference materials,
* rubric or grading criteria, when available,
* lecturer-specific constraints.

Separate:

**explicit requirements**

from:

**inferred recommendations**.

Never present an inference as an official requirement.

---

# 7. Material Retrieval

When the user asks for a file:

1. identify the exact course/activity,
2. identify the exact requested file,
3. download only that file unless broader retrieval is explicitly required,
4. save it to the configured HEBAT downloads location,
5. verify the file exists,
6. verify file type and basic integrity,
7. read it only after verification.

Avoid downloading large collections "just in case."

---

# 8. File Verification

A downloaded material should be checked for:

* file existence,
* filename,
* extension/type,
* non-zero size,
* readable structure,
* expected format.

For PDFs, verify that the file can actually be opened/read before using its contents.

When a PDF is being analyzed, use the appropriate PDF inspection/rendering workflow rather than relying only on metadata.

---

# 9. Material Understanding

Do not stop at downloading a file.

When the user asks to understand or use the material:

```text
Course Context
      ↓
Relevant Material
      ↓
Required Concepts
      ↓
Assignment Relationship
      ↓
Learning Objective
      ↓
Next Action
```

Extract only what is relevant to the user's current task unless they explicitly request a comprehensive digest.

---

# 10. Connecting HEBAT to the Learning OS

HEBAT content should be connected to the IT Learning OS when the relationship is explicit.

Possible mappings:

```text
Course Material → Concept
Assignment → Practice Task
Project → Milestone
Quiz/Question → Recall Evidence
Lab → Practical Evidence
Deadline → Learning Schedule
Feedback → Mastery Update
Weak Area → Next Focus
```

Do not force every course activity into a learning-state record.

Only create the connection when there is a clear relationship.

---

# 11. Material-to-Learning Mapping

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

---

# 12. Academic Digest

When the user asks for a course digest, prioritize actionable information.

Recommended structure:

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

---

# 13. Deadline Handling

Treat deadlines as **time-sensitive data**.

For each deadline, capture:

* exact date,
* exact time when available,
* timezone when relevant,
* course,
* activity,
* submission target,
* current status.

Use absolute dates in summaries when ambiguity is possible.

Example:

> Due Monday, August 24, 2026 at 23:59 WIB.

Do not infer a deadline from a general weekly schedule when the activity contains an explicit deadline.

---

# 14. Deadline Risk Classification

When helpful, classify deadlines:

### Safe

Sufficient time and no obvious blockers.

### Attention

Deadline is approaching or preparation remains.

### At Risk

Major unfinished work, unclear requirements, or technical blocker.

### Blocked

Submission cannot safely proceed because an essential requirement, file, permission, or portal state is unavailable.

The classification is advisory and should be based on observable evidence.

---

# 15. Submission Preparation

Before any upload/submission action, prepare the complete intended transaction.

Confirm:

**Course:**
**Activity:**
**Deadline:**
**Filename:**
**File type:**
**Submission consequence:**
**Existing submission:** yes/no/unknown
**Required action:** upload / replace / submit / confirm

The system should show this information before crossing the human-approval boundary.

---

# 16. Human-in-the-Loop Boundary

Uploading or final-submitting an academic artifact is consequential.

Therefore:

**Prepare automatically.
Approve explicitly.
Execute narrowly.
Verify externally.**

Approval must occur before:

* upload,
* replacing a previous submission,
* final submission,
* confirming an irreversible submission state.

Do not treat an earlier general instruction as permanent approval for future consequential actions.

---

# 17. Approval Message

Before execution, present a compact confirmation containing:

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

---

# 18. Revalidation After Approval

Approval is not enough by itself.

Immediately before execution, revalidate:

* authenticated session,
* course,
* activity,
* deadline,
* file,
* file format,
* existing submission state.

This protects against state changes between preparation and execution.

---

# 19. Narrowest-Action Principle

Perform only the smallest action required.

Examples:

If the user asks to upload a file, do not automatically final-submit unless the LMS requires it and that action was explicitly approved.

If the user asks to inspect a deadline, do not modify the assignment.

If the user asks to download one PDF, do not download the full course.

---

# 20. Existing Submission Protection

Before replacing or resubmitting:

1. determine whether a previous submission exists,
2. identify its status when available,
3. identify whether replacement is allowed,
4. surface the consequence,
5. obtain approval before destructive/replacement action.

Never overwrite a previous academic submission silently.

---

# 21. Submission Verification

After an upload or final submission:

verify the portal's actual confirmation.

Preferred evidence includes:

* submission status,
* submission timestamp,
* receipt/reference number,
* uploaded filename,
* portal confirmation message.

Do not claim:

> "Submitted successfully"

unless the LMS actually confirms the submission.

---

# 22. Failure Handling

If an action fails:

capture:

* target activity,
* attempted action,
* failure state,
* whether the file changed,
* whether a partial upload occurred,
* whether the previous submission remains intact,
* exact next safe action.

Never retry blindly when the submission state is uncertain.

---

# 23. Stop Conditions

Stop rather than guessing when encountering:

* expired authentication,
* ambiguous activity,
* changed activity identity,
* unsupported file format,
* uncertain deadline,
* missing required file,
* unclear previous submission status,
* ambiguous selectors,
* portal errors,
* unclear consequence,
* uncertain confirmation.

When stopped, report the blocker and preserve the current safe state.

---

# 24. Security and Privacy

Never expose:

* passwords,
* cookies,
* access tokens,
* session identifiers,
* private browser state,
* authentication headers,
* hidden portal data,
* internal selectors.

Use only the minimum information necessary to explain the academic result.

---

# 25. PDF and Document Reading

For academic PDFs:

1. verify the source/file,
2. inspect structure,
3. identify relevant sections,
4. extract or read the needed content,
5. preserve context,
6. cite the material when appropriate,
7. connect findings to the assignment or Learning OS.

Do not summarize from a filename alone.

Do not infer unseen pages from a partial extraction.

---

# 26. Assignment Grounding

Before creating an assignment deliverable based on HEBAT material:

```text
Assignment Brief
       +
Lecturer Instructions
       +
Required Material
       +
Relevant Learning Concepts
       ↓
Assignment Grounding
       ↓
Planning
       ↓
Build
       ↓
QA
```

The assignment should be grounded in the actual course requirements rather than a generic template.

---

# 27. Conflict Resolution

When HEBAT information conflicts with stored knowledge:

**current portal state wins for current course logistics.**

When lecturer instructions conflict with a generic skill rule:

**lecturer instructions win.**

When a file conflicts with a filename or earlier cached version:

**the verified current file wins.**

When the portal state is uncertain:

**stop and surface the uncertainty.**

---

# 28. Academic Action vs Learning Action

Keep these two actions separate.

### Academic action

Examples:

* download,
* upload,
* submit,
* inspect activity,
* confirm deadline.

### Learning action

Examples:

* read,
* explain,
* practice,
* recall,
* build,
* review,
* assess mastery.

The LMS tells the learner **what the course requires**.

The Learning OS determines **how the learner can become capable of doing it**.

---

# 29. Recommended Combined Workflow

For assignments requiring learning and submission:

```text
HEBAT
 ↓
Identify requirement
 ↓
Retrieve material
 ↓
Verify material
 ↓
Understand concepts
 ↓
Learning OS
 ↓
Diagnose prerequisites
 ↓
Plan practice
 ↓
Produce evidence
 ↓
Build assignment artifact
 ↓
QA
 ↓
HEBAT
 ↓
Prepare submission
 ↓
Human approval
 ↓
Revalidate
 ↓
Upload / submit
 ↓
Portal confirmation
 ↓
Learning OS
 ↓
Record evidence + review
```

This closes the loop between coursework and actual learning.

---

# 30. Completion Contract

Every completed HEBAT interaction should return the relevant subset of:

**Course identity**
Verified course name/code when available.

**Activity identity**
Exact activity or assignment.

**Freshness status**
Fresh, stale, unknown, or unavailable.

**Material/file status**
Retrieved path, filename, type, and verification status when applicable.

**Requirement status**
What the assignment actually requires.

**Approval status**
Not required / pending / approved / rejected.

**Execution status**
Not executed / executed / failed / uncertain.

**Portal verification**
Confirmed evidence from the LMS.

**Learning connection**
The corresponding concept, task, evidence, or review checkpoint when applicable.

**Next action**
One safe, bounded learning or academic action.

---

# 31. Standard Output Patterns

### Course status

```text
Course
Freshness
Current Activities
Upcoming Deadlines
Important Changes
Next Learning Action
```

### Assignment inspection

```text
Course
Activity
Deadline
Requirements
Required Files
Submission Rules
Learning Implications
Next Action
```

### Material retrieval

```text
Course
Activity
File
Path
File Verification
Relevant Content
Learning Connection
```

### Submission preparation

```text
Course
Activity
Deadline
File
Existing Submission
Proposed Action
Consequence
Approval Required
```

### Submission completion

```text
Course
Activity
File
Action
Approval
Portal Confirmation
Timestamp
Receipt / Reference
Learning Record
```

---

# 32. Operating Rules

The system must:

**verify before relying,**

**retrieve before summarizing,**

**distinguish official requirements from recommendations,**

**connect academic work to learning only when justified,**

**prepare before requesting approval,**

**revalidate immediately before consequential actions,**

**verify the portal after execution,**

**never claim success without confirmation.**

The canonical HEBAT lifecycle is:

**Discover → Refresh → Identify → Retrieve → Verify → Understand → Ground → Prepare → Approve → Execute → Confirm → Learn**

The final objective is not merely:

> "The assignment was submitted."

It is:

> **"The learner understands the requirement, has produced defensible evidence of learning, and the academic action was completed safely and verifiably."**
