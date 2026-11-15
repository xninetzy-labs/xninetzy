# hebat-academic — §22–33

Contents: 22. Approval Context; 23. Approval Semantics; 24. Revalidation Before Execution; 25. Narrowest-Action Principle; 26. Existing Submission Protection; 27. Execution; 28. Submission Verification; 29. Verification States; 30. Security and Privacy; 31. Error Handling; 32. Conflict Resolution; 33. Learning OS Integration

## 22. Approval Context

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

## 23. Approval Semantics

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

## 24. Revalidation Before Execution

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

## 25. Narrowest-Action Principle

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

## 26. Existing Submission Protection

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

## 27. Execution

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

## 28. Submission Verification

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

## 29. Verification States

Use:

```text
verified
failed
uncertain
```

#### verified

LMS explicitly confirms the intended action.

#### failed

LMS or execution process explicitly reports failure.

#### uncertain

The result cannot be reliably established.

Never convert `uncertain` into `verified`.

---

## 30. Security and Privacy

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

## 31. Error Handling

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

## 32. Conflict Resolution

#### Current LMS vs stored knowledge

Current verified LMS state wins.

#### Current lecturer instruction vs generic convention

Lecturer instruction wins.

#### Current file vs cached file

Current verified file wins.

#### Multiple current instructions

Prefer the most specific authoritative instruction.

#### Unresolved conflict

Stop and surface it.

Never silently resolve a material conflict through assumption.

---

## 33. Learning OS Integration

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
