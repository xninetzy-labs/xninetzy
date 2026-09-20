from __future__ import annotations

from xninetzy.context.evaluation.context_eval import evaluate_context
from xninetzy.context.evaluation.hallucination import (
    HALLUCINATION_LEVEL_CRITICAL,
    HALLUCINATION_LEVEL_NONE,
    detect_hallucination,
)
from xninetzy.context.evaluation.memory_eval import evaluate_memory
from xninetzy.context.evaluation.outcome import (
    OUTCOME_AUDIT_INCOMPLETE,
    OUTCOME_AUDIT_PASS,
    OUTCOME_AUDIT_PARTIAL,
    evaluate_outcome,
)
from xninetzy.context.evaluation.root_cause import (
    ROOT_CAUSE_CONFIDENCE_HIGH,
    ROOT_CAUSE_CONFIDENCE_LOW,
    analyze_root_cause,
)
from xninetzy.context.evaluation.routing_eval import evaluate_routing
from xninetzy.context.evaluation.scoring import (
    aggregate_scores,
    score_domain,
)
from xninetzy.context.evaluation.security_eval import (
    SECURITY_RISK_HIGH,
    SECURITY_RISK_LOW,
    SECURITY_RISK_MEDIUM,
    evaluate_security,
)
from xninetzy.context.evaluation.skill_eval import (
    SKILL_DEPRECATED,
    SKILL_EXCELLENT,
    SKILL_POOR,
    evaluate_skill,
)
from xninetzy.context.evaluation.tool_eval import (
    TOOL_MONITOR,
    TOOL_PROMOTE,
    TOOL_REMOVE,
    evaluate_tool,
)


def test_outcome_pass_when_match():
    audit = evaluate_outcome(objective="x", expected="ok", observed="ok")
    assert audit.verdict == OUTCOME_AUDIT_PASS


def test_outcome_partial_when_some_criteria_missed():
    audit = evaluate_outcome(
        objective="x",
        expected="ok",
        observed="ok",
        success_criteria=("a", "b", "c"),
        observed_criteria_hits=("a",),
    )
    assert audit.verdict == OUTCOME_AUDIT_PARTIAL


def test_outcome_incomplete_when_all_criteria_missed():
    audit = evaluate_outcome(
        objective="x",
        expected="ok",
        observed="ok",
        success_criteria=("a", "b"),
        observed_criteria_hits=(),
    )
    assert audit.verdict == OUTCOME_AUDIT_INCOMPLETE


def test_context_audit_metrics_computed():
    audit = evaluate_context(
        retrieved=("a", "b", "c"),
        relevant=("a", "b"),
        required=("a", "b", "d"),
        stale=("c",),
        duplicates=("b",),
    )
    assert audit.retrieved_count == 3
    assert audit.relevant_count == 2
    assert audit.stale_count == 1
    assert 0.0 < audit.precision <= 1.0


def test_context_audit_handles_empty_retrieval():
    audit = evaluate_context(
        retrieved=(),
        relevant=(),
        required=("x",),
    )
    assert audit.precision == 0.0
    assert audit.recall == 0.0


def test_memory_audit_detects_duplicates():
    memories = (
        {"id": "1", "usefulness": 0.9, "k": "v"},
        {"id": "2", "usefulness": 0.9, "k": "v"},
        {"id": "3", "usefulness": 0.1, "conflict": True},
    )
    audit = evaluate_memory(memories=memories)
    assert audit.duplicate_count == 1
    assert audit.conflicting_count == 1


def test_routing_suboptimal_when_alt_better():
    audit = evaluate_routing(
        chosen="a",
        candidates=("a", "b"),
        success_history={"a": 1, "b": 10},
        failure_history={"a": 9, "b": 1},
    )
    assert audit.suboptimal is True


def test_routing_not_suboptimal_when_chosen_known():
    audit = evaluate_routing(
        chosen="a",
        candidates=("a", "b"),
        success_history={"a": 10, "b": 1},
        failure_history={"a": 0, "b": 9},
    )
    assert audit.suboptimal is False


def test_skill_deprecated_when_never_invoked():
    audit = evaluate_skill(
        skill_name="x",
        invocation_count=0,
        success_count=0,
    )
    assert audit.verdict == SKILL_DEPRECATED


def test_skill_excellent_high_success_reuse():
    audit = evaluate_skill(
        skill_name="x",
        invocation_count=10,
        success_count=10,
        reuse_count=5,
    )
    assert audit.verdict == SKILL_EXCELLENT


def test_skill_poor_low_success():
    audit = evaluate_skill(
        skill_name="x",
        invocation_count=10,
        success_count=2,
    )
    assert audit.verdict == SKILL_POOR


def test_tool_promote_high_value():
    audit = evaluate_tool(
        tool_name="x",
        success_count=10,
        failure_count=1,
        avg_latency_ms=100.0,
    )
    assert audit.verdict == TOOL_PROMOTE


def test_tool_remove_low_success():
    audit = evaluate_tool(
        tool_name="x",
        success_count=1,
        failure_count=10,
        avg_latency_ms=200.0,
    )
    assert audit.verdict == TOOL_REMOVE


def test_tool_monitor_default():
    audit = evaluate_tool(
        tool_name="x",
        success_count=5,
        failure_count=3,
        avg_latency_ms=200.0,
    )
    assert audit.verdict == TOOL_MONITOR


def test_security_low_when_empty():
    audit = evaluate_security()
    assert audit.risk_level == SECURITY_RISK_LOW


def test_security_high_with_critical_indicator():
    audit = evaluate_security(triggered=("credential_leakage",))
    assert audit.risk_level == SECURITY_RISK_HIGH
    assert "redact secrets" in "; ".join(audit.mitigations)


def test_security_medium_with_moderate_indicator():
    audit = evaluate_security(triggered=("supply_chain",))
    assert audit.risk_level == SECURITY_RISK_MEDIUM


def test_hallucination_none_when_supported():
    audit = detect_hallucination(
        claims=("a", "b"),
        supported_refs={"0": ("ref-1",), "1": ("ref-2",)},
    )
    assert audit.level == HALLUCINATION_LEVEL_NONE


def test_hallucination_critical_when_many_unsupported():
    audit = detect_hallucination(
        claims=("a", "b", "c", "d", "e"),
        supported_refs={},
    )
    assert audit.level == HALLUCINATION_LEVEL_CRITICAL


def test_root_cause_high_with_multiple_evidence():
    analysis = analyze_root_cause(
        symptom="x",
        hypotheses=("h1", "h2"),
        evidence_refs=("e1", "e2", "e3"),
    )
    assert analysis.confidence == ROOT_CAUSE_CONFIDENCE_HIGH


def test_root_cause_low_with_no_evidence():
    analysis = analyze_root_cause(
        symptom="x",
        hypotheses=("h1",),
    )
    assert analysis.confidence == ROOT_CAUSE_CONFIDENCE_LOW


def test_root_cause_low_when_threshold_too_high():
    analysis = analyze_root_cause(
        symptom="x",
        hypotheses=("h1",),
        evidence_refs=("e1",),
        confidence_threshold=0.99,
    )
    assert analysis.confidence == ROOT_CAUSE_CONFIDENCE_LOW


def test_root_cause_empty_hypotheses():
    analysis = analyze_root_cause(
        symptom="x",
        hypotheses=(),
    )
    assert analysis.root_cause == "undetermined"


def test_score_domain_validates_range():
    score = score_domain(domain="x", score=0.5)
    assert score.weighted() == 0.5
    import pytest
    with pytest.raises(ValueError):
        score_domain(domain="x", score=1.5)


def test_score_domain_validates_weight():
    import pytest
    with pytest.raises(ValueError):
        score_domain(domain="x", score=0.5, weight=0.0)


def test_aggregate_scores_weighted():
    scores = (
        score_domain(domain="a", score=0.8, weight=2.0),
        score_domain(domain="b", score=0.4, weight=1.0),
    )
    agg = aggregate_scores(scores)
    expected = (0.8 * 2.0 + 0.4 * 1.0) / 3.0
    assert abs(agg.overall - expected) < 1e-6


def test_aggregate_scores_empty():
    agg = aggregate_scores(())
    assert agg.overall == 0.0
