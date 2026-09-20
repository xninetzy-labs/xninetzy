from __future__ import annotations

import pytest

from xninetzy.context.learning.benchmark_engine import (
    register_benchmark,
    run_learning_benchmark,
)
from xninetzy.context.learning.evolution_engine import (
    evolution_state,
    propose_evolution,
    reset_evolution,
    transition_proposal,
)
from xninetzy.context.learning.experiment_engine import (
    ABTestStatus,
    ABTestAccepted,
    clear_tests,
    create_ab_test,
    finalize_test,
    record_observation,
)
from xninetzy.context.learning.pattern_engine import (
    PATTERN_TYPE_FAILURE,
    PATTERN_TYPE_SUCCESS,
    detect_patterns,
)


def setup_function(_fn):
    clear_tests()
    reset_evolution()


def teardown_function(_fn):
    clear_tests()
    reset_evolution()


def test_detect_patterns_filters_by_min_frequency():
    observations = (
        {"context_key": "ctx", "category": "cat", "outcome": "success"},
        {"context_key": "ctx", "category": "cat", "outcome": "success"},
        {"context_key": "ctx", "category": "cat", "outcome": "success"},
        {"context_key": "ctx", "category": "cat", "outcome": "failure"},
        {"context_key": "ctx", "category": "cat", "outcome": "failure"},
    )
    pattern = detect_patterns(observations=observations, min_frequency=2)
    assert any(s.pattern_type == PATTERN_TYPE_SUCCESS for s in pattern.signals)
    assert any(s.pattern_type == PATTERN_TYPE_FAILURE for s in pattern.signals)


def test_detect_patterns_returns_empty_when_below_threshold():
    observations = (
        {"context_key": "ctx", "category": "cat", "outcome": "success"},
    )
    pattern = detect_patterns(observations=observations, min_frequency=2)
    assert pattern.signals == ()


def test_detect_patterns_filters_by_context():
    observations = (
        {"context_key": "ctx1", "category": "cat", "outcome": "success"},
        {"context_key": "ctx1", "category": "cat", "outcome": "success"},
        {"context_key": "ctx1", "category": "cat", "outcome": "success"},
        {"context_key": "ctx2", "category": "cat", "outcome": "success"},
        {"context_key": "ctx2", "category": "cat", "outcome": "success"},
        {"context_key": "ctx2", "category": "cat", "outcome": "success"},
    )
    pattern = detect_patterns(
        observations=observations,
        min_frequency=2,
        context_keys=("ctx1",),
    )
    assert all(s.context_key == "ctx1" for s in pattern.signals)


def test_create_ab_test_validates_inputs():
    with pytest.raises(ValueError):
        create_ab_test(test_id="", baseline="a", candidate="b", metric_name="m")
    with pytest.raises(ValueError):
        create_ab_test(test_id="t", baseline="a", candidate="a", metric_name="m")


def test_ab_test_observation_and_finalize():
    test = create_ab_test(
        test_id="t1",
        baseline="baseline",
        candidate="candidate",
        metric_name="acc",
    )
    assert test.status == ABTestStatus
    for value in (0.5, 0.6, 0.7):
        record_observation(
            test_id="t1",
            outcome=__import__("xninetzy.context.learning.experiment_engine", fromlist=["ExperimentOutcome"]).ExperimentOutcome(
                variant="baseline",
                metric_value=value,
                sample_size=1,
            ),
        )
    for value in (0.7, 0.8, 0.9):
        record_observation(
            test_id="t1",
            outcome=__import__("xninetzy.context.learning.experiment_engine", fromlist=["ExperimentOutcome"]).ExperimentOutcome(
                variant="candidate",
                metric_value=value,
                sample_size=1,
            ),
        )
    result = finalize_test(test_id="t1", min_samples=5)
    assert result.winner == "candidate"
    assert result.status == ABTestAccepted


def test_ab_test_insufficient_samples():
    create_ab_test(test_id="t2", baseline="a", candidate="b", metric_name="m")
    record_observation(
        test_id="t2",
        outcome=__import__("xninetzy.context.learning.experiment_engine", fromlist=["ExperimentOutcome"]).ExperimentOutcome(
            variant="a", metric_value=0.5, sample_size=1,
        ),
    )
    result = finalize_test(test_id="t2", min_samples=10)
    assert result.winner is None
    assert "insufficient" in "; ".join(result.notes)


def test_ab_test_higher_is_better_false_reverses_winner():
    create_ab_test(test_id="t3", baseline="a", candidate="b", metric_name="latency")
    for v in (10.0, 11.0, 12.0):
        record_observation(
            test_id="t3",
            outcome=__import__("xninetzy.context.learning.experiment_engine", fromlist=["ExperimentOutcome"]).ExperimentOutcome(
                variant="a", metric_value=v, sample_size=1,
            ),
        )
    for v in (5.0, 6.0, 7.0):
        record_observation(
            test_id="t3",
            outcome=__import__("xninetzy.context.learning.experiment_engine", fromlist=["ExperimentOutcome"]).ExperimentOutcome(
                variant="b", metric_value=v, sample_size=1,
            ),
        )
    result = finalize_test(test_id="t3", min_samples=5, higher_is_better=False)
    assert result.winner == "b"


def test_register_benchmark_records():
    benchmark = register_benchmark(
        name="coding",
        category="dev",
        description="code generation quality",
        target_metrics=("pass_rate",),
    )
    assert benchmark.last_score is None


def test_run_learning_benchmark_requires_registration():
    with pytest.raises(ValueError):
        run_learning_benchmark(name="nope", score=0.5, last_run_at="2026-01-01")


def test_run_learning_benchmark_updates_score():
    register_benchmark(
        name="coding",
        category="dev",
        description="x",
        target_metrics=("pass_rate",),
    )
    updated = run_learning_benchmark(
        name="coding", score=0.7, last_run_at="2026-01-01"
    )
    assert updated.last_score == 0.7


def test_propose_evolution_validates_confidence():
    with pytest.raises(ValueError):
        propose_evolution(
            proposal_id="p1",
            title="t",
            problem="p",
            proposed_change="c",
            expected_impact="e",
            risk_level="low",
            confidence=1.5,
        )


def test_propose_evolution_transitions_to_validated():
    proposal = propose_evolution(
        proposal_id="p1",
        title="t",
        problem="p",
        proposed_change="c",
        expected_impact="e",
        risk_level="low",
        confidence=0.8,
    )
    assert proposal.stage == "proposed"
    decision = transition_proposal(proposal_id="p1", decision="validated")
    assert decision.next_stage == "validated"


def test_propose_evolution_transitions_to_deployed():
    propose_evolution(
        proposal_id="p2",
        title="t",
        problem="p",
        proposed_change="c",
        expected_impact="e",
        risk_level="low",
        confidence=0.8,
    )
    transition_proposal(proposal_id="p2", decision="validated")
    decision = transition_proposal(proposal_id="p2", decision="approved")
    assert decision.next_stage == "approved"
    decision = transition_proposal(proposal_id="p2", decision="deployed")
    assert decision.next_stage == "deployed"


def test_propose_evolution_rejected():
    propose_evolution(
        proposal_id="p3",
        title="t",
        problem="p",
        proposed_change="c",
        expected_impact="e",
        risk_level="low",
        confidence=0.8,
    )
    decision = transition_proposal(proposal_id="p3", decision="rejected")
    assert decision.next_stage == "rejected"


def test_evolution_state_snapshots():
    propose_evolution(
        proposal_id="p4",
        title="t",
        problem="p",
        proposed_change="c",
        expected_impact="e",
        risk_level="low",
        confidence=0.8,
    )
    transition_proposal(proposal_id="p4", decision="validated")
    transition_proposal(proposal_id="p4", decision="approved")
    state = evolution_state()
    assert "p4" in state.accepted
