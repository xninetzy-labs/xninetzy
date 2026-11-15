from __future__ import annotations

from xninetzy.context.routing.production import (
    CANARY_DEFAULT_SAMPLE_RATE,
    PROD_VERSION,
    ROLLOUT_PHASES,
    RolloutStage,
    RolloutState,
    _stage_transition_allowed,
    evaluate_rollout_promotion,
    write_state,
)
from xninetzy.context.routing.regression import (
    RegressionCheck,
    RegressionReport,
    RegressionStatus,
)


def _empty_state() -> RolloutState:
    return RolloutState(
        stage=RolloutStage.SHADOW,
        entered_at="2026-09-28T00:00:00+00:00",
        days_in_stage=0,
        canary_sample_rate=CANARY_DEFAULT_SAMPLE_RATE,
        shadow_days=14,
        canary_days=0,
        production_days=0,
        promotion_blocked=False,
    )


def test_version() -> None:
    assert PROD_VERSION == "1.0.0"
    assert len(ROLLOUT_PHASES) == 8


def test_legal_transitions() -> None:
    assert _stage_transition_allowed(RolloutStage.SHADOW, RolloutStage.CANARY)
    assert _stage_transition_allowed(RolloutStage.CANARY, RolloutStage.REGRESSION)
    assert _stage_transition_allowed(RolloutStage.APPROVED, RolloutStage.PRODUCTION)
    assert not _stage_transition_allowed(RolloutStage.SHADOW, RolloutStage.PRODUCTION)
    assert not _stage_transition_allowed(RolloutStage.DEPRECATED, RolloutStage.PRODUCTION)


def test_promotion_blocked_by_regression_failure() -> None:
    state = _empty_state()
    reg_report = RegressionReport(
        version="1.0.0",
        generated_at="2026-09-28T00:00:00+00:00",
        checks=(
            RegressionCheck(
                name="routing_quality",
                status=RegressionStatus.FAILED,
                observed="top1=0.0",
                threshold="≥0.7",
            ),
        ),
        overall=RegressionStatus.FAILED,
        block_reasons=("routing_quality: top1 below 0.7",),
    )
    req = evaluate_rollout_promotion(
        current_state=state,
        target_stage=RolloutStage.CANARY,
        regression_report=reg_report,
    )
    assert not req.approved
    assert any("regression" in r.lower() for r in req.block_reasons)


def test_promotion_blocked_by_insufficient_shadow_days() -> None:
    state = RolloutState(
        stage=RolloutStage.CANARY,
        entered_at="2026-09-28T00:00:00+00:00",
        days_in_stage=0,
        canary_sample_rate=0.1,
        shadow_days=0,
        canary_days=7,
        production_days=0,
        promotion_blocked=False,
    )
    reg_report = RegressionReport(
        version="1.0.0",
        generated_at="2026-09-28T00:00:00+00:00",
        checks=(),
        overall=RegressionStatus.PASSED,
    )
    req = evaluate_rollout_promotion(
        current_state=state,
        target_stage=RolloutStage.PRODUCTION,
        regression_report=reg_report,
    )
    assert not req.approved
    assert any("shadow" in r for r in req.block_reasons)


def test_promotion_allowed_when_all_gates_pass() -> None:
    state = RolloutState(
        stage=RolloutStage.APPROVED,
        entered_at="2026-09-28T00:00:00+00:00",
        days_in_stage=0,
        canary_sample_rate=0.1,
        shadow_days=14,
        canary_days=7,
        production_days=7,
        promotion_blocked=False,
    )
    reg_report = RegressionReport(
        version="1.0.0",
        generated_at="2026-09-28T00:00:00+00:00",
        checks=(),
        overall=RegressionStatus.PASSED,
    )
    req = evaluate_rollout_promotion(
        current_state=state,
        target_stage=RolloutStage.PRODUCTION,
        regression_report=reg_report,
    )
    assert req.approved
    assert not req.block_reasons


def test_state_serialization(tmp_path) -> None:
    state = _empty_state()
    path = write_state(state, tmp_path)
    import pathlib
    assert pathlib.Path(path).exists()
