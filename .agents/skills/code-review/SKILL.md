---
name: code-review
description: Pre-merge code review against the project's own rules (no comments, no silent retries, idempotency contracts, error propagation, naming, layering). Produces a per-file diff-anchored review with severity-tiered findings. Use whenever a PR or branch is about to be merged, or the operator asks "is this change ready?".
metadata:
  author: xninetzy
  version: "1.0.0"
  scope: domain
  priority: P1
  required_tools:
    - repo_diff
    - repo_search
    - repo_symbol
    - repo_architecture
  optional_tools:
    - repo_test
    - repo_dependency
    - lightning_record_action
    - learning_attach_resource
  trigger_conditions:
    - a PR is about to be merged
    - the operator asks "review this diff"
    - a feature branch is ready for QA
    - an external contributor submits a patch
  prerequisites:
    - target diff reachable (`git diff base...head` or PR URL)
    - project rulebook loaded (CLAUDE.md / AGENTS.md)
---

# code-review

Pre-merge diff review against project rules and standard engineering
hygiene. Companion to `tdd-workflow` and the `repo_diff` MCP tool.

## Pipeline

```
DIFF
   ↓
RULE_LOAD
   ↓
PER_FILE_SCAN
   ↓
NAMING_CHECK
   ↓
COMMENT_SCAN
   ↓
ERROR_PROPAGATION
   ↓
IDEMPOTENCY_CHECK
   ↓
LAYER_BOUNDARY_CHECK
   ↓
TEST_COVERAGE_CHECK
   ↓
REVIEW_REPORT
```

## Operating procedure

```
LOAD_DIFF
   ↓
LOAD_PROJECT_RULES
   ↓
SCAN_PER_FILE
   ↓
EMIT_FINDINGS
   ↓
SUGGEST_REWRITES
   ↓
BLOCK_OR_APPROVE
```

## Operating rules

1. Every finding is anchored to `{file_path}:{line_number}`.
2. Comment-related findings use the project's exact rule wording
   (e.g. "No comments in source code (rule §4)").
3. Never rewrite a function in the review — propose the rewrite as a
   separate, reviewable diff suggestion.
4. Approval is **blocked** when any `critical` or `high` finding is
   unresolved.
5. Layer-boundary violations cite the offending import statement.

## Required outputs

- Per-file findings: `{file, line, severity, rule, evidence, suggestion}`
- Verdict: `approve | request_changes | comment_only`
- Coverage delta: `{lines_added, lines_covered_by_test, coverage_pct}`

## Anti-patterns

- "Looks good to me" without a per-file scan
- Approving a PR that introduces comments without flagging them
- Treating a passing CI as proof the change is correct
