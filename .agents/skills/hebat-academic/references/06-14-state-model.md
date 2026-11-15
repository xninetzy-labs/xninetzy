# hebat-academic — §6–14

Contents: 6. State Model; 7. Freshness Model; 8. Refresh Rules; 9. Identity Verification; 10. Course Discovery; 11. Activity Discovery; 12. Deadline Handling; 13. Deadline Risk; 14. Material Retrieval

## 6. State Model

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

## 7. Freshness Model

Use explicit freshness states:

```text
fresh
stale
unknown
unavailable
```

#### Fresh

Recently verified against the current LMS state.

#### Stale

Previously verified but potentially outdated.

#### Unknown

No reliable verification timestamp/state exists.

#### Unavailable

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

## 8. Refresh Rules

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

## 9. Identity Verification

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

## 10. Course Discovery

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

## 11. Activity Discovery

When asked about assignments or activities:

1. identify the target course
2. retrieve relevant activities
3. filter by activity type where possible
4. identify deadlines
5. identify completion/submission state
6. verify the exact target activity

Do not assume the newest activity is the requested activity.

---

## 12. Deadline Handling

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

## 13. Deadline Risk

Use advisory states:

```text
safe
attention
at_risk
blocked
```

#### safe

Deadline sufficiently distant and no known blocker.

#### attention

Deadline approaching or preparation remains.

#### at_risk

Major unfinished work, unresolved requirement, or technical blocker exists.

#### blocked

The learner cannot safely complete the task with the currently available information or access.

These states are informational.

Do not create unnecessary urgency.

---

## 14. Material Retrieval

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
