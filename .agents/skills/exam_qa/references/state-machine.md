# Exam QA State Machine

Canonical phase transitions for `ExamRunState`:

```
planned -> ready -> running -> (paused <-> running)
                       |            |
                       v            v
                  submitted -> graded
                       |
                       v
                   failed -> ready (retry)
```

Any source phase may transition to `cancelled`. The terminal phases are
`graded` and `cancelled` — once entered, no further transitions are
accepted.

## Authorization Gate

For `scenario.kind == "exam"`, the row in `exam_authorization` must
include a non-null `approval_id`. Without approval, the run stays in
`PHASE_FAILED` with note `"missing_authorization"`.

## Evidence Discipline

Every graded question writes a row to `evidence_artifacts` keyed by
`(run_id, question_id)`. Re-runs are idempotent on this key.