# Learning Companion

Xninetzy includes a learning companion subsystem that turns evidence-grounded teaching into a measurable practice: mastery, misconception detection, scaffolding fading, hint ladders, and independence tracking.

## Components

- `xninetzy/os/learning/pedagogy.py` — PedagogyEngine: hint ladder L0-L7, misconception detection, dependency detection, confidence calibration, scaffold fading, next action.
- `xninetzy/os/learning/mastery.py` — MasteryEngine: state classification (UNKNOWN -> INTRODUCED -> FRAGILE -> DEVELOPING -> FUNCTIONAL -> STRONG -> TRANSFERABLE), review scheduling, independence score.
- `xninetzy/schemas/learning_session.py` — `LearningSession`, `ConceptMastery`, `AttemptRecord`, `HintEvent`, `LearningError`, `Misconception`, `PedagogyPolicy`.
- `xninetzy/tools/ecosystem/learning_companion_tools.py` — 8 MCP tools.

## Hint ladder

```
0 no_hint
1 restate_task
2 point_to_concept
3 point_to_subproblem
4 strategic_hint
5 next_step
6 partial_solution
7 full_worked_solution
```

The PedagogyEngine escalates only when prior hint failed and the learner did not progress.

## Mastery dimensions

`understanding`, `retrieval`, `application`, `transfer`, `explanation`. Composite drives state classification.

## Independence metric

```
independent_solves + low_hint_attempts
———————————————————————————————————————
        2 * total_attempts
```

A high dependency risk (>0.5 full-solution reveals) triggers intervention.

## MCP usage

```python
learning_session_start(user_id, subject, topic, goal, mode="LEARN")
learning_attempt_submit(session_id, concept_id, task, user_answer, confidence_before, correct, independent, hint_level_used)
learning_hint(session_id, concept_id)
learning_misconception_check(session_id)
learning_calibration(session_id)
learning_independence(session_id)
learning_next_action(session_id)
```

## Modes

`LEARN`, `PRACTICE`, `QUIZ`, `EXAM`, `REVIEW`, `DEBUG`, `PROJECT`, `RESEARCH`, `TEACH_BACK`, `FLASHCARD`, `DRILL`, `REFLECTION`.
