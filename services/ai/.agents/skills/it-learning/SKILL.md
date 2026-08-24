# IT Learning OS

```yaml
---
name: it-learning
description: General-purpose, evidence-driven learning operating system for IT, software engineering, programming, backend, databases, cloud, DevOps, Docker, system design, cybersecurity, AI agents, RAG, data analytics, machine learning, and adjacent technical domains. Supports goal definition, prerequisite mapping, adaptive roadmaps, study sessions, active recall, deliberate practice, project-based learning, evidence collection, mastery assessment, progress reviews, and next-focus decisions.
metadata:
  scope: general
  owner: xninetzy
  language: en
  version: "2.0.0"
  lifecycle: "target -> diagnose -> map -> plan -> practice -> evidence -> assess -> review -> adapt"
---
```

# IT Learning OS

This skill is a reusable operating system for learning technical subjects.

It should optimize for **demonstrable competence**, not time spent studying.

The core model is:

**Target → Current State → Prerequisites → Roadmap → Concept → Session/Task → Practice → Evidence → Mastery → Review → Next Focus**

The system should continuously answer:

**What am I trying to become capable of doing?**
**What do I already know?**
**What prerequisite is missing?**
**What should I practice next?**
**What evidence proves I can do it?**
**What remains weak?**

---

# 1. Learning Philosophy

## 1.1 Outcome before curriculum

Start with the desired capability, not with a generic list of technologies.

Prefer:

> "Build and deploy a REST API with authentication, PostgreSQL, Docker, testing, and CI."

over:

> "Learn backend development."

A target should describe an observable capability whenever possible.

---

## 1.2 Mastery is evidence-based

Never infer mastery from:

* time spent,
* number of tutorials completed,
* notes written,
* number of videos watched,
* confidence alone.

Mastery should be supported by evidence such as:

* correctly solving problems,
* implementing a feature,
* explaining a concept without notes,
* debugging an unfamiliar failure,
* designing an architecture,
* writing tests,
* interpreting data,
* completing a project milestone,
* passing a recall attempt,
* making correct trade-off decisions.

---

## 1.3 Confidence and correctness are separate

Track both:

**Confidence:** "I think I understand this."

**Performance:** "I demonstrated that I understand this."

A learner may be:

* high confidence + correct,
* high confidence + incorrect,
* low confidence + correct,
* low confidence + incorrect.

The second state is especially important because it can hide misconceptions.

---

# 2. Learning State Model

Represent each learning target using the following state:

```text
Target
  ↓
Current Level
  ↓
Prerequisites
  ↓
Roadmap
  ↓
Concept
  ↓
Study Session
  ↓
Practice / Artifact
  ↓
Evidence
  ↓
Mastery Assessment
  ↓
Review
  ↓
Next Focus
```

A concept should not become the next adaptive focus until its prerequisite state is checked.

---

# 3. Step 1: Define the Target

Before planning, determine:

* desired outcome,
* current skill level,
* deadline,
* available weekly time,
* preferred learning format,
* required output/artifact,
* constraints,
* motivation or use case, when relevant.

When enough information is already available, do not repeatedly ask for it.

When information is missing but not essential, make a clearly labeled assumption and proceed.

---

# 4. Step 2: Diagnose the Current State

Assess the learner across four dimensions:

### Knowledge

Can the learner explain the underlying concepts?

### Application

Can the learner use the concepts to solve a problem?

### Production

Can the learner build something independently?

### Debugging

Can the learner diagnose and recover from failure?

A learner is not considered proficient merely because they can reproduce a tutorial.

---

# 5. Diagnostic Evidence

Use lightweight diagnostics before building a long roadmap.

Possible methods:

* short recall questions,
* small coding task,
* debugging task,
* concept explanation,
* architecture sketch,
* SQL query challenge,
* data interpretation task,
* small implementation task.

Diagnostics should be **bounded** and should reveal prerequisite gaps.

---

# 6. Step 3: Build the Prerequisite Graph

Represent learning as dependencies rather than a flat topic list.

Example:

```text
Programming Fundamentals
        ↓
Data Structures
        ↓
HTTP + APIs
        ↓
Backend Framework
        ↓
Database Integration
        ↓
Authentication
        ↓
Testing
        ↓
Docker
        ↓
Deployment
```

For AI:

```text
Python
 ↓
Data Handling
 ↓
Linear Algebra Basics
 ↓
ML Fundamentals
 ↓
Embeddings
 ↓
Vector Search
 ↓
RAG
 ↓
Tool Use
 ↓
Agents
 ↓
Evaluation
```

Do not schedule a concept before its required prerequisites are sufficiently understood.

---

# 7. Step 4: Build the Roadmap

Each roadmap should contain measurable milestones.

Every milestone should specify:

* capability,
* concepts,
* prerequisite assumptions,
* practice task,
* expected artifact,
* success criterion,
* review checkpoint.

Avoid roadmaps that only contain topic names.

Bad:

```text
Week 1: Docker
Week 2: Kubernetes
Week 3: Cloud
```

Better:

```text
Milestone 1:
Containerize a backend service.

Evidence:
- working Dockerfile
- local container execution
- documented environment variables
- successful health check

Success:
Service runs reproducibly from a clean environment.
```

---

# 8. Adaptive Planning

When roadmap state exists, generate the next bounded plan from the current state rather than restarting the curriculum.

Prioritize:

1. blocked prerequisites,
2. weak concepts,
3. overdue recall,
4. failed or incomplete evidence,
5. dependencies for upcoming milestones,
6. high-value practice opportunities.

Do not automatically choose the hardest topic.

Choose the **highest-value reachable next step**.

---

# 9. Daily / Session Planning

Each study session should have:

### Objective

One clearly bounded capability.

### Context

Why the task matters in the roadmap.

### Work

Specific actions to perform.

### Evidence

What should exist at the end.

### Success criterion

What counts as "done correctly."

### Recall

What should be recalled after practice.

### Reflection

What remains uncertain.

Avoid sessions that contain too many unrelated objectives.

---

# 10. Study Session Lifecycle

Use:

```text
planned
  ↓
started
  ↓
active practice
  ↓
evidence produced
  ↓
completed
  ↓
mastery assessed
  ↓
review scheduled
```

A study session is incomplete when the learner only consumes material without producing evidence.

---

# 11. Active Learning Priority

Prefer this approximate order:

**Recall → Attempt → Feedback → Correction → Explanation → Re-attempt**

over:

**Read → Highlight → Watch → Read Again**

Use passive material as support, not as the primary proof of learning.

---

# 12. Active Recall

Use due recall before rereading whenever practical.

Recall should test:

* definitions,
* relationships,
* procedures,
* trade-offs,
* debugging logic,
* architecture decisions,
* examples,
* counterexamples.

Do not only ask:

> "What is X?"

Also ask:

> "When would you use X instead of Y?"

> "What breaks if this assumption is false?"

> "How would you debug this?"

> "What trade-off does this design introduce?"

---

# 13. Practice Design

Practice should progress from:

**guided → partial → independent → unfamiliar**

A learner should eventually encounter tasks where the solution is not directly demonstrated.

For programming, progressively move from:

```text
follow example
→ modify example
→ implement from specification
→ debug broken implementation
→ design solution independently
```

---

# 14. Project-Based Learning

Projects should be broken into incremental milestones.

For technical projects, inspect:

* architecture,
* modules,
* dependencies,
* data flow,
* APIs/interfaces,
* persistence,
* error handling,
* testing,
* deployment,
* observability,
* security where relevant.

Do not treat "build an app" as one task.

Use:

```text
Project
 ↓
Architecture
 ↓
Modules
 ↓
Milestones
 ↓
Implementation
 ↓
Tests
 ↓
Integration
 ↓
Deployment
 ↓
Evaluation
```

---

# 15. Evidence Types

Evidence may include:

### Conceptual evidence

* explanation,
* diagram,
* comparison,
* worked example.

### Practical evidence

* code,
* SQL,
* notebook,
* API,
* Docker image/configuration,
* deployment,
* dashboard,
* model,
* agent workflow.

### Performance evidence

* problem-solving result,
* debugging result,
* test result,
* design review,
* timed recall.

### Project evidence

* milestone completion,
* repository state,
* architecture decision record,
* tests,
* demo.

Evidence should be specific enough that another person could inspect it.

---

# 16. Mastery Model

Use a qualitative or numeric mastery scale, but never treat the number as truth by itself.

Recommended levels:

```text
0 — Not exposed
1 — Familiar
2 — Guided
3 — Functional
4 — Independent
5 — Transferable
```

### 0 — Not exposed

No meaningful understanding yet.

### 1 — Familiar

Recognizes terminology and basic purpose.

### 2 — Guided

Can perform tasks with substantial guidance.

### 3 — Functional

Can solve standard tasks independently.

### 4 — Independent

Can solve unfamiliar problems and debug common failures.

### 5 — Transferable

Can apply the concept in new contexts, explain trade-offs, teach it, and integrate it into larger systems.

---

# 17. Mastery Evidence Threshold

Do not upgrade mastery solely because the learner answers one question correctly.

Prefer multiple evidence points:

```text
Recall
+
Application
+
Independent attempt
+
Transfer/debugging
```

For important concepts, require evidence across at least two different modes.

Example:

**SQL joins**

Evidence:

1. explain INNER vs LEFT JOIN,
2. write correct queries,
3. debug a wrong join,
4. choose a join strategy for a real schema.

---

# 18. Misconception Handling

When an answer is wrong, distinguish:

* factual gap,
* conceptual misunderstanding,
* procedural error,
* syntax error,
* careless mistake,
* prerequisite gap,
* interpretation error.

Do not merely provide the correct answer.

The learner should understand **why the reasoning failed**.

When useful, create a targeted contrast:

```text
Incorrect mental model
        ↓
Why it fails
        ↓
Correct model
        ↓
Minimal example
        ↓
Re-attempt
```

---

# 19. External Research

When external research is required:

1. search current and authoritative sources,
2. identify the source type,
3. separate external findings from internal material,
4. prefer primary documentation and academic sources,
5. record the date/context when information can change.

Especially verify current information for:

* programming libraries,
* APIs,
* cloud services,
* frameworks,
* model capabilities,
* pricing,
* security practices,
* deployment platforms,
* software versions.

Do not present unstable technical information as timeless fact.

---

# 20. Resource Selection

Choose resources based on the learner's immediate bottleneck.

Possible resource types:

* official documentation,
* textbooks,
* academic papers,
* technical courses,
* tutorials,
* reference implementations,
* datasets,
* coding environments,
* documentation examples.

Avoid assigning many resources simultaneously.

A strong resource should answer:

**Why this resource now?**

---

# 21. Feedback Loop

After every meaningful practice cycle:

```text
Attempt
→ Evaluate
→ Identify error
→ Correct
→ Re-attempt
```

Do not move forward simply because the learner finished the assigned material.

---

# 22. Review System

Review should inspect:

* mastered concepts,
* weak concepts,
* failed recall,
* recurring errors,
* unfinished evidence,
* prerequisite blockers,
* motivation/energy constraints,
* roadmap progress.

The review should produce a decision:

**continue / reinforce / revisit prerequisite / change practice type / advance**

---

# 23. Adaptive Next Focus

The next focus should satisfy:

```text
reachable
AND relevant
AND prerequisite-safe
AND evidence-informed
```

Prioritize concepts with:

* high dependency value,
* weak mastery,
* repeated failure,
* upcoming project relevance,
* overdue recall.

Do not choose a concept that has an unmet prerequisite merely because it appears later in the roadmap.

---

# 24. Time and Energy

Study planning should account for available capacity.

Separate:

**time available**

from:

**cognitive energy**

A difficult debugging task may be appropriate for a high-energy session, while recall or review may be better when energy is low.

Do not equate more study hours with more learning.

---

# 25. Handling Deadlines

When a deadline exists:

1. identify the required deliverable,
2. identify minimum viable competence,
3. identify critical prerequisites,
4. prioritize evidence-producing tasks,
5. defer lower-value enrichment.

The roadmap may be compressed, but prerequisite relationships should not be ignored.

---

# 26. Graded Work Boundary

Do not independently complete graded academic work when the learning context requires learner participation.

Instead, support:

* explanation,
* scaffolding,
* hints,
* examples,
* debugging,
* feedback,
* practice,
* review.

When an external assignment explicitly permits direct assistance, follow its requirements.

---

# 27. Do Not Overbuild the Learning System

Avoid creating:

* huge task lists,
* unnecessary databases,
* excessive tracking fields,
* broad roadmaps with no immediate action,
* dozens of resources,
* complex milestone structures without evidence.

The system should remain operational.

Prefer:

**one clear next action + one success criterion + one evidence artifact.**

---

# 28. Standard Session Record

Each completed session should contain:

```text
Target:
Roadmap:
Concept:
Objective:
Duration:
Energy:
Task:
Evidence:
Result:
Confidence:
Mastery:
Errors:
Reflection:
Next Action:
Review Date:
Recall Due:
```

Do not fabricate fields that were not actually observed.

---

# 29. Progress Review Format

A review should answer:

### What improved?

Specific demonstrated capabilities.

### What remains weak?

Concepts with weak evidence.

### What was blocked?

Prerequisites, environment, time, or understanding.

### What should change?

Practice type, resource, scope, or sequence.

### What comes next?

One bounded next action.

---

# 30. Completion Contract

Every learning interaction that advances the learning state should end with:

**Target and stage**
What the learner is currently trying to achieve.

**Evidence/source status**
What evidence exists and which sources support the plan.

**One bounded next action**
The smallest meaningful next step.

**Success criterion**
What observable result counts as completion.

**Next review or recall checkpoint**
When or under what condition the learner should revisit the concept.

If evidence is missing, state explicitly:

> **Evidence status: insufficient**

Never imply mastery without supporting evidence.

---

# 31. Default Output Structure

For a planning request:

```text
Target
Current State
Prerequisites
Roadmap
Next Session
Evidence Required
Success Criterion
Review Checkpoint
```

For a study session:

```text
Objective
Brief Context
Practice Task
Evidence to Produce
Success Criterion
Recall
Reflection
Next Focus
```

For a progress review:

```text
Demonstrated Progress
Weak Concepts
Evidence Gaps
Prerequisite Issues
Mastery Assessment
Adaptation
Next Action
Review / Recall
```

---

# 32. Operating Rule

The system should always move the learner toward **independent capability**.

The goal is not:

> "I have studied this."

The goal is:

> "I can use this correctly, explain it, debug it, and apply it in a new situation."

The canonical lifecycle is:

**Target → Diagnose → Map → Plan → Practice → Evidence → Assess → Review → Adapt**

And the final decision is always:

**What is the smallest evidence-producing action that most effectively moves the learner toward the target?**
