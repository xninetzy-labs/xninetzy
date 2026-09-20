from __future__ import annotations

from xninetzy.context.reasoning.critic import (
    CRITIC_SEVERITY_BLOCKER,
    CRITIC_SEVERITY_WARNING,
    CRITIC_VERDICT_FAIL,
    CRITIC_VERDICT_PASS,
    CRITIC_VERDICT_WARN,
    critique_outcome,
)


def test_critique_passes_when_expected_matches_actual():
    verdict = critique_outcome(expected="ok", actual="ok")
    assert verdict.verdict == CRITIC_VERDICT_PASS
    assert verdict.is_passing is True
    assert verdict.has_blocker is False
    assert verdict.defects == ()


def test_critique_fails_on_expectation_mismatch():
    verdict = critique_outcome(expected="ok", actual="error")
    assert verdict.verdict == CRITIC_VERDICT_FAIL
    assert verdict.has_blocker is True
    assert any(d.code == "EXPECTATION_MISMATCH" for d in verdict.defects)


def test_critique_warns_on_unsupported_claim():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        claims=("the system probably works",),
    )
    assert verdict.verdict == CRITIC_VERDICT_WARN
    assert any(d.code.startswith("UNSUPPORTED_CLAIM") for d in verdict.defects)


def test_critique_warns_on_empty_claim():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        claims=("", "valid claim"),
    )
    assert verdict.verdict == CRITIC_VERDICT_WARN
    assert any(d.code.startswith("EMPTY_CLAIM") for d in verdict.defects)


def test_critique_fails_on_missing_evidence_code():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        missing_evidence_codes=("PRIMARY_SOURCE",),
    )
    assert verdict.verdict == CRITIC_VERDICT_FAIL
    assert any(d.code == "MISSING_EVIDENCE_PRIMARY_SOURCE" for d in verdict.defects)


def test_critique_fails_on_contradiction():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        contradictions=("claim A contradicts claim B",),
    )
    assert verdict.verdict == CRITIC_VERDICT_FAIL
    assert any(d.code == "CONTRADICTION" for d in verdict.defects)


def test_critique_blocker_severity_assigned():
    verdict = critique_outcome(expected="ok", actual="error")
    assert verdict.defects[0].severity == CRITIC_SEVERITY_BLOCKER


def test_critique_warning_severity_assigned():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        claims=("maybe this works",),
    )
    assert verdict.defects[0].severity == CRITIC_SEVERITY_WARNING


def test_critique_checked_claims_preserved():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        claims=("a", "b", "c"),
    )
    assert verdict.checked_claims == ("a", "b", "c")


def test_critique_notes_preserved():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        notes=("depth=routine", "context=ctx"),
    )
    assert "depth=routine" in verdict.notes


def test_critique_to_dict_structure():
    verdict = critique_outcome(expected="ok", actual="ok")
    data = verdict.to_dict()
    assert data["verdict"] == "pass"
    assert data["defects"] == []
    assert data["checked_claims"] == []


def test_critique_defect_to_dict_includes_refs():
    verdict = critique_outcome(
        expected="ok",
        actual="ok",
        evidence_ids=("src-1", "src-2"),
        missing_evidence_codes=("AUDIT_LOG",),
    )
    defect = verdict.defects[0]
    data = defect.to_dict()
    assert data["code"] == "MISSING_EVIDENCE_AUDIT_LOG"
    assert data["severity"] == CRITIC_SEVERITY_BLOCKER
    assert "src-1" in data["evidence_refs"]
