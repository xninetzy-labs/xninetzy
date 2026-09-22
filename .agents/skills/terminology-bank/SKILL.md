---
name: "terminology-bank"
description: "Maintain per-domain canonical term lists with aliases, definitions, banned forms, first-use notes. Run consistency pass against draft text. Activates during editorial review for academic or technical documents."
metadata:
  scope: "editing"
  intent_class: "EDITING"
  consumes: "source-evaluation"
  produces: "terminology_findings"
  tier: "0"
---
# terminology-bank

Bank of canonical domain vocabulary. One entry per term. Run a
consistency pass over draft text and emit findings; do not rewrite the
draft itself.

## Entry schema

```yaml
- domain: <ml|statistics|hci|biomed|...>
  canonical: "<preferred form>"
  aliases: ["<form>", "<form>"]
  definition: "<one-line, sourced where possible>"
  do_not_use: ["<form>", "<form>"]
  first_use_note: "<expansion or qualifier required at first mention>"
```

Per-domain term lists are append-only during editing and trimmed at
freeze time.

## Seed entries (non-exhaustive)

- `ml`: "machine learning" (aliases: ["ML"]), definition: "algorithms
  that learn parameters from data to make predictions or decisions",
  do_not_use: ["AI engine", "smart algorithm"], first_use_note: spell
  out "machine learning (ML)"; subsequent uses may use "ML".
- `statistics`: "p-value" (aliases: ["p"]), definition: "probability of
  observing data at least as extreme as the result, assuming the null
  hypothesis", do_not_use: ["significance value", "alpha value"],
  first_use_note: report as "p-value = 0.012" with effect size and
  confidence interval alongside; never equate with "significance".
- `hci`: "usability" (aliases: []), definition: "effectiveness,
  efficiency, and satisfaction with which specified users achieve
  specified goals in a specified context of use", do_not_use:
  ["user-friendliness", "intuitive"], first_use_note: "usability
  (effectiveness, efficiency, satisfaction in a specified context of
  use)" — full ISO 9241-11 expansion required at first mention.
- `biomed`: "randomization" (aliases: []), definition: "allocation of
  participants to arms by a random process with adequate allocation
  concealment", do_not_use: ["random selection" when describing
  sampling], first_use_note: state allocation concealment mechanism
  (centralized, sequentially numbered, sealed envelopes, etc.).

## Operations

- **ingest** — add a new term. Require: domain, canonical, definition,
  source. Aliases and do_not_use are optional but recommended.
- **lookup** — return canonical form + definition + first-use note for
  a given term or alias.
- **consistency_pass** — scan draft text. Emit findings of shape
  `{location, term, issue_kind, suggestion}` where `issue_kind` is one
  of `ALIAS_USED`, `FIRST_USE_MISSING`, `BANNED_USE`, `CROSS_DOMAIN`.
- **freeze** — lock the bank. Reject new entries until unfrozen; mark
  the lock timestamp and reviewer.

## Finding shapes

- `ALIAS_USED` — alias detected in body without prior first-use
  expansion. Suggest canonical form on first detection; allow alias
  thereafter only if first-use already established.
- `FIRST_USE_MISSING` — canonical term appears before its required
  first-use expansion. Suggest inserting the expansion.
- `BANNED_USE` — `do_not_use` form detected. Suggest canonical.
- `CROSS_DOMAIN` — term registered in domain A but used in domain B
  context without domain switch marker. Suggest either domain switch
  or alternate term.

## Worked micro

Draft section 1: "Our ML pipeline outperforms prior baselines."
- `ALIAS_USED` at the first "ML" — the section has no prior
  "machine learning (ML)" expansion. Suggest: replace first occurrence
  with "machine learning (ML)"; later "ML" occurrences are fine.
- No `BANNED_USE` — "AI engine" does not appear.

## Failure modes

- `BANK_BLOAT` — entries accumulate without curation. Mitigation:
  monthly freeze review; entries without a use in the last 90 days are
  flagged for archival.
- `FIRST_USE_TYRANT` — consistency pass demands full expansion in
  every sentence. Mitigation: first-use rule applies only to the first
  appearance per section; honor author-set first-use anchors.
- `CROSS_DOMAIN_LEAK` — terms from one domain appear in another
  without justification. Mitigation: require `domain:` on every entry;
  flag any term whose surrounding paragraph signals a different domain.

## Routing

- Defer prose rewrite to `academic-editor`.
- Defer final polish and citation tightening to `paper-review`.
- Defer new term justification and source evaluation to
  `source-evaluation` (consumes) and `citation-validation`.
- This skill produces findings only; it does not modify the draft.

## Output contract

`terminology_findings`: list of
`{location, term, issue_kind, suggestion}` plus a bank snapshot
showing registered domains and entry counts per domain.