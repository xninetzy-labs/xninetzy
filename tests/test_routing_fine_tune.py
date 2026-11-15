from __future__ import annotations

from xninetzy.context.routing.fine_tune import (
    FINE_TUNE_VERSION,
    GateStatus,
    evaluate_fine_tune_gates,
    write_proposal,
)


def test_version_constant() -> None:
    assert FINE_TUNE_VERSION == "1.0.0"


def test_evaluate_with_no_data_returns_deferred() -> None:
    proposal = evaluate_fine_tune_gates(
        owner_approved=None,
        gpu_available=None,
    )
    assert proposal.overall == GateStatus.DEFERRED
    assert proposal.gates
    assert any(g.status in (GateStatus.PENDING, GateStatus.DEFERRED) for g in proposal.gates)


def test_evaluate_with_minimal_blocking_returns_failed() -> None:
    proposal = evaluate_fine_tune_gates(
        benchmark_top1=0.5,
        benchmark_topk=0.6,
        benchmark_test_n=10,
        owner_approved=False,
        gpu_available=False,
        p95_latency_ms=200.0,
    )
    assert proposal.overall == GateStatus.FAILED
    assert len(proposal.blocked_reasons) > 0


def test_evaluate_with_all_passing(tmp_path) -> None:
    from xninetzy.context.routing.calibration import CalibrationRecord, CalibrationRegistry

    reg = CalibrationRegistry(storage_dir=tmp_path / "cal")
    for layer in ("L2_domain", "L3_skill", "L4_task", "L5_capability", "L5_tool"):
        for domain in ("research", "academic", "career"):
            reg.register(
                CalibrationRecord(
                    layer=layer,
                    domain=domain,
                    coefficients=(1.0, 0.0),
                    n_samples=200,
                    ece=0.04,
                    brier=0.08,
                    trained_at="2026-09-28T00:00:00+00:00",
                    train_split_hash="abc",
                )
            )

    proposal = evaluate_fine_tune_gates(
        benchmark_top1=0.95,
        benchmark_topk=0.95,
        benchmark_test_n=300,
        top5_recall=0.96,
        hard_negative_report={"research_knowledge": {"accuracy": 1.0, "n": 20, "positive_hit": 20, "missed": 0}},
        shadow_decisions=[{"agreement_top1": True, "agreement_topk": 3, "latency_new_ms": 5.0}] * 50,
        shadow_days_observed=14,
        owner_approved=True,
        gpu_available=True,
        p95_latency_ms=20.0,
        final_action_rate=0.01,
        calibration_dir=str(tmp_path / "cal"),
    )
    assert proposal.overall == GateStatus.PASSED
    assert not proposal.blocked_reasons


def test_write_proposal_creates_file(tmp_path) -> None:
    proposal = evaluate_fine_tune_gates()
    path = write_proposal(proposal, tmp_path)
    import pathlib

    assert pathlib.Path(path).exists()
