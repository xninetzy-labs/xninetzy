from __future__ import annotations

import pytest

from xninetzy.context.learning.experiment_engine import (
    ExperimentOutcome,
    create_ab_test,
    finalize_test,
    record_observation,
)
from xninetzy.context.learning.statistics import (
    delta_with_confidence,
    welch_t,
    wilson_score,
)


def test_wilson_score_perfect():
    assert wilson_score(50, 50) == pytest.approx(0.9286, abs=0.001)


def test_wilson_score_no_trials():
    assert wilson_score(0, 0) == 0.0


def test_wilson_score_zero_successes():
    assert wilson_score(0, 100) == 0.0


def test_wilson_score_full_successes():
    assert wilson_score(100, 100) == pytest.approx(0.9630, abs=0.001)


def test_welch_t_insufficient_samples():
    t, p = welch_t((0.5,), (0.9,))
    assert t == 0.0 and p == 1.0


def test_welch_t_significant_difference():
    baseline = (0.5, 0.5, 0.5, 0.5, 0.5)
    candidate = (0.9, 0.9, 0.9, 0.9, 0.9)
    t, p = welch_t(baseline, candidate)
    assert p < 0.001


def test_welch_t_no_difference():
    baseline = (0.5, 0.6, 0.4, 0.5, 0.5)
    candidate = (0.5, 0.6, 0.4, 0.5, 0.5)
    t, p = welch_t(baseline, candidate)
    assert p > 0.5


def test_delta_with_confidence_significant():
    baseline = (0.5, 0.5, 0.5, 0.5, 0.5, 0.5)
    candidate = (0.9, 0.9, 0.9, 0.9, 0.9, 0.9)
    stat = delta_with_confidence(baseline, candidate, higher_is_better=True, baseline_name="a", candidate_name="b")
    assert stat["winner"] == "b"
    assert stat["significant"] is True
    assert stat["delta"] == pytest.approx(0.4, abs=0.01)


def test_delta_with_confidence_no_significant_difference():
    baseline = (0.5, 0.5, 0.5)
    candidate = (0.5, 0.5, 0.5)
    stat = delta_with_confidence(baseline, candidate, higher_is_better=True, baseline_name="a", candidate_name="b")
    assert stat["winner"] is None
    assert stat["significant"] is False


def test_finalize_test_rejects_insufficient_samples():
    test = create_ab_test(
        test_id="wt1",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    record_observation(
        test_id="wt1",
        outcome=ExperimentOutcome(variant="a", metric_value=0.5, sample_size=1),
    )
    result = finalize_test(test_id="wt1", min_samples=5)
    assert result.winner is None
    assert "insufficient" in str(result.notes)


def test_finalize_test_welch_significant_accepts_candidate():
    create_ab_test(
        test_id="wt2",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    for v in (0.5, 0.5, 0.5, 0.5, 0.5, 0.5):
        record_observation(test_id="wt2", outcome=ExperimentOutcome(variant="a", metric_value=v, sample_size=1))
    for v in (0.9, 0.9, 0.9, 0.9, 0.9, 0.9):
        record_observation(test_id="wt2", outcome=ExperimentOutcome(variant="b", metric_value=v, sample_size=1))
    result = finalize_test(test_id="wt2", min_samples=5, min_confidence=0.7)
    assert result.winner == "b"


def test_finalize_test_welch_no_significant_rejects():
    create_ab_test(
        test_id="wt3",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    for v in (0.5, 0.5, 0.5, 0.5, 0.5):
        record_observation(test_id="wt3", outcome=ExperimentOutcome(variant="a", metric_value=v, sample_size=1))
    for v in (0.5, 0.51, 0.49, 0.5, 0.5):
        record_observation(test_id="wt3", outcome=ExperimentOutcome(variant="b", metric_value=v, sample_size=1))
    result = finalize_test(test_id="wt3", min_samples=5, min_confidence=0.95)
    assert result.winner in ("a", None)


def test_finalize_test_legacy_mode_still_works():
    create_ab_test(
        test_id="wt4",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    for v in (0.5, 0.5, 0.5):
        record_observation(test_id="wt4", outcome=ExperimentOutcome(variant="a", metric_value=v, sample_size=1))
    for v in (0.9, 0.9, 0.9):
        record_observation(test_id="wt4", outcome=ExperimentOutcome(variant="b", metric_value=v, sample_size=1))
    result = finalize_test(test_id="wt4", min_samples=3, use_welch=False)
    assert result.winner == "b"
