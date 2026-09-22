---
name: "citation-validation"
description: "Validate citations in a document: verify each citation exists, metadata is accurate, citation supports the nearby claim, formatting is consistent. Flags orphan citations, mismatched claims, and unverifiable references. Default non-mutating."
metadata:
  scope: "review"
  intent_class: "REVIEW"
  consumes: "source-evaluation"
  produces: "citation_validation_report"
  tier: "0"
---
# citation-validation

Validate every in-text citation against its reference-list entry. Six checks per citation, four finding shapes, two severity bands.

## Six checks per (in-text, reference) pair

1. EXISTENCE — every citation key in body resolves to exactly one entry in the reference list.
2. FORMAT — in-text rendering and reference entry both follow the declared style (APA 7 / Chicago 17 / IEEE / Vancouver). Detect from document metadata; fail closed if undeclared.
3. PROXIMITY — the claim has at least one citation within N sentences (N=3 default; 1 for direct quotations).
4. SUPPORT — the cited source actually supports the claim. Requires reading the source text; semantic match alone is insufficient.
5. RECENCY — the cited source falls within the topic-decay window. Default windows: CS/AI 3y, biomedicine 5y, social-science 7y, history any.
6. AUTHORSHIP — author names match between in-text and reference entry exactly (initials, surname order, "et al." thresholds).

Reference normalization runs once per entry, not per check:

- Journal name: abbreviated or full, consistently within the document.
- DOI: resolves (HTTP 200 + landing page reachable) or flagged.
- Year: present, four digits, matches in-text year.

## Finding shape

Each finding is one record:

```
{
  citation_key: str,
  location: {section, paragraph, sentence_offset},
  check_failed: "EXISTENCE" | "FORMAT" | "PROXIMITY" | "SUPPORT" | "RECENCY" | "AUTHORSHIP",
  suggested_fix: str
}
```

## Severity

- HARD: EXISTENCE, SUPPORT. Any HARD finding fails submission.
- SOFT: FORMAT, PROXIMITY, RECENCY, AUTHORSHIP. Any SOFT finding accepts the document with a warning; never block on FORMAT alone if AUTHORSHIP and EXISTENCE pass.

## Worked micro

Reference list (3 entries):

- `[smith2020]` Smith, J. (2020). On frogs. *Journal of Herpetology*, 12(3), 45-58.
- `[doe2018]` Doe, A. (2018). Amphibian decline. *Nature*, 555, 123-130.
- `[wang2022]` Wang, L. (2022). Newts are not frogs. *Biology Letters*, 18(1), 20210456.

In-text citations (4):

1. "Frogs are declining globally [smith2020]." — claims match source → OK.
2. "Frogs cause autism [doe2018]." — source is about decline, not autism → UNSUPPORTED (HARD).
3. "All amphibians are frogs [wang2022]." — Wang says newts are not frogs; contradicts claim → UNSUPPORTED (HARD), plus claim is wrong.
4. "Recent work confirms the trend [kang2024]." — `kang2024` not in reference list → ORPHAN (HARD, EXISTENCE).

Result: 3 HARD findings. Document fails submission. Suggested fixes are concrete and copy-pastable.

## Failure modes of the validator itself

- STYLE_HALO: one FORMAT flag elevates the whole document's perceived quality down. Mitigate by reporting check-level granularity; never roll up.
- FALSE_NEGATIVE: a citation that is correct but does not match the declared style (e.g., AMA used where Vancouver was declared). Fix: re-run with the actual style declared; the citation is fine.
- ORPHAN_REFERENCE: an entry in the reference list never cited in body. Flag separately as `UNUSED_REFERENCE` (SOFT); do not conflate with EXISTENCE failures.

## Routing hints

- For evaluating new or unfamiliar sources before citation: defer to `source-evaluation`.
- For fixing prose around a flagged citation: defer to `academic-editor`.
- For final pre-submission pass: defer to `paper-review`.
