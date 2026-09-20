from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xninetzy.context.evaluation.audit import (
    EVAL_VERDICT_FAIL,
    EVAL_VERDICT_PASS,
    EVAL_VERDICT_WARN,
    AuditFindings,
    AuditReport,
    AuditVerdict,
    evaluate_audit_trail,
)
from xninetzy.context.evaluation.outcome import (
    OUTCOME_AUDIT_INCOMPLETE,
    OUTCOME_AUDIT_MISLEADING,
    OUTCOME_AUDIT_PARTIAL,
    OUTCOME_AUDIT_PASS,
    evaluate_outcome,
)
from xninetzy.context.evaluation.scoring import (
    DomainScore,
    QualityScores,
    aggregate_scores,
    score_domain,
)
from xninetzy.context.evaluation.security_eval import (
    SECURITY_RISK_HIGH,
    evaluate_security,
)
from xninetzy.context.evaluation.signal_gen import (
    LearningSignalBatch,
    extract_signals,
)
from xninetzy.context.evaluation.tool_eval import (
    TOOL_DEMOTE,
    TOOL_MONITOR,
    TOOL_PROMOTE,
    TOOL_REMOVE,
)
from xninetzy.context.learning.benchmark_engine import (
    LearningBenchmark,
    run_learning_benchmark,
)
from xninetzy.context.learning.evolution_engine import (
    EvolutionProposal,
    propose_evolution,
)
from xninetzy.context.learning.experiment_engine import (
    ABTestResult,
    finalize_test,
)
from xninetzy.context.learning.pattern_engine import (
    PatternSignal,
    detect_patterns,
)


def audit_outcome_label(audit_outcome: str | None) -> str:
    mapping: dict[str | None, str] = {
        "ok": OUTCOME_AUDIT_PASS,
        "error": OUTCOME_AUDIT_PARTIAL,
        "blocked": OUTCOME_AUDIT_INCOMPLETE,
        "critic_fail": OUTCOME_AUDIT_MISLEADING,
        "replan": OUTCOME_AUDIT_PARTIAL,
        "ok_with_warnings": OUTCOME_AUDIT_PARTIAL,
        "halted_after_success": OUTCOME_AUDIT_PASS,
        "replayed": OUTCOME_AUDIT_PASS,
        "rejected_policy": OUTCOME_AUDIT_INCOMPLETE,
        None: OUTCOME_AUDIT_INCOMPLETE,
    }
    return mapping.get(audit_outcome, OUTCOME_AUDIT_PARTIAL)


@dataclass(frozen=True, slots=True)
class InvocationAuditSummary:
    request_id: str
    provider_id: str
    capability: str
    audit_outcome: str | None
    latency_ms: int | None
    error: str | None
    expected: str
    observed: str
    outcome_label: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "capability": self.capability,
            "audit_outcome": self.audit_outcome,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "expected": self.expected,
            "observed": self.observed,
            "outcome_label": self.outcome_label,
        }


def build_invocation_summary(
    *,
    request_id: str,
    provider_id: str,
    capability: str,
    audit_outcome: str | None,
    latency_ms: int | None,
    error: str | None,
) -> InvocationAuditSummary:
    label = audit_outcome_label(audit_outcome)
    expected = "ok"
    if audit_outcome in ("blocked", "rejected_policy"):
        expected = "policy_gate"
    return InvocationAuditSummary(
        request_id=request_id,
        provider_id=provider_id,
        capability=capability,
        audit_outcome=audit_outcome,
        latency_ms=latency_ms,
        error=error,
        expected=expected,
        observed=audit_outcome or "missing",
        outcome_label=label,
    )


@dataclass(frozen=True, slots=True)
class EvaluationCycleResult:
    summaries: tuple[InvocationAuditSummary, ...]
    audit_report: AuditReport
    quality_scores: QualityScores
    learning_signals: LearningSignalBatch
    security_indicators: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "summaries": [s.to_dict() for s in self.summaries],
            "audit_report": self.audit_report.to_dict(),
            "quality_scores": self.quality_scores.to_dict(),
            "learning_signals": self.learning_signals.to_dict(),
            "security_indicators": list(self.security_indicators),
            "notes": list(self.notes),
        }


def evaluate_invocation_cycle(
    *,
    summaries: tuple[InvocationAuditSummary, ...],
    security_indicators: tuple[str, ...] = (),
    min_confidence_to_learn: float = 0.7,
) -> EvaluationCycleResult:
    verdicts: list[AuditVerdict] = []
    domain_scores: list[DomainScore] = []
    notes: list[str] = []
    error_count = 0
    block_count = 0
    for summary in summaries:
        outcome = evaluate_outcome(
            objective=f"request {summary.request_id}",
            expected=summary.expected,
            observed=summary.observed,
            evidence_refs=(summary.request_id,),
        )
        score = 1.0 if outcome.verdict == OUTCOME_AUDIT_PASS else 0.5 if outcome.verdict == OUTCOME_AUDIT_PARTIAL else 0.0
        if summary.audit_outcome == "error":
            error_count += 1
        if summary.audit_outcome in ("blocked", "rejected_policy"):
            block_count += 1
        if outcome.verdict == OUTCOME_AUDIT_PASS:
            label = EVAL_VERDICT_PASS
        elif outcome.verdict == OUTCOME_AUDIT_PARTIAL:
            label = EVAL_VERDICT_WARN
        elif outcome.verdict == OUTCOME_AUDIT_MISLEADING:
            label = EVAL_VERDICT_FAIL
        else:
            label = EVAL_VERDICT_FAIL
        verdicts.append(
            AuditVerdict(
                label=label,
                score=score,
                findings=AuditFindings(
                    passed=(summary.request_id,) if score == 1.0 else (),
                    warnings=() if score >= 0.5 else (),
                    failed=(summary.request_id,) if score < 0.5 else (),
                    critical=(summary.request_id,) if summary.audit_outcome == "critic_fail" else (),
                ),
            )
        )
        domain_scores.append(
            score_domain(
                domain=summary.capability,
                score=score,
                weight=1.0,
                notes=(f"outcome={summary.audit_outcome}",),
            )
        )
    audit_report = evaluate_audit_trail(verdicts=tuple(verdicts))
    quality_scores = aggregate_scores(tuple(domain_scores))
    findings_payload = tuple(
        {
            "source": summary.capability,
            "summary": (
                f"request={summary.request_id} outcome={summary.audit_outcome}"
                + (f" error={summary.error}" if summary.error else "")
            ),
            "confidence": (
                0.9 if summary.audit_outcome == "ok"
                else 0.6 if summary.audit_outcome == "blocked"
                else 0.3
            ),
            "evidence_refs": (summary.request_id,),
        }
        for summary in summaries
    )
    signals = extract_signals(
        findings=findings_payload,
        min_confidence_to_learn=min_confidence_to_learn,
    )
    security_audit = evaluate_security(triggered=security_indicators)
    if security_audit.risk_level == SECURITY_RISK_HIGH:
        notes.append("security risk high — escalate to owner")
    if error_count:
        notes.append(f"{error_count} invocation errors observed")
    if block_count:
        notes.append(f"{block_count} invocations blocked by policy")
    return EvaluationCycleResult(
        summaries=summaries,
        audit_report=audit_report,
        quality_scores=quality_scores,
        learning_signals=signals,
        security_indicators=security_indicators,
        notes=tuple(notes),
    )


def synthesize_pattern_observations(
    *,
    summaries: tuple[InvocationAuditSummary, ...],
) -> tuple[dict[str, Any], ...]:
    observations: list[dict[str, Any]] = []
    for summary in summaries:
        outcome = "success" if summary.audit_outcome == "ok" else "failure"
        observations.append(
            {
                "context_key": summary.provider_id,
                "category": summary.capability,
                "outcome": outcome,
            }
        )
    return tuple(observations)


def detect_invocation_patterns(
    *,
    summaries: tuple[InvocationAuditSummary, ...],
    min_frequency: int = 3,
) -> tuple[PatternSignal, ...]:
    observations = synthesize_pattern_observations(summaries=summaries)
    pattern = detect_patterns(
        observations=observations,
        min_frequency=min_frequency,
    )
    return pattern.signals


def build_evolution_proposal_from_cycle(
    *,
    proposal_id: str,
    cycle: EvaluationCycleResult,
    risk_level: str = "medium",
    confidence: float = 0.7,
) -> EvolutionProposal:
    failed_capabilities = sorted({
        summary.capability
        for summary in cycle.summaries
        if summary.audit_outcome not in ("ok", "replayed")
    })
    problem = "Failed or blocked invocations detected: " + ", ".join(
        failed_capabilities[:5]
    )
    change = (
        "Tune provider selection, side-effect policy, or audit ledger "
        "based on failed capabilities"
    )
    impact = "Reduce invocation failure rate and improve quality score"
    evidence = (
        cycle.audit_report.overall.label,
        f"score={cycle.quality_scores.overall:.2f}",
    )
    return propose_evolution(
        proposal_id=proposal_id,
        title="Tune failed capabilities",
        problem=problem or "no failed capabilities",
        proposed_change=change,
        expected_impact=impact,
        risk_level=risk_level,
        confidence=confidence,
        evidence_refs=evidence,
    )


def record_benchmark_for_cycle(
    *,
    name: str,
    cycle: EvaluationCycleResult,
    last_run_at: str,
) -> LearningBenchmark | None:
    if cycle.quality_scores.overall <= 0.0:
        return None
    return run_learning_benchmark(
        name=name,
        score=cycle.quality_scores.overall,
        last_run_at=last_run_at,
    )


def finalize_pending_ab_test(
    *,
    test_id: str,
    min_samples: int = 5,
    min_confidence: float = 0.6,
    higher_is_better: bool = True,
) -> ABTestResult:
    return finalize_test(
        test_id=test_id,
        min_samples=min_samples,
        min_confidence=min_confidence,
        higher_is_better=higher_is_better,
    )


def summarize_tool_verdicts(
    *,
    tool_metrics: dict[str, dict[str, int]],
) -> dict[str, str]:
    verdicts: dict[str, str] = {}
    for tool_name, counts in tool_metrics.items():
        success = int(counts.get("success", 0))
        failure = int(counts.get("failure", 0))
        latency = float(counts.get("avg_latency_ms", 0.0))
        cost = float(counts.get("cost_score", 0.5))
        if success + failure < 3:
            verdicts[tool_name] = TOOL_MONITOR
            continue
        if failure > success:
            verdicts[tool_name] = TOOL_REMOVE
            continue
        if cost > 0.7 and latency > 3000:
            verdicts[tool_name] = TOOL_DEMOTE
            continue
        verdicts[tool_name] = TOOL_PROMOTE
    return verdicts
