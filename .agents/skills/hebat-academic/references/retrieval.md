# HEBAT Academic — Retrieval, Freshness, and Material Verification

This reference expands course discovery, freshness model, material retrieval, file verification, and PDF reading. Read it when handling LMS session state and downloaded artifacts.

## Course discovery

When accessing the LMS:

1. identify the authenticated account/session,
2. identify available courses,
3. verify course names and identifiers,
4. determine freshness of course information,
5. select the relevant course,
6. inspect only the necessary activity/material context.

Avoid unnecessary synchronization of the entire LMS.

## Freshness model

Maintain a simple state:

```text
fresh
stale
unknown
unavailable
```

* **Fresh** — information has been recently verified and no material change is suspected.
* **Stale** — information exists but should be refreshed before being used for a time-sensitive or consequential action.
* **Unknown** — there is insufficient information to determine freshness.
* **Unavailable** — the system cannot access the relevant portal state.

Never silently convert **unknown** into **fresh**.

## Course and activity identity

Before reading or acting on a record, verify:

**Course** — course name, course code when available, term/semester when relevant.

**Activity** — activity title, activity type, associated course, deadline, submission status, required file or response format.

Do not act on an activity solely because its title looks similar to another activity.

## Material retrieval

When the user asks for a file:

1. identify the exact course/activity,
2. identify the exact requested file,
3. download only that file unless broader retrieval is explicitly required,
4. save it to the configured HEBAT downloads location,
5. verify the file exists,
6. verify file type and basic integrity,
7. read it only after verification.

Avoid downloading large collections "just in case."

## File verification

A downloaded material should be checked for:

* file existence,
* filename,
* extension/type,
* non-zero size,
* readable structure,
* expected format.

For PDFs, verify that the file can actually be opened/read before using its contents. When a PDF is being analyzed, use the appropriate PDF inspection/rendering workflow rather than relying only on metadata.

## Material understanding

Do not stop at downloading a file. When the user asks to understand or use the material:

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

## Connecting HEBAT to the Learning OS

HEBAT content should be connected to the IT Learning OS when the relationship is explicit. Possible mappings:

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

Do not force every course activity into a learning-state record. Only create the connection when there is a clear relationship.

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

## PDF and document reading

For academic PDFs:

1. verify the source/file,
2. inspect structure,
3. identify relevant sections,
4. extract or read the needed content,
5. preserve context,
6. cite the material when appropriate,
7. connect findings to the assignment or Learning OS.

Do not summarize from a filename alone. Do not infer unseen pages from a partial extraction.

## Security and privacy

Never expose passwords, cookies, access tokens, session identifiers, private browser state, authentication headers, hidden portal data, or internal selectors. Use only the minimum information necessary to explain the academic result.