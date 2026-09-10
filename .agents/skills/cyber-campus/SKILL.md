---
name: cyber-campus
description: Safety-first operating system for the owner's Cyber Campus or university SIS session. Use when authorized authentication, course/KRS reads, schedule or grade inspection, quota or prerequisite analysis, staged KRS planning, approval-gated writes, submission verification, or auditable evidence collection is required.
metadata:
  scope: general
  platform: "Cyber Campus / university SIS"
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "discover -> session-check -> navigate -> read -> normalize -> analyze -> dry-run -> hash -> approve -> revalidate -> stage -> verify -> final-approve -> submit -> confirm -> audit"
---

# Cyber Campus Academic OS

This skill is the reusable workflow for safely interacting with the **Cyber Campus, university Student Information System, or comparable academic portal**.

It covers both read operations and consequential academic actions: login/session status, portal navigation, student profile, academic status, semester history, schedules, grades, course offerings, prerequisites, quotas, KRS planning, staged KRS changes, final KRS submission, confirmation, and audit evidence.

The guiding principle is:

> **Read first, normalize second, plan before writing, approve consequential actions, revalidate immediately before execution, and never claim success without portal confirmation.**

The canonical lifecycle is:

**Discover → Session Check → Navigate → Read → Normalize → Analyze → Dry Run → Hash → Approve → Revalidate → Stage → Verify → Final Approve → Submit → Confirm → Audit**

## When to use

* the user asks to inspect grades, schedule, academic status, or current KRS;
* the user asks to plan, stage, or submit KRS changes;
* the user asks to verify quota, prerequisite, or eligibility state;
* the user asks to confirm whether a portal mutation actually happened.

## When NOT to use

* reading the underlying content of HEBAT or Moodle materials — use `hebat-academic`;
* generic web analysis without an authenticated portal — use `xninetzy-web-analysis`;
* UACC or UnairSatu SSO operations — use `xninetzy-uacc`.

## Domain separation

Keep these concerns distinct:

* **Identity/session** — who is authenticated and whether the session remains valid.
* **Academic read state** — what the portal currently reports.
* **Planning state** — what the learner intends to do.
* **Approval state** — whether a consequential action has been explicitly authorized.
* **Execution state** — what has actually been changed in the portal.
* **Verification state** — what the portal confirms after execution.

A proposed KRS plan is never an executed KRS registration.

## Core workflow

1. **Session check.** Confirm whether an authenticated session exists, is still valid, and matches the expected owner scope before any protected operation. Reuse an active session when valid; trigger the supported verification flow when required.
2. **Navigate deterministically.** Use typed navigation only. Before reading a page, verify current portal context, target domain, semester when relevant, page identity, and session validity. Never assume a familiar URL corresponds to the intended academic record.
3. **Read with identity.** Every academic read must identify the portal, page/domain, academic period, and record type. Grades from an unspecified semester must not be summarized.
4. **Normalize.** Convert portal output into typed records (grades, schedule, offerings, KRS). Never fill fields with guesses when the portal does not expose them.
5. **Analyze.** Inspect quota, prerequisites, eligibility, schedule conflicts, and credit constraints using current portal state, not memory.
6. **Dry-run KRS.** Produce a plan listing selected courses, class groups, total credits, conflicts, blocked selections, quota risks, and unresolved uncertainties. No portal mutation during dry run.
7. **Hash the action.** Bind the exact intended change set (academic period, selected classes, action type) into a stable hash for approval integrity.
8. **Approve and revalidate.** Show the exact plan, require explicit confirmation, and immediately recheck session, period, current KRS, offerings, prerequisites, eligibility, quota, window, and hash. Invalidate approval and stop on any material change.
9. **Stage and verify.** Apply the narrowest supported write, read back the staged state, compare against the approved plan, and stop on any difference. Final submission is a separate approval gate.
10. **Submit and confirm.** Execute once after a second explicit approval, capture portal confirmation (status, timestamp, receipt/reference, page evidence), and store the minimum audit record.
11. **Audit and report.** Persist the audit trail without secrets; classify the final outcome as `not_changed | partially_applied | fully_applied | submitted | unknown`.

## Read vs write contract

**Read operations** (grades, schedule, academic status, offerings, prerequisites, quotas, current KRS) return verified portal state without requiring an execution approval gate.

**Write operations** (selecting or removing a course, modifying KRS, submitting KRS) require explicit approval through the staged workflow above.

## Safety invariants

* Never solve or bypass CAPTCHA.
* Never infer, log, or echo CAPTCHAs, credentials, session cookies, OTP tokens, or grade tokens.
* Never invent selectors, JavaScript, undocumented endpoints, form field order, or portal-specific identifiers.
* Never claim a KRS action succeeded without portal confirmation; never overwrite a previous submission silently.
* Treat stale portal state as stale; refresh quotas, offerings, and submission state before consequential decisions.

## Reference map

* `references/lifecycle.md` — full 16-step lifecycle detail, state model, and stop conditions.
* `references/krs-staging.md` — KRS dry-run, approval binding, action hash, staging, verification, and final submission.
* `references/policies.md` — typed schemas, freshness states, security, audit trail, and completion contract.

## Routing

* HEBAT course material and assignment retrieval → `hebat-academic`.
* Academic work orchestration → `xninetzy-assignment-orchestrator`.
* Cross-session continuity → `xninetzy-memory`.
* General academic safety rules → `xninetzy-academic-safety`.
* Lightweight adapter for MCP tools → `xninetzy-cyber-campus`.

## Completion contract

Every Cyber Campus interaction returns the relevant subset of:

**Period/page read** — exact academic context.
**Structured result** — normalized portal information.
**Freshness/session status** — current and authenticated.
**Conflicts or uncertainty** — anything preventing a confident conclusion.
**Approval phase** — not required, pending, approved, or completed.
**Execution status** — not executed, staged, submitted, failed, or unknown.
**Verification evidence** — portal-confirmed result.
**Next action** — one safe, bounded action when applicable.