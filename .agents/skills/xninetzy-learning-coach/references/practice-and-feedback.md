# Xninetzy Learning Coach — Practice and Feedback

This reference expands the practice ladder, transfer practice, retrieval practice, feedback loop, feedback granularity, hint ladder, misconception repair, and project-based learning. Read it when designing practice rounds or responding to learner attempts.

## Independent practice

The learner should eventually solve a task without the demonstration directly in view. Prefer tasks that require:

* retrieval,
* application,
* decision-making,
* debugging,
* explanation.

Independent practice is a stronger mastery signal than successful imitation.

## Transfer practice

Once standard practice becomes reliable, introduce variation. Examples:

* new dataset,
* different API,
* unfamiliar bug,
* changed constraints,
* alternative architecture,
* different problem formulation.

Transfer is evidence that knowledge is organized deeply enough to generalize.

## Retrieval practice

Ask the learner to recall before rereading whenever practical. Possible prompts:

* **Recall** — definition, purpose, scope.
* **Compare** — when would you choose X instead of Y?
* **Explain** — explain without using the key jargon.
* **Predict** — what will this return or do?
* **Debug** — why does this fail?
* **Design** — how would you restructure under a different constraint?

Do not only ask `What is X?` Also ask:

* When would you use X instead of Y?
* What breaks if this assumption is false?
* How would you debug this?
* What trade-off does this design introduce?

## Feedback loop

After each meaningful attempt:

```text
Attempt
  ↓
Evaluate
  ↓
Identify exact issue
  ↓
Explain correction
  ↓
Re-attempt
```

Feedback should identify:

* what was correct,
* what failed,
* why,
* what to change,
* what to try next.

Avoid generic praise such as `Good job!` when precise feedback is more useful.

## Feedback granularity

Match feedback to the error.

* **Syntax error** — point to the syntax issue.
* **Conceptual error** — correct the mental model.
* **Procedural error** — fix the sequence of operations.
* **Strategy error** — explain why the chosen approach is inefficient or inappropriate.
* **Transfer error** — connect the familiar principle to the unfamiliar context.

Do not give a long theoretical explanation for a simple typo.

## Hint ladder

For difficult problems, use progressively stronger hints:

```text
Hint 1: Recall the relevant concept.
Hint 2: Identify the key constraint.
Hint 3: Consider this intermediate state.
Hint 4: Use this strategy.
Hint 5: Show a worked solution.
```

Do not immediately reveal the complete solution when productive struggle remains useful.

## Misconception repair

Use:

```text
Existing mental model
        ↓
Counterexample
        ↓
Why the model fails
        ↓
Correct model
        ↓
New example
        ↓
Re-attempt
```

This is preferable to simply saying `That's wrong.`

## Learning through projects

When the learner is building something:

```text
Project Need
 ↓
Relevant Concept
 ↓
Minimal Explanation
 ↓
Immediate Implementation
 ↓
Test
 ↓
Debug
 ↓
Reflect
```

Project work should become learning evidence when it actually demonstrates understanding.

## Project evidence

Strong evidence includes:

* implemented feature,
* passing test,
* debugged defect,
* architecture explanation,
* documented trade-off,
* reproducible command,
* working prototype,
* successful deployment.

Do not treat a copied tutorial implementation as strong evidence of independent mastery.

## Academic integration

When learning is driven by an academic requirement:

```text
Assignment Requirement
 ↓
Required Competence
 ↓
Prerequisites
 ↓
Diagnostic
 ↓
Learning Session
 ↓
Evidence
 ↓
Assignment Output
```

The assignment artifact and learning mastery should remain separate states.

## Time-aware lesson design

Respect available time.

### Very short session

Use: recall + one focused explanation + one task.

### Normal session

Use: diagnostic + teaching + guided practice + independent practice + recall.

### Extended session

Use: diagnostic + teaching + multiple practice rounds + transfer task + review.

Do not create a one-hour curriculum when only ten minutes are available.

## Energy-aware adaptation

When energy is low: prefer recall, review, debugging a familiar pattern, summarization from memory.

When energy is high: prefer unfamiliar problems, architecture design, difficult debugging, transfer tasks, project implementation.

Use available learner state when it is explicitly known.

## Session plan

A standard session may contain:

```yaml
learning_outcome:
prerequisites:
diagnostic:
explanation:
worked_example:
guided_practice:
independent_practice:
recall_questions:
success_criteria:
evidence:
review_date:
```

Add only the components that are useful for the current session.

## Success criteria

A lesson is successful when the learner can demonstrate the target capability. Examples:

* Correctly solve 4 out of 5 representative problems without hints.
* Implement the feature independently and pass the target test suite.
* Explain the concept and distinguish it from the two most common confusions.
* Debug two unfamiliar examples without being shown the solution.

Avoid `Watched the lesson.` or `Read the chapter.` Those are activities, not learning outcomes.