from xninetzy.skills.validators import (
    anti_slop,
    argument_coherence_pass,
    citation_fidelity,
    evidence_claim_alignment,
    requirement_coverage,
    run_all,
    scoring_rubric_pass,
    submission_readiness_check,
    terminology_bank_pass,
    terminology_consistency,
)


def test_anti_slop_clean() -> None:
    text = "We reduced latency by 40% after deploying the new index."
    r = anti_slop(text)
    assert r.passed


def test_anti_slop_flags_pattern() -> None:
    text = "In today's fast-paced world, we must dive deep into cutting-edge solutions."
    r = anti_slop(text)
    assert not r.passed
    assert len(r.findings) >= 2


def test_citation_fidelity_orphan() -> None:
    r = citation_fidelity("Studies show X improves outcomes.", valid_citations=["smith2020"])
    assert r.passed


def test_citation_fidelity_unapproved() -> None:
    r = citation_fidelity("Studies show X [unknown2025].", valid_citations=["smith2020"])
    assert not r.passed


def test_evidence_claim_alignment_missing_citation() -> None:
    text = "Research shows that the treatment is effective."
    r = evidence_claim_alignment(text)
    assert not r.passed


def test_requirement_coverage_pass() -> None:
    text = "This proposal addresses scalability, cost, and reliability."
    r = requirement_coverage(text, ["scalability", "cost", "reliability"])
    assert r.passed


def test_requirement_coverage_fail() -> None:
    text = "We address scalability and cost."
    r = requirement_coverage(text, ["scalability", "cost", "reliability"])
    assert not r.passed


def test_terminology_consistency_approved_only() -> None:
    text = "The System processes input."
    r = terminology_consistency(text, approved_terms=["System", "Input"])
    assert r.passed


def test_run_all() -> None:
    text = "Scalability and cost are addressed [smith2020]."
    reports = run_all(text, ["scalability", "cost"], ["smith2020"], ["Scalability"])
    assert all(r.passed for r in reports)


def test_submission_readiness_combined() -> None:
    text = "In today's world, research shows X [smith2020]."
    r = submission_readiness_check(text, ["scalability"], ["smith2020"])
    assert not r.passed


def test_terminology_bank_pass_clean() -> None:
    r = terminology_bank_pass("We use machine learning throughout.", do_not_use=["AI engine"])
    assert r.passed


def test_terminology_bank_pass_flags() -> None:
    r = terminology_bank_pass("Our AI engine solves it.", do_not_use=["AI engine"])
    assert not r.passed


def test_scoring_rubric_pass_complete() -> None:
    r = scoring_rubric_pass(["innovation", "feasibility"], {"innovation": True, "feasibility": True})
    assert r.passed


def test_scoring_rubric_pass_incomplete() -> None:
    r = scoring_rubric_pass(["innovation", "feasibility"], {"innovation": True})
    assert not r.passed


def test_argument_coherence_pass_single_paragraph() -> None:
    r = argument_coherence_pass("Single paragraph body.")
    assert r.passed


def test_argument_coherence_pass_flags_repeat_opener() -> None:
    text = "First we analyze the data.\n\nFirst the analysis reveals trends.\n\nNext steps follow."
    r = argument_coherence_pass(text)
    assert any("same opening word" in f.message for f in r.findings)
