---
name: scoring-rubric
description: Normalize and apply competition/scoring rubrics. Produce per-criterion evaluation sheet with weighted scores and threshold checks. Activates whenever quantitative scoring drives selection.
metadata:
  scope: xninetzy
  intent_class: PROPOSAL
  consumes: requirement-coverage
  produces: rubric_score
  tier: "0"
---

# Scoring Rubric Mapper

## Inputs

- Rubric spec: criterion name, max_score, weight_pct, descriptor per band
- Draft artifacts to be scored (paragraphs, sections, files)
- Optional funding tier / context flags

## Normalized Rubric Object

```yaml
rubric_id:             "<stable hash>"
source:               "<rubric name>"
normalized_at:        "<iso8601>"
criteria:
  - criterion_id:     "<snake_case>"
    label:            "<human label>"
    max_score:        <int|float>
    weight:           <float, 0..1, sum == 1>
    scoring_method:   "additive" | "multiplicative" | "threshold"
    bands:
      - band_id:       "excellent" | "good" | "fair" | "poor" | "fail"
        descriptor:   "<plain text>"
        range:        [<lo>, <hi>]   # inclusive
    threshold:        { type: "eliminate_if_below", value: <float> }  # optional
    funding_tiers:    [<tier>, ...]   # optional applicability filter
```

Normalization rules:

- Convert `weight_pct` to `weight = weight_pct / 100`, then renormalize so
  `sum(criteria.weight) == 1.0` within `1e-6`.
- Derive `scoring_method` from max_score: `1` → `threshold`, otherwise
  `additive`. Promote to `multiplicative` only when rubric explicitly states
  compounding (rare).
- Resolve band ranges from descriptors by walking `poor` → `excellent`,
  filling gaps so ranges are contiguous and cover `[0, max_score]`.
- Preserve hard thresholds (eliminate_if_below) as first-class fields; never
  collapse into weight.

## Per-Criterion Evaluation Sheet

For each criterion produce one record:

```yaml
- criterion_id:   "innovation"
  label:          "Innovation"
  weight:         0.30
  max_score:      10
  raw_score:      8
  weighted_score: 0.24            # raw/max * weight
  band:           "good"
  band_descriptor:"..."
  evidence_refs:
    - draft_paragraph_id: "p2"
      coverage: "full"            # full | partial | none
    - draft_paragraph_id: "p5"
      coverage: "partial"
  coverage_map:  ["p2","p3","p5"] # paragraphs contributing
  notes:         "<one line>"
```

Per-criterion evaluation steps:

- Collect evidence: grep rubric descriptor keywords against draft
  paragraphs/sections; record `coverage: full|partial|none` per match.
- Pick the highest-coverage band whose range contains the raw score.
- Compute `weighted_score = raw_score / max_score * weight`.
- Mark `eliminated: true` if `threshold.eliminate_if_below` is set and
  raw_score < threshold.
- Mark `not_applicable: true` if `funding_tiers` is set and current tier
  not in list (then weighted_score = 0, weight redistributes via
  renormalize_on_skip flag).

## Worked Micro Example

Input rubric:

```yaml
- Innovation  : max 10, weight 30%
- Feasibility: max 10, weight 25%
- Impact     : max 10, weight 25%
- Team       : max 10, weight 20%
```

Normalized weights: 0.30, 0.25, 0.25, 0.20 (already sum to 1.0).

Draft paragraph map for Innovation:

| Paragraph | Maps to Innovation? | Coverage |
|---|---|---|
| p2: "novel contrastive pretraining across modalities" | yes | full |
| p3: "beats prior SOTA by 4.1 on GLUE" | yes | partial |
| p5: "deployable on a single A100" | yes | partial |
| p7: "team lead previously shipped X" | no | none |

Innovation raw_score: 8 (descriptor "good" band, 7..9). weighted_score =
8/10 * 0.30 = 0.24.

## Edge Cases

- Binary pass/fail criteria: `max_score = 1`, `scoring_method = threshold`,
  raw_score ∈ {0, 1}. Treat `weight` like any other; do not silently drop.
- Hard thresholds: when `eliminate_if_below` triggers, set aggregate state to
  `ELIMINATED` regardless of remaining scores.
- Funding-tier weighted criteria: only score criteria whose
  `funding_tiers` includes current tier; renormalize remaining weights to
  sum to 1.0 before aggregating.
- Single-criterion rubrics: weight forced to 1.0; aggregate equals raw/max.
- Zero-weight criteria (advisory): score but exclude from aggregate; expose
  in evaluation sheet with `advisory: true`.

## Failure Modes

- `WEIGHT_NORMALIZATION_ERROR` — `sum(weights)` outside `[1.0 - 1e-6, 1.0 + 1e-6]`.
  Halt; emit diagnostic listing per-criterion weight.
- `BAND_AMBIGUITY` — two bands overlap in range, or descriptor language
  shared across band boundaries. Resolve by trimming to non-overlapping
  ranges (keep upper band wins on tie) and surface a warning.
- `SCORE_CEILING_DRIFT` — one criterion's weighted_score > 0.5 of aggregate
  while total rubric weight on it < 0.5 (i.e. inflation). Re-anchor raw_score
  to descriptor ceiling and flag in notes.
- `MISSING_THRESHOLD` — binary criterion present in spec but no
  `threshold.eliminate_if_below` and no band descriptor for `0`. Inject
  band `fail: range [0, 0]` and warn.
- `CRITERION_SKIPPED` — funding-tier mismatch; redistribute remaining weights
  and warn.

## Output Artifact

Emit one rubric_score artifact:

```yaml
artifact_id:    "rubric_score::<rubric_id>::<submission_id>"
rubric_id:      "..."
aggregate:      <float, 0..1>
state:          "PASS" | "FAIL" | "ELIMINATED" | "INCOMPLETE"
per_criterion:  [<evaluation records>]
warnings:       [<failure_mode>, ...]
eliminated_by:  "<criterion_id>" | null
advisory:       [<records with advisory: true>]
```

## Routing Hints

- Defer completeness checks to `requirement-coverage` before scoring;
  missing requirements will inflate raw scores unfairly.
- Defer final aggregate + submission gating to `submission-readiness`;
  scoring-rubric produces the per-criterion sheet + aggregate, the readiness
  layer enforces minimum thresholds and aggregates across rubrics.
- When rubric is incomplete (weights absent), request `requirement-coverage`
  to derive default weights from requirement priority.