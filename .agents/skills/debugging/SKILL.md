---
name: debugging
description: Structured debugging workflow for unexpected runtime behavior — collects evidence before forming hypotheses, narrows to a single root cause, and proposes a verifiable fix. Use whenever the operator reports "X is broken", "why is Y doing Z?", or the system produces an unexpected error.
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - repo_search
    - repo_symbol
    - repo_diff
    - observability_query
    - memory_failure_store
  optional_tools:
    - repo_test
    - lightning_record_action
    - hitl_request_approval
    - os_inbox
    - action_policy_evaluate
  trigger_conditions:
    - the operator reports an unexpected error
    - a tool returns an empty / malformed result
    - a metric is off-baseline
    - the operator asks "why is X happening?"
  prerequisites:
    - failing scenario reachable (test, command, request)
    - observability / logs available for the failing scenario
---

# debugging

Evidence-first debugging workflow. No hypothesis before the evidence is
on the table. Companion to `observability_*` and `memory_failure_store`.

## Pipeline

```
SYMPTOM
   ↓
REPRODUCE
   ↓
OBSERVED_STATE
   ↓
EVIDENCE_TABLE
   ↓
HYPOTHESES_RANKED
   ↓
CONTROLLED_TEST
   ↓
ROOT_CAUSE
   ↓
MINIMAL_FIX
   ↓
REGRESSION_TEST
```

The pipeline is intentionally linear until the `HYPOTHESES_RANKED` step
— the order of the preceding steps is not optional.

## Operating procedure

```
CAPTURE_SYMPTOM
   ↓
WRITE_REPRO
   ↓
COLLECT_EVIDENCE
   ↓
LIST_HYPOTHESES
   ↓
RANK_BY_EVIDENCE
   ↓
DESIGN_CONTROLLED_TEST
   ↓
PROVE_OR_DISPROVE
   ↓
EMIT_FIX
```

## Operating rules

1. **No fix before root cause.** Symptoms are not root causes.
2. Every hypothesis must cite the evidence that supports it **and**
   the evidence that would refute it.
3. The regression test must fail before the fix and pass after — no
   "I checked manually".
4. Multiple hypotheses are normal; jumping to the first plausible one
   is the #1 debugging failure mode.
5. If the bug crosses module boundaries, escalate to
   `architecture-analysis` before proposing the fix.

## Required outputs

- Reproduction recipe (commands / inputs)
- Evidence table: `{timestamp, source, value, interpretation}`
- Hypothesis matrix: `{hypothesis, supporting_evidence, refuting_evidence, likelihood}`
- Root cause statement (one sentence)
- Proposed patch (diff)
- Regression test stub

## Anti-patterns

- "I added a print statement and it works now" without explaining why
- "It's a race condition" as a guess, not a measured observation
- Fixing the symptom (e.g. wrapping in try/except) instead of the
  cause
