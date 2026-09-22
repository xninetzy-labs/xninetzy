---
name: "argument-coherence"
description: "Detect logical flow problems (missing premise, non sequitur, topic break, circular reasoning, false dichotomy) in existing prose. Produces a finding list with locations and minimal-edit suggestions. Activates during editorial review."
metadata:
  intent_class: "EDITING"
  consumes: "evidence-synthesis, claim-lattice"
  produces: "coherence_findings"
  tier: "0"
---

# argument-coherence

## Purpose

Editor-pass skill. Surfaces logical flow defects in existing prose
without rewriting voice. Produces a finding list a human editor can
act on; does not return a polished redraft.

## Pattern catalog

Each pattern below maps to a finding record with location, pattern,
and suggested fix direction.

### PREMISE_MISSING

- Signal: claim asserted with no supporting premise in scope.
- Fix direction: insert a one-sentence premise; cite evidence-synthesis
  artifact if available.

### NON_SEQUITUR

- Signal: paragraph conclusion does not follow from its premises.
- Fix direction: either add a bridging inference or drop the
  unsupported conclusion.

### TOPIC_BREAK

- Signal: paragraph topic shifts without a transition sentence.
- Fix direction: insert a transition or split into a new section.

### CIRCULAR_REASONING

- Signal: conclusion appears verbatim or paraphrased as its own
  premise in the same paragraph or preceding paragraph.
- Fix direction: replace one end of the loop with an external premise.

### STRAWMAN

- Signal: refutes a position no source actually holds; the
  counter-position is weaker than the live debate.
- Fix direction: restate the position in its strongest form, then
  refute that.

### FALSE_DICHOTOMY

- Signal: "either X or Y" presented as exhaustive when a third
  option exists or when X and Y are not mutually exclusive.
- Fix direction: name the excluded middle or recast as a spectrum.

### LOADED_LANGUAGE

- Signal: emotionally charged framing that no cited datum supports.
- Fix direction: replace with neutral phrasing that matches the
  underlying data, or attach the missing evidence.

## Finding record

Each finding produces:

```yaml
location: "paragraph N" | "sentence N"
pattern: <pattern name>
fix_direction: <one-line instruction>
severity: high | medium | low
```

Severity is high when the defect blocks understanding, medium when
it weakens trust, low when it is a polish item.

## Workflow

1. Parse the prose into paragraphs (split on blank lines).
2. Extract the central claim of each paragraph as one sentence.
3. Classify inter-paragraph relationships: supports, refutes,
   neutral, unrelated.
4. Flag every pattern that fires; record location, pattern, fix.
5. Suggest minimum edits: insertion, deletion, or rewrite of one
   sentence, not full paragraphs.

## Worked micro-example

Input (three paragraphs):

```
P1: Remote work improved access to global talent pools.
P2: Office cultures therefore accelerate onboarding more than
    remote setups ever could.
P3: Hybrid arrangements remain the dominant policy in 2026.
```

Claims extracted:

- P1: remote work broadens talent access.
- P2: office culture accelerates onboarding more than remote.
- P3: hybrid is the dominant 2026 policy.

Relationship P1 -> P2: neutral (P1 about talent, P2 about
onboarding). NON_SEQUITUR fires. Fix direction: insert a
transition or drop P2's claim. P3 -> P1/P2: neutral,
INTRODUCES new topic without bridge; TOPIC_BREAK fires.

Output findings:

- P2: NON_SEQUITUR, severity high.
- P3: TOPIC_BREAK, severity medium.

## Failure modes

- OVER_EDIT: rewrites prose that was not broken. Hold edits to the
  minimum sentence required to clear the flag.
- LOCAL_OPTIMUM: clears every per-paragraph flag but loses the
  global arc. Re-read end-to-end before emitting findings.
- TONE_COLLAPSE: drifts into robotic phrasing. Never strip the
  author's voice; only redirect it around the defect.

## Routing hints

- Voice and cadence questions: defer to professional-editor.
- Citation integrity questions: defer to academic-editor.
- Anti-slop pass: run anti-slop after coherence fix, never before.

## Out of scope

- Spelling and grammar (handled by linters).
- Argument discovery (handled by evidence-synthesis).
- Source-grade audit (handled by source-selector).
