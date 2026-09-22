---
name: methodology-rater
description: Rate a study's methodology across 6 axes (design fit, sample, control, measurement, analysis, transparency) with bands + composite. Activates during paper review or research design vetting.
metadata:
  scope: paper-analysis
  intent_class: REVIEW
  consumes: paper-analysis
  produces: methodology_scorecard
  tier: 0
---

# methodology-rater

Score a study's methodology across 6 axes on a 0..1 scale. Produce a
methodology_scorecard with per-axis band, raw score, red flags, and a
weighted composite.

## Axes and weights

| Axis           | Weight | What it measures |
|----------------|-------:|------------------|
| DESIGN_FIT     | 0.25   | Study design matches the research question |
| SAMPLE_REP     | 0.15   | Representativeness + power justification |
| VAR_CONTROL    | 0.20   | Confounder control (matching / randomization / stratification) |
| MEASUREMENT    | 0.15   | Validity + reliability of instruments |
| ANALYSIS       | 0.15   | Appropriate tests + assumption checks |
| TRANSPARENCY   | 0.10   | Preregistration, replication, code/data availability |

Composite = sum(weight_i * score_i).

## Bands

Thresholds apply per axis.

| Band     | Range     |
|----------|-----------|
| CRITICAL | 0.00 ..< 0.40 |
| POOR     | 0.40 ..< 0.65 |
| ADEQUATE | 0.65 ..< 0.85 |
| STRONG   | 0.85 .. 1.00 |

## Axis rubrics + red flags

### DESIGN_FIT (0.25)

- STRONG (>=0.85): design canonically matches question (RCT for causality,
  cross-sectional for prevalence, cohort for incidence, case-control for
  rare outcomes, qualitative for lived experience).
- ADEQUATE (0.65..<0.85): reasonable design with minor mismatch (e.g.
  cross-sectional used to imply causation but acknowledged as limitation).
- POOR (0.40..<0.65): notable mismatch (case series used to estimate
  effect, single-case for population claim).
- CRITICAL (<0.40): design cannot answer the question at all.

Red flags: claims causality from cross-sectional/ecological data; uses
qualitative sample size to claim prevalence; retrospective design for
prospective-only question.

### SAMPLE_REP (0.15)

- STRONG: probability sampling with documented power calc + achieved power.
- ADEQUATE: probability sampling, power calc present, minor representativeness gap.
- POOR: convenience sample OR no power calc.
- CRITICAL: convenience sample AND no power calc, or n < 10 per group for
  inferential stats.

Red flags: convenience-only sampling; missing power justification; n too
small for planned test; post-hoc power only; selective recruitment.

### VAR_CONTROL (0.20)

- STRONG: randomization with allocation concealment, or strong matching +
  adjustment, plus sensitivity analysis.
- ADEQUATE: randomization OR multivariate adjustment for known confounders.
- POOR: limited control, key confounders unmeasured.
- CRITICAL: no control for known strong confounders.

Red flags: no adjustment for age/sex when relevant; selection bias
unaddressed; immortal-time bias; collider conditioning.

### MEASUREMENT (0.15)

- STRONG: validated instrument, reported reliability (alpha/ICC), blinded
  outcome assessment.
- ADEQUATE: validated instrument, reliability reported elsewhere.
- POOR: ad-hoc instrument, no reliability.
- CRITICAL: outcome measured by unvalidated instrument with no reliability.

Red flags: self-report for objective outcome without validation; outcome
assessor not blinded when feasible; floor/ceiling effects ignored.

### ANALYSIS (0.15)

- STRONG: appropriate test, assumption checks reported, effect sizes +
  CIs, multiple-comparison correction where needed.
- ADEQUATE: appropriate test + effect sizes, assumption checks partial.
- POOR: p-values only, assumption checks missing.
- CRITICAL: inappropriate test (e.g. t-test on skewed data, chi-square on
  small expected counts, parametric on ordinal).

Red flags: p-only reporting; no effect size; p-hacking signals; HARKing;
circular analysis.

### TRANSPARENCY (0.10)

- STRONG: preregistered, code + data shared, replication prior.
- ADEQUATE: preregistered OR data shared with clear methods.
- POOR: methods described, no preregistration, no sharing.
- CRITICAL: methods unclear, no preregistration, no sharing, or
  inconsistencies with prior versions.

Red flags: outcomes changed vs protocol; selective reporting; "data
available on request" with no follow-through; image/data manipulation
concerns.

## Worked micro

Hypothetical cross-sectional study, n=200, single-site clinic, no
power calc, validated survey instrument, multivariate logistic
regression for confounders, no preregistration.

| Axis        | Score | Band     | Why |
|-------------|------:|----------|-----|
| DESIGN_FIT  | 0.85  | STRONG   | Cross-sectional fits prevalence question |
| SAMPLE_REP  | 0.35  | CRITICAL | Convenience single-site + no power calc |
| VAR_CONTROL | 0.65  | ADEQUATE | Multivariate adjustment present |
| MEASUREMENT | 0.80  | ADEQUATE | Validated survey, reliability not reported in extract |
| ANALYSIS   | 0.70  | ADEQUATE | Appropriate test, no assumption/effect-size detail |
| TRANSPARENCY| 0.40  | POOR     | No preregistration, no sharing |

Composite = 0.25*0.85 + 0.15*0.35 + 0.20*0.65 + 0.15*0.80 + 0.15*0.70 + 0.10*0.40
          = 0.2125 + 0.0525 + 0.1300 + 0.1200 + 0.1050 + 0.0400
          = 0.6600 (AVERAGE overall)

Verdict: design is right, execution is shaky. Recommend
SAMPLE_REP fix (power calc + multi-site) and TRANSPARENCY fix
(preregister or share data) before treating estimates as robust.

## Failure modes

- OVER_CREDIT: gives 0.7 to seriously flawed designs. Guard: any axis
  in CRITICAL caps the composite at 0.55; flag explicitly.
- UNDER_CREDIT: over-penalizes small n. Guard: small n in a well-powered
  pilot is ADEQUATE on SAMPLE_REP; small n for a confirmatory claim is
  CRITICAL. Distinguish pilot vs confirmatory intent.
- DISCIPLINE_BIAS: applies biomed standards (RCT, preregistration) onto
  interpretivist research. Guard: rate MEASUREMENT and ANALYSIS against the
  conventions of the stated paradigm; flag paradigm before scoring.
- SCORE_DRIFT: same paper scores differently across raters. Guard:
  cite the rubric level (STRONG/ADEQUATE/POOR/CRITICAL) and the red-flag
  checklist literally for each axis; record evidence sentence per axis.

## Routing hints

- Full review (claims, interpretation, novelty): defer to paper-review.
- Interpretive or theoretical concerns: defer to research-critic.
- Statistical deep-dive (test choice, model specification): defer to
  regression-analysis.
- Output is a methodology_scorecard, not a verdict on the paper's
  truth value.

## Output shape

methodology_scorecard = {
  axes: [
    {name, score, band, evidence, red_flags[]}
  ],
  composite,
  verdict: "AVERAGE" | "BELOW_AVERAGE" | "ABOVE_AVERAGE",
  caveats: [...],
  routing: [...]
}