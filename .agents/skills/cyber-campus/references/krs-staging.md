# Cyber Campus — KRS Staging

This reference expands the KRS planning, staging, approval binding, and submission workflow. Read it when an actual KRS write is being prepared or executed.

## KRS planning phases

KRS planning has two separate phases.

### Planning

No portal state is changed.

### Execution

The portal is actually modified.

The planning phase inspects:

* desired courses,
* prerequisites,
* eligibility,
* quota,
* credits,
* schedule conflicts,
* academic constraints,
* registration window,
* current selections.

## KRS dry run

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

## Credit calculation

Calculate total credits from the verified selected courses.

```text
Course A = 3
Course B = 3
Course C = 2
Course D = 4
Total = 12 credits
```

Do not use course count as a substitute for credit totals. If a credit cap exists, compare the total against the portal's current constraint rather than a remembered default.

## Schedule conflict detection

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

when both classes occur on the same day. Report:

* conflicting courses,
* exact overlapping interval,
* whether the conflict is definite or uncertain.

Do not silently resolve conflicts by choosing one course.

## KRS plan identity

Every prepared KRS plan should have a unique plan identifier:

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

## Approval binding

Approval must be bound to the specific plan:

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

## Action hash

Create an action hash from the exact intended change set:

```text
hash(
  academic_period,
  selected_classes,
  class_groups,
  action_type,
  relevant constraints
)
```

The hash is an integrity mechanism, not academic evidence by itself. Do not expose sensitive internal values unnecessarily.

## First approval gate

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

## Revalidation after approval

Immediately before writing, recheck:

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

If any critical state changed, **invalidate the previous approval and stop**. Do not apply a plan against changed portal state.

## Staged KRS write

Apply the narrowest supported write. Preferred flow:

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

## Staged verification

After staging, verify:

* every selected course is present,
* every class group is correct,
* credit total matches,
* no unexpected selection was added,
* no approved selection disappeared,
* conflicts remain acceptable,
* portal reports the expected staged state.

If the staged result differs from the approved plan: **stop**. Do not final-submit.

## Final approval gate

Final submission is a separate consequential action. Require a second explicit approval after staged verification:

```text
Verified staged KRS:
Total credits:
Courses:
Differences from approved plan:
Submission consequence:
Final approval required:
```

Approval for staging is not automatically approval for final submission.

## Final submission

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

## Submission confirmation

Successful submission requires observable portal evidence:

* submitted status,
* confirmation message,
* receipt/reference number,
* timestamp,
* official confirmation page,
* verified final KRS state.

Preserve the minimum necessary evidence for auditability.

## Screenshot evidence

When permitted and useful, preserve screenshots of:

* final KRS,
* confirmation page,
* receipt,
* important state transition.

Screenshots should never contain unnecessary secrets. Do not treat a screenshot as proof when it does not clearly show the relevant state.

## Change detection

At every consequential transition, compare:

```text
previous verified state
vs
current portal state
```

Stop when there is a material difference. Examples:

* quota decreased,
* class disappeared,
* prerequisite changed,
* KRS changed,
* registration window closed,
* session expired.

## Failure handling

If a KRS action fails, record:

* plan ID,
* action phase,
* intended action,
* portal result,
* whether staging changed,
* whether final submission occurred,
* whether the original KRS remains intact,
* receipt/reference if any,
* safest next action.

Never assume a failed browser/tool operation means the portal did not change. Re-read the portal before retrying.

## Partial success

A portal may partially apply changes:

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

## Recommendation boundary

The system may analyze and recommend a KRS plan, but recommendation is not registration. Keep these states separate:

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