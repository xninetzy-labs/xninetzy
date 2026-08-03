from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, datetime
from pathlib import Path

SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SOURCE_HEADER = "source_id,title,authors_or_organization,year,source_type,publisher_or_venue,doi,url,access_date,research_question,objective,method,sample_or_dataset,context,key_findings,limitations,conflict_of_interest,relevance,quality,full_text_status,verification_status,notes\n"
CLAIM_HEADER = "claim_id,claim,claim_type,supporting_sources,opposing_sources,evidence_quality,context,confidence,uncertainty,status,target_section,review_notes\n"


def documents(title: str, slug: str, language: str) -> dict[str, str]:
    created_at = datetime.now(UTC).date().isoformat()
    status = "Not started"
    return {
        "README.md": f"# {title}\n\nStatus: Phase 0 initialized\n\nSlug: `{slug}`\n\nOutput language: {language}\n\nCreated: {created_at}\n\n## Progress\n\n- [ ] Tool audit\n- [ ] Problem definition\n- [ ] Research questions\n- [ ] Methodology\n- [ ] Search strategy\n- [ ] Source verification\n- [ ] Claim-evidence ledger\n- [ ] Analysis and synthesis\n- [ ] Adversarial review\n- [ ] Final report\n- [ ] Validation\n",
        "00-research-charter.md": f"# Research charter\n\n## Title\n\n{title}\n\n## Main question\n\nunknown\n\n## Objective\n\nunknown\n\n## Intended use\n\nunknown\n\n## Audience\n\nunknown\n\n## Scope and constraints\n\nunknown\n\n## Requested outputs\n\n- Markdown final report\n\n## Status\n\n{status}\n",
        "01-tool-audit.md": "# Tool audit\n\n| Tool or capability | Status | Purpose | Limitation | Fallback |\n|---|---|---|---|---|\n",
        "02-problem-definition.md": "# Problem definition\n\n## Problem statement\n\nunknown\n\n## Unit of analysis\n\nunknown\n\n## Stakeholders\n\nunknown\n\n## Scope\n\nunknown\n\n## Out of scope\n\nunknown\n\n## Decision supported\n\nunknown\n\n## Misinterpretation risks\n\nunknown\n",
        "03-research-questions.md": "# Research questions\n\n## Main question\n\nunknown\n\n## Subquestions\n\n1. unknown\n\n## Hypotheses\n\nNot applicable unless explicitly defined and testable.\n",
        "04-methodology.md": "# Methodology\n\n## Research modes\n\nunknown\n\n## Design and rationale\n\nunknown\n\n## Inclusion criteria\n\nunknown\n\n## Exclusion criteria\n\nunknown\n\n## Screening and extraction\n\nunknown\n\n## Quality assessment\n\nunknown\n\n## Analysis and synthesis\n\nunknown\n\n## Bias and limitations\n\nunknown\n",
        "05-search-strategy.md": "# Search strategy\n\n## Concepts and synonyms\n\nunknown\n\n## Queries\n\nunknown\n\n## Filters\n\nunknown\n\n## Opposing-evidence search\n\nunknown\n\n## Citation chaining\n\nunknown\n\n## Stop conditions\n\nunknown\n",
        "06-source-matrix.csv": SOURCE_HEADER,
        "07-source-notes.md": "# Verified source notes\n\nAdd a section per source after full-text or authoritative metadata inspection.\n",
        "08-data-notes.md": "# Data notes\n\nStatus: not applicable until data is acquired or analyzed.\n",
        "09-claim-evidence-ledger.csv": CLAIM_HEADER,
        "10-conflict-log.md": "# Conflict log\n\nNo conflicts assessed yet.\n",
        "11-analysis.md": "# Analysis\n\nAnalysis begins after verified extraction and claim mapping.\n",
        "12-synthesis.md": "# Synthesis\n\nSynthesis begins after analysis and conflict review.\n",
        "13-research-gap.md": "# Research gaps\n\nNo gap claim has been validated yet.\n",
        "14-recommendations.md": "# Recommendations\n\nRecommendations begin after evidence synthesis.\n",
        "15-outline.md": "# Report outline\n\nOutline begins after sufficient evidence coverage.\n",
        "16-draft.md": "# Draft\n\nDrafting begins after the source matrix and claim ledger support material findings.\n",
        "17-final-report.md": f"# {title}\n\nStatus: not final\n\nNo conclusion has been produced before evidence validation.\n",
        "references.bib": "",
        "assumptions.md": "# Assumptions and limitations\n\n## Working assumptions\n\n- unknown\n\n## Limitations\n\n- Research has not started.\n",
        "risk-register.md": "# Risk register\n\n| Risk | Stakeholder | Likelihood | Impact | Mitigation | Residual risk |\n|---|---|---|---|---|---|\n",
        "validation-report.md": "# Validation report\n\nStatus: not run\n\n## Scope validation\n\nNot assessed.\n\n## Tool validation\n\nNot assessed.\n\n## Source validation\n\nNot assessed.\n\n## Evidence validation\n\nNot assessed.\n\n## Citation validation\n\nNot assessed.\n\n## Data validation\n\nNot applicable unless data is used.\n\n## Diagram validation\n\nNot applicable unless diagrams are created.\n\n## Document validation\n\nNot assessed.\n\n## Adversarial review\n\nNot run.\n\n## Limitations\n\nResearch has not started.\n",
        "qa/source-audit.md": "# Source audit\n\nStatus: not run\n",
        "qa/citation-audit.md": "# Citation audit\n\nStatus: not run\n",
        "qa/claim-audit.md": "# Claim audit\n\nStatus: not run\n",
        "qa/adversarial-review.md": "# Adversarial review\n\nStatus: not run\n",
        "qa/visual-audit.md": "# Visual audit\n\nStatus: not applicable unless visual outputs are created.\n",
    }


def initialize(repository: Path, slug: str, title: str, language: str) -> dict[str, object]:
    if not repository.is_dir():
        raise ValueError(f"Repository does not exist or is not a directory: {repository}")
    if not SLUG_PATTERN.fullmatch(slug):
        raise ValueError("Slug must be lowercase kebab-case.")
    research_root = (repository / "docs" / "research").resolve()
    target = (research_root / slug).resolve()
    if target.parent != research_root:
        raise ValueError("Research target escapes docs/research.")
    target.mkdir(parents=True, exist_ok=True)
    created: list[str] = []
    skipped: list[str] = []
    for relative_path, content in documents(title, slug, language).items():
        destination = target / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        if destination.exists():
            skipped.append(relative_path)
            continue
        destination.write_text(content, encoding="utf-8")
        created.append(relative_path)
    return {"workspace": str(target), "created": created, "skipped": skipped}


def main() -> None:
    parser = argparse.ArgumentParser(description="Initialize an auditable research workspace.")
    parser.add_argument("--repository", required=True)
    parser.add_argument("--slug", required=True)
    parser.add_argument("--title", required=True)
    parser.add_argument("--output-language", default="Indonesian")
    args = parser.parse_args()
    result = initialize(
        Path(args.repository).expanduser().resolve(),
        args.slug.strip(),
        args.title.strip(),
        args.output_language.strip(),
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
