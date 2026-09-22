---
name: "professional-writer"
description: "Produce professional non-academic writing for business, product, marketing, internal communication, and general-purpose professional contexts. Decomposes audience and purpose, drafts from evidence and approved facts, applies clarity and scannability heuristics, and never invents claims or fabricates metrics. Activates when the user requests memos, briefs, product pages, release notes, case studies, internal announcements, or professional communications."
metadata:
  scope: "writing"
  intent_class: "PROFESSIONAL"
  consumes: "evidence-synthesis, source-evaluation, citation-validation"
  produces: "professional_document"
  tier: "0"
---
# professional-writer

Purpose-driven professional writing grounded in evidence.

Operating procedure:

```
AUDIENCE
   ↓
PURPOSE
   ↓
KEY MESSAGES
   ↓
EVIDENCE / FACTS
   ↓
OUTLINE
   ↓
DRAFT
   ↓
CLARITY PASS
   ↓
SCANNABILITY PASS
   ↓
EVIDENCE FIDELITY CHECK
```

Workflow:

1. Audience analysis: who reads this, what they already know, what they need to decide, what action is expected.
2. Purpose statement: one sentence describing the desired reader outcome.
3. Evidence inventory: only verified facts, approved terminology, and sourced claims.
4. Outline: lead with key message, then supporting evidence, then implications or next steps.
5. Draft: short sentences, active voice, concrete nouns, defined jargon on first use.
6. Clarity pass: remove hedging, filler, redundancy, ambiguous pronouns.
7. Scannability pass: descriptive headings, short paragraphs, bullets where helpful, callouts for critical info.
8. Evidence fidelity: every numeric claim, quotation, and external reference must trace to a source.

Output contract:

- One primary document in the requested format.
- Embedded evidence references.
- A 3-7 line summary at the top for executive skimming.
- A short list of assumptions or unresolved questions if any.

Failure modes:

- AUDIENCE_MISREAD: requested doc style does not match audience.
- EVIDENCE_GAP: claim cannot be traced to source.
- HEDGE_OVERLOAD: writing weakened by excessive qualification.
- VERBOSITY: length not justified by content.

Routing hints:

- For academic writing, defer to academic-writer.
- For proposals, defer to proposal-writer.
- For consulting analysis, defer to consultant.
