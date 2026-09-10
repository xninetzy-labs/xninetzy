# Research artifact contract

Use this reference when the request includes a writable workspace or concrete deliverables. Create only artifacts relevant to the selected profile and requested formats.

## Configuration intake

Capture:

- title or topic;
- main question;
- objective and background;
- result-use context;
- target audience and depth;
- geography and source date range;
- source and output languages;
- writing and citation style;
- source and length targets;
- repository path and research slug;
- requested outputs;
- time, cost, access, technology, ethics, privacy, and other constraints.

For missing fields, search current context, repository documents, and approved owner knowledge. Record `unknown` when unresolved. Add working assumptions without inventing facts. Ask only when the answer changes the core question, safety, jurisdiction, population, or deliverable.

## Workspace layout

For a full project use the relevant subset of:

```text
docs/research/<slug>/
├── README.md
├── 00-research-charter.md
├── 01-tool-audit.md
├── 02-problem-definition.md
├── 03-research-questions.md
├── 04-methodology.md
├── 05-search-strategy.md
├── 06-source-matrix.csv
├── 07-source-notes.md
├── 08-data-notes.md
├── 09-claim-evidence-ledger.csv
├── 10-conflict-log.md
├── 11-analysis.md
├── 12-synthesis.md
├── 13-research-gap.md
├── 14-recommendations.md
├── 15-outline.md
├── 16-draft.md
├── 17-final-report.md
├── references.bib
├── assumptions.md
├── risk-register.md
├── validation-report.md
├── data/
│   ├── raw/
│   ├── processed/
│   └── README.md
├── diagrams/
│   ├── research-map.mmd
│   ├── research-map.png
│   ├── evidence-flow.mmd
│   ├── evidence-flow.png
│   ├── conceptual-model.mmd
│   └── conceptual-model.png
├── scripts/
├── outputs/
│   ├── final-report.docx
│   ├── final-report.pdf
│   ├── executive-summary.pdf
│   └── presentation.pptx
└── qa/
    ├── source-audit.md
    ├── citation-audit.md
    ├── claim-audit.md
    ├── adversarial-review.md
    └── visual-audit.md
```

Do not create `data/`, `diagrams/`, `scripts/`, or `outputs/` until the project will put real content there. Use `scripts/init_research_workspace.py` for the core files. It validates the slug, writes only under `<repository>/docs/research/`, and never overwrites existing work.

## Phase persistence

After each phase:

1. save findings to the owning artifact;
2. update README status and completion checklist;
3. record new assumptions and limitations;
4. add sources and claims immediately;
5. update conflicts and risks;
6. verify expected files and row counts.

When context becomes crowded, stop nonessential exploration, summarize into artifacts, remove duplicates from working context, and reload only the files needed for the next phase.

## Universal report

Adapt this structure to the research modes:

1. Cover: title, report type, author or `unknown`, organization or `unknown`, date, version.
2. Executive summary: problem, objective, method, findings, confidence, recommendations, limitations.
3. Introduction: background, scope, questions, significance.
4. Methodology: design, search, inclusion, exclusion, quality assessment, analysis, bias, limitations.
5. Context and definitions.
6. Findings organized by question or theme.
7. Comparative analysis when relevant.
8. Conflicting evidence.
9. Synthesis and uncertainty.
10. Research gaps.
11. Recommendations.
12. Implementation or next steps when relevant.
13. Risks and ethical considerations.
14. Limitations.
15. Conclusion proportional to evidence.
16. References.
17. Appendices for matrices, queries, dictionaries, tables, diagrams, and validation.

## Citation and bibliography

Use the requested citation style. Place citations next to the supported claim, add page or section locators when relevant, mark secondary citation, verify direct quotations, and include only sources read and used. Never invent DOI, ISBN, URL, author, title, date, page, or quote.

Keep `references.bib` synchronized with the final report. Audit missing citations, unused references, duplicates, metadata conflicts, citation concentration, circular citation, excessive secondary citation, outdated sources, and retractions.

## Diagrams and visualization

Create a diagram only when it materially clarifies relationships, sequences, hierarchy, architecture, evidence flow, risk, or comparison. Store editable Mermaid, PlantUML, Graphviz, or equivalent source plus rendered PNG or SVG, caption, evidence basis, and limitations.

Mark hypothetical links explicitly. Validate syntax, render at readable resolution, inspect the output, and verify files before claiming success. Never invent relationships to make a diagram look complete.

## Data artifacts

Keep raw and processed data separate. Add a dictionary with field, type, unit, source, meaning, missing-value policy, and transformations. Record source license, access date, exclusions, cleaning, dependencies, and reproducibility instructions in `data/README.md` and analysis scripts.

## DOCX, PDF, and presentation

Generate only requested formats after Markdown stabilizes.

- DOCX/PDF: consistent headings, table of contents when useful, captions, page numbers, readable citations, complete bibliography, working links, intentional page breaks, embedded fonts or safe fallbacks, and no overflow.
- Presentation: usually 10–20 slides covering title, problem, objective, method, evidence landscape, findings, conflicts, synthesis, recommendations, risks, limitations, next steps, and references.
- Render PDFs and slides to images when tooling permits. Inspect the cover, executive summary, methods, first page of each section, tables, diagrams, references, and last page for clipping, overflow, blank pages, broken characters, orphan headings, low resolution, and numbering errors.

## Compact final handoff

Do not paste the full report into terminal or chat. Return:

1. status and topic;
2. research modes;
3. main and subquestions;
4. methodology;
5. total, verified, excluded, and inaccessible sources;
6. overall evidence quality;
7. principal findings and conflicts;
8. gaps and recommendations;
9. confidence, limitations, and risks;
10. citation and adversarial-review status;
11. outputs created;
12. paths to final report, source matrix, claim ledger, and validation report.
