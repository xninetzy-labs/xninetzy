---
name: tdd-workflow
description: 'Forces every code-modification task to go through test → implement →
  verify, with the test step pre-writing a regression test that fails before any code
  change. Used for any change touching: deterministic logic, security boundaries,
  idempotency contracts, MCP tool signatures, repository migration, schema changes.
  Refuses to advance if the regression test does not exist, does not run, or does
  not reproduce the bug. Use whenever the operator asks to modify source code, fix
  a bug, or accept that "the test proves the change".'
metadata:
  author: xninetzy
  version: 1.0.0
  scope: engineering
  priority: P0
  required_tools: '["read_file","write_file","grep_search","glob_files","bash_run","ruff_check","pytest_run"]'
  optional_tools: '["lightning_episode_start","lightning_record_action","repo_search","repo_test","repo_diff","os_inbox","hitl_request_approval"]'
  trigger_conditions: '["the operator asks for any code change","the operator reports
    a bug","verification of a previous change is requested"]'
  prerequisites: '["failing regression test that reproduces the issue OR a written
    red-test for the new behavior","project root + test runner known","lint available
    (`ruff`)"]'
---


# tdd-workflow

The default contract for every code change in Xninetzy: prove the
defect exists, fix it, prove the fix is correct, prove nothing else
regressed. No shortcuts.

## The cycle

```
RED
   ↓
GREEN
   ↓
REFACTOR
   ↓
REGRESS
   ↓
HANDOFF
```

### 1. RED — write the regression test first

Before any code change:

- locate the existing test file (pytest, fastapi test client, etc.)
- write a focused test that reproduces the bug or asserts the new
  behavior
- run the test, confirm it fails for the right reason
- capture the failing output via `lightning_record_action`

If a regression test cannot be written (the bug lives in a non-
testable layer like a deployment script), escalate to the owner.

Never start a code change without a recorded failing test.

### 2. GREEN — make the smallest possible change

Make the minimum code change needed to make the failing test pass.

- stay inside the file the test exercises when possible
- prefer guarded narrow fixes to broad refactors
- no "while I'm here" modifications; track them as separate tasks

Verify:

```
pytest <new_test>     → pass
ruff check <changed_paths>
```

### 3. REFACTOR — strengthen the design

After the test passes, review the change for:

- whether the fix should be expressed in a more general primitive
  (helper, policy, idempotency layer)
- whether the regression test should be extended to cover the
  generalized primitive
- whether other sites in the codebase should adopt the same primitive

Refactor under the same red-green discipline; extend the test first
if the change introduces a new contract.

### 4. REGRESS — confirm nothing else broke

Run:

- `pytest <full affected module>`
- `ruff check <all changed paths>`
- the broader regression surface (`pytest -ra` for fast, full sweep
  before merge)

If any pre-existing test fails that the change should not affect:

- revert the change
- isolate the failing test
- fix forward

Do not push past a regression without explicit owner sign-off.

### 5. HANDOFF — persist the change

- ensure the change is committed (operator-driven; this skill does not
  push)
- ensure the diff matches the recorded failing test (use `repo_diff`)
- emit a handoff record via `os_inbox` with:
  - test name(s)
  - what the change fixed
  - risk surface affected
  - regression tests confirmed

## What this skill never does

- modifies source code without a recorded failing test
- claims a fix is verified without running it
- hides a failing test behind a skip / xfail / `@pytest.mark.skip`
- bypasses `ruff` or removes a test to pass a build
- commits secrets, env values, or generated artifacts

## Output contract

A tdd-workflow invocation returns:

```
tdd-workflow record
task_id: <uuid>
red_test:
    path: <...>
    name: <...>
    failure_capture: <output excerpt>
green_change:
    files_changed: [<path>, ...]
    diff_summary: <string>
regress:
    full_module_pass: bool
    lint_clean: bool
verdict: SHIPPED | BLOCKED
```

## Failure classification

| Class                          | Action                                |
|--------------------------------|---------------------------------------|
| `NO_RED_TEST`                   | refuse to advance; require regression test |
| `TEST_NOT_RUNNABLE`             | escalate to owner                    |
| `GREEN_BUT_REGRESS`            | revert; isolate failing test         |
| `LINT_FAILED`                  | run `ruff check --fix`; re-run       |
| `LINT_REVERTED_TO_PASS`        | refuse; lint regressions are real failures |

## Recovery

- failing test still fails after fix → revert and start again
- new test was wrong (asserts the wrong thing) → fix the test first,
  then re-attempt the change
- regression in a sibling test → revert and investigate the
  cross-effect
- permission denied or environment issue → escalate to owner

## See also

- `repo-context-packaging` — locating the right test file when the
  codebase is large
- `structured-project-execution` — durable spine for the change
- `mcp-development` — discipline for MCP tool signature changes
- `security-review` — discipline for changes touching authn/z or secrets
