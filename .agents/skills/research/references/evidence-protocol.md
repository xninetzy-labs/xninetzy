# Evidence and analysis protocol

Use this reference to design searches, assess sources, extract data, build claims, resolve conflicts, and identify gaps.

## Contextual source hierarchy

1. **Tier 1 — Primary and authoritative:** original research and datasets, official documentation and repositories, standards, regulators, statutes, official judgments, government statistics, institutional reports, experiment reports, and primary archives.
2. **Tier 2 — High-quality synthesis:** systematic reviews, meta-analyses, consensus statements, guidelines, academic handbooks, and rigorous review papers.
3. **Tier 3 — Reputable secondary:** academic books, transparent industry reports, mature institutional analysis, engineering documentation, and well-described case studies.
4. **Tier 4 — Practitioner:** technical blogs, conference talks, tutorials, expert interviews, and specialist podcasts.
5. **Tier 5 — Exploratory:** forums, Reddit, social media, comments, opinion pieces, showcases, and personal blogs.

Tier is contextual, not an automatic quality score. Use Tier 5 to discover language, questions, pain points, experiences, and leads unless opinion or experience is itself the research object.

## Source-quality assessment

Rate each source High, Medium, Low, or Unclear across authority, primary versus secondary status, methodology, sample or dataset, transparency, reproducibility, recency, relevance, context match, conflict of interest, peer review, citation support, limitation disclosure, full-text accessibility, and metadata verification. Record the rationale. A large organization, prestigious venue, or high citation count does not automatically earn High.

## Search design

Build a concept table containing primary terms, synonyms, alternative spellings, abbreviations, historic terminology, technical terminology, local-language terms, and negative keywords. Record Boolean, broad, narrow, domain-filtered, date-filtered, and language-filtered queries.

Use staged passes:

1. foundational landscape;
2. current state;
3. primary and authoritative evidence;
4. direct core evidence;
5. opposing, negative, failure, and replication evidence;
6. implementation and evaluation evidence;
7. safety, ethics, legal, and operational risk evidence;
8. citation chaining and gap completion.

Search specifically for evidence that could falsify the initial hypothesis. Never use the search-result snippet as the sole basis for a material claim.

## Source record

For each candidate record:

`source_id, title, authors_or_organization, year, source_type, publisher_or_venue, doi, url, access_date, research_question, objective, method, sample_or_dataset, context, key_findings, limitations, conflict_of_interest, relevance, quality, full_text_status, verification_status, notes`

Before use, verify title, author or organization, date, venue, DOI or stable URL, version, relevant passage, methods, underlying data, limitations, and funding or conflicts where relevant. Prefer publisher, DOI registry, regulator, official repository, or official archive metadata when records disagree.

For abstract-only evidence, set `full_text_status=abstract-only`, avoid method or result details not present in the abstract, and reduce confidence accordingly.

## Statement taxonomy

- **Verified Fact:** supported by authoritative primary evidence or convergent credible sources.
- **Reported Claim:** attributed to a party but not independently verified.
- **Research Finding:** a result from a named method, sample or dataset, and context.
- **Synthesis:** a conclusion integrating multiple sources.
- **Inference:** a logical interpretation not directly stated by sources.
- **Hypothesis:** a testable proposition not yet established.
- **Proposal:** a suggested design or solution.
- **Recommendation:** an evidence-informed action under explicit constraints.
- **Uncertainty:** an unresolved lack of knowledge or precision.
- **Unresolved Conflict:** material evidence disagreement without justified resolution.

Do not force a label onto every sentence. Apply labels to material claims in the ledger and use prose markers where readers could otherwise confuse fact, inference, proposal, or uncertainty.

## Claim-evidence ledger

Use:

`claim_id, claim, claim_type, supporting_sources, opposing_sources, evidence_quality, context, confidence, uncertainty, status, target_section, review_notes`

Allowed status values are `supported`, `partially supported`, `disputed`, `unsupported`, `hypothesis`, `proposal`, and `excluded`. Material final-report claims must be traceable to ledger rows. A source may support several claims only if the inspected content genuinely supports each one.

## Data extraction and analysis

Preserve raw data unchanged. Record source, access time, license, dictionary, missing-value policy, exclusions, cleaning, transformations, units, dependency versions, and random seeds. Save executable scripts and calculation checks.

For quantitative work, assess distributions, effect size, uncertainty intervals, missingness, outliers, subgroups, sensitivity, and robustness as appropriate. Do not select a method only because it produces statistical significance.

For qualitative work, record the coding approach, theme construction, researcher interpretation, disagreements, evidence excerpts within copyright limits, and saturation limitations. Never fabricate interviews, participants, observations, or quotes.

## Conflict analysis

For each conflict record:

`conflict_id, issue, source_a, source_b, type_of_conflict, possible_explanation, evidence_assessment, resolution_status, impact_on_conclusion`

Test whether differences arise from definitions, populations, periods, locations, methods, datasets, sample sizes, measures, models, conflicts of interest, evidence quality, technology change, regulation change, or publication bias. Preserve unresolved conflicts and lower conclusion confidence when necessary.

## Gap validation

Classify gaps as knowledge, evidence, methodological, population, geographic, temporal, theoretical, implementation, evaluation, reproducibility, policy, or data gaps.

Before claiming a gap, search alternative terminology, trace citations backward and forward, inspect recent reviews, check relevant non-English sources, and state search boundaries. For each confirmed gap record evidence, importance, affected stakeholders, a researchable question, proposed method, and feasibility.

## Synthesis standard

For each theme answer:

1. what is known;
2. which evidence supports it;
3. how strong and transferable that evidence is;
4. which contexts it applies to;
5. what evidence conflicts;
6. plausible reasons for differences;
7. what remains unknown;
8. implications for the intended decision;
9. the next validation step.

Avoid serial summaries and simple vote counts. Weight evidence by quality, relevance, method, data, context, and uncertainty.
