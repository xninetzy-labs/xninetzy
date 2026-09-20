from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.context.learning.benchmark_engine import (
    LearningBenchmark,
    register_benchmark,
    run_learning_benchmark,
)
from xninetzy.context.learning.evolution_engine import (
    EvolutionDecision,
    EvolutionProposal,
    EvolutionStage,
    EvolutionState,
    evolution_state,
    propose_evolution,
    reset_evolution,
    transition_proposal,
)
from xninetzy.context.learning.experiment_engine import (
    ABTest,
    ABTestResult,
    ExperimentOutcome,
    create_ab_test,
    finalize_test,
    record_observation,
)
from xninetzy.context.learning.pattern_engine import (
    PATTERN_TYPE_FAILURE,
    PATTERN_TYPE_SUCCESS,
    DetectedPattern,
    detect_patterns,
)


@tool
def learning_detect_patterns(
    observations_json: str,
    min_frequency: int = 3,
    context_keys: list[str] | None = None,
) -> dict:
    """Detect recurring success/failure patterns from observations.

    Args:
        observations_json: JSON list of {context_key, category, outcome}
        min_frequency: minimum frequency to count as a pattern
        context_keys: optional filter
    """
    import json as _json

    raw = _json.loads(observations_json)
    pattern: DetectedPattern = detect_patterns(
        observations=tuple(raw),
        min_frequency=int(min_frequency),
        context_keys=tuple(context_keys or ()),
    )
    return pattern.to_dict()


@tool
def learning_create_ab_test(
    test_id: str,
    baseline: str,
    candidate: str,
    metric_name: str,
) -> dict:
    """Create an A/B test between baseline and candidate.

    Args:
        test_id: unique test id
        baseline: baseline variant name
        candidate: candidate variant name
        metric_name: metric to compare
    """
    test: ABTest = create_ab_test(
        test_id=test_id,
        baseline=baseline,
        candidate=candidate,
        metric_name=metric_name,
    )
    return test.to_dict()


@tool
def learning_record_ab_observation(
    test_id: str,
    variant: str,
    metric_value: float,
    sample_size: int = 1,
) -> dict:
    """Record one observation for a running A/B test.

    Args:
        test_id: test id
        variant: variant name (baseline or candidate)
        metric_value: observed metric value
        sample_size: sample size for this observation
    """
    outcome = ExperimentOutcome(
        variant=variant,
        metric_value=float(metric_value),
        sample_size=int(sample_size),
    )
    test: ABTest = record_observation(test_id=test_id, outcome=outcome)
    return test.to_dict()


@tool
def learning_finalize_ab_test(
    test_id: str,
    min_samples: int = 5,
    min_confidence: float = 0.6,
    higher_is_better: bool = True,
) -> dict:
    """Finalize A/B test and decide winner.

    Args:
        test_id: test id
        min_samples: minimum total samples required
        min_confidence: minimum confidence for accept
        higher_is_better: direction of improvement
    """
    result: ABTestResult = finalize_test(
        test_id=test_id,
        min_samples=int(min_samples),
        min_confidence=float(min_confidence),
        higher_is_better=bool(higher_is_better),
    )
    return result.to_dict()


@tool
def learning_register_benchmark(
    name: str,
    category: str,
    description: str,
    target_metrics: list[str],
) -> dict:
    """Register a permanent learning benchmark.

    Args:
        name: benchmark name
        category: benchmark category (coding/research/etc.)
        description: free-text description
        target_metrics: list of metric names the benchmark tracks
    """
    benchmark: LearningBenchmark = register_benchmark(
        name=name,
        category=category,
        description=description,
        target_metrics=tuple(target_metrics),
    )
    return benchmark.to_dict()


@tool
def learning_run_benchmark(
    name: str,
    score: float,
    last_run_at: str,
) -> dict:
    """Record a benchmark run.

    Args:
        name: registered benchmark name
        score: 0..1 score
        last_run_at: ISO timestamp
    """
    benchmark: LearningBenchmark = run_learning_benchmark(
        name=name,
        score=float(score),
        last_run_at=last_run_at,
    )
    return benchmark.to_dict()


@tool
def learning_propose_evolution(
    proposal_id: str,
    title: str,
    problem: str,
    proposed_change: str,
    expected_impact: str,
    risk_level: str,
    confidence: float,
    evidence_refs: list[str] | None = None,
) -> dict:
    """Propose a system evolution.

    Args:
        proposal_id: unique proposal id
        title: short title
        problem: problem description
        proposed_change: what to change
        expected_impact: expected improvement
        risk_level: low|medium|high
        confidence: 0..1 confidence
        evidence_refs: list of evidence refs
    """
    proposal: EvolutionProposal = propose_evolution(
        proposal_id=proposal_id,
        title=title,
        problem=problem,
        proposed_change=proposed_change,
        expected_impact=expected_impact,
        risk_level=risk_level,
        confidence=float(confidence),
        evidence_refs=tuple(evidence_refs or ()),
    )
    return proposal.to_dict()


@tool
def learning_transition_evolution(
    proposal_id: str,
    decision: str,
    reason: str = "",
) -> dict:
    """Move an evolution proposal to next stage (or reject).

    Args:
        proposal_id: proposal id
        decision: 'validated' | 'approved' | 'deployed' | 'rejected'
        reason: free-text reason
    """
    out: EvolutionDecision = transition_proposal(
        proposal_id=proposal_id,
        decision=decision,
        reason=reason,
    )
    return out.to_dict()


@tool
def learning_state() -> dict:
    """Snapshot current evolution state (proposals + accepted/rejected/deployed)."""
    state: EvolutionState = evolution_state()
    return state.to_dict()


@tool
def learning_reset_evolution() -> dict:
    """Clear all evolution proposals (testing only)."""
    reset_evolution()
    return {"cleared": True}


__all__ = [
    "EvolutionStage",
    "PATTERN_TYPE_FAILURE",
    "PATTERN_TYPE_SUCCESS",
    "learning_create_ab_test",
    "learning_detect_patterns",
    "learning_finalize_ab_test",
    "learning_propose_evolution",
    "learning_record_ab_observation",
    "learning_register_benchmark",
    "learning_reset_evolution",
    "learning_run_benchmark",
    "learning_state",
    "learning_transition_evolution",
]
