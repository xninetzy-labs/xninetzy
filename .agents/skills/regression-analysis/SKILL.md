---
name: "regression-analysis"
description: "Diagnose regressions by diffing the pre/post behavior of a system, identifying the commit that introduced the change, and proposing a minimal revert or fix. Use when the operator reports a previously-passing test now fails, a metric regressed, or a behavior changed unexpectedly."
metadata:
  author: "xninetzy"
  version: "1.0.0"
  scope: "domain"
  priority: "P1"
  required_tools:
    - repo_diff
    - repo_search
    - repo_symbol
    - repo_test
    - repo_risk
  optional_tools:
    - lightning_record_action
    - observability_emit
    - memory_failure_store
    - hitl_request_approval
  trigger_conditions:
    - a previously-passing test now fails
    - a metric regressed vs. its baseline
    - the operator says "this used to work"
    - a canary rollout needs a rollback decision
  prerequisites:
    - failing test or metric trace reachable
    - pre-regression baseline reachable (commit / snapshot / metric window)
---

# regression-analysis

Diagnose and propose minimal remediation for regressions.
Companion to `tdd-workflow` and the `repo_diff` / `repo_risk` MCP tools.

## Pipeline

```
FAILING_TEST
   ↓
BASELINE_COMMIT
   ↓
BISECT_CANDIDATES
   ↓
EVIDENCE_TRIAGE
   ↓
MINIMAL_FIX_PROPOSAL
   ↓
REGRESSION_TEST_ASSERTION
   ↓
HANDOFF
```

## Operating procedure

```
REPRODUCE
   ↓
LOCALIZE
   ↓
ISOLATE_COMMIT
   ↓
PROPOSE_FIX
   ↓
WRITE_REGRESSION_TEST
   ↓
VERIFY
```

## Operating rules

1. Never mark a regression as "fixed" without a regression test that
   fails before the fix and passes after.
2. Bisect candidates must be ranked by `{touches_failing_code × recency}`.
3. The minimal fix must be **smaller** than the reverted commit —
   otherwise prefer the revert.
4. If the regression crosses a layer boundary, escalate to
   `architecture-analysis` before proposing the fix.
5. Always pair the diagnosis with the evidence chain that proved it.

## Required outputs

- Bisect shortlist: `{commit, author, timestamp, score, why}`
- Failing-call trace: `{call_site, last_known_good_commit, suspect}`
- Proposed patch (diff, not prose)
- Regression test stub that reproduces the failure

## Anti-patterns

- "Just revert HEAD" without bisecting
- "It's flaky, re-run it" without isolating the cause
- Proposing a refactor as the fix for a single regression
