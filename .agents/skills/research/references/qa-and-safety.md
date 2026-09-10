# Quality, validation, ethics, and safety

Use this reference before finalizing any research project and throughout high-stakes research.

## Independent adversarial review

Review the stable draft to find defects, not to improve its style. Test for:

- fabricated or unverifiable sources, metadata, data, quotes, and results;
- unsupported claims and citation mismatch;
- confirmation, selection, and publication bias;
- correlation presented as causation;
- overgeneralization and invalid comparison;
- missing negative or opposing evidence;
- outdated or superseded information;
- weak or mislabeled methodology;
- misleading statistics or absent denominators and baselines;
- hidden assumptions and missing uncertainty;
- scope drift, ambiguous definitions, and internal contradiction;
- recommendations without evidence, feasibility, owner, metric, or fallback;
- missing stakeholders, ethical risks, or affected vulnerable groups;
- conclusions stronger than the underlying evidence.

For every issue record `issue_id`, severity, location, issue, evidence, impact, correction, resolution, and remaining risk. Resolve critical issues before the final report. Update the claim ledger, source matrix, limitations, and citation audit after revisions.

## Source audit

For every final source verify:

1. title, authors or organization, date, venue, URL or DOI, and version;
2. full-text or abstract-only status;
3. the exact content supporting each linked claim;
4. methods, sample or dataset, limitations, and funding or conflicts when relevant;
5. current status, including corrections, retraction, withdrawal, supersession, or outdated guidance.

Record excluded sources and exclusion reasons. Do not report an inaccessible source as fully reviewed.

## Claim audit

Reconcile the report with the claim ledger. Count supported, partially supported, disputed, unsupported, hypotheses, proposals, recommendations, and excluded claims. Remove or relabel unsupported material. Check that confidence reflects the weakest decisive evidence and that context limitations travel with the claim.

## Citation audit

Check every material factual statement and research finding for a nearby supporting citation. Verify references exist, metadata matches the inspected source, locators are accurate, and direct quotations comply with copyright limits. Detect unused entries, missing entries, duplicates, circular support, and overreliance on one source or secondary summaries.

## Validation report

`validation-report.md` must include:

1. scope validation: main question, final scope, scope changes, unresolved questions;
2. tool validation: tools used, failed, disabled, fallbacks, and limitations;
3. source validation: total, primary, secondary, peer-reviewed, official, inaccessible, excluded, outdated, and disputed sources;
4. evidence validation: claim-status counts, hypotheses, proposals, and removed unsupported claims;
5. citation validation: citation count, missing and unused references, duplicates, metadata conflicts, invalid DOI or URL;
6. data validation when relevant: raw data, processing, missingness, scripts, reproducibility, calculation checks;
7. diagram validation when relevant: source, syntax, render, visual inspection, limitations;
8. document validation: requested formats, page or slide counts, tables, figures, references, and preview results;
9. adversarial review: issues found, resolved, and residual risks;
10. candid limitations.

Do not claim a zero count unless it was actually checked. Use `not assessed` or `not applicable` with a reason when necessary.

## Ethics, privacy, and safety review

Assess privacy, consent, necessity of personal data, sensitive data, discrimination, bias, vulnerable groups, dual use, misuse, security, environmental cost, conflicts of interest, stakeholder harm, legal constraints, and reputational risk.

Collect no personal data that is unnecessary. Redact or anonymize sensitive data, never write secrets or session material to artifacts, and respect source licenses and access controls. Raise the evidence threshold for consequential decisions and recommend qualified professional validation where legal, medical, financial, safety, or policy interpretation exceeds the available evidence.

## Reproducibility review

Confirm another researcher can reconstruct:

- configuration and working assumptions;
- exact search terms, sources, filters, dates, and screening logic;
- source metadata and access status;
- extraction and quality decisions;
- data transformations, scripts, dependencies, and seeds;
- claim-to-source mappings;
- conflict and gap decisions;
- document and diagram generation steps.

Record what cannot be reproduced because of unavailable tools, dynamic pages, deleted sources, proprietary access, privacy restrictions, or time constraints.

## Completion checklist

Complete or explicitly mark not applicable:

- research charter and problem definition;
- research questions, methodology, and search strategy;
- source matrix, verified notes, and bibliography;
- claim ledger and conflict analysis;
- analysis, synthesis, gaps, and evidence-linked recommendations;
- assumptions, limitations, and risk register;
- source, claim, citation, adversarial, visual, and document audits;
- requested reports, datasets, diagrams, and office formats;
- validation report and exact output paths.

The work is not complete if critical review findings remain unresolved, promised files do not exist, citations are unverified, or the conclusion exceeds the evidence.
