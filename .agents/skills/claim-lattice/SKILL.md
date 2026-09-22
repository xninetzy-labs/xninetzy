---
name: claim-lattice
description: Maintain the claim ↔ evidence ↔ source graph with confidence propagation. Activates when multiple claims must be evidence-grounded together (synthesis, cross-checking, contradiction detection).
metadata:
  scope: project
  intent_class: RESEARCH
  consumes: source-evaluation, citation-validation
  produces: claim_lattice
  tier: "0"
---

# Claim Lattice

Maintains a typed three-level graph: **claims → evidence → sources**, with
propagated confidence so a reader can see *why* a claim is trusted, not just
*that* it is asserted.

## Graph representation (JSON)

```json
{
  "claims": {
    "C1": {
      "text": "...",
      "confidence": 0.73,
      "evidence_ids": ["E1", "E2", "E3"],
      "source_ids": ["S1", "S2"]
    }
  },
  "evidence": {
    "E1": {"excerpt": "...", "source_id": "S1", "kind": "primary"},
    "E2": {"excerpt": "...", "source_id": "S1", "kind": "primary"},
    "E3": {"excerpt": "...", "source_id": "S2", "kind": "secondary"}
  },
  "sources": {
    "S1": {"url": "https://...", "authority_score": 0.9, "freshness": "2026-09-01"},
    "S2": {"url": "https://...", "authority_score": 0.6, "freshness": "2024-11-15"}
  }
}
```

Evidence kind:

- `primary` — direct observation, dataset, official doc, or first-party statement.
- `secondary` — paraphrase, summary, or third-party report citing the primary.
- `derived` — inference from one or more evidences (still tracks its source ids).

## Confidence propagation

For each claim:

```
n = len(distinct source_ids)
authority = mean(authority_score over source_ids)        # 0..1
quality   = mean(1.0 if kind=="primary" else 0.6 if "secondary" else 0.4
                 over evidence_ids)
count     = 1 - exp(-n/3)                                 # 0..1, ~0.63 at n=3
claim_conf = authority * quality * count
```

`count_factor` saturates: 3 independent supporting sources already give ~0.63
of the maximum weight; further sources add diminishing returns, discouraging
citation spam.

## Adding a claim

1. Mint `Cn`.
2. Locate or add evidence rows under `E*`, each pointing to a `Sn`.
3. Locate or add the source rows under `S*` with `authority_score` from
   `source-evaluation` and `freshness` as the publish/observed date.
4. Recompute `Cn.confidence` from the formula above.
5. Persist via the active skill contract; emit a `claim_lattice` artifact.

## Failure modes

- `ORPHAN_CLAIM` — `claim.evidence_ids` is empty or every evidence lacks a source.
- `EVIDENCE_LOOP` — evidence `Ea` cites source `Sb` whose evidence `Eb` cites
  back to a source already in the chain, forming a cycle.
- `LOW_TRUST_PATH` — every `source_id` in the claim has `authority_score < 0.4`;
  reject the claim or request stronger sources.
- `CITATION_LATENCY` — `freshness` on every supporting source is older than the
  claim's topic recency threshold; flag for refresh.
- `SOURCE_WITHOUT_AUTHORITY` — source exists but has no `authority_score`;
  defer to `source-evaluation` before trusting.
- `CHAIN_BREAK` — evidence cites a `source_id` not present in `sources`.

## Worked micro-example

Claim: *Solar PV LCOE fell below $0.05/kWh in utility-scale installs in 2024.*

```json
{
  "claims": {
    "C1": {
      "text": "Solar PV LCOE < $0.05/kWh (utility, 2024)",
      "confidence": 0.71,
      "evidence_ids": ["E1", "E2", "E3"],
      "source_ids": ["S1", "S2"]
    }
  },
  "evidence": {
    "E1": {"excerpt": "Lazard LCOE+ 2024: utility PV $0.04–0.06/kWh",
           "source_id": "S1", "kind": "secondary"},
    "E2": {"excerpt": "IRENA Renewable Power Costs 2024: median $0.045/kWh",
           "source_id": "S1", "kind": "secondary"},
    "E3": {"excerpt": "BloombergNEF New Energy Outlook 2024 spot prices",
           "source_id": "S2", "kind": "primary"}
  },
  "sources": {
    "S1": {"url": "https://www.lazard.com/.../lcoeplus.pdf",
           "authority_score": 0.9, "freshness": "2024-06-15"},
    "S2": {"url": "https://about.bnef.com/newo/",
           "authority_score": 0.85, "freshness": "2024-09-01"}
  }
}
```

Propagation:

```
authority = (0.9 + 0.85) / 2           = 0.875
quality   = (0.6 + 0.6 + 1.0) / 3      = 0.733
count     = 1 - exp(-2/3)              = 0.487
confidence = 0.875 * 0.733 * 0.487     ≈ 0.31  (rounds to 0.31)
```

(Note: 0.31 reflects two sources only — adding a third independent primary
source would push this past 0.6.)

## Cross-checks to run after each update

- Every `evidence.source_id` resolves to an entry in `sources`.
- Every `claim.evidence_ids` is non-empty.
- No cycles between `evidence → source → evidence`.
- Authority mean of a claim's sources ≥ 0.4, else raise `LOW_TRUST_PATH`.

## Routing

- New source needed → hand off to `source-evaluation` to mint a `source_id`
  with `authority_score` and `freshness`.
- Broken chain (missing IDs, mismatched excerpts) → hand off to
  `citation-validation`.
- Multi-claim synthesis with contradictions → keep claims separate, attach
  `contradicts: ["C2"]` and let the next pass reconcile.

## Activation triggers

- Synthesis tasks that must cite ≥3 independent sources per claim.
- Cross-checking one source's claims against another's.
- Contradiction hunts across a literature set.
- Any deliverable that will be graded on evidence quality, not just coverage.