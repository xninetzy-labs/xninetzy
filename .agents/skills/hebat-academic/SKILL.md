---

name: hebat-academic

description: Academic operating system for HEBAT, Moodle, and compatible LMS platforms. Use for course discovery, freshness-aware activity tracking, assignment and deadline identification, learning-material retrieval, file verification, assignment grounding, submission preparation, human-approved submission execution, external submission verification, and learning-state integration.

metadata:
        scope: general
        platform: "HEBAT/Moodle-like LMS"
        owner: xninetzy
        language: en
        version: "3.0.0"
        lifecycle: "discover -> refresh -> identify -> retrieve -> verify -> understand -> ground -> prepare -> approve -> revalidate -> execute -> confirm -> learn"
-------------------------------------------------------------------------------------------------------------------------------------------------------------

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

# 6. State Model

Treat LMS information as stateful data.

Every important LMS object should conceptually have:

```text
Identity
State
Timestamp
Source
Freshness
Confidence
```

For example:

```text
Course
  ├── identity
  ├── current status
  ├── last verified time
  └── source

Activity
  ├── identity
  ├── deadline
  ├── requirements
  ├── submission state
  ├── last verified time
  └── source

File
  ├── filename
  ├── type
  ├── size
  ├── version
  ├── integrity
  └── source
```

Do not collapse these properties into a single vague "current" flag.

---

# 7. Freshness Model

Use explicit freshness states:

```text
fresh
stale
unknown
unavailable
```

### Fresh

Recently verified against the current LMS state.

### Stale

Previously verified but potentially outdated.

### Unknown

No reliable verification timestamp/state exists.

### Unavailable

The LMS or relevant data could not be accessed.

Never present:

```text
stale
unknown
unavailable
```

as equivalent to:

```text
current
```

---

# 8. Refresh Rules

Refresh before consequential decisions when:

* deadline may have changed
* activity may have been modified
* submission state matters
* user asks for current status
* assignment instructions are uncertain
* required file may have changed
* an existing submission may be replaced
* cached information is stale
* the portal shows contradictory state

Do not unnecessarily synchronize the entire LMS.

Prefer:

```text
minimum required retrieval
```

over:

```text
full LMS synchronization
```

---

# 9. Identity Verification

Never identify an activity using title similarity alone.

Verify as many of the following as available:

```text
Course
Course code
Semester/term
Activity ID
Activity title
Activity type
Deadline
Submission state
Instruction context
Required file/response format
```

If multiple activities have similar titles:

1. compare course
2. compare term
3. compare activity identity
4. compare deadline
5. compare instructions
6. stop if ambiguity remains material

Never guess which activity the user means when the consequences are significant.

---

# 10. Course Discovery

When discovering courses:

1. retrieve available courses
2. identify active/relevant courses
3. avoid unnecessary retrieval of unrelated courses
4. distinguish current from archived courses
5. verify course identity before acting

Represent course state conceptually as:

```text
Course
├── name
├── code
├── term
├── status
├── activity count
└── freshness
```

---

# 11. Activity Discovery

When asked about assignments or activities:

1. identify the target course
2. retrieve relevant activities
3. filter by activity type where possible
4. identify deadlines
5. identify completion/submission state
6. verify the exact target activity

Do not assume the newest activity is the requested activity.

---

# 12. Deadline Handling

Deadlines are time-sensitive.

For each deadline capture:

* course
* activity
* exact date
* exact time when available
* timezone
* submission target
* current submission status
* source
* freshness

Prefer absolute dates:

```text
Monday, August 24, 2026 at 23:59 WIB
```

over:

```text
next Monday
```

when ambiguity is possible.

Never infer an activity deadline from:

* weekly schedules
* course calendars
* remembered patterns

when the activity contains an explicit deadline.

---

# 13. Deadline Risk

Use advisory states:

```text
safe
attention
at_risk
blocked
```

### safe

Deadline sufficiently distant and no known blocker.

### attention

Deadline approaching or preparation remains.

### at_risk

Major unfinished work, unresolved requirement, or technical blocker exists.

### blocked

The learner cannot safely complete the task with the currently available information or access.

These states are informational.

Do not create unnecessary urgency.

---

# 14. Material Retrieval

Retrieve only the material required for the current task.

When downloading a file, verify:

```text
exists
non-zero size
expected filename
expected type
readable structure
expected source
```

When version information exists, preserve it.

If a new file appears to replace an older file:

* identify the newer source
* avoid silently mixing versions
* use the verified current version for current work

---

# 15. File Integrity

For important academic files, verify:

* file exists
* extension matches content
* file is non-empty
* file opens successfully
* expected structure is present
* expected pages/sheets/slides exist where applicable

For PDFs, when layout matters:

```text
extract
→ render
→ inspect
```

Do not consider successful text extraction sufficient for visual validation.

Route detailed PDF validation to `pdf`.

---

# 16. Understand

Extract only the information relevant to the current task unless the user explicitly requests a comprehensive digest.

Identify:

* learning objective
* assignment objective
* required output
* required evidence
* required concepts
* methodology
* constraints
* deadline
* submission rules
* grading criteria
* lecturer-specific instructions

Do not rewrite the entire course when the user only needs one assignment requirement.

---

# 17. Grounding

Before assignment planning, establish:

```text
Course Context
+
Assignment Requirement
+
Relevant Learning Material
+
Required Evidence
+
Expected Output
```

The LMS provides academic grounding.

Specialized assignment skills determine:

* research strategy
* argument architecture
* artifact design
* document generation

Do not duplicate those responsibilities here.

---

# 18. Assignment Grounding Contract

When handing context to another skill, preserve:

```text
course_identity
activity_identity
official_instructions
deadline
submission_rules
required_format
required_materials
relevant_learning_objectives
grading_constraints
known_ambiguities
source_freshness
```

This prevents downstream agents from accidentally working from incomplete LMS context.

---

# 19. Academic Digest

When asked for a course digest, prioritize:

```text
Course
Current Status
Upcoming Deadlines
New Activities
Important Materials
Assignment Requirements
Submission Status
Risks / Ambiguities
Recommended Next Action
```

Keep the digest actionable.

Do not overwhelm the learner with irrelevant portal information.

---

# 20. Submission State Model

Treat submission as a state machine:

```text
NOT_STARTED
    ↓
PREPARED
    ↓
PENDING_APPROVAL
    ↓
APPROVED
    ↓
REVALIDATED
    ↓
EXECUTING
    ↓
SUBMITTED
    ↓
VERIFIED
```

Possible failure states:

```text
BLOCKED
FAILED
UNCERTAIN
```

Never jump directly from:

```text
PREPARED → VERIFIED
```

without actual LMS confirmation.

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

# 22. Approval Context

Before requesting approval, present:

```text
Target
Course
Activity
Current deadline
File
File type
File size
Action
Existing submission
Consequence
Current LMS state
Approval required
```

The user must be able to understand the action without seeing portal internals.

Do not hide material consequences.

---

# 23. Approval Semantics

Approval must be:

* explicit
* current
* specific to the intended action
* based on the current verified state

Examples of acceptable approval:

```text
Submit this file.
```

```text
Yes, upload and submit it to Assignment 3.
```

Do not infer approval from:

```text
Looks good.
```

unless the action being approved is unambiguous in context.

Do not reuse approval for another activity or another file.

---

# 24. Revalidation Before Execution

Immediately before a consequential action:

1. refresh relevant LMS state
2. verify activity identity
3. verify deadline
4. verify submission state
5. verify intended file
6. verify action consequence
7. verify approval still corresponds to the action

If any material property changed:

```text
STOP
→ surface the change
→ request renewed approval if necessary
```

Never execute using obsolete approval after a material state change.

---

# 25. Narrowest-Action Principle

Perform only the action required.

If the user requests:

```text
upload file
```

do not automatically:

* submit another file
* replace an existing submission
* edit course content
* modify unrelated settings
* post comments
* send messages

Minimize action scope.

---

# 26. Existing Submission Protection

Before upload/submission, determine whether an existing submission exists.

If yes, surface:

```text
Existing submission detected.
```

Then identify:

* existing filename
* submission timestamp
* current status
* whether replacement is allowed
* whether replacement changes grading/submission state

Never overwrite silently.

If replacement is consequential, require explicit approval specifically covering replacement.

---

# 27. Execution

After approval:

1. execute only the approved action
2. avoid unrelated portal interactions
3. capture the resulting LMS state
4. do not claim success before verification

If execution fails:

* report failure
* preserve the known state
* do not repeatedly retry blindly
* determine whether retry is safe
* request approval again if the action scope materially changes

---

# 28. Submission Verification

After execution, independently verify:

* activity identity
* submission status
* uploaded filename
* timestamp
* receipt/reference number if available
* LMS confirmation
* visible submission state

A local upload result is not sufficient evidence of LMS submission.

The authoritative confirmation must come from the LMS.

---

# 29. Verification States

Use:

```text
verified
failed
uncertain
```

### verified

LMS explicitly confirms the intended action.

### failed

LMS or execution process explicitly reports failure.

### uncertain

The result cannot be reliably established.

Never convert `uncertain` into `verified`.

---

# 30. Security and Privacy

Treat LMS access as sensitive.

Never expose:

* passwords
* access tokens
* cookies
* session identifiers
* authentication headers
* private browser state
* hidden portal data
* internal selectors
* raw request headers
* technical credentials

Do not include portal internals in evidence presented to the learner.

Use the minimum information necessary to explain the academic state.

---

# 31. Error Handling

When LMS access fails:

1. identify whether the failure is authentication, connectivity, permission, portal state, or unknown
2. preserve the last verified state
3. mark freshness appropriately
4. do not claim current status
5. do not execute consequential actions
6. tell the learner what remains uncertain

When an activity cannot be uniquely identified:

```text
STOP
→ report ambiguity
→ ask for the minimum missing information
```

---

# 32. Conflict Resolution

### Current LMS vs stored knowledge

Current verified LMS state wins.

### Current lecturer instruction vs generic convention

Lecturer instruction wins.

### Current file vs cached file

Current verified file wins.

### Multiple current instructions

Prefer the most specific authoritative instruction.

### Unresolved conflict

Stop and surface it.

Never silently resolve a material conflict through assumption.

---

# 33. Learning OS Integration

The LMS should provide evidence to the learner's broader learning system without becoming a duplicate LMS.

Map relevant events as:

| LMS Item          | Learning OS Mapping |
| ----------------- | ------------------- |
| Lecture/material  | Concept             |
| Assignment brief  | Target/constraint   |
| Practical task    | Practice            |
| Project milestone | Evidence            |
| Lecturer feedback | Evaluation          |
| Deadline          | Schedule constraint |
| Failed task       | Weak concept        |
| Review activity   | Recall checkpoint   |

Only create learning-state updates when sufficient evidence exists.

Do not infer mastery merely because an assignment was submitted.

---

# 34. Mastery Evidence

Distinguish:

```text
activity completed
≠
concept mastered
```

Possible evidence:

* assignment completion
* correct answer
* lecturer feedback
* revision quality
* repeated successful application
* assessment result
* demonstrated explanation

A submission alone should not automatically increase mastery confidence.

---

# 35. Routing

Route specialized work:

* Cross-domain assignment orchestration → `xninetzy-assignment-orchestrator`
* Assignment foundation → `hebat-assignment`
* Research → `xninetzy-deep-research`
* Artifact generation → `xninetzy-artifact-orchestrator`
* PDF processing → `pdf`
* Learning capability development → `it-learning`
* Learning coaching → `xninetzy-learning-coach`
* Obsidian ingestion → `xninetzy-obsidian-orchestra`
* Cyber Campus → `xninetzy-cyber-campus`
* UACC → `xninetzy-uacc`
* General web analysis → `xninetzy-web-analysis`

This skill remains the LMS control layer.

---

# 36. Reference Map

```text
references/
├── retrieval.md
├── grounding.md
└── submission.md
```

### retrieval.md

Contains:

* course discovery
* activity retrieval
* freshness handling
* material retrieval
* file verification
* PDF reading handoff

### grounding.md

Contains:

* assignment requirement extraction
* course-context mapping
* conflict resolution
* learning-objective mapping
* Learning OS integration

### submission.md

Contains:

* submission state machine
* approval protocol
* pre-execution revalidation
* existing-submission protection
* narrowest-action principle
* execution verification
* failure recovery

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

# 39. Operating Objective

The HEBAT Academic OS should minimize two classes of failure:

```text
ACADEMIC FAILURE
= wrong course
+ wrong activity
+ wrong requirement
+ stale deadline
+ wrong material
+ incomplete grounding

OPERATIONAL FAILURE
= unauthorized action
+ wrong file
+ silent replacement
+ stale approval
+ unverified submission
+ false success claim
```

The system succeeds when it provides:

```text
Current Context
+
Correct Academic Grounding
+
Explicit Human Control
+
Minimal Action
+
External Verification
+
Useful Learning Evidence
```
