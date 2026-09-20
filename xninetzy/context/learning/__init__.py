from __future__ import annotations

from xninetzy.context.learning.benchmark_engine import (
    LearningBenchmark,
    LearningBenchmarkRegistry,
    get_benchmark_registry,
    register_benchmark,
    reset_benchmark_registry,
    run_learning_benchmark,
)
from xninetzy.context.learning.evolution_engine import (
    EvolutionDecision,
    EvolutionProposal,
    EvolutionStage,
    EvolutionState,
    propose_evolution,
    reset_evolution,
    transition_proposal,
)
from xninetzy.context.learning.experiment_engine import (
    ABTest,
    ABTestResult,
    ABTestStatus,
    ExperimentOutcome,
    clear_tests,
    create_ab_test,
    finalize_test,
    get_test,
    list_tests,
    record_observation,
)
from xninetzy.context.learning.pattern_engine import (
    DetectedPattern,
    PatternSignal,
    PATTERN_TYPE_FAILURE,
    PATTERN_TYPE_SUCCESS,
    detect_patterns,
)
from xninetzy.context.learning import statistics
from xninetzy.context.learning.statistics import (
    delta_with_confidence,
    welch_t,
    wilson_score,
)

PACKAGE_MARKER: str = "xninetzy.context.learning"

__all__ = [
    "ABTest",
    "ABTestResult",
    "ABTestStatus",
    "DetectedPattern",
    "EvolutionDecision",
    "EvolutionProposal",
    "EvolutionStage",
    "EvolutionState",
    "ExperimentOutcome",
    "LearningBenchmark",
    "LearningBenchmarkRegistry",
    "PACKAGE_MARKER",
    "PATTERN_TYPE_FAILURE",
    "PATTERN_TYPE_SUCCESS",
    "PatternSignal",
    "clear_tests",
    "create_ab_test",
    "delta_with_confidence",
    "detect_patterns",
    "finalize_test",
    "get_benchmark_registry",
    "get_test",
    "list_tests",
    "propose_evolution",
    "record_observation",
    "register_benchmark",
    "reset_benchmark_registry",
    "reset_evolution",
    "run_learning_benchmark",
    "statistics",
    "transition_proposal",
    "welch_t",
    "wilson_score",
]
