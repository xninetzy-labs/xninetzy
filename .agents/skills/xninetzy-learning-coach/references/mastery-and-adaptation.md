# Xninetzy Learning Coach — Mastery and Adaptation

This reference expands mastery evidence, mastery scale and thresholds, confidence tracking, spaced review, forgetting/relearning, error memory, energy-aware adaptation, stop/escalation, coach decision function, session plan template, and completion contract. Read it when assessing mastery or scheduling the next intervention.

## Mastery evidence

Use multiple forms of evidence:

```text
Recall
+
Application
+
Independent Practice
+
Transfer / Debugging
```

For important concepts, avoid declaring mastery from only one successful recall response.

## Mastery scale

Recommended scale:

```text
0 — Unfamiliar
1 — Familiar
2 — Guided
3 — Functional
4 — Independent
5 — Transferable
```

### 0 — Unfamiliar

Cannot yet recognize or explain the core concept.

### 1 — Familiar

Recognizes terminology and broad purpose.

### 2 — Guided

Can perform with significant scaffolding.

### 3 — Functional

Can perform standard tasks independently.

### 4 — Independent

Can solve unfamiliar variations and debug common failures.

### 5 — Transferable

Can apply the concept to new domains, explain trade-offs, and integrate it with surrounding concepts.

## Mastery thresholds

A concept should advance only when evidence supports the transition.

Example progressions:

```text
2 → 3: successful guided task + successful independent standard task
3 → 4: independent standard task + unfamiliar/debugging task
4 → 5: transfer task + clear explanation of trade-offs
```

Adapt thresholds to the domain rather than treating them as universal scoring rules.

## Learning evidence object

A useful evidence record contains:

```text
concept
task
attempt
result
error_type
feedback
re_attempt
confidence
mastery_estimate
evidence_artifact
date
```

Only record facts actually observed.

## Confidence tracking

Track:

```text
confidence
+
correctness
```

Example:

```text
high confidence + incorrect   → probable misconception
low confidence + correct     → strengthen retrieval confidence
high confidence + correct    → candidate for transfer practice
```

This helps detect the dangerous state of **confident misunderstanding**.

## Spaced review

Schedule review based on demonstrated performance. A concept that is weak, recently corrected, or repeatedly forgotten should return sooner. A concept that is independently solved, successfully recalled later, or transferable can be reviewed less frequently. Do not use an arbitrary fixed interval for every concept.

## Review modes

Review may use:

* free recall,
* flash-style questions,
* explain-from-memory,
* code reconstruction,
* debugging,
* comparison,
* mini-project,
* retrieval from a concept graph.

Rotate formats where useful to test robust knowledge.

## Forgetting and relearning

A previously mastered concept may become rusty. Do not automatically reset mastery to zero. Distinguish:

```text
mastered but rusty
```

from:

```text
never mastered
```

Use the shortest review intervention capable of restoring performance.

## Error memory

Previous errors should influence future teaching.

Example:

```text
Previous error:
Confused authorization with authentication

Future intervention:
Contrast both concepts before introducing OAuth roles
```

Do not repeatedly teach the entire topic if the actual weakness is narrow.

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

## Stop / escalation conditions

Stop teaching the current concept and reassess when:

* a prerequisite gap is discovered,
* repeated attempts fail for the same conceptual reason,
* instructions are ambiguous,
* the learner's target changed,
* the task requires information unavailable in the session,
* the learner has already demonstrated mastery.

Do not grind through increasingly complex explanations when the missing prerequisite is obvious.

## Adaptive decision rules

After every meaningful attempt:

* **Correct and easy** — increase difficulty or introduce transfer.
* **Correct with heavy guidance** — reduce scaffolding and repeat independently.
* **Incorrect with correct concept** — target the procedural mistake.
* **Incorrect due to misconception** — repair the mental model.
* **Incorrect due to prerequisite gap** — switch to the prerequisite.
* **Correct but uncertain** — use another recall or application task.

## Coach decision function

Conceptually:

```text
next_focus =
  highest_value(
    prerequisite_safe,
    target_relevant,
    evidence_weak,
    practice_ready,
    review_due
  )
```

Do not select a next concept solely because it is the next item in a curriculum.

## Relationship to Learning OS

The Learning Coach handles **how to teach and adapt.** The Learning OS handles **how to manage the roadmap, sessions, evidence, mastery state, and progress.**

Recommended flow:

```text
Learning OS
 ↓
Current target
 ↓
Learning Coach
 ↓
Diagnosis / teaching / practice
 ↓
Evidence
 ↓
Learning OS
 ↓
Mastery update / review scheduling
```

## Relationship to Graph RAG

When prerequisite or concept relationships materially improve learning:

```text
Target Concept
 ↓
Prerequisite Graph
 ↓
Known Concepts
 ↓
Missing Concept
 ↓
Teaching Sequence
```

Use graph relationships as structured reasoning, not as unquestioned truth.

## Relationship to Deep Research

Use deep research when the learner needs evidence beyond stable conceptual knowledge: current framework behavior, disputed technical practice, academic literature, current standards, or emerging methods. Research supports learning; it does not replace active practice.

## Relationship to Academic Systems

Academic portals can provide upcoming assignments, courses, deadlines, and required material. They should inform learning priorities but should not automatically redefine mastery.

## Completion contract

Every meaningful coaching cycle should return the relevant subset of:

**Learning outcome** — what capability was targeted.

**Current state** — what the learner demonstrated.

**Evidence** — what was actually observed.

**Feedback** — the most important correction or reinforcement.

**Mastery state** — current evidence-based estimate.

**Next focus** — one bounded learning action.

**Review checkpoint** — when or under what condition the learner should retrieve the concept again.

If evidence is insufficient: **Mastery status: insufficient evidence.** Never infer mastery from passive exposure alone.

## Standard coaching output

```text
Target
Current Knowledge
Prerequisite Check
Diagnostic
Teaching
Practice
Feedback
Evidence
Mastery
Next Focus
Recall / Review
```

For a short interaction, compress the structure rather than omitting the evidence logic.

## Operating rules

The system must:

* retrieve relevant prior knowledge,
* check prerequisites before advancing,
* diagnose before over-teaching,
* teach from first principles when needed,
* connect new ideas to known concepts,
* use worked examples strategically,
* move quickly into retrieval and practice,
* provide targeted feedback,
* adapt difficulty based on evidence,
* separate confidence from correctness,
* record demonstrated evidence,
* schedule spaced review,
* repair misconceptions explicitly,
* use projects as real-world practice when appropriate,
* never mark mastery from passive reading or viewing alone.

The canonical teaching loop is:

**Diagnose → Explain → Connect → Demonstrate → Retrieve → Practice → Evaluate → Feedback → Adapt → Evidence → Review**