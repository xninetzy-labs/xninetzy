# Cyber Campus — Policies, Schemas, and Audit

This reference collects typed schemas, freshness policy, audit trail, and the completion contract. Read it when implementing typed readers/writers or auditing a consequential action.

## Standard read output

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

## Standard KRS plan output

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

## Standard submission output

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

## Audit trail

For consequential actions, maintain an auditable record:

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

## Read vs write contract

### Read operations

Examples:

* grades,
* schedule,
* academic status,
* offerings,
* prerequisites,
* quotas,
* current KRS.

These return verified portal state without requiring an execution approval gate.

### Write operations

Examples:

* selecting a course,
* removing a course,
* modifying KRS,
* submitting KRS.

These require explicit approval through the staged workflow.

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

## Freshness policy

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

## Completion contract

Every interaction returns the relevant subset of:

**Period/page read** — exact academic context.

**Structured result** — normalized portal information.

**Freshness/session status** — whether the result is current and authenticated.

**Conflicts or uncertainty** — anything preventing a confident conclusion.

**Approval phase** — not required, pending, approved, or completed.

**Execution status** — not executed, staged, submitted, failed, or unknown.

**Verification evidence** — portal-confirmed result.

**Next action** — one safe, bounded action when applicable.

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