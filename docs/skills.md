# Writing / Proposal / Academic / Consulting Skill Stack

22 native skills ship in this release, organized by intent class.

## Intent classes

`PROFESSIONAL`, `CONSULTING`, `PROPOSAL`, `ACADEMIC`, `RESEARCH`, `TECHNICAL`, `EDITING`, `REVIEW`.

## Skills

| Skill | Intent class | Purpose |
|---|---|---|
| professional-writer | PROFESSIONAL | Business/product/marketing/communication writing |
| executive-writer | PROFESSIONAL | 1-page summaries, exec memos, decision briefs |
| business-writer | PROFESSIONAL | Case studies, market analyses, business plans |
| technical-content-writer | TECHNICAL | Tutorials, READMEs, API explanations, runbooks |
| consultant | CONSULTING | MECE analysis, hypotheses, decision-oriented output |
| consultant-challenge | REVIEW | Stress-test consultant output |
| proposal-writer | PROPOSAL | Competitive proposals |
| competition-proposal | PROPOSAL | Rubric-optimized competition submissions |
| research-proposal | PROPOSAL | Thesis/grant research proposals |
| grant-proposal | PROPOSAL | Funder-aligned grant submissions |
| proposal-red-team | REVIEW | Adversarial proposal review |
| academic-writer | ACADEMIC | Academic text with citation discipline |
| research-paper-writer | ACADEMIC | IMRaD structure papers |
| scientific-paper-writer | ACADEMIC | Empirical scientific papers |
| literature-review-writer | ACADEMIC | Thematic literature synthesis |
| paper-review | REVIEW | Research paper critique |
| academic-editor | EDITING | Academic draft editing |
| professional-editor | EDITING | Professional draft editing |
| submission-readiness | REVIEW | Pre-submission checklist |
| anti-slop | REVIEW | Slop pattern removal pass |
| evidence-synthesis | RESEARCH | Multi-source evidence ledger |
| citation-validation | REVIEW | Citation existence + alignment check |
| source-evaluation | RESEARCH | Source authority + freshness grading |

## Routing

```python
from xninetzy.skills.router import route_request, pipeline_for_intent

result = route_request("write a literature review for my thesis")
# result.primary.skill_name = "literature-review-writer" or "academic-writer"

pipeline = pipeline_for_intent("ACADEMIC")
# ["literature-review-writer", "evidence-synthesis", "academic-writer", "citation-validation", "academic-editor", "paper-review"]
```

## Validation

```python
from xninetzy.skills.validators import anti_slop, citation_fidelity, requirement_coverage

anti_slop("In today's world, we dive deep into cutting-edge solutions.")
# ValidatorReport(passed=False, findings=[...])

citation_fidelity("X improves outcomes [smith2020].", valid_citations=["smith2020"])
# ValidatorReport(passed=True, findings=[])
```

## MCP tools

`skill_route`, `skill_compose`, `skill_validate_output`, `skill_validate_anti_slop`, `skill_validate_submission_readiness`, `skill_capabilities`.

## Skill frontmatter

All 22 skills expose an `intent_class` metadata field that drives routing. Composition pipelines are predefined per intent class.
