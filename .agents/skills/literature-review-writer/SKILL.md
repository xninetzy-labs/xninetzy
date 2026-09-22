---
name: "literature-review-writer"
description: "Synthesize a literature review from a set of sources or a ResearchPacket. Structures by theme, method, chronology, or debate. Surfaces contradictions and gaps explicitly. Activates when sources, papers, or a research packet are provided."
metadata:
  scope: "writing"
  intent_class: "ACADEMIC"
  consumes: "source-evaluation, evidence-synthesis, citation-validation"
  produces: "literature_review"
  tier: "0"
---
# literature-review-writer

Synthesize a literature review from a set of sources or a ResearchPacket. Structures by theme, method, chronology, or debate. Surfaces contradictions and gaps explicitly. Activates when sources, paper.

Operating procedure:

```
INPUT
   ↓
EVIDENCE / FACTS
   ↓
STRUCTURE
   ↓
DRAFT
   ↓
VALIDATION PASS
   ↓
FINAL
```

Workflow:

1. Confirm intent, audience, and target artifact.
2. Inventory evidence, facts, and constraints.
3. Choose structure aligned to intent class.
4. Draft with evidence-grounded claims only.
5. Run validation passes: evidence-claim alignment, citation integrity, anti-slop, intent-class consistency.
6. Surface unresolved questions and assumptions explicitly.

Output contract:

- One primary artifact in the requested format.
- Embedded evidence references where claims appear.
- A short assumption / unresolved list if any.
- A validation summary noting the passes executed.

Failure modes:

- EVIDENCE_GAP: claim cannot be traced to source.
- INTENT_DRIFT: artifact drifted from original request class.
- VOICE_MISMATCH: register or tone inconsistent with audience.
- STRUCTURE_MISMATCH: sectioning inappropriate for artifact class.

Routing hints:

- For deeper evidence work, defer to evidence-synthesis.
- For review of existing draft, defer to professional-editor or academic-editor.
- For final-pass cleanup, defer to anti-slop and submission-readiness.
