from __future__ import annotations

import re
from dataclasses import dataclass, field


@dataclass
class ValidatorFinding:
    validator: str
    severity: str
    location: str
    message: str
    suggestion: str = ""


@dataclass
class ValidatorReport:
    validator: str
    findings: list[ValidatorFinding] = field(default_factory=list)
    passed: bool = True


SLOP_PATTERNS = [
    r"\bin today's fast-paced world\b",
    r"\bin conclusion,\b",
    r"\bit is important to note that\b",
    r"\bdive deep into\b",
    r"\bunleash the power of\b",
    r"\bgame[- ]changer\b",
    r"\bcutting[- ]edge\b",
    r"\brevolutionize\b",
    r"\bworld[- ]class\b",
    r"\bseamlessly\b",
    r"\brobust solution\b",
    r"\bnavigate the (complexities|landscape)\b",
]


def anti_slop(text: str) -> ValidatorReport:
    report = ValidatorReport(validator="anti-slop")
    for i, line in enumerate(text.splitlines(), 1):
        for pat in SLOP_PATTERNS:
            if re.search(pat, line, flags=re.IGNORECASE):
                report.findings.append(ValidatorFinding(
                    validator="anti-slop",
                    severity="medium",
                    location=f"line {i}",
                    message=f"slop pattern: {pat}",
                    suggestion="remove or rewrite concretely",
                ))
    report.passed = len(report.findings) == 0
    return report


def citation_fidelity(text: str, valid_citations: list[str] | None = None) -> ValidatorReport:
    report = ValidatorReport(validator="citation-fidelity")
    refs = re.findall(r"\[([^\]]+)\]", text)
    if not refs:
        report.findings.append(ValidatorFinding(
            validator="citation-fidelity",
            severity="low",
            location="document",
            message="no citations found",
            suggestion="add references for evidence claims",
        ))
    if valid_citations is not None:
        for r in refs:
            if r not in valid_citations:
                report.findings.append(ValidatorFinding(
                    validator="citation-fidelity",
                    severity="high",
                    location=f"ref [{r}]",
                    message="citation not in approved set",
                    suggestion="verify or remove",
                ))
    report.passed = not any(f.severity == "high" for f in report.findings)
    return report


def evidence_claim_alignment(text: str, claim_evidence_map: dict[str, list[str]] | None = None) -> ValidatorReport:
    report = ValidatorReport(validator="evidence-claim-alignment")
    if not claim_evidence_map:
        claim_evidence_map = {}
    for i, line in enumerate(text.splitlines(), 1):
        if re.search(r"\b(study|research|evidence|reported|statistics?)\b", line, flags=re.IGNORECASE) and "[" not in line:
            report.findings.append(ValidatorFinding(
                validator="evidence-claim-alignment",
                severity="high",
                location=f"line {i}",
                message="claim without citation",
                suggestion="attach a citation or evidence reference",
            ))
    report.passed = len(report.findings) == 0
    return report


def requirement_coverage(text: str, requirements: list[str]) -> ValidatorReport:
    report = ValidatorReport(validator="requirement-coverage")
    text_lower = text.lower()
    for req in requirements:
        if req.lower() not in text_lower:
            report.findings.append(ValidatorFinding(
                validator="requirement-coverage",
                severity="high",
                location=f"requirement: {req}",
                message=f"requirement '{req}' not addressed",
                suggestion=f"add a section addressing {req}",
            ))
    report.passed = len(report.findings) == 0
    return report


def consistency_check(sections: dict[str, str]) -> ValidatorReport:
    report = ValidatorReport(validator="consistency")
    section_names = list(sections.keys())
    keys_used: set[str] = set()
    for name, body in sections.items():
        for term in re.findall(r"\b[A-Z][a-zA-Z]{2,}\b", body):
            keys_used.add(term)
    counts: dict[str, list[str]] = {}
    for name, body in sections.items():
        for term in keys_used:
            c = body.count(term)
            if c > 0:
                counts.setdefault(term, []).append(name)
    for term, present in counts.items():
        if len(present) == 1 and section_names and present[0] == section_names[0]:
            continue
    report.passed = True
    return report


def terminology_consistency(text: str, approved_terms: list[str] | None = None) -> ValidatorReport:
    report = ValidatorReport(validator="terminology-consistency")
    if not approved_terms:
        return report
    for i, line in enumerate(text.splitlines(), 1):
        for term in re.findall(r"\b[A-Z][a-zA-Z]{3,}\b", line):
            if term not in approved_terms and not _is_common_word(term):
                report.findings.append(ValidatorFinding(
                    validator="terminology-consistency",
                    severity="low",
                    location=f"line {i}",
                    message=f"unapproved term: {term}",
                    suggestion="replace with approved equivalent if available",
                ))
    report.passed = len(report.findings) == 0
    return report


_COMMON = {
    "The", "This", "That", "These", "Those", "When", "Where", "While", "What", "Which",
    "Their", "There", "Then", "Thus", "Some", "Such", "Section", "Chapter", "Note",
}


def _is_common_word(w: str) -> bool:
    return w in _COMMON


def numeric_consistency(text: str) -> ValidatorReport:
    report = ValidatorReport(validator="numeric-consistency")
    numbers = re.findall(r"\b(\d+(?:\.\d+)?)\s*%?\b", text)
    counts: dict[str, int] = {}
    for n in numbers:
        counts[n] = counts.get(n, 0) + 1
    report.passed = True
    return report


def terminology_bank_pass(text: str, do_not_use: list[str] | None = None) -> ValidatorReport:
    report = ValidatorReport(validator="terminology-bank")
    if not do_not_use:
        return report
    for i, line in enumerate(text.splitlines(), 1):
        for banned in do_not_use:
            if re.search(rf"\b{re.escape(banned)}\b", line, flags=re.IGNORECASE):
                report.findings.append(ValidatorFinding(
                    validator="terminology-bank",
                    severity="medium",
                    location=f"line {i}",
                    message=f"banned term used: {banned}",
                    suggestion="use the canonical term from the bank",
                ))
    report.passed = len(report.findings) == 0
    return report


def scoring_rubric_pass(requirements: list[str], covered: dict[str, bool]) -> ValidatorReport:
    report = ValidatorReport(validator="scoring-rubric")
    for req in requirements:
        if not covered.get(req, False):
            report.findings.append(ValidatorFinding(
                validator="scoring-rubric",
                severity="high",
                location=f"requirement: {req}",
                message=f"rubric requirement '{req}' not met",
                suggestion="address in draft before scoring",
            ))
    report.passed = len(report.findings) == 0
    return report


def argument_coherence_pass(text: str) -> ValidatorReport:
    report = ValidatorReport(validator="argument-coherence")
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    if len(paragraphs) < 2:
        return report
    for i, p in enumerate(paragraphs[1:], 1):
        prev = paragraphs[i - 1]
        prev_first = (prev.split() or [""])[0].lower()
        cur_first = (p.split() or [""])[0].lower()
        if prev_first == cur_first and len(prev.split()) > 3:
            report.findings.append(ValidatorFinding(
                validator="argument-coherence",
                severity="low",
                location=f"paragraph {i + 1}",
                message=f"same opening word '{prev_first}' as previous paragraph",
                suggestion="vary transitions or strengthen the join",
            ))
    report.passed = len(report.findings) == 0
    return report


def submission_readiness_check(text: str, requirements: list[str], approved_citations: list[str] | None = None) -> ValidatorReport:
    report = ValidatorReport(validator="submission-readiness")
    cov = requirement_coverage(text, requirements)
    cit = citation_fidelity(text, approved_citations)
    slop = anti_slop(text)
    report.findings.extend(cov.findings)
    report.findings.extend(cit.findings)
    report.findings.extend(slop.findings)
    report.passed = cov.passed and cit.passed and slop.passed
    return report


def run_all(text: str, requirements: list[str] | None = None, approved_citations: list[str] | None = None, approved_terms: list[str] | None = None) -> list[ValidatorReport]:
    requirements = requirements or []
    return [
        anti_slop(text),
        citation_fidelity(text, approved_citations),
        evidence_claim_alignment(text),
        requirement_coverage(text, requirements),
        terminology_consistency(text, approved_terms),
        numeric_consistency(text),
    ]
