---
name: academic-writing-suite
description: 'Routes manuscript work: field-specific section drafting (ML, CS systems, economics, humanities), journal adaptation, APA/MLA/IEEE/Harvard conversion, reviewer rebuttals, paragraph polish, de-AI prose. Use for any paper, thesis or journal text.'
metadata:
  scope: writing
  intent_class: ACADEMIC
  consumes: academic-writer, academic-editor, paper-review, citation-validation, anti-slop, literature-review-writer
  produces: academic_document
  tier: '0'
  keywords: manuscript paper thesis skripsi jurnal makalah naskah journal submission camera-ready abstract introduction method experiments related work conclusion section polish paragraph grammar word choice academic English proofread SCI manuscript editing cite style convert citation reference bibliography sitasi daftar pustaka APA MLA IEEE Harvard Chicago Vancouver rebuttal response to reviewers reviewer comments revision humanize AI-sounding robotic prose LaTeX tex econ economics identification CVPR NeurIPS ICML ACL ICLR systems networking philosophy target journal style
---
# academic-writing-suite

Router for academic manuscript work. Load one row, read only the slice needed, then follow it. Paths are relative to this skill directory. Large guides have a sibling `*.index.md` with `start-end heading` lines: read the index, then the slice with offset and limit.

## Route
| Request | Load |
|---|---|
| Draft or fix Abstract, Introduction, Method, Experiments, Related Work, Conclusion (ML, CV, NLP) | `references/ml-sections/guide.md`, then `references/ml-sections/references/<section>.md` |
| CS systems, networking, ML-adjacent paper; story, outline, compression, red-team, figures | `references/cs-systems/guide.md` (+ `guide.index.md`) |
| Economics paper, identification, tables, referee response, JMP | `references/econ/guide.index.md`, then slices of `guide.md`; `specialized-tasks.md`, `review-checklist.md` |
| Philosophy or interdisciplinary paper: plan then compose | `references/humanities/strategist/guide.md`, then `composer/guide.md` |
| Adapt a manuscript to a target journal using sample papers | `references/journal-adapt/guide.md` (+ `base_rules/`, `templates/`) |
| `.tex` or thesis multi-pass review (logic, consistency, bibliography, layout, figures) | `references/latex-review/orchestrator.md`; each `agents/*.md` is a checklist, run it inline or as a native subagent; principles in `principles.md` |
| Polish grammar, word choice, voice, coherence per paragraph | `references/polish.md` |
| Convert or check citation style (APA, MLA, IEEE, Harvard, Chicago, Vancouver) | `references/cite-style.md` |
| Response to reviewers, rebuttal letter | `references/rebuttal.md` |
| Prose sounds AI-written (stock phrases, forced triads, filler) | `references/humanize.index.md`, then slices of `humanize.md` |

## Hand off to existing skills
Peer-review critique of a paper: `paper-review`. Citations exist and support claims: `citation-validation`. Argument and evidence edit: `academic-editor`. Plain formal writing in any field: `academic-writer`. Literature review: `literature-review` (sources missing) or `literature-review-writer` (sources in hand). Final slop pass: `anti-slop`. Find or download papers: `research` skill and the `paper_research` MCP, not this skill.

## Invariants
1. Never invent citations, data, results, baselines or experiments. Missing evidence becomes a flagged gap, not a sentence.
2. Preserve the author's claims, numbers, terminology and voice. Change what the reader needs, nothing else.
3. Edit for readers, never to lower AI-detector scores. The owner's own work stays the owner's: no ghost-writing of graded submissions beyond what was asked, and no submission without explicit approval.
4. Load one route per task. Do not read a whole guide when an index slice answers the question.
5. Mixed requests: run routes in order draft, polish, citations, anti-slop.

## Output contract
Deliver the artifact or changed text first. Then a compact change log (`[type] before → after`) and a short list of open items (flags, missing fields, TODO for the author). Do not echo unchanged input. State which route and which files were used.

Provenance, licenses and exclusions: `PROVENANCE.md`.
