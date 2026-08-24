# Cyber Campus Academic OS

```yaml
---
name: cyber-campus
description: General-purpose, safety-first academic portal operating system for the owner's Cyber Campus or university SIS. Supports authenticated session inspection, navigation, profile and academic-status reads, schedules, grades, semester history, course offerings, quota and prerequisite analysis, KRS planning, staged changes, approval-gated writes, submission verification, and auditable evidence. Uses typed deterministic portal adapters and never invents selectors, credentials, CAPTCHA solutions, tokens, or portal state.
metadata:
  scope: general
  platform: "Cyber Campus / university SIS"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> session-check -> navigate -> read -> normalize -> analyze -> dry-run -> hash -> approve -> revalidate -> stage -> verify -> final-approve -> submit -> confirm -> audit"
---
```

# Cyber Campus Academic OS

This skill provides a reusable workflow for safely interacting with a **Cyber Campus, university Student Information System, or comparable academic portal**.

It covers both **read operations** and **consequential academic actions**, especially:

* login/session status,
* portal navigation,
* student profile,
* academic status,
* semester history,
* schedules,
* grades,
* course offerings,
* prerequisites,
* quotas,
* KRS planning,
* staged KRS changes,
* final KRS submission,
* confirmation and audit evidence.

The guiding principle is:

> **Read first, normalize second, plan before writing, approve consequential actions, revalidate immediately before execution, and never claim success without portal confirmation.**

The canonical lifecycle is:

**Discover → Session Check → Navigate → Read → Normalize → Analyze → Dry Run → Hash → Approve → Revalidate → Stage → Verify → Final Approve → Submit → Confirm → Audit**

---

# 1. Core Principles

## 1.1 The portal is the authority for current academic state

Current portal data should be treated as authoritative for:

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

---

## 1.2 The adapter is the execution boundary

The model should decide:

**what academic information or action is needed**

The portal adapter should determine:

**how the portal must technically be accessed.**

Never invent:

* selectors,
* arbitrary JavaScript,
* undocumented endpoints,
* form field order,
* portal-specific identifiers,
* credentials,
* CAPTCHA responses,
* grade tokens.

If the adapter does not support an operation, stop rather than improvising.

---

# 2. Domain Separation

Keep the following concerns distinct:

### Identity/session

Who is authenticated and whether the session remains valid.

### Academic read state

What the portal currently reports.

### Planning state

What the learner intends to do.

### Approval state

Whether a consequential action has been explicitly authorized.

### Execution state

What has actually been changed in the portal.

### Verification state

What the portal confirms after execution.

This prevents a proposed KRS plan from being mistaken for an actual KRS registration.

---

# 3. Session State

Represent session status explicitly.

Recommended states:

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

---

# 4. Login and Verification

When login is required:

1. check whether an existing authenticated session is still valid,
2. initiate the supported owner-bound verification flow,
3. preserve the portal's required sequence,
4. wait for asynchronous CAPTCHA/reCAPTCHA settlement,
5. read the result through typed adapter methods.

Never:

* solve CAPTCHA automatically,
* bypass CAPTCHA,
* infer CAPTCHA answers,
* expose credentials,
* expose session cookies,
* log private verification tokens.

CAPTCHA is a **human verification boundary**, not a reasoning problem to automate.

---

# 5. WhatsApp / Owner Verification

When the portal requires owner verification or a grade token:

* use the configured owner-bound verification workflow,
* keep token values private,
* do not echo token contents into prompts or logs,
* confirm only the resulting authenticated state,
* preserve the minimum required audit information.

The final response may say:

> Verification completed.

It should not reveal the secret token itself.

---

# 6. Navigation

Use deterministic typed navigation.

Before reading a page, verify:

* current portal context,
* target domain,
* semester when relevant,
* page identity,
* session validity.

Do not assume that a familiar URL or page title corresponds to the intended academic record.

---

# 7. Page Identity

Every academic read should identify at least:

**Portal**

**Page/domain**

**Academic period**

**Record type**

Examples:

```text
Grades → 2026/2027 Semester 1
Schedule → 2026/2027 Semester 1
Offerings → 2026/2027 Semester 1
KRS → 2026/2027 Semester 1
```

This prevents cross-semester confusion.

---

# 8. Typed Academic Data

Normalize portal output into structured fields.

## Grades

Possible fields:

```text
course_code
course_name
credits
grade
grade_points
semester
status
```

## Schedule

Possible fields:

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

## Course Offering

Possible fields:

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

## KRS Selection

Possible fields:

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

---

# 9. Minimal Snapshots

When persistent state is needed, store only the minimum information necessary.

Good snapshot contents:

* academic period,
* relevant record identifiers,
* normalized values,
* timestamp,
* source/page identity,
* snapshot hash when required.

Do not store:

* passwords,
* cookies,
* browser state,
* CAPTCHA answers,
* grade tokens,
* session secrets,
* unnecessary raw portal HTML.

---

# 10. Freshness

Academic portal information is time-sensitive.

Use:

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

---

# 11. Grade Reading

Grade reading requires special care.

Workflow:

1. verify session,
2. complete required private token/verification step,
3. select the exact academic period,
4. read the typed grade record,
5. disclose the exact period read,
6. verify that the returned data matches the requested period,
7. report uncertainty if the portal does not provide sufficient confirmation.

Example:

> Grades read for 2025/2026 Semester 2.

Do not summarize grades from an unspecified or inferred semester.

---

# 12. Semester Disambiguation

If the user asks:

> "What are my grades?"

and multiple periods exist, first determine the intended period from the portal context when possible.

If the portal requires a period selection, use the explicitly selected period.

When uncertainty materially changes the answer, stop and ask.

---

# 13. Academic Status

When reading academic status, distinguish:

* currently active,
* registered,
* on leave,
* graduated,
* academic hold,
* administrative restriction,
* other portal-defined states.

Use the portal's exact status terminology when possible.

Do not infer sensitive institutional consequences beyond what the portal reports.

---

# 14. Schedule Analysis

For schedule requests:

1. read the exact semester,
2. normalize meeting times,
3. group by day,
4. detect overlapping intervals,
5. identify potential gaps only when useful.

Represent a conflict as an actual time overlap, not merely adjacent classes.

Example:

```text
09:00–10:40
10:40–12:20
```

is not an overlap.

---

# 15. Course Offering Analysis

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

---

# 16. Prerequisite Reasoning

Prerequisites should come from:

1. current portal rules,
2. official curriculum data,
3. verified course requirements.

Do not infer prerequisites from:

* course order,
* naming,
* assumed curriculum structure.

Represent states explicitly:

```text
satisfied
not_satisfied
uncertain
not_required
```

A course with an unmet required prerequisite should not be treated as safely selectable.

---

# 17. Quota Handling

Quota is volatile.

For each relevant class, distinguish:

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

Never present a prior "available" state as current without refreshing the portal.

---

# 18. KRS Planning

KRS planning has two separate phases:

### Planning

No portal state is changed.

### Execution

The portal is actually modified.

The planning phase should inspect:

* desired courses,
* prerequisites,
* eligibility,
* quota,
* credits,
* schedule conflicts,
* academic constraints,
* registration window,
* current selections.

---

# 19. KRS Dry Run

Before any KRS write:

```text
Current KRS
+
Available Offerings
+
Prerequisites
+
Eligibility
+
Quota
+
Schedule
+
Credit Constraints
↓
Dry-Run Plan
```

The dry-run should produce:

* selected courses,
* selected class groups,
* total credits,
* conflicts,
* blocked selections,
* quota risks,
* unresolved uncertainties.

No portal mutation occurs during dry run.

---

# 20. Credit Calculation

Calculate total credits from the verified selected courses.

Example:

```text
Course A = 3
Course B = 3
Course C = 2
Course D = 4
Total = 12 credits
```

Do not use course count as a substitute for credit totals.

If a credit cap exists, compare the total against the portal's current constraint rather than a remembered default.

---

# 21. Schedule Conflict Detection

For each planned class:

```text
day
start_time
end_time
```

detect whether:

```text
start_A < end_B
AND
start_B < end_A
```

when both classes occur on the same day.

Report:

* conflicting courses,
* exact overlapping interval,
* whether the conflict is definite or uncertain.

Do not silently resolve conflicts by choosing one course.

---

# 22. KRS Plan Identity

Every prepared KRS plan should have a unique plan identifier.

Conceptually:

```text
Plan ID
Semester
Selected Classes
Total Credits
Constraints
Snapshot Hash
Action Hash
Created At
```

This gives the approval process a stable object to refer to.

---

# 23. Approval Binding

Approval must be bound to the specific plan.

The approval context should include:

```text
owner
plan_id
academic_period
selected_classes
total_credits
portal_snapshot_hash
action_hash
```

This prevents approval for one plan from being reused accidentally for another.

---

# 24. Action Hash

Create an action hash from the exact intended change set.

Conceptually:

```text
hash(
  academic_period,
  selected_classes,
  class_groups,
  action_type,
  relevant constraints
)
```

The hash is an integrity mechanism, not academic evidence by itself.

Do not expose sensitive internal values unnecessarily.

---

# 25. First Approval Gate

Before staging any KRS changes, show:

```text
Target:
Academic Period:
Plan ID:
Selected Classes:
Total Credits:
Conflicts:
Quota Risks:
Current KRS Impact:
Action:
Approval Required:
```

The user must explicitly approve the specific plan.

---

# 26. Revalidation After Approval

Immediately before writing:

recheck:

* session,
* academic period,
* current KRS,
* selected offerings,
* prerequisites,
* eligibility,
* quota,
* registration window,
* action hash,
* snapshot hash.

If any critical state changed:

**invalidate the previous approval and stop.**

Do not apply a plan against changed portal state.

---

# 27. Staged KRS Write

Apply the narrowest supported write.

Preferred flow:

```text
Approve
 ↓
Revalidate
 ↓
Stage selection
 ↓
Read staged KRS
 ↓
Compare against approved plan
```

Do not immediately jump from approval to final submission if the portal supports a staged state.

---

# 28. Staged Verification

After staging, verify:

* every selected course is present,
* every class group is correct,
* credit total matches,
* no unexpected selection was added,
* no approved selection disappeared,
* conflicts remain acceptable,
* portal reports the expected staged state.

If the staged result differs from the approved plan:

**stop.**

Do not final-submit.

---

# 29. Final Approval Gate

Final submission is a separate consequential action.

Require a second explicit approval after staged verification.

The user should see:

```text
Verified staged KRS:
Total credits:
Courses:
Differences from approved plan:
Submission consequence:
Final approval required:
```

Approval for staging is **not** automatically approval for final submission.

---

# 30. Final Submission

Before final submission:

1. verify session,
2. verify staged KRS,
3. verify academic period,
4. verify current portal state,
5. verify no material change,
6. verify final approval matches the current staged plan,
7. submit,
8. wait for portal confirmation.

Do not claim final registration merely because staging succeeded.

---

# 31. Submission Confirmation

Successful submission requires observable portal evidence such as:

* submitted status,
* confirmation message,
* receipt/reference number,
* timestamp,
* official confirmation page,
* verified final KRS state.

Preserve the minimum necessary evidence for auditability.

---

# 32. Screenshot Evidence

When permitted and useful, preserve screenshots of:

* final KRS,
* confirmation page,
* receipt,
* important state transition.

Screenshots should never contain unnecessary secrets.

Do not treat a screenshot as proof when it does not clearly show the relevant state.

---

# 33. Change Detection

At every consequential transition, compare:

```text previous verified state
vs
current portal state
```

Stop when there is a material difference.

Examples:

* quota decreased,
* class disappeared,
* prerequisite changed,
* KRS changed,
* registration window closed,
* session expired.

---

# 34. Failure Handling

If a KRS action fails:

record:

* plan ID,
* action phase,
* intended action,
* portal result,
* whether staging changed,
* whether final submission occurred,
* whether the original KRS remains intact,
* receipt/reference if any,
* safest next action.

Never assume a failed browser/tool operation means the portal did not change.

Re-read the portal before retrying.

---

# 35. Partial Success

A portal may partially apply changes.

Therefore:

```text
request
 ↓
portal response
 ↓
re-read actual state
 ↓
classify result
```

Possible outcomes:

```text
not_changed
partially_applied
fully_applied
submitted
unknown
```

Do not retry until the actual state is known.

---

# 36. Stop Conditions

Stop when:

* session expires,
* CAPTCHA is required,
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

---

# 37. Security and Privacy

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

---

# 38. Audit Trail

For consequential actions, maintain an auditable record containing:

```text
plan_id
academic_period
action_type
approval_status
snapshot_hash
action_hash
execution_time
portal_result
receipt/reference
verification_status
```

Do not store secret authentication material in the audit record.

---

# 39. Read vs Write Contract

## Read operations

Examples:

* grades,
* schedule,
* academic status,
* offerings,
* prerequisites,
* quotas,
* current KRS.

These should return verified portal state without requiring an execution approval gate.

## Write operations

Examples:

* selecting a course,
* removing a course,
* modifying KRS,
* submitting KRS.

These require explicit approval according to the staged workflow.

---

# 40. Recommendation Boundary

The system may analyze and recommend a KRS plan, but recommendation is not registration.

Keep these states separate:

```text
recommended
planned
approved
staged
verified
submitted
confirmed
```

Never describe a planned course as already registered.

---

# 41. Academic Planning Integration

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

---

# 42. Graph Integration

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

---

# 43. Standard Read Output

For a normal academic query:

```text
Academic Period
Page / Domain
Freshness
Session Status
Requested Data
Relevant Constraints
Conflicts / Uncertainty
Evidence
Next Action
```

---

# 44. Standard KRS Plan Output

```text
Academic Period
Current KRS
Proposed Selections
Total Credits
Prerequisite Status
Quota Status
Schedule Conflicts
Eligibility
Plan ID
Snapshot Hash
Approval Status
```

---

# 45. Standard Submission Output

```text
Academic Period
Plan ID
Approved Action
Staged Result
Final Approval
Submission Result
Portal Confirmation
Timestamp
Receipt / Reference
Audit Status
```

---

# 46. Completion Contract

Every interaction should return the relevant subset of:

**Period/page read**
Exact academic context.

**Structured result**
Normalized portal information.

**Freshness/session status**
Whether the result is current and authenticated.

**Conflicts or uncertainty**
Anything preventing a confident conclusion.

**Approval phase**
Not required, pending, approved, or completed.

**Execution status**
Not executed, staged, submitted, failed, or unknown.

**Verification evidence**
Portal-confirmed result.

**Next action**
One safe, bounded action when applicable.

---

# 47. Operating Rules

The system must:

**check session before protected actions,**

**identify the exact academic period,**

**use deterministic typed readers and writers,**

**never invent selectors or portal internals,**

**never solve or bypass CAPTCHA,**

**keep credentials and verification tokens private,**

**read before recommending,**

**dry-run before writing,**

**bind approval to the exact plan,**

**revalidate after approval and before every write phase,**

**separate staging approval from final submission approval,**

**verify the portal after every consequential action,**

**preserve audit evidence without storing secrets,**

**stop whenever portal state becomes ambiguous.**

The central safety principle is:

> **A proposed academic action is not an executed academic action, and an executed action is not a successful action until the portal confirms it.**

The canonical lifecycle is:

**Discover → Session Check → Navigate → Read → Normalize → Analyze → Dry Run → Hash → Approve → Revalidate → Stage → Verify → Final Approve → Submit → Confirm → Audit**
