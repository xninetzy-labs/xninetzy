---
name: "exam_qa:run-dry-practice"
description: "Run a practice or dry-run scenario against a fixture, scoring each question with the local heuristic provider. Produces evidence bundles and a graded ExamRunState. Always idempotent — replays return the same run_id."
metadata:
  scope: "task"
  owner: "xninetzy"
  language: "en"
  version: "0.1.0"
  lifecycle: "load -> select -> run -> grade -> evidence"
---

# Task: Run Dry or Practice Exam

## Inputs

- `scenario_id` (must be `kind in {"dry_run", "practice"}`)
- Optional `selector` (sequential or randomized with seed)

## Procedure

1. Load scenario via DB; verify `kind != "exam"` (no HITL needed for
   dry / practice runs).
2. Load fixture and select questions via `select_questions`.
3. Initialize `ExamRunState` in `PHASE_PLANNED`.
4. Transition: planned → ready → running → submitted → graded using the
   canonical state machine.
5. For each question, evaluate locally using
   `resolve_provider(PROVIDER_LOCAL)` heuristic scorer.
6. Persist evidence bundles via `evidence_artifacts` table.
7. Emit final `ExamRunState` with aggregate score.

## Outputs

- `ExamRunState` with `phase == "graded"` and `score`
- `tuple[EvidenceBundle, ...]` one per question
- Idempotent: same `(run_id, scenario_id)` returns the same result