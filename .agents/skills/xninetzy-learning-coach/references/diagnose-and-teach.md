# Xninetzy Learning Coach — Diagnose, Teach, and Connect

This reference expands learning outcome, prerequisite model, prior knowledge retrieval, diagnostic gate, first-principles teaching, knowledge connections, worked examples, guided practice, retrieval prompts, question difficulty, and Socratic mode. Read it when preparing a teaching session.

## Learning outcome

Every teaching cycle should begin with a concrete outcome.

Weak: `Understand databases.`

Better: `Explain normalization up to 3NF, identify common schema anomalies, and normalize a previously unseen relational schema without step-by-step guidance.`

For technical learning:

> Implement and debug a REST endpoint with validation, persistence, and tests.

For academic learning:

> Explain the assigned concept and independently solve representative problems using the required method.

## Prerequisite model

Before teaching the target, inspect its prerequisite chain. Example:

```text
Variables
  ↓
Functions
  ↓
Data Structures
  ↓
Algorithms
```

or:

```text
HTTP
  ↓
REST
  ↓
Authentication
  ↓
Authorization
  ↓
Secure API Design
```

A concept with an unresolved prerequisite should trigger one of:

* prerequisite repair,
* diagnostic,
* scaffolded explanation,
* safe progression with explicit caveat.

Do not blindly teach an advanced topic while foundational gaps remain.

## Prior knowledge retrieval

Retrieve relevant knowledge rather than dumping the learner's entire history into the session.

Useful prior state:

* already mastered concepts,
* familiar terminology,
* previous examples,
* known misconceptions,
* recent project experience,
* prior failed recall,
* previous feedback.

Avoid repeating explanations that strong evidence shows are already mastered.

## Diagnostic gate

Before a major lesson, use a lightweight diagnostic.

Possible diagnostics:

* recall questions,
* "explain in your own words,"
* predict the output,
* identify the bug,
* solve one representative problem,
* draw a concept map,
* choose between alternatives and justify the choice.

The diagnostic should be small enough to be practical but strong enough to expose the main misconception or prerequisite gap.

## Diagnostic interpretation

Classify the learner's state:

```text
unfamiliar
familiar
partial
functional
independent
transferable
```

When useful, distinguish the reason for failure:

```text
knowledge_gap
prerequisite_gap
conceptual_misconception
procedural_error
syntax_error
careless_error
interpretation_error
transfer_failure
```

This determines the next teaching move.

## Teaching from first principles

When a concept is weak:

1. define the core idea,
2. explain why it exists,
3. identify its mechanism,
4. connect it to something known,
5. use a minimal example,
6. expose the important edge case,
7. ask the learner to reconstruct the idea.

Avoid beginning with jargon-heavy definitions when a simpler mental model is possible.

## Knowledge connections

Connect new ideas to established concepts.

Example:

```text
SQL JOIN
  ↓
Relational Sets
  ↓
Matching Rows
  ↓
INNER / LEFT / RIGHT Semantics
```

or:

```text
Docker Container
  ↓
Process Isolation
  ↓
Filesystem / Network Namespace
  ↓
Reproducible Runtime Environment
```

Connections help the learner organize knowledge rather than memorize isolated facts.

## Worked examples

Use worked examples when the learner needs to see the reasoning process. A good worked example should expose:

* input,
* reasoning,
* decision points,
* intermediate state,
* final result,
* common mistake.

Do not hide the reasoning behind `The answer is X.`

## Guided practice

After explanation, provide a partially scaffolded task.

Example:

```text
Step 1: identify the relevant concept
Step 2: choose the operation
Step 3: complete the implementation
Step 4: verify the result
```

Gradually remove scaffolding.

## Retrieval prompts

* **Recall** — `What is the purpose of a database index?`
* **Compare** — `When would you choose a B-tree index instead of a hash index?`
* **Explain** — `Explain transaction isolation without using the words "ACID" or "database."`
* **Predict** — `What will this query return?`
* **Debug** — `Why does this endpoint return a race condition?`
* **Design** — `How would you structure this system if latency became the primary constraint?`

## Question difficulty

Adaptive difficulty should evolve approximately as:

```text
recognition
→ recall
→ application
→ debugging
→ comparison
→ design
→ transfer
```

Do not increase difficulty solely because the learner answered one easy question correctly.

## Socratic mode

When appropriate, ask questions that lead the learner toward the answer. Use guided questioning to strengthen reasoning rather than withholding help artificially. Examples:

> What invariant should remain true after each iteration?

> Which part of the data structure changes when this operation runs?

> What assumption does this solution rely on?

## Preferred learning style

Treat stated learning preferences as **format preferences**, not fixed cognitive types. Examples:

* visual explanations,
* code-first examples,
* analogies,
* step-by-step walkthroughs,
* exercises first.

Do not assume a learner can only learn through one modality. Adapt format while maintaining active practice and evidence.