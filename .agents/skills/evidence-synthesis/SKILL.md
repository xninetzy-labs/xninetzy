---
name: "evidence-synthesis"
description: "Synthesize evidence from multiple sources into a structured ledger: claims with supporting evidence, contradictions, gaps, confidence ratings. Activates whenever multiple sources must be combined into a single evidence base for downstream writing skills."
metadata:
  scope: "research"
  intent_class: "RESEARCH"
  consumes: "source-evaluation, citation-validation"
  produces: "evidence_synthesis"
  tier: "0"
---
# evidence-synthesis

Input:

- sources: list of `{source_id, author, venue, year}`
- evidence: list of raw excerpts pulled from sources
- claims: list of claims to ground

Output:

- claim `<->` evidence `<->` source ledger (one row per claim)
- per-claim confidence (propagated through claim-lattice)
- contradiction cluster report
- gap list (claims with zero evidence after pass)

Workflow (5 steps):

1. Normalize evidence into `{evidence_id, source_id, excerpt, claim_keys[]}`.
2. Attach each evidence to one or more claims via `claim_keys`.
3. Propagate confidence through claim-lattice (parent claim inherits confidence of children unless explicitly decoupled).
4. Detect contradictions: for any claim with both supporting and refuting evidence, emit `HIGH_DISAGREEMENT` cluster, preserve both sides.
5. Gap detection: emit any claim whose evidence set is empty or whose sources fail the independence rule.

Minimum evidence threshold: 2 independent sources per claim. Independence = different author AND different venue AND different year. Two excerpts from the same author-venue-year pair count as 1 source.

Contradiction handling: never silently average. Preserve both supporting and refuting evidence. Tag cluster `HIGH_DISAGREEMENT` and surface to downstream writer; writer chooses framing.

Worked micro (5 claims, 12 evidence, 6 sources):

| claim_id | evidence_count | sources                                | confidence |
|----------|----------------|----------------------------------------|------------|
| C1       | 4              | S1, S2, S4, S5                          | HIGH       |
| C2       | 2              | S1, S3                                  | MEDIUM     |
| C3       | 3              | S2, S4, S6 (S4 refutes)                 | LOW (HIGH_DISAGREEMENT) |
| C4       | 0              | -                                       | UNGROUNDED |
| C5       | 1              | S3 only (S3+S5 same author/venue/year) | UNGROUNDED (independence fail) |

Contradictions: C3 has S2+S6 supporting vs S4 refuting. Surface both sides; do not collapse.
Gaps: C4 (no evidence), C5 (independence failure on S3/S5).

Failure modes:

- `SOURCE_DOUBLE`: same author-venue-year pair counted twice as independent. Mitigation: enforce `(author, venue, year)` tuple uniqueness in source set before scoring.
- `SILENT_DROP`: low-confidence evidence dropped without flag. Mitigation: retain evidence; downgrade claim confidence; never delete rows.
- `SYNTHESIS_FABRICATION`: claim asserted without evidence but tagged green. Mitigation: confidence floor UNGROUNDED when evidence_count == 0; reject HIGH/MEDIUM tags without threshold met.

Routing hints:

- Confidence propagation detail: defer to claim-lattice.
- Adding new sources to the set: defer to source-evaluation.
- Per-evidence quality scoring: defer to evidence-grader.
- Citation rendering downstream: defer to citation-validation.
