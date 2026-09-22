---
name: requirement-coverage
description: Map competition/RFP requirements to draft sections, compute weighted coverage score, surface unaddressed requirements. Activates when a competition ruleset or rubric exists and must be matched.
metadata:
  intent_class: PROPOSAL
  consumes: scoring-rubric
  produces: coverage_report
  tier: 0
---

# Requirement Coverage

Map every rulebook requirement to a draft section, score it, surface gaps.

## Inputs

- rulebook: competition / RFP ruleset
- scoring-rubric: weights per criterion
- draft: optional artifact to score against

## Outputs

- coverage_report: per-requirement map with score band and gap notes
- weighted_total: aggregate score 0-100
- unfunded_requirements: requirements with coverage == 0

## Workflow

1. Extract each requirement from rulebook as `R{id}` with verbatim text + weight.
2. For each requirement, locate matching section in draft by keyword + intent.
3. Assign score band:
   - 0 = SILENT_OMISSION (requirement not addressed)
   - 1-3 = partial (tangential or weak evidence)
   - 4-7 = substantive (addresses substance, missing polish or evidence)
   - 8-10 = strong (explicit, evidenced, well-structured)
4. Compute weighted contribution: `weight * band / 10`.
5. Roll up `weighted_total` = `sum(weighted) / sum(weights) * 100`.
6. Flag `unfunded_requirements` = where band == 0.
7. Emit gap notes: missing evidence, missing subsection, weak framing.

## Coverage Bands

| Band | Label | Action |
|------|-------|--------|
| 0 | UNCOVERED | BLOCKER - must address before submission |
| 1-3 | PARTIAL | needs expansion + evidence |
| 4-7 | SUBSTANTIVE | polish + targeted evidence |
| 8-10 | STRONG | defend in review |

## Worked Template

```
Criterion: Innovation - weight 30%
Draft section: 4.2 Novel Architecture
Band: 5/10 PARTIAL
Evidence cited: [arxiv:2401.01234, internal-prototype]
Gap: no comparison vs prior art; no quantitative ablation
Weighted contribution: 0.30 * 5/10 = 0.15 -> 15.0 points of 30
```

## Failure Modes

- SILENT_OMISSION: requirement present in rulebook, never referenced in draft. Score 0.
- WEIGHT_MISREAD: treat all requirements as equal weight. Always honor rubric weights.
- DOUBLE_COUNTING: same evidence cited under multiple requirements. Flag as risk.
- RUBRIC_DRIFT: draft addresses rulebook but ignores published scoring rubric. Defer to scoring-rubric.
- EVIDENCE_GAP: claim made but no citation. Demote band by 1-2 until cited.

## Routing

- Quantitative rubric parsing: scoring-rubric
- Draft composition: authoring prose for weak sections
- Final pre-submission pass: submission-readiness
- Competition framing and structure: competition-proposal

## Checklist

- [ ] Every rulebook requirement has R{id}
- [ ] Weight sourced from scoring-rubric, not guessed
- [ ] Each draft section mapped to >=1 R{id}
- [ ] Band assigned with 1-sentence justification
- [ ] Evidence cited for bands >= 7
- [ ] Weighted total recomputed after edits
- [ ] unfunded_requirements list is empty (or all items waived)
- [ ] No requirement double-counted across sections

## Cross-references

- scoring-rubric: parse + apply weights
- proposal-writer: draft new sections for partial bands
- competition-proposal: structural framing
- submission-readiness: final formatting + compliance pass