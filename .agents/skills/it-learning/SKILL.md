---

...

...
name: "it-learning"
description: "Evidence-driven learning operating system for IT, software engineering, programming, backend, databases, cloud, DevOps, Docker, system design, cybersecurity, AI agents, RAG, data analytics, machine learning, and adjacent technical domains. Use for goal definition, prerequisite mapping, adaptive roadmaps, study sessions, active recall, deliberate practice, evidence collection, mastery assessment, progress reviews, and next-focus decisions."
metadata:
  scope: "general"
  owner: "xninetzy"
  language: "en"
  version: "2.0.0"
  lifecycle: "target -> diagnose -> map -> plan -> practice -> evidence -> assess -> review -> adapt"
...

# IT Learning OS

This skill is a reusable operating system for learning technical subjects. It should optimize for **demonstrable competence**, not time spent studying.

The core model is:

**Target → Current State → Prerequisites → Roadmap → Concept → Session/Task → Practice → Evidence → Mastery → Review → Next Focus**

The system should continuously answer:

* What am I trying to become capable of doing?
* What do I already know?
* What prerequisite is missing?
* What should I practice next?
* What evidence proves I can do it?
* What remains weak?

## Learning philosophy

* **Outcome before curriculum.** Start with the desired capability, not with a generic list of technologies. Prefer "Build and deploy a REST API with authentication, PostgreSQL, Docker, testing, and CI" over "Learn backend development."
* **Mastery is evidence-based.** Never infer mastery from time spent, tutorials completed, notes written, videos watched, or confidence alone. Mastery is supported by evidence: correct solutions, implementations, explanations, debugging, design, tests, data interpretation, project milestones, recall, and trade-off decisions.
* **Confidence and correctness are separate.** Track both. High confidence + incorrect is the most dangerous state.

## When to use

* planning a new learning goal in any IT or adjacent technical domain;
* building or refining a roadmap, sessions, recall cards, or evidence records;
* assessing mastery and adjusting the next focus;
* reviewing weekly progress.

## When NOT to use

* setting a vague life goal without a technical outcome — use `define-goal`;
* academic assignment workflow — use `hebat-academic` and `xninetzy-assignment-orchestrator`;
* deep research into unfamiliar topics — use `xninetzy-deep-research`.

## Core workflow

1. **Define the target.** Determine desired outcome, current skill level, deadline, available weekly time, preferred learning format, required artifact, constraints, and motivation or use case. Ask only when missing information would materially change the plan.
2. **Diagnose the current state.** Assess knowledge, application, production, and debugging. Use lightweight diagnostics before building a long roadmap: recall questions, small coding tasks, debugging tasks, concept explanations, architecture sketches, SQL query challenges, data interpretation tasks, or small implementation tasks.
3. **Map prerequisites.** Represent learning as dependencies rather than a flat topic list. Do not schedule a concept before its required prerequisites are sufficiently understood.
4. **Build the roadmap.** Each roadmap should contain measurable milestones. Every milestone should specify capability, concepts, prerequisite assumptions, practice task, expected artifact, success criterion, and review checkpoint. Avoid roadmaps that only contain topic names.
5. **Plan the next session.** Generate a bounded session from the current state rather than restarting the curriculum. Prioritize blocked prerequisites, weak concepts, overdue recall, failed or incomplete evidence, dependencies for upcoming milestones, and high-value practice opportunities.
6. **Practice actively.** Prefer `recall → attempt → feedback → correction → explanation → re-attempt` over `read → highlight → watch → read again`. Use passive material as support, not as the primary proof of learning.
7. **Collect evidence.** Record demonstration artifacts specific enough that another person could inspect them: code, SQL, notebook, API, Docker image, deployment, dashboard, model, agent workflow, debug result, design review, or recall result.
8. **Assess mastery.** Promote mastery only when multiple evidence points support the transition: recall + application + independent attempt + transfer/debugging.
9. **Review and adapt.** Inspect mastered concepts, weak concepts, failed recall, recurring errors, unfinished evidence, prerequisite blockers, motivation/energy constraints, and roadmap progress. Produce decisions: continue, reinforce, revisit prerequisite, change practice type, or advance.

## Evidence hierarchy

Evidence should be specific enough that another person could inspect it:

* **Conceptual** — explanation, diagram, comparison, worked example.
* **Practical** — code, SQL, notebook, API, Docker image, deployment, dashboard, model, agent workflow.
* **Performance** — problem-solving result, debugging result, test result, design review, timed recall.
* **Project** — milestone completion, repository state, architecture decision record, tests, demo.

## Mastery scale

Recommended qualitative scale:

```text
0 — Not exposed        — no meaningful understanding yet
1 — Familiar           — recognizes terminology and basic purpose
2 — Guided             — can perform with substantial guidance
3 — Functional         — can solve standard tasks independently
4 — Independent        — can solve unfamiliar problems and debug
5 — Transferable       — can apply in new contexts, explain trade-offs, teach
```

Do not treat the number as truth by itself. Mastery must be supported by evidence.

## Adaptive next focus

The next focus should satisfy:

```text
reachable
AND relevant
AND prerequisite-safe
AND evidence-informed
```

Prioritize concepts with high dependency value, weak mastery, repeated failure, upcoming project relevance, or overdue recall. Do not choose a concept that has an unmet prerequisite merely because it appears later in the roadmap.

## Time and energy

Study planning should account for available capacity. Separate **time available** from **cognitive energy**. A difficult debugging task may be appropriate for a high-energy session, while recall or review may be better when energy is low. Do not equate more study hours with more learning.

## Graded work boundary

Do not independently complete graded academic work when the learning context requires learner participation. Instead, support explanation, scaffolding, hints, examples, debugging, feedback, practice, and review. When an external assignment explicitly permits direct assistance, follow its requirements.

## Routing

* Personal goal framing → `define-goal`.
* Adaptive coaching and recall → `xninetzy-learning-coach`.
* Cross-domain learning state → `xninetzy-memory`.
* Research into unfamiliar topics → `xninetzy-deep-research`.
* Prerequisite and concept relationships → `graph-rag`.

## Reference map

* `references/targets-and-roadmap.md` — target definition, diagnostic evidence, prerequisite graphs, milestone structure, and adaptive planning.
* `references/sessions-and-practice.md` — session planning, active recall, practice design, project-based learning, evidence types, and misconception handling.
* `references/mastery-and-review.md` — mastery thresholds, feedback loops, spaced review, resource selection, external research, deadlines, and standard session record.

## Operating rules

The system must:

* move the learner toward independent capability;
* prefer measurable evidence over time spent;
* bound scope and produce one bounded next action at a time;
* check prerequisites before scheduling a concept;
* distinguish confidence from correctness;
* schedule spaced review from demonstrated performance;
* never mark mastery from passive exposure alone;
* preserve user changes in repositories and not silently expand scope.

The final decision is always:

**What is the smallest evidence-producing action that most effectively moves the learner toward the target?**