---
name: outline-builder
description: Generate ordered outlines (section + depth + purpose + word budget) tailored to intent class. Activates when a draft needs structural planning before writing.
metadata:
  scope: skill
  intent_class: TECHNICAL
  consumes: none
  produces: outline
  tier: 0
---

# Outline Builder

Build a structural outline before drafting any prose artifact. Output is
an ordered section list with depth (H1/H2/H3), one-line purpose, and a
word budget per section.

## Inputs

- `intent_class` ∈ {`PROPOSAL`, `ACADEMIC`, `TECHNICAL`, `PROFESSIONAL`}
- `topic` (string)
- `total_words` (int, default 2500)
- `template` (optional, override default)

## Output Schema

For each section:

```text
- [depth] section_name | purpose: ... | words: N (pct%)
```

Deliverable ends with `total_words` matching the request.

## Section Templates

### ACADEMIC — IMRaD

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Introduction | Frame problem + state aim | 15 |
| 2 | Methods | Reproducible procedure | 20 |
| 3 | Results | Findings w/ evidence | 20 |
| 4 | Discussion | Interpret + compare | 25 |
| 5 | Conclusion | Recap + future work | 10 |
| 6 | References | Cite sources | 10 |

### ACADEMIC — Literature Review

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Scope | Boundaries of review | 10 |
| 2 | Methodology | Search + inclusion criteria | 15 |
| 3 | Themes | Thematic synthesis | 25 |
| 4 | Critique | Methodological limits | 20 |
| 5 | Gaps | Open questions | 15 |
| 6 | Synthesis | Integration + position | 15 |

### PROPOSAL — Competitive (grant / RFP / investor)

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Executive Summary | Decision-grade synopsis | 10 |
| 2 | Problem | Pain point + stakes | 15 |
| 3 | Solution | Approach + differentiation | 20 |
| 4 | Impact | Outcomes + metrics | 15 |
| 5 | Team | Capability proof | 10 |
| 6 | Timeline | Phases + milestones | 10 |
| 7 | Budget | Cost justification | 10 |
| 8 | Appendix | Supporting evidence | 10 |

### PROPOSAL — Research

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Background | Field state + need | 15 |
| 2 | Objectives | SMART goals | 10 |
| 3 | Hypothesis | Testable claim | 5 |
| 4 | Methodology | Design + instruments | 25 |
| 5 | Workplan | Tasks + schedule | 15 |
| 6 | Deliverables | Tangible outputs | 10 |
| 7 | References | Cited works | 10 |
| 8 | Budget (optional) | Cost lines | 10 |

### PROFESSIONAL — Executive Memo

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Context | Situation + stakes | 10 |
| 2 | Decision Required | The ask | 5 |
| 3 | Options | Plausible paths | 25 |
| 4 | Recommendation | Pick + rationale | 25 |
| 5 | Risks | Failure modes | 20 |
| 6 | Next Steps | Owner + due date | 15 |

### TECHNICAL — Tutorial

| # | Section | Purpose | Default % |
|---|---|---|---|
| 1 | Goal | What reader builds | 5 |
| 2 | Prerequisites | Knowledge + tooling | 5 |
| 3 | Concepts | Mental models | 15 |
| 4 | Steps | Ordered actions | 40 |
| 5 | Verification | Tests + sanity checks | 15 |
| 6 | Troubleshooting | Common pitfalls | 10 |
| 7 | Next | Where to go from here | 10 |

## Ordering Rules

1. Claims precede evidence.
2. Problem precedes solution.
3. Methodology follows hypothesis.
4. Recommendation follows options.
5. Conclusion always last in the body.

## Word Budget Allocator

- Sum of section percentages = 100.
- Default rule: each section rounded to the nearest 50 words.
- If `total_words < 800`, compress Discussion/Themes by 5 % and
  expand Conclusion/Next by 5 %.
- If a section exceeds 40 % of the total, force split into sub-sections.

## Depth Rule

- Maximum 3 levels deep (`#` → `##` → `###`).
- Anything beyond level 3 must become narrative prose, not new headings.

## Worked Example

Topic: "Industry 4.0 adoption in Indonesian SMEs"
Intent: `ACADEMIC` (Literature Review) — `total_words` = 2500

```text
- [H1] Scope | purpose: bound the review to SE Asia mfg SMEs 2018-2025 | words: 250 (10%)
  - [H2] Geography + sector boundary
  - [H2] Time window + rationale
- [H1] Methodology | purpose: PRISMA-style source selection | words: 375 (15%)
  - [H2] Databases queried
  - [H2] Inclusion / exclusion criteria
- [H1] Themes | purpose: synthesize adoption drivers + barriers | words: 625 (25%)
  - [H2] Digital readiness
  - [H2] Workforce capability
  - [H2] Financing constraints
- [H1] Critique | purpose: assess methodological limits | words: 500 (20%)
  - [H2] Sampling bias
  - [H2] Self-report caveats
- [H1] Gaps | purpose: surface under-researched areas | words: 375 (15%)
  - [H2] Micro-firm dynamics
  - [H2] Policy-firm interaction
- [H1] Synthesis | purpose: position + agenda for further work | words: 375 (15%)
  - [H2] Integrated finding
  - [H2] Research agenda
```

Total: 2500 words, depth ≤ 2, every section ≤ 25 %.

## Failure Modes

- `OVER_OUTLINE`: ≥ 7 H levels or ≥ 4 numeric levels — flatten to prose.
- `UNBALANCED`: any section > 40 % of total — split or trim.
- `MISSING_SECTION`: no conclusion / next-steps block — insert.
- `COPY_PASTE_TEMPLATE`: section list unchanged from the template
  without topic-specific purpose lines — re-purpose each row.

## Routing Hints

- After outline approval → defer to `professional-editor` for prose
  drafting of each section.
- For final structural audit (heading hierarchy, word-budget adherence,
  reference completeness) → defer to `submission-readiness`.
- For research evidence per section → defer to `research-planner`.

## Anti-Overreach

- Do not draft section prose here; outline only.
- Do not invent sources or claims to fill gaps.
- Do not commit to a final word count below 400 unless the user asks
  for a micro-outline.
