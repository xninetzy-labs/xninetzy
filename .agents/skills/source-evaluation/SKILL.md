---
name: "source-evaluation"
description: "Evaluate a source for authority, recency, methodology, primary-vs-secondary status, and topic fit. Produces a graded scorecard. Activates whenever a source must be trusted, cited, or excluded from evidence synthesis."
metadata:
  scope: "research"
  intent_class: "RESEARCH"
  consumes: "none"
  produces: "source_scorecard"
  tier: "0"
---
# source-evaluation

Score a source on six axes, each in [0.0, 1.0]. Composite drives trust tier.

Axes:

- AUTHORITY: author credentials, venue reputation, editorial process. Peer-reviewed journal with named authors + DOI = high. Anonymous blog = low.
- RECENCY: publication date vs the topic's decay rate. Fast-moving topic (LLM benchmarks, regulations, prices) needs <12 months. Slow-moving (mathematics, history) tolerates decades.
- METHODOLOGY: how the source was produced. RCT with preregistration = high. Anecdote = low. Survey, simulation, observational study fall in between.
- PRIMARY_VS_SECONDARY: does the source itself report the observation, or only summarize others? 1.0 = raw data, original measurement, first-person testimony. 0.0 = tertiary review or summary-of-summary.
- TOPIC_FIT: relevance to the specific claim being supported. Off-topic high-quality source still scores low here.
- TRANSPARENCY: declared conflicts of interest, methods disclosed, data available, limitations stated.

Per-axis bands:

- < 0.40  → UNRELIABLE on that axis
- 0.40-0.64 → MARGINAL on that axis
- 0.65-0.84 → SOLID on that axis
- >= 0.85 → STRONG on that axis

Composite:

```
composite = mean(AUTHORITY, RECENCY, METHODOLOGY, PRIMARY_VS_SECONDARY, TOPIC_FIT, TRANSPARENCY)
if PRIMARY_VS_SECONDARY >= 0.9:
    composite += 0.10
composite = min(composite, 1.0)
```

Tier recommendations from composite:

- composite >= 0.85 AND PRIMARY_VS_SECONDARY >= 0.85 → claim-quality evidence; cite as the load-bearing reference for the claim.
- 0.65 <= composite < 0.85 → citeable as supporting evidence; do not let it carry a claim alone.
- 0.50 <= composite < 0.65 → mention only if no better source exists; flag explicitly as marginal.
- composite < 0.50 → EXCLUDE. Do not cite. Do not paraphrase. Do not use as background color.

Worked micro — NEJM 2024 peer-reviewed RCT:

```
AUTHORITY        = 0.95   peer-reviewed, named authors, NEJM
RECENCY          = 0.95   2024, current clinical practice
METHODOLOGY      = 0.85   RCT, preregistered, large N
PRIMARY          = 1.00   original trial report
TOPIC_FIT        = 0.90   matches claim exactly
TRANSPARENCY     = 0.80   COI declared, methods in supplement
composite (mean) = 0.908
bonus (primary)  = +0.10
final composite  = 1.00   → claim-quality
```

Worked micro — 2010 personal blog post on a clinical topic:

```
AUTHORITY        = 0.30   anonymous author, no credentials
RECENCY          = 0.20   2010, topic decayed
METHODOLOGY      = 0.10   anecdote, no method
PRIMARY          = 0.20   secondary impression
TOPIC_FIT        = 0.50   related topic but not the claim
TRANSPARENCY     = 0.30   no COI, no methods
composite (mean) = 0.267
bonus            = 0      (primary < 0.9)
final composite  = 0.27   → EXCLUDE
```

Failure modes:

- HALO_EFFECT: one strong axis (e.g. NEJM brand) inflates the others without evidence. Score each axis from the artifact, not the venue.
- RECENCY_HALO: assuming new = better. RECENCY must be calibrated to the topic's decay rate. A 1980 number-theory proof is still STRONG on RECENCY.
- BLOG_AS_SOURCE: treating Medium / Substack / corporate blogs as authoritative. Default AUTHORITY <= 0.4 unless the author is independently credentialed and cited.
- VENUE_SUBSTITUTION: scoring METHODOLOGY from the journal tier rather than the actual study design. A Nature commentary is not Nature research.
- TOPIC_FIT_INFLATION: accepting a tangentially related high-authority source because it is convenient.
- SECONDARY_PRIMARY_DRIFT: treating a literature review or summary as PRIMARY_VS_SECONDARY = 1.0. Reviews are secondary by definition.

Routing hints:

- When the scored source joins a claim-lattice node, defer to claim-lattice to attach the scorecard to the right node and propagate tier.
- Before any publication or claim finalization, defer to citation-validation to confirm the citation matches the scorecard and the composite meets the tier gate.
- For multi-source synthesis, average composites only when sources are independent; weight PRIMARY sources higher.
