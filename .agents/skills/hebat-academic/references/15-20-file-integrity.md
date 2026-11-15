# hebat-academic — §15–20

Contents: 15. File Integrity; 16. Understand; 17. Grounding; 18. Assignment Grounding Contract; 19. Academic Digest; 20. Submission State Model

## 15. File Integrity

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

## 16. Understand

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

## 17. Grounding

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

## 18. Assignment Grounding Contract

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

## 19. Academic Digest

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

## 20. Submission State Model

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
