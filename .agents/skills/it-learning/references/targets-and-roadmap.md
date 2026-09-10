# IT Learning — Targets, Diagnostics, and Roadmaps

This reference expands target definition, current-state diagnostics, prerequisite graphs, roadmap construction, and adaptive planning. Read it when scoping a new learning goal or refining an existing roadmap.

## Target definition

Before planning, determine:

* desired outcome,
* current skill level,
* deadline,
* available weekly time,
* preferred learning format,
* required output/artifact,
* constraints,
* motivation or use case when relevant.

When enough information is already available, do not repeatedly ask for it. When information is missing but not essential, make a clearly labeled assumption and proceed.

## Current-state diagnosis

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

## Diagnostic evidence

Use lightweight diagnostics before building a long roadmap:

* short recall questions,
* small coding task,
* debugging task,
* concept explanation,
* architecture sketch,
* SQL query challenge,
* data interpretation task,
* small implementation task.

Diagnostics should be bounded and should reveal prerequisite gaps.

## Prerequisite graph

Represent learning as dependencies rather than a flat topic list.

For backend:

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

## Roadmap construction

Each roadmap should contain measurable milestones. Every milestone should specify:

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

## Adaptive planning

When roadmap state exists, generate the next bounded plan from the current state rather than restarting the curriculum. Prioritize:

1. blocked prerequisites,
2. weak concepts,
3. overdue recall,
4. failed or incomplete evidence,
5. dependencies for upcoming milestones,
6. high-value practice opportunities.

Do not automatically choose the hardest topic. Choose the **highest-value reachable next step**.

## Resource selection

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

Avoid assigning many resources simultaneously. A strong resource should answer: **Why this resource now?**

## External research

When external research is required:

1. search current and authoritative sources,
2. identify the source type,
3. separate external findings from internal material,
4. prefer primary documentation and academic sources,
5. record the date/context when information can change.

Especially verify current information for programming libraries, APIs, cloud services, frameworks, model capabilities, pricing, security practices, deployment platforms, and software versions. Do not present unstable technical information as timeless fact.

## Deadline handling

When a deadline exists:

1. identify the required deliverable,
2. identify minimum viable competence,
3. identify critical prerequisites,
4. prioritize evidence-producing tasks,
5. defer lower-value enrichment.

The roadmap may be compressed, but prerequisite relationships should not be ignored.

## Avoid overbuilding

Avoid creating:

* huge task lists,
* unnecessary databases,
* excessive tracking fields,
* broad roadmaps with no immediate action,
* dozens of resources,
* complex milestone structures without evidence.

Prefer **one clear next action + one success criterion + one evidence artifact.**