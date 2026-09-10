# HEBAT Academic — Submission, Approval, and Verification

This reference expands the submission preparation, approval message, revalidation, narrowest-action principle, existing submission protection, failure handling, and stop conditions. Read it when preparing or executing any upload or final submission.

## Submission preparation

Before any upload/submission action, prepare the complete intended transaction. Confirm:

* **Course:**
* **Activity:**
* **Deadline:**
* **Filename:**
* **File type:**
* **Submission consequence:**
* **Existing submission:** yes/no/unknown
* **Required action:** upload / replace / submit / confirm

The system should show this information before crossing the human-approval boundary.

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

## Human-in-the-loop boundary

Uploading or final-submitting an academic artifact is consequential. Therefore:

**Prepare automatically. Approve explicitly. Execute narrowly. Verify externally.**

Approval must occur before upload, replacing a previous submission, final submission, or confirming an irreversible submission state. Do not treat an earlier general instruction as permanent approval for future consequential actions.

## Revalidation after approval

Approval is not enough by itself. Immediately before execution, revalidate:

* authenticated session,
* course,
* activity,
* deadline,
* file,
* file format,
* existing submission state.

This protects against state changes between preparation and execution.

## Narrowest-action principle

Perform only the smallest action required.

Examples:

* If the user asks to upload a file, do not automatically final-submit unless the LMS requires it and that action was explicitly approved.
* If the user asks to inspect a deadline, do not modify the assignment.
* If the user asks to download one PDF, do not download the full course.

## Existing submission protection

Before replacing or resubmitting:

1. determine whether a previous submission exists,
2. identify its status when available,
3. identify whether replacement is allowed,
4. surface the consequence,
5. obtain approval before destructive/replacement action.

Never overwrite a previous academic submission silently.

## Submission verification

After an upload or final submission, verify the portal's actual confirmation. Preferred evidence includes:

* submission status,
* submission timestamp,
* receipt/reference number,
* uploaded filename,
* portal confirmation message.

Do not claim `submitted successfully` unless the LMS actually confirms the submission.

## Failure handling

If an action fails, capture:

* target activity,
* attempted action,
* failure state,
* whether the file changed,
* whether a partial upload occurred,
* whether the previous submission remains intact,
* exact next safe action.

Never retry blindly when the submission state is uncertain.

## Stop conditions

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

## Security and privacy

Never expose passwords, cookies, access tokens, session identifiers, private browser state, authentication headers, hidden portal data, or internal selectors. Use only the minimum information necessary to explain the academic result.

## Standard output patterns

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

## Operating rules

The system must:

* verify before relying,
* retrieve before summarizing,
* distinguish official requirements from recommendations,
* connect academic work to learning only when justified,
* prepare before requesting approval,
* revalidate immediately before consequential actions,
* verify the portal after execution,
* never claim success without confirmation.

The final objective is not merely "the assignment was submitted." It is:

> **"The learner understands the requirement, has produced defensible evidence of learning, and the academic action was completed safely and verifiably."**