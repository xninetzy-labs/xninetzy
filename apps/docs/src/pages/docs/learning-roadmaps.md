---
layout: ../../layouts/DocsLayout.astro
title: Adaptive learning roadmaps
description: Level-aware 7-, 14-, and 30-day plans connected to validated knowledge sources.
section: Integrations
---

The roadmap planner does not force every request into a 14-day template.
Duration, learner level, and available evidence select different strategies.

| Duration | Phases | Strategy |
|---|---:|---|
| ≤ 7 days | 4 | sprint |
| 8–14 days | 5 | balanced |
| > 14 days | 6 | deep practice |

Every phase has a day range, focus, and outcome. The plan covers every day from
the first through the final day. An `advanced` level begins with a prerequisite
and foundation audit instead of repeating beginner material.

## Source-aware planning

`learning_create_roadmap` accepts optional `source_ids`. Without explicit
IDs, the system searches relevant internal knowledge sources. References are
bounded, deduplicated, persisted in roadmap metadata, and represented as
`learning_resources` with internal URIs:

```text
xninetzy://knowledge/source/<id>
```

When internal evidence is unavailable, the draft says that sources still need
to be found and validated. General model knowledge is never presented as vault
evidence.

## Activation and progress

A roadmap draft requires approval. After activation, the first-day item becomes
a shared task. Completing that task from WhatsApp or MCP updates the learning
task, roadmap progress, milestone state, and roadmap state through an idempotent
reducer.

## Study sessions

An active roadmap can have one owner session in progress at a time. A session
stores focus, planned and actual duration, energy before and after, mastery from
`0` to `1`, reflection, and evidence references. An `idempotency_key`
prevents WhatsApp or MCP retries from opening duplicate sessions.

| Tool | Purpose |
|---|---|
| `learning_start_study_session` | Start or resume the active session |
| `learning_complete_study_session` | Persist results and close idempotently |
| `learning_list_study_sessions` | List session history |
| `learning_get_study_progress` | Summarize tasks, sessions, minutes, and mastery |
| `learning_generate_today_plan` | Build today's adaptive focus |
| `learning_define_concept` | Add a concept and prerequisite, milestone, or task links |
| `learning_record_concept_evidence` | Record idempotent evidence and update mastery |
| `learning_get_concept_map` | Inspect concepts and roadmap readiness |

Completion writes progress and `learning_session_completed` in the same SQLite
transaction. A retry does not duplicate progress or events.

## Concept graph and evidence

Each roadmap milestone becomes a typed concept. Ordered concepts are connected
as prerequisites, and first-day tasks are linked to their relevant concepts.
Existing roadmaps are backfilled idempotently during startup migration.

```text
roadmap
  → milestone
  → concept
       → prerequisite concept
       → learning task
       → study session
       → evidence
       → mastery 0..1
```

Evidence has an idempotency key and payload hash. Retrying the same payload does
not update mastery twice; reusing a key for different data is rejected. The
first evidence establishes baseline mastery. Later evidence uses
`40% previous mastery + 60% new score`. A score of at least 80% is
`mastered`; a prerequisite is ready at 70%.

Completing a linked study session creates concept evidence in the same
transaction. The concept graph then guides today's plan, weekly review,
attention queue, and Personal Context toward the next weak concept.

WhatsApp can inspect the map with:

```text
/concepts <roadmap-id>
```

Evidence references are local records, not automatic factual citations.
Knowledge claims still require `knowledge_answer` and citation validation.

## Active recall and spaced repetition

A recall card belongs to one concept and stores a question, expected answer,
explicit keywords, and optional source references. Due questions can be read
without exposing the expected answer:

```text
/recall
/recall <roadmap-id>
```

Submit an answer with confidence from 1 to 5:

```text
/recall answer <card-id> <confidence> <answer>
```

Grading is deterministic keyword coverage. The expected answer appears only
after the attempt is saved. Confidence is a metacognitive signal and never
inflates correctness.

Bounded SM-2 scheduling applies these rules:

- quality below `3` records a lapse, resets repetition, and schedules one day later;
- the first successful review is scheduled after one day;
- the second successful review is scheduled after six days;
- later reviews use the previous interval and an ease factor no lower than `1.3`.

The attempt, schedule update, concept evidence, mastery, and completion event are
one transaction. A retry with the same day and payload cannot duplicate the
attempt.

Due recall enters the adaptive plan before a new session, receives special
attention-queue priority, appears in Personal Context, and is summarized in the
weekly review. An active study session remains first so the system does not
abandon in-progress state.

| Tool | Purpose |
|---|---|
| `learning_create_recall_card` | Create an immutable card for one concept |
| `learning_due_recall` | List due questions |
| `learning_submit_recall_answer` | Grade, update evidence and mastery, and schedule atomically |

## Adaptive daily plan

The plan mode follows current state:

- `start`: no session exists; begin with the smallest pending task;
- `resume`: a session is still active;
- `reinforce`: latest mastery is below 60%;
- `practice`: mastery is 60–79%;
- `advance`: mastery is at least 80%.

When a concept graph exists, the planner selects only concepts whose
prerequisites meet readiness. Recent energy adjusts the timebox to 15, 25, or
35 minutes. The same adaptive focus enters internal LangGraph Personal Context,
so WhatsApp and MCP clients read one learning state.

Example:

```text
Start a study session for the Graph RAG roadmap.
Complete the session with mastery 0.7 and link my notes as evidence.
Show today's adaptive learning plan.
```
