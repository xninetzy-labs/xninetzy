---
name: it-learning
description: Build and run evidence-backed IT learning plans for programming, backend, databases, Docker, system design, AI agents, RAG, data analytics, and machine learning. Use for roadmaps, prerequisite concepts, study sessions, active recall, practice projects, mastery evidence, progress reviews, and adaptive next-focus decisions.
metadata:
  triggers: "learning roadmap concept prerequisite study session practice project mastery recall machine learning data analytics"
  lifecycle: "target-practice-evidence-mastery-adapt"
  version: "1.1"
---

# IT Learning OS

Model progress as `roadmap -> concept -> session/task -> evidence -> mastery -> next focus`. Do not infer mastery from time spent or a confident answer.

## Workflow

1. Clarify target outcome, current level, deadline, available time, and preferred artifact.
2. Search internal material before calling a plan source-backed; label external research separately.
3. Read or create a roadmap with measurable milestones, bounded tasks, resources, and review checkpoints.
4. Inspect prerequisites and concept state before selecting the next focus.
5. Prefer `learning_generate_today_plan` when roadmap state exists.
6. Start real work with `learning_start_study_session` and connect it to the roadmap.
7. Produce a small artifact, test, explanation, or recall attempt as evidence.
8. Complete with duration, energy, mastery estimate, reflection, and evidence using `learning_complete_study_session`.
9. Use due recall before rereading; keep confidence separate from correctness.
10. Review weak concepts, failed recall, and obstacles before adapting the plan.

Connect projects to architecture, modules, data flow, tests, and incremental milestones. A concept with unmet prerequisites must not become the adaptive next focus. Do not create a large task set, activate a broad roadmap, or complete graded work without the required approval.

## Completion contract

Return target and stage, evidence/source status, one bounded next action, success criterion, and the next review or recall checkpoint. If evidence is missing, say so explicitly.
