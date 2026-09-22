---
name: "research-paper-writer"
description: "Draft a research paper following IMRaD or discipline-equivalent structure: abstract, introduction, methods, results, discussion, conclusion. Requires a populated ResearchPacket or equivalent. Activates when user supplies data, findings, or research packet."
metadata:
  scope: "writing"
  intent_class: "ACADEMIC"
  consumes: "evidence-synthesis, citation-validation, academic-writer"
  produces: "research_paper"
  tier: "0"
---
# research-paper-writer

Draft a research paper following IMRaD or discipline-equivalent structure: abstract, introduction, methods, results, discussion, conclusion. Requires a populated ResearchPacket or equivalent. Activate.

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
