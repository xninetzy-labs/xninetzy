from __future__ import annotations

import json
from pathlib import Path

import pytest

from xninetzy.context.capability_graph.graph import seed_from_registry
from xninetzy.context.gateway.registry import upsert_provider
from xninetzy.context.gateway.trust import (
    HEALTH_OK,
    TRANSPORT_STDIO,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_UNVERIFIED,
)
from xninetzy.context.evaluation.integration import (
    audit_outcome_label,
    build_evolution_proposal_from_cycle,
    build_invocation_summary,
    detect_invocation_patterns,
    evaluate_invocation_cycle,
    finalize_pending_ab_test,
    record_benchmark_for_cycle,
    summarize_tool_verdicts,
    synthesize_pattern_observations,
)
from xninetzy.context.evaluation.catalog_audit import (
    synthesize_catalog_report,
)
from xninetzy.context.evaluation.self_audit import build_self_audit
from xninetzy.context.invocation.contract import InvocationRequest
from xninetzy.context.learning.benchmark_engine import (
    LearningBenchmark,
    get_benchmark_registry,
    register_benchmark,
)
from xninetzy.context.learning.evolution_engine import (
    EvolutionProposal,
    reset_evolution,
)
from xninetzy.context.learning.experiment_engine import clear_tests
from xninetzy.context.orchestrator.invokable import (
    Invocable,
    InvocableResult,
    clear_invokable_registry,
    register_invokable,
)
from xninetzy.context.orchestrator.pipeline import (
    OUTCOME_OK,
    execute_invocation,
    execute_pipeline_with_evaluation,
)
from xninetzy.db.migrations import run_migrations


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "eval.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    clear_invokable_registry()
    clear_tests()
    reset_evolution()
    yield db_file
    clear_invokable_registry()
    clear_tests()
    reset_evolution()


class _StubInvocable(Invocable):
    def __init__(self, provider_id, payload=None):
        self.provider_id = provider_id
        self._payload = payload

    def invoke(self, capability, args):
        return InvocableResult(payload=self._payload, latency_ms=10)

    def is_healthy(self):
        return True


def _seed_provider(provider_id: str, trust_tier: int):
    upsert_provider(
        provider_id=provider_id,
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=trust_tier,
        risk_class="low" if trust_tier == TRUST_TIER_KNOWN_EXTERNAL else "unreviewed",
        capabilities=("do_thing",),
        health_state=HEALTH_OK,
    )


def _request(**overrides) -> InvocationRequest:
    base = dict(
        request_id="req-1",
        intent="x",
        capability="do_thing",
        context_key="ctx",
        query="",
        args=(("k", "v"),),
        side_effect="read_only",
        idempotency_key=None,
        approval_id=None,
    )
    base.update(overrides)
    return InvocationRequest(**base)


def test_audit_outcome_label_mapping():
    assert audit_outcome_label("ok") == "pass"
    assert audit_outcome_label("error") == "partial"
    assert audit_outcome_label("blocked") == "incomplete"
    assert audit_outcome_label("critic_fail") == "misleading"
    assert audit_outcome_label(None) == "incomplete"
    assert audit_outcome_label("unknown") == "partial"


def test_build_invocation_summary_uses_expected_policy_gate():
    summary = build_invocation_summary(
        request_id="r1",
        provider_id="p",
        capability="c",
        audit_outcome="blocked",
        latency_ms=5,
        error="denied",
    )
    assert summary.expected == "policy_gate"


def test_build_invocation_summary_uses_expected_ok_for_normal():
    summary = build_invocation_summary(
        request_id="r2",
        provider_id="p",
        capability="c",
        audit_outcome="ok",
        latency_ms=5,
        error=None,
    )
    assert summary.expected == "ok"
    assert summary.outcome_label == "pass"


def test_evaluate_invocation_cycle_aggregates():
    summaries = (
        build_invocation_summary(
            request_id="r1",
            provider_id="p",
            capability="c1",
            audit_outcome="ok",
            latency_ms=10,
            error=None,
        ),
        build_invocation_summary(
            request_id="r2",
            provider_id="p",
            capability="c2",
            audit_outcome="error",
            latency_ms=20,
            error="x",
        ),
    )
    cycle = evaluate_invocation_cycle(summaries=summaries)
    assert cycle.audit_report.overall.score >= 0.0
    assert cycle.quality_scores.overall > 0.0
    assert cycle.learning_signals.signals != ()


def test_evaluate_invocation_cycle_marks_security_high():
    summaries = (
        build_invocation_summary(
            request_id="r1",
            provider_id="p",
            capability="c",
            audit_outcome="ok",
            latency_ms=10,
            error=None,
        ),
    )
    cycle = evaluate_invocation_cycle(
        summaries=summaries,
        security_indicators=("credential_leakage",),
    )
    assert any("security" in n.lower() for n in cycle.notes)


def test_bridge_persists_signal_episodes_to_memory():
    from xninetzy.context.evaluation.learning_bridge import (
        persist_signal_episodes,
    )
    from xninetzy.context.evaluation.signal_gen import extract_signals
    batch = extract_signals(
        findings=(
            {"source": "do_thing", "summary": "ok", "confidence": 0.9, "evidence_refs": ("r1",)},
            {"source": "do_thing", "summary": "weak", "confidence": 0.5, "evidence_refs": ("r2",)},
            {"source": "do_thing", "summary": "ignore", "confidence": 0.1, "evidence_refs": ("r3",)},
        ),
    )
    persisted = persist_signal_episodes(
        cycle_owner="local",
        cycle_id="cycle-test-1",
        batch=batch,
        related_capabilities=("do_thing",),
    )
    assert len(persisted) == 2


def test_bridge_creates_lightning_proposal_on_high_failure_rate():
    from xninetzy.context.evaluation.learning_bridge import (
        bridge_cycle_to_learning,
    )
    from xninetzy.context.evaluation.signal_gen import extract_signals
    batch = extract_signals(
        findings=(
            {"source": "c", "summary": "ok", "confidence": 0.9, "evidence_refs": ("r1",)},
        ),
    )
    result = bridge_cycle_to_learning(
        cycle_owner="local",
        cycle_id="cycle-test-fail",
        batch=batch,
        error_rate=0.8,
        block_rate=0.0,
        overall_quality=0.2,
        related_capabilities=("c",),
    )
    assert len(result.persisted_episode_ids) >= 1


def test_bridge_skips_proposal_when_quality_is_high():
    from xninetzy.context.evaluation.learning_bridge import (
        bridge_cycle_to_learning,
    )
    from xninetzy.context.evaluation.signal_gen import extract_signals
    batch = extract_signals(
        findings=(
            {"source": "c", "summary": "ok", "confidence": 0.9, "evidence_refs": ("r1",)},
        ),
    )
    result = bridge_cycle_to_learning(
        cycle_owner="local",
        cycle_id="cycle-test-pass",
        batch=batch,
        error_rate=0.0,
        block_rate=0.0,
        overall_quality=0.9,
        related_capabilities=("c",),
    )
    assert result.lightning_proposal_ids == ()


def test_execute_pipeline_with_evaluation_emits_bridge():
    _seed_provider("known-x", TRUST_TIER_KNOWN_EXTERNAL)
    register_invokable(
        "known-x",
        _StubInvocable("known-x", payload={"ok": True}),
    )
    req = _request(request_id="r-bridge-1")
    result = execute_pipeline_with_evaluation(requests=[req])
    assert "bridge" in result


def test_synthesize_pattern_observations_providers_categories():
    summaries = (
        build_invocation_summary(
            request_id="r1",
            provider_id="pA",
            capability="do_thing",
            audit_outcome="ok",
            latency_ms=10,
            error=None,
        ),
        build_invocation_summary(
            request_id="r2",
            provider_id="pA",
            capability="do_thing",
            audit_outcome="ok",
            latency_ms=10,
            error=None,
        ),
    )
    observations = synthesize_pattern_observations(summaries=summaries)
    assert len(observations) == 2
    assert observations[0]["context_key"] == "pA"


def test_detect_invocation_patterns_finds_success_cluster():
    summaries = tuple(
        build_invocation_summary(
            request_id=f"r{i}",
            provider_id="pA",
            capability="do_thing",
            audit_outcome="ok",
            latency_ms=10,
            error=None,
        )
        for i in range(5)
    )
    signals = detect_invocation_patterns(
        summaries=summaries,
        min_frequency=3,
    )
    assert any(s.pattern_type == "success" for s in signals)


def test_build_evolution_proposal_from_cycle_creates_valid():
    cycle = evaluate_invocation_cycle(
        summaries=(
            build_invocation_summary(
                request_id="r1",
                provider_id="p",
                capability="c",
                audit_outcome="error",
                latency_ms=10,
                error="x",
            ),
        ),
    )
    proposal: EvolutionProposal = build_evolution_proposal_from_cycle(
        proposal_id="p1",
        cycle=cycle,
        confidence=0.8,
    )
    assert "failed" in proposal.problem.lower() or "blocked" in proposal.problem.lower()
    assert proposal.confidence == 0.8


def test_record_benchmark_for_cycle_returns_none_when_zero():
    cycle = evaluate_invocation_cycle(summaries=())
    result = record_benchmark_for_cycle(
        name="x",
        cycle=cycle,
        last_run_at="2026-01-01",
    )
    assert result is None


def test_record_benchmark_for_cycle_creates_entry():
    register_benchmark(
        name="quality",
        category="system",
        description="x",
        target_metrics=("overall",),
    )
    cycle = evaluate_invocation_cycle(
        summaries=(
            build_invocation_summary(
                request_id="r1",
                provider_id="p",
                capability="c",
                audit_outcome="ok",
                latency_ms=10,
                error=None,
            ),
        ),
    )
    result: LearningBenchmark | None = record_benchmark_for_cycle(
        name="quality",
        cycle=cycle,
        last_run_at="2026-01-01",
    )
    assert result is not None
    assert result.last_score is not None
    assert get_benchmark_registry().get("quality") is not None


def test_finalize_pending_ab_test_returns_result():
    create_ab_test = __import__(
        "xninetzy.context.learning.experiment_engine",
        fromlist=["create_ab_test", "record_observation", "ExperimentOutcome"],
    )
    test = create_ab_test.create_ab_test(
        test_id="t1",
        baseline="a",
        candidate="b",
        metric_name="acc",
    )
    for v in (0.5, 0.6, 0.7):
        create_ab_test.record_observation(
            test_id="t1",
            outcome=create_ab_test.ExperimentOutcome(
                variant="a",
                metric_value=v,
                sample_size=1,
            ),
        )
    for v in (0.7, 0.8, 0.9):
        create_ab_test.record_observation(
            test_id="t1",
            outcome=create_ab_test.ExperimentOutcome(
                variant="b",
                metric_value=v,
                sample_size=1,
            ),
        )
    result = finalize_pending_ab_test(test_id="t1", min_samples=5)
    assert result.winner == "b"


def test_summarize_tool_verdicts_classifies():
    metrics = {
        "good": {"success": 10, "failure": 1, "avg_latency_ms": 100.0, "cost_score": 0.3, "security_risk": 0.0},
        "bad": {"success": 1, "failure": 10, "avg_latency_ms": 100.0, "cost_score": 0.3, "security_risk": 0.0},
        "expensive": {"success": 8, "failure": 1, "avg_latency_ms": 4000.0, "cost_score": 0.9, "security_risk": 0.0},
    }
    verdicts = summarize_tool_verdicts(tool_metrics=metrics)
    assert verdicts["good"] == "promote"
    assert verdicts["bad"] == "remove"
    assert verdicts["expensive"] == "demote"


def test_synthesize_catalog_report_groups_promote_remove():
    metrics = {
        "good": {"success": 10, "failure": 1, "avg_latency_ms": 100.0},
        "bad": {"success": 1, "failure": 10, "avg_latency_ms": 100.0},
    }
    report = synthesize_catalog_report(tool_metrics=metrics)
    assert "good" in report.promote_tools
    assert "bad" in report.remove_tools


def test_execute_pipeline_with_evaluation_returns_cycle():
    _seed_provider("known-x", TRUST_TIER_KNOWN_EXTERNAL)
    register_invokable(
        "known-x",
        _StubInvocable("known-x", payload={"ok": True}),
    )
    req = _request(request_id="r-cycle-1")
    result = execute_pipeline_with_evaluation(requests=[req])
    cycle = result["cycle"]
    assert cycle.audit_report is not None
    assert cycle.quality_scores is not None
    assert cycle.learning_signals is not None


def test_execute_pipeline_with_evaluation_security_pass_through():
    _seed_provider("known-x", TRUST_TIER_KNOWN_EXTERNAL)
    register_invokable(
        "known-x",
        _StubInvocable("known-x", payload={"ok": True}),
    )
    req = _request(request_id="r-sec")
    result = execute_pipeline_with_evaluation(
        requests=[req],
        security_indicators=("unsafe_execution",),
    )
    cycle = result["cycle"]
    assert "unsafe_execution" in cycle.security_indicators


def test_self_audit_reports_layers():
    snapshot = build_self_audit()
    assert snapshot.total_tools > 0
    assert snapshot.total_groups > 0
    assert len(snapshot.evaluation_layers) >= 15
    assert len(snapshot.learning_engines) == 5
    assert "depth" in snapshot.reasoning_modules
    assert "critic" in snapshot.reasoning_modules
    assert "stop" in snapshot.reasoning_modules
    assert len(snapshot.evaluation_files) >= 15
    assert len(snapshot.learning_files) == 6


def test_invocation_outcome_mapping_pipeline():
    _seed_provider("unverified-x", TRUST_TIER_UNVERIFIED)
    register_invokable(
        "unverified-x",
        _StubInvocable("unverified-x", payload={"ok": True}),
    )
    req = _request(request_id="r-outcome")
    outcome = execute_invocation(req)
    assert outcome.result.outcome == OUTCOME_OK
    summary = build_invocation_summary(
        request_id=outcome.audit.request_id,
        provider_id=outcome.audit.provider_id,
        capability=outcome.audit.capability,
        audit_outcome=outcome.audit.outcome,
        latency_ms=outcome.audit.latency_ms,
        error=outcome.audit.error,
    )
    assert summary.outcome_label == "pass"


def test_invocation_outcome_mapping_error():
    summary = build_invocation_summary(
        request_id="r",
        provider_id="p",
        capability="c",
        audit_outcome="error",
        latency_ms=10,
        error="boom",
    )
    assert summary.outcome_label == "partial"


def test_invocation_outcome_mapping_replan():
    summary = build_invocation_summary(
        request_id="r",
        provider_id="p",
        capability="c",
        audit_outcome="replan",
        latency_ms=10,
        error=None,
    )
    assert summary.outcome_label == "partial"
