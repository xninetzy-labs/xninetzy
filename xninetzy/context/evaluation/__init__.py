from __future__ import annotations

from xninetzy.context.evaluation.audit import (
    AuditFindings,
    AuditReport,
    AuditVerdict,
    EVAL_VERDICT_CRITICAL,
    EVAL_VERDICT_FAIL,
    EVAL_VERDICT_PASS,
    EVAL_VERDICT_WARN,
    evaluate_audit_trail,
)
from xninetzy.context.evaluation.catalog_audit import (
    CatalogAuditReport,
    SkillCatalogAudit,
    ToolCatalogAudit,
    audit_skill_catalog,
    audit_tool_catalog,
    synthesize_catalog_report,
)
from xninetzy.context.evaluation.benchmark import (
    BenchmarkComparison,
    BenchmarkEngine,
    BenchmarkMetric,
    BenchmarkResult,
    compare_to_benchmark,
    run_benchmark,
)
from xninetzy.context.evaluation.context_eval import (
    ContextAudit,
    evaluate_context,
)
from xninetzy.context.evaluation.hallucination import (
    HallucinationAudit,
    HALLUCINATION_LEVEL_CRITICAL,
    HALLUCINATION_LEVEL_HIGH,
    HALLUCINATION_LEVEL_LOW,
    HALLUCINATION_LEVEL_MEDIUM,
    HALLUCINATION_LEVEL_NONE,
    detect_hallucination,
)
from xninetzy.context.evaluation.memory_eval import (
    MemoryAudit,
    evaluate_memory,
)
from xninetzy.context.evaluation.outcome import (
    OutcomeAudit,
    OUTCOME_AUDIT_INCOMPLETE,
    OUTCOME_AUDIT_MISLEADING,
    OUTCOME_AUDIT_PARTIAL,
    OUTCOME_AUDIT_PASS,
    evaluate_outcome,
)
from xninetzy.context.evaluation.root_cause import (
    ROOT_CAUSE_CONFIDENCE_HIGH,
    ROOT_CAUSE_CONFIDENCE_LOW,
    ROOT_CAUSE_CONFIDENCE_MEDIUM,
    RootCauseAnalysis,
    analyze_root_cause,
)
from xninetzy.context.evaluation.routing_eval import (
    RoutingAudit,
    evaluate_routing,
)
from xninetzy.context.evaluation.scoring import (
    DomainScore,
    QualityScores,
    aggregate_scores,
    score_domain,
)

__all__ = [
    "DomainScore",
    "InvocationAuditSummary",
    "QualityScores",
    "audit_outcome_label",
    "build_invocation_summary",
    "aggregate_scores",
    "score_domain",
]
from xninetzy.context.evaluation.security_eval import (
    SecurityAudit,
    SECURITY_RISK_HIGH,
    SECURITY_RISK_LOW,
    SECURITY_RISK_MEDIUM,
    evaluate_security,
)
from xninetzy.context.evaluation.signal_gen import (
    LEARN,
    MONITOR,
    IGNORE,
    LearningSignal,
    LearningSignalBatch,
    extract_signals,
)
from xninetzy.context.evaluation.skill_eval import (
    SkillAudit,
    evaluate_skill,
)
from xninetzy.context.evaluation.tool_eval import (
    ToolAudit,
    evaluate_tool,
)
from xninetzy.context.evaluation.integration import (
    EvaluationCycleResult,
    InvocationAuditSummary,
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
from xninetzy.context.evaluation.self_audit import (
    SelfAuditSnapshot,
    build_self_audit,
)
from xninetzy.context.evaluation.learning_bridge import (
    LearningBridgeResult,
    bridge_cycle_to_learning,
    create_lightning_proposal_from_cycle,
    persist_signal_episodes,
)

PACKAGE_MARKER: str = "xninetzy.context.evaluation"

__all__ = [
    "AuditFindings",
    "AuditReport",
    "AuditVerdict",
    "BenchmarkComparison",
    "BenchmarkEngine",
    "BenchmarkMetric",
    "BenchmarkResult",
    "CatalogAuditReport",
    "ContextAudit",
    "EVAL_VERDICT_CRITICAL",
    "EVAL_VERDICT_FAIL",
    "EVAL_VERDICT_PASS",
    "EVAL_VERDICT_WARN",
    "EvaluationCycleResult",
    "HALLUCINATION_LEVEL_CRITICAL",
    "HALLUCINATION_LEVEL_HIGH",
    "HALLUCINATION_LEVEL_LOW",
    "HALLUCINATION_LEVEL_MEDIUM",
    "HALLUCINATION_LEVEL_NONE",
    "HallucinationAudit",
    "IGNORE",
    "LEARN",
    "LearningBridgeResult",
    "LearningSignal",
    "LearningSignalBatch",
    "MONITOR",
    "MemoryAudit",
    "OUTCOME_AUDIT_INCOMPLETE",
    "OUTCOME_AUDIT_MISLEADING",
    "OUTCOME_AUDIT_PARTIAL",
    "OUTCOME_AUDIT_PASS",
    "OutcomeAudit",
    "PACKAGE_MARKER",
    "ROOT_CAUSE_CONFIDENCE_HIGH",
    "ROOT_CAUSE_CONFIDENCE_LOW",
    "ROOT_CAUSE_CONFIDENCE_MEDIUM",
    "RootCauseAnalysis",
    "RoutingAudit",
    "SECURITY_RISK_HIGH",
    "SECURITY_RISK_LOW",
    "SECURITY_RISK_MEDIUM",
    "SecurityAudit",
    "SelfAuditSnapshot",
    "SkillAudit",
    "SkillCatalogAudit",
    "ToolAudit",
    "ToolCatalogAudit",
    "aggregate_scores",
    "analyze_root_cause",
    "audit_skill_catalog",
    "audit_tool_catalog",
    "bridge_cycle_to_learning",
    "build_evolution_proposal_from_cycle",
    "build_invocation_summary",
    "build_self_audit",
    "compare_to_benchmark",
    "create_lightning_proposal_from_cycle",
    "detect_hallucination",
    "detect_invocation_patterns",
    "evaluate_audit_trail",
    "evaluate_context",
    "evaluate_invocation_cycle",
    "evaluate_memory",
    "evaluate_outcome",
    "evaluate_routing",
    "evaluate_security",
    "evaluate_skill",
    "evaluate_tool",
    "extract_signals",
    "finalize_pending_ab_test",
    "persist_signal_episodes",
    "record_benchmark_for_cycle",
    "run_benchmark",
    "score_domain",
    "summarize_tool_verdicts",
    "synthesize_catalog_report",
    "synthesize_pattern_observations",
]
