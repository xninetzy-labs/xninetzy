# Cyber Campus — Full Lifecycle

This reference expands the 16-step lifecycle into operational detail. Read it when the core `SKILL.md` workflow is not enough.

## Core principles

### 1.1 The portal is the authority for current academic state

Current portal data is authoritative for:

* current semester,
* active academic status,
* current schedule,
* registered classes,
* available offerings,
* quotas,
* grades,
* KRS status,
* submission status,
* portal deadlines.

Stored memory, screenshots, previous conversations, or cached data must not silently override current verified portal state.

### 1.2 The adapter is the execution boundary

The model decides **what academic information or action is needed**. The portal adapter determines **how the portal must technically be accessed**. Never invent selectors, arbitrary JavaScript, undocumented endpoints, form field order, portal-specific identifiers, credentials, CAPTCHA responses, or grade tokens. If the adapter does not support an operation, stop rather than improvising.

## Session state

Represent session status explicitly:

```text
unknown
unauthenticated
authenticated
expired
challenge_required
blocked
unavailable
```

Before any protected operation:

1. inspect session status,
2. reuse an active authenticated session when valid,
3. trigger the supported verification/login process when required,
4. do not assume authentication persists indefinitely.

## Login and verification

When login is required:

1. check whether an existing authenticated session is still valid;
2. initiate the supported owner-bound verification flow;
3. preserve the portal's required sequence;
4. wait for asynchronous CAPTCHA/OTP settlement;
5. read the result through typed adapter methods.

CAPTCHA is a human verification boundary, not a reasoning problem to automate. Never solve, bypass, or infer CAPTCHA answers. Never expose credentials, session cookies, or verification tokens. The final response may report `verification completed` but never reveal the secret value.

## Page identity

Every academic read must identify:

* **Portal**
* **Page/domain**
* **Academic period**
* **Record type**

Examples:

```text
Grades → 2026/2027 Semester 1
Schedule → 2026/2027 Semester 1
Offerings → 2026/2027 Semester 1
KRS → 2026/2027 Semester 1
```

This prevents cross-semester confusion.

## Typed academic data

Normalize portal output into structured fields.

### Grades

```text
course_code
course_name
credits
grade
grade_points
semester
status
```

### Schedule

```text
course_code
course_name
class_group
day
start_time
end_time
room
lecturer
semester
```

### Course offering

```text
course_code
course_name
credits
class_group
lecturer
schedule
quota_total
quota_remaining
prerequisites
eligibility
registration_status
```

### KRS selection

```text
course_code
class_group
credits
schedule
status
conflict
eligibility
```

Never fill fields with guesses when the portal does not expose them.

## Minimal snapshots

When persistent state is needed, store only the minimum:

* academic period,
* relevant record identifiers,
* normalized values,
* timestamp,
* source/page identity,
* snapshot hash when required.

Never store passwords, cookies, browser state, CAPTCHA answers, grade tokens, session secrets, or unnecessary raw portal HTML.

## Freshness

Academic portal information is time-sensitive. Use:

```text
fresh
stale
unknown
unavailable
```

Refresh before consequential decisions when:

* quota may have changed,
* course offerings may have changed,
* registration window changed,
* grades were recently released,
* current selections may have changed,
* another session may have modified the KRS.

Never use a stale quota snapshot as if it were current.

## Grade reading

Grade reading requires special care:

1. verify session,
2. complete required private token/verification step,
3. select the exact academic period,
4. read the typed grade record,
5. disclose the exact period read,
6. verify that the returned data matches the requested period,
7. report uncertainty if the portal does not provide sufficient confirmation.

Do not summarize grades from an unspecified or inferred semester.

## Semester disambiguation

If the user asks "What are my grades?" and multiple periods exist, first determine the intended period from the portal context when possible. If the portal requires a period selection, use the explicitly selected period. When uncertainty materially changes the answer, stop and ask.

## Academic status

When reading academic status, distinguish:

* currently active,
* registered,
* on leave,
* graduated,
* academic hold,
* administrative restriction,
* other portal-defined states.

Use the portal's exact status terminology when possible. Do not infer sensitive institutional consequences beyond what the portal reports.

## Schedule analysis

For schedule requests:

1. read the exact semester,
2. normalize meeting times,
3. group by day,
4. detect overlapping intervals,
5. identify potential gaps only when useful.

A conflict is an actual time overlap, not merely adjacent classes. Adjacent blocks such as `09:00–10:40` and `10:40–12:20` are not an overlap.

## Course offering analysis

Before recommending a course selection, inspect:

* course code,
* course name,
* credits,
* class/group,
* prerequisite,
* quota,
* remaining seats,
* schedule,
* eligibility,
* registration state,
* academic restrictions.

Do not recommend a class as available merely because it appears in a static catalog.

## Prerequisite reasoning

Prerequisites should come from:

1. current portal rules,
2. official curriculum data,
3. verified course requirements.

Do not infer prerequisites from course order, naming, or assumed curriculum structure. Represent states explicitly:

```text
satisfied
not_satisfied
uncertain
not_required
```

A course with an unmet required prerequisite should not be treated as safely selectable.

## Quota handling

Quota is volatile. For each relevant class, distinguish:

```text
quota_total
quota_used
quota_remaining
availability_state
snapshot_time
```

Possible availability states:

```text
available
limited
full
unknown
```

Never present a prior `available` state as current without refreshing the portal.

## Stop conditions

Stop when:

* session expires,
* CAPTCHA/OTP is required,
* token is unavailable,
* selectors are ambiguous,
* course identity is unclear,
* semester is unclear,
* quota changed,
* prerequisites changed,
* approval hash no longer matches,
* staged KRS differs from plan,
* portal returns an unexpected state,
* submission confirmation is missing,
* an operation becomes broader than approved.

Stopping is safer than guessing.

## Security and privacy

Never expose or persist:

* passwords,
* session cookies,
* authentication headers,
* CAPTCHA answers,
* grade tokens,
* private verification codes,
* browser state,
* hidden portal HTML,
* raw private network requests.

Use the smallest amount of academic information needed to complete the task.

## Academic planning integration

When combined with a learning system:

```text
Cyber Campus
  ↓
Current Academic State
  ↓
Course / KRS Constraints
  ↓
Learning OS
  ↓
Prerequisite Analysis
  ↓
Study Roadmap
```

For example:

```text
Current course:
Database Systems

Learning concepts:
SQL
Normalization
Transactions
Indexing

Weak concept:
Transactions

Next learning focus:
Transaction isolation and concurrency
```

The portal provides the academic context; the Learning OS handles capability development.

## Graph integration

When a graph system is available, useful relationships may include:

```text
Course
  ── requires ──> Concept

Course
  ── prerequisite ──> Course

KRS Plan
  ── selects ──> Class

Class
  ── belongs_to ──> Course

Course
  ── supports ──> Learning Goal
```

Do not infer these relationships without supporting evidence.

## Operating rules

The system must:

* check session before protected actions,
* identify the exact academic period,
* use deterministic typed readers and writers,
* never invent selectors or portal internals,
* never solve or bypass CAPTCHA,
* keep credentials and verification tokens private,
* read before recommending,
* dry-run before writing,
* bind approval to the exact plan,
* revalidate after approval and before every write phase,
* separate staging approval from final submission approval,
* verify the portal after every consequential action,
* preserve audit evidence without storing secrets,
* stop whenever portal state becomes ambiguous.

The central safety principle is:

> **A proposed academic action is not an executed academic action, and an executed action is not a successful action until the portal confirms it.**