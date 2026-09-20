from __future__ import annotations

from langchain_core.tools import tool

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
from xninetzy.context.evaluation.benchmark import (
    BenchmarkComparison,
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
    HALLUCINATION_LEVEL_CRITICAL,
    HALLUCINATION_LEVEL_HIGH,
    HALLUCINATION_LEVEL_LOW,
    HALLUCINATION_LEVEL_MEDIUM,
    HALLUCINATION_LEVEL_NONE,
    HallucinationAudit,
    detect_hallucination,
)
from xninetzy.context.evaluation.memory_eval import (
    MemoryAudit,
    evaluate_memory,
)
from xninetzy.context.evaluation.outcome import (
    OUTCOME_AUDIT_INCOMPLETE,
    OUTCOME_AUDIT_MISLEADING,
    OUTCOME_AUDIT_PARTIAL,
    OUTCOME_AUDIT_PASS,
    OutcomeAudit,
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
from xninetzy.context.evaluation.security_eval import (
    SECURITY_RISK_HIGH,
    SECURITY_RISK_LOW,
    SECURITY_RISK_MEDIUM,
    SecurityAudit,
    evaluate_security,
)
from xninetzy.context.evaluation.signal_gen import (
    IGNORE,
    LEARN,
    MONITOR,
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
from xninetzy.context.evaluation.self_audit import (
    SelfAuditSnapshot,
    build_self_audit,
)
from xninetzy.context.evaluation.catalog_audit import (
    CatalogAuditReport,
    audit_skill_catalog,
    synthesize_catalog_report,
)


@tool
def evaluation_outcome(
    objective: str,
    expected: str,
    observed: str,
    success_criteria: list[str] | None = None,
    observed_criteria_hits: list[str] | None = None,
) -> dict:
    """Evaluate an outcome against expected + criteria.

    Args:
        objective: free-text objective description
        expected: expected result
        observed: actual result
        success_criteria: optional list of criteria names
        observed_criteria_hits: criteria actually satisfied
    """
    audit: OutcomeAudit = evaluate_outcome(
        objective=objective,
        expected=expected,
        observed=observed,
        success_criteria=tuple(success_criteria or ()),
        observed_criteria_hits=tuple(observed_criteria_hits or ()),
    )
    return audit.to_dict()


@tool
def evaluation_context(
    retrieved: list[str],
    relevant: list[str],
    required: list[str],
    stale: list[str] | None = None,
    duplicates: list[str] | None = None,
) -> dict:
    """Audit context retrieval precision/recall/freshness.

    Args:
        retrieved: items actually retrieved
        relevant: subset of retrieved that are relevant
        required: items required for the task
        stale: retrieved items considered stale
        duplicates: retrieved items duplicated within the set
    """
    audit: ContextAudit = evaluate_context(
        retrieved=tuple(retrieved),
        relevant=tuple(relevant),
        required=tuple(required),
        stale=tuple(stale or ()),
        duplicates=tuple(duplicates or ()),
    )
    return audit.to_dict()


@tool
def evaluation_memory(memories: list[dict]) -> dict:
    """Audit memory usefulness, conflicts, duplicates.

    Args:
        memories: list of memory dicts (each may carry usefulness/conflict)
    """
    audit: MemoryAudit = evaluate_memory(memories=tuple(memories))
    return audit.to_dict()


@tool
def evaluation_routing(
    chosen: str,
    candidates: list[str],
    success_history: dict[str, int] | None = None,
    failure_history: dict[str, int] | None = None,
) -> dict:
    """Audit a routing decision.

    Args:
        chosen: chosen provider/skill name
        candidates: alternative candidates considered
        success_history: per-candidate success counts
        failure_history: per-candidate failure counts
    """
    audit: RoutingAudit = evaluate_routing(
        chosen=chosen,
        candidates=tuple(candidates),
        success_history=success_history,
        failure_history=failure_history,
    )
    return audit.to_dict()


@tool
def evaluation_skill(
    skill_name: str,
    invocation_count: int,
    success_count: int,
    reuse_count: int = 0,
    complexity_score: float = 0.5,
) -> dict:
    """Audit a skill's effectiveness.

    Args:
        skill_name: skill identifier
        invocation_count: total invocations
        success_count: invocations with success outcome
        reuse_count: invocations reused across distinct contexts
        complexity_score: 0..1 complexity score
    """
    audit: SkillAudit = evaluate_skill(
        skill_name=skill_name,
        invocation_count=int(invocation_count),
        success_count=int(success_count),
        reuse_count=int(reuse_count),
        complexity_score=float(complexity_score),
    )
    return audit.to_dict()


@tool
def evaluation_tool(
    tool_name: str,
    success_count: int,
    failure_count: int,
    avg_latency_ms: float,
    cost_score: float = 0.5,
    security_risk: float = 0.0,
) -> dict:
    """Audit a tool's quality and value.

    Args:
        tool_name: tool identifier
        success_count: success invocations
        failure_count: failure invocations
        avg_latency_ms: average latency
        cost_score: 0..1 cost score (higher = more expensive)
        security_risk: 0..1 security risk
    """
    audit: ToolAudit = evaluate_tool(
        tool_name=tool_name,
        success_count=int(success_count),
        failure_count=int(failure_count),
        avg_latency_ms=float(avg_latency_ms),
        cost_score=float(cost_score),
        security_risk=float(security_risk),
    )
    return audit.to_dict()


@tool
def evaluation_security(
    triggered: list[str] | None = None,
    additional_risk: float = 0.0,
) -> dict:
    """Audit security risk from triggered indicators.

    Args:
        triggered: list of indicator names
            (prompt_injection|memory_poisoning|context_poisoning|tool_abuse|
             mcp_poisoning|supply_chain|credential_leakage|unsafe_execution|
             routing_attack)
        additional_risk: extra risk score 0..1
    """
    audit: SecurityAudit = evaluate_security(
        triggered=tuple(triggered or ()),
        additional_risk=float(additional_risk),
    )
    return audit.to_dict()


@tool
def evaluation_hallucination(
    claims: list[str],
    supported_refs: dict[str, list[str]] | None = None,
) -> dict:
    """Detect hallucinated claims.

    Args:
        claims: list of claim strings
        supported_refs: dict mapping claim index -> list of supporting refs
    """
    supported: dict[str, tuple[str, ...]] = {}
    if supported_refs:
        for key, refs in supported_refs.items():
            supported[str(key)] = tuple(refs)
    audit: HallucinationAudit = detect_hallucination(
        claims=tuple(claims),
        supported_refs=supported or None,
    )
    return audit.to_dict()


@tool
def evaluation_root_cause(
    symptom: str,
    hypotheses: list[str],
    evidence_refs: list[str] | None = None,
    confidence_threshold: float = 0.7,
) -> dict:
    """Pick the most likely root cause from hypotheses.

    Args:
        symptom: observable symptom
        hypotheses: candidate causes (first = primary hypothesis)
        evidence_refs: list of evidence ids/refs
        confidence_threshold: threshold for high confidence
    """
    analysis: RootCauseAnalysis = analyze_root_cause(
        symptom=symptom,
        hypotheses=tuple(hypotheses),
        evidence_refs=tuple(evidence_refs or ()),
        confidence_threshold=float(confidence_threshold),
    )
    return analysis.to_dict()


@tool
def evaluation_score(
    domains: list[dict],
) -> dict:
    """Aggregate weighted domain scores.

    Args:
        domains: list of {domain, score, weight?, notes?}

    Returns:
        QualityScores with per-domain breakdown + overall weighted.
    """
    domain_scores: list[DomainScore] = []
    for entry in domains:
        domain_scores.append(
            score_domain(
                domain=str(entry["domain"]),
                score=float(entry["score"]),
                weight=float(entry.get("weight", 1.0)),
                notes=tuple(entry.get("notes") or ()),
            )
        )
    scores: QualityScores = aggregate_scores(tuple(domain_scores))
    return scores.to_dict()


@tool
def evaluation_run_benchmark(
    name: str,
    metrics_json: str,
    notes: list[str] | None = None,
) -> dict:
    """Register a benchmark result by name.

    Args:
        name: benchmark name
        metrics_json: JSON list of {name, baseline, candidate, higher_is_better?}
        notes: optional notes
    """
    import json as _json

    raw = _json.loads(metrics_json)
    metrics: list[BenchmarkMetric] = []
    for entry in raw:
        metrics.append(
            BenchmarkMetric(
                name=str(entry["name"]),
                baseline=float(entry["baseline"]),
                candidate=float(entry["candidate"]),
                higher_is_better=bool(entry.get("higher_is_better", True)),
            )
        )
    result: BenchmarkResult = run_benchmark(
        name=name,
        metrics=tuple(metrics),
        notes=tuple(notes or ()),
    )
    return result.to_dict()


@tool
def evaluation_compare_benchmark(
    name: str,
    candidate_metrics_json: str,
) -> dict:
    """Compare candidate metrics against a registered baseline.

    Args:
        name: benchmark name (must be previously registered)
        candidate_metrics_json: JSON list of {name, baseline, candidate,
            higher_is_better?}
    """
    import json as _json

    raw = _json.loads(candidate_metrics_json)
    metrics: list[BenchmarkMetric] = []
    for entry in raw:
        metrics.append(
            BenchmarkMetric(
                name=str(entry["name"]),
                baseline=float(entry["baseline"]),
                candidate=float(entry["candidate"]),
                higher_is_better=bool(entry.get("higher_is_better", True)),
            )
        )
    comparison: BenchmarkComparison = compare_to_benchmark(
        name=name,
        candidate_metrics=tuple(metrics),
    )
    return comparison.to_dict()


@tool
def evaluation_extract_signals(
    findings_json: str,
    min_confidence_to_learn: float = 0.7,
    min_confidence_to_monitor: float = 0.4,
) -> dict:
    """Extract learning signals from findings.

    Args:
        findings_json: JSON list of {source, summary, confidence,
            evidence_refs?, notes?}
        min_confidence_to_learn: threshold for LEARN action
        min_confidence_to_monitor: threshold for MONITOR action
    """
    import json as _json

    raw = _json.loads(findings_json)
    findings: list[dict] = []
    for entry in raw:
        findings.append(
            {
                "source": str(entry.get("source", "unknown")),
                "summary": str(entry.get("summary", "")),
                "confidence": float(entry.get("confidence", 0.0)),
                "evidence_refs": tuple(entry.get("evidence_refs") or ()),
                "notes": tuple(entry.get("notes") or ()),
            }
        )
    batch: LearningSignalBatch = extract_signals(
        findings=tuple(findings),
        min_confidence_to_learn=float(min_confidence_to_learn),
        min_confidence_to_monitor=float(min_confidence_to_monitor),
    )
    return batch.to_dict()


@tool
def evaluation_self_audit() -> dict:
    """Return XNINETZY self-audit snapshot (tools, modules, capabilities)."""
    snapshot: SelfAuditSnapshot = build_self_audit()
    return snapshot.to_dict()


@tool
def evaluation_run_pipeline_cycle(
    requests_json: str,
    security_indicators: list[str] | None = None,
    min_confidence_to_learn: float = 0.7,
) -> dict:
    """Execute a batch of synthetic invocations and evaluate the cycle.

    Args:
        requests_json: JSON list of {request_id, intent, capability,
            context_key, query, side_effect, idempotency_key, approval_id,
            provider_id}
        security_indicators: optional list of triggered security indicators
        min_confidence_to_learn: signal threshold
    """
    import json as _json
    from xninetzy.context.invocation.contract import InvocationRequest
    from xninetzy.context.orchestrator.pipeline import (
        execute_pipeline_with_evaluation,
    )

    raw = _json.loads(requests_json)
    requests = []
    for entry in raw:
        requests.append(
            InvocationRequest(
                request_id=str(entry["request_id"]),
                intent=str(entry.get("intent", "x")),
                capability=str(entry["capability"]),
                context_key=str(entry.get("context_key", "ctx")),
                query=str(entry.get("query", "")),
                side_effect=entry.get("side_effect"),
                idempotency_key=entry.get("idempotency_key"),
                approval_id=entry.get("approval_id"),
            )
        )
    result = execute_pipeline_with_evaluation(
        requests,
        security_indicators=tuple(security_indicators or ()),
        min_confidence_to_learn=float(min_confidence_to_learn),
    )
    cycle = result["cycle"]
    return {
        "outcomes": [
            {
                "request_id": o.audit.request_id,
                "provider_id": o.audit.provider_id,
                "audit_outcome": o.audit.outcome,
            }
            for o in result["outcomes"]
        ],
        "cycle": cycle.to_dict(),
    }


@tool
def evaluation_audit_tool_catalog(
    tool_metrics_json: str,
) -> dict:
    """Audit the entire tool catalog from metrics.

    Args:
        tool_metrics_json: JSON dict {tool_name: {success, failure,
            avg_latency_ms, cost_score, security_risk}}
    """
    import json as _json

    raw = _json.loads(tool_metrics_json)
    report: CatalogAuditReport = synthesize_catalog_report(tool_metrics=raw)
    return report.to_dict()


@tool
def evaluation_audit_skill_catalog(
    skill_metrics_json: str,
) -> dict:
    """Audit the skill catalog from metrics.

    Args:
        skill_metrics_json: JSON dict {skill_name: {invocation_count,
            success_count, reuse_count, complexity_score}}
    """
    import json as _json

    raw = _json.loads(skill_metrics_json)
    audits = audit_skill_catalog(skill_metrics=raw)
    return {
        "skill_audits": [a.to_dict() for a in audits],
    }


@tool
def evaluation_audit_trail(
    verdicts_json: str,
) -> dict:
    """Aggregate a list of per-domain verdicts into one overall report.

    Args:
        verdicts_json: JSON list of {label, score, findings}
    """
    import json as _json

    raw = _json.loads(verdicts_json)
    verdicts: list[AuditVerdict] = []
    for entry in raw:
        findings_raw = entry.get("findings", {}) or {}
        findings = AuditFindings(
            passed=tuple(findings_raw.get("passed", ()) or ()),
            warnings=tuple(findings_raw.get("warnings", ()) or ()),
            failed=tuple(findings_raw.get("failed", ()) or ()),
            critical=tuple(findings_raw.get("critical", ()) or ()),
        )
        verdicts.append(
            AuditVerdict(
                label=str(entry["label"]),
                score=float(entry["score"]),
                findings=findings,
            )
        )
    report: AuditReport = evaluate_audit_trail(verdicts=tuple(verdicts))
    return report.to_dict()


__all__ = [
    "DomainScore",
    "EVAL_VERDICT_CRITICAL",
    "EVAL_VERDICT_FAIL",
    "EVAL_VERDICT_PASS",
    "EVAL_VERDICT_WARN",
    "HALLUCINATION_LEVEL_CRITICAL",
    "HALLUCINATION_LEVEL_HIGH",
    "HALLUCINATION_LEVEL_LOW",
    "HALLUCINATION_LEVEL_MEDIUM",
    "HALLUCINATION_LEVEL_NONE",
    "IGNORE",
    "LEARN",
    "LearningSignalBatch",
    "MONITOR",
    "OUTCOME_AUDIT_INCOMPLETE",
    "OUTCOME_AUDIT_MISLEADING",
    "OUTCOME_AUDIT_PARTIAL",
    "OUTCOME_AUDIT_PASS",
    "QualityScores",
    "ROOT_CAUSE_CONFIDENCE_HIGH",
    "ROOT_CAUSE_CONFIDENCE_LOW",
    "ROOT_CAUSE_CONFIDENCE_MEDIUM",
    "SECURITY_RISK_HIGH",
    "SECURITY_RISK_LOW",
    "SECURITY_RISK_MEDIUM",
    "evaluation_audit_skill_catalog",
    "evaluation_audit_tool_catalog",
    "evaluation_audit_trail",
    "evaluation_compare_benchmark",
    "evaluation_context",
    "evaluation_extract_signals",
    "evaluation_hallucination",
    "evaluation_memory",
    "evaluation_outcome",
    "evaluation_root_cause",
    "evaluation_routing",
    "evaluation_run_benchmark",
    "evaluation_run_pipeline_cycle",
    "evaluation_score",
    "evaluation_security",
    "evaluation_self_audit",
    "evaluation_skill",
    "evaluation_tool",
]
