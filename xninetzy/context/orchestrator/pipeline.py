from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from xninetzy.context.gateway.router import (
    RouterCandidate,
    RouterDecision,
    record_decision_outcome,
)
from xninetzy.context.gateway.trust import (
    HEALTH_OK,
    TRANSPORT_LOCAL,
    TRUST_TIER_LOCAL,
)
from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_READ_ONLY,
)
from xninetzy.context.invocation.contract import (
    InvocationContext,
    InvocationRequest,
    InvocationResult,
    build_invocation_context,
)
from xninetzy.context.invocation.resolve import resolve_invocation_route
from xninetzy.context.reasoning.critic import (
    CRITIC_VERDICT_FAIL,
    CRITIC_VERDICT_WARN,
    CriticVerdict,
    critique_outcome,
)
from xninetzy.context.reasoning.depth import classify_request_depth
from xninetzy.context.reasoning.stop import (
    STOP_HALT,
    STOP_REPLAN,
    StopDecision,
    should_stop,
)
from xninetzy.context.orchestrator.invokable import (
    Invocable,
    InvocableError,
    resolve_invokable,
)
from xninetzy.context.policy.audit import (
    AUDIT_OUTCOME_BLOCKED,
    AUDIT_OUTCOME_ERROR,
    AUDIT_OUTCOME_OK,
    AuditLedgerEntry,
    complete_audit_entry,
    find_audit_by_idempotency,
    record_audit_start,
)
from xninetzy.context.policy.gate import (
    POLICY_BLOCK,
    POLICY_REQUIRE_APPROVAL,
    PolicyDecision,
    evaluate_policy,
)


OUTCOME_OK: str = AUDIT_OUTCOME_OK
OUTCOME_ERROR: str = AUDIT_OUTCOME_ERROR
OUTCOME_BLOCKED: str = AUDIT_OUTCOME_BLOCKED
OUTCOME_REPLAYED: str = "replayed"
OUTCOME_REJECTED_POLICY: str = "rejected_policy"
OUTCOME_CRITIC_FAIL: str = "critic_fail"
OUTCOME_REPLAN: str = "replan"


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    invocation: InvocationContext
    route_decision: Any
    policy: PolicyDecision
    audit: AuditLedgerEntry
    result: InvocationResult | None
    critic: CriticVerdict | None = None
    stop: StopDecision | None = None
    depth_name: str | None = None


def _build_route_for_local_self(
    request: InvocationRequest,
    chosen_provider_id: str,
    chosen_capability: str,
    context_key: str,
) -> Any:
    from xninetzy.context.gateway.router import (
        RouterCandidate,
        RouterDecision,
    )
    candidate = RouterCandidate(
        provider_id=chosen_provider_id,
        capability=chosen_capability,
        transport=TRANSPORT_LOCAL,
        trust_tier=TRUST_TIER_LOCAL,
        health_state=HEALTH_OK,
        score=1.0,
        reasons=("local self",),
    )
    return RouterDecision(
        request_id=request.request_id,
        intent=request.intent,
        context_key=context_key,
        chosen=candidate,
        candidates=(candidate,),
        fallback_used=False,
        stage_trace=(),
    )


def _find_invokable(provider_id: str) -> Invocable | None:
    if provider_id == "local:xninetzy":
        return None
    return resolve_invokable(provider_id)


def _build_request_for_capability(
    request: InvocationRequest,
    capability: str,
) -> InvocationRequest:
    return InvocationRequest(
        request_id=request.request_id,
        intent=request.intent,
        capability=capability,
        context_key=request.context_key,
        query=request.query,
        args=request.args,
        side_effect=request.side_effect,
        idempotency_key=request.idempotency_key,
        approval_id=request.approval_id,
        min_trust_tier=request.min_trust_tier,
        metadata=request.metadata,
    )


def execute_invocation(
    request: InvocationRequest,
    *,
    invocation_override: Invocable | None = None,
    now: str | None = None,
) -> PipelineOutcome:
    invocation = build_invocation_context(request)
    side_effect_name = (
        invocation.side_effect_class.name
        if invocation.side_effect_class is not None
        else SIDE_EFFECT_READ_ONLY
    )
    audit_skippable = bool(request.metadata.get("audit_skippable", False))
    if (
        audit_skippable
        and side_effect_name == SIDE_EFFECT_READ_ONLY
        and invocation_override is None
    ):
        from xninetzy.context.orchestrator.invokable import resolve_invokable
        invokable = resolve_invokable("local:xninetzy")
        if invokable is None:
            policy = evaluate_policy(
                trust_tier=TRUST_TIER_LOCAL,
                side_effect=side_effect_name,
                approval_id=request.approval_id,
                idempotency_key=request.idempotency_key,
            )
            depth = classify_request_depth(
                side_effect=side_effect_name, trust_tier=TRUST_TIER_LOCAL
            )
            result = InvocationResult(
                request_id=request.request_id,
                provider_id="local:xninetzy",
                capability=request.capability,
                outcome=OUTCOME_OK,
                latency_ms=0,
                payload=None,
                audited=False,
            )
            return PipelineOutcome(
                invocation=invocation,
                route_decision=_build_route_for_local_self(
                    request, "local:xninetzy", request.capability, request.context_key
                ),
                policy=policy,
                audit=AuditLedgerEntry(
                    id=0,
                    request_id=request.request_id,
                    provider_id="local:xninetzy",
                    capability=request.capability,
                    side_effect_class=side_effect_name,
                    idempotency_key=request.idempotency_key,
                    approval_id=request.approval_id,
                    args_hash=invocation.args_hash,
                    args_bytes=invocation.args_bytes,
                    context_key=request.context_key,
                    outcome=None,
                    latency_ms=None,
                    error=None,
                    started_at=now or _utcnow(),
                    finished_at=None,
                ),
                result=result,
                depth_name=depth.name,
            )
    route = resolve_invocation_route(request)
    chosen = route.decision.chosen
    if chosen is None and route.eligible_providers:
        fallback_provider = route.eligible_providers[0]
        chosen = RouterCandidate(
            provider_id=fallback_provider.provider_id,
            capability=fallback_provider.capabilities[0]
            if fallback_provider.capabilities
            else request.capability,
            transport=fallback_provider.transport,
            trust_tier=fallback_provider.trust_tier,
            health_state=fallback_provider.health_state,
            score=0.0,
            reasons=("eligible fallback from policy tier filter",),
        )
        route_decision = RouterDecision(
            request_id=route.decision.request_id,
            intent=route.decision.intent,
            context_key=route.decision.context_key,
            chosen=chosen,
            candidates=route.decision.candidates + (chosen,),
            fallback_used=True,
            stage_trace=route.decision.stage_trace,
        )
    else:
        route_decision = route.decision
    chosen_provider_id = chosen.provider_id if chosen is not None else "local:xninetzy"
    chosen_capability = (
        chosen.capability if chosen is not None else request.capability
    )
    if invocation_override is not None and chosen_provider_id != "local:xninetzy":
        chosen_provider_id = invocation_override.provider_id
    trust_tier = chosen.trust_tier if chosen is not None else TRUST_TIER_LOCAL
    if chosen is not None and chosen.provider_id == "local:xninetzy":
        route_decision = _build_route_for_local_self(
            request, chosen.provider_id, chosen.capability, request.context_key
        )
    policy = evaluate_policy(
        trust_tier=trust_tier,
        side_effect=side_effect_name,
        approval_id=request.approval_id,
        idempotency_key=request.idempotency_key,
    )
    replay = (
        find_audit_by_idempotency(request.idempotency_key)
        if request.idempotency_key
        else None
    )
    if policy.outcome == POLICY_BLOCK:
        audit = record_audit_start(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            side_effect_class=side_effect_name,
            idempotency_key=None,
            approval_id=request.approval_id,
            args_hash=invocation.args_hash,
            args_bytes=invocation.args_bytes,
            context_key=request.context_key,
            now=now,
        )
        audit = complete_audit_entry(
            audit_id=audit.id,
            outcome=AUDIT_OUTCOME_BLOCKED,
            error=policy.reason,
            now=now,
        )
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_BLOCKED,
            latency_ms=None,
            error=policy.reason,
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=audit,
            result=result,
        )
    if policy.outcome == POLICY_REQUIRE_APPROVAL:
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_REJECTED_POLICY,
            latency_ms=None,
            error=policy.reason,
            audited=False,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=AuditLedgerEntry(
                id=0,
                request_id=request.request_id,
                provider_id=chosen_provider_id,
                capability=chosen_capability,
                side_effect_class=side_effect_name,
                idempotency_key=request.idempotency_key,
                approval_id=request.approval_id,
                args_hash=invocation.args_hash,
                args_bytes=invocation.args_bytes,
                context_key=request.context_key,
                outcome=None,
                latency_ms=None,
                error=None,
                started_at=now or _utcnow(),
                finished_at=None,
            ),
            result=result,
        )
    if replay is not None and replay.outcome == AUDIT_OUTCOME_OK:
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=replay.provider_id,
            capability=replay.capability,
            outcome=OUTCOME_REPLAYED,
            latency_ms=replay.latency_ms,
            error=None,
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=replay,
            result=result,
        )
    invocable = (
        invocation_override
        if invocation_override is not None
        else _find_invokable(chosen_provider_id)
    )
    audit = record_audit_start(
        request_id=request.request_id,
        provider_id=chosen_provider_id,
        capability=chosen_capability,
        side_effect_class=side_effect_name,
        idempotency_key=request.idempotency_key,
        approval_id=request.approval_id,
        args_hash=invocation.args_hash,
        args_bytes=invocation.args_bytes,
        context_key=request.context_key,
        now=now,
    )
    if invocable is None:
        missing_msg = f"no invocable registered for provider_id={chosen_provider_id}"
        audit = complete_audit_entry(
            audit_id=audit.id,
            outcome=AUDIT_OUTCOME_ERROR,
            error=missing_msg,
            now=now,
        )
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_ERROR,
            latency_ms=None,
            error=missing_msg,
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=audit,
            result=result,
        )
    invoke_request = _build_request_for_capability(request, chosen_capability)
    try:
        invocable_result = invocable.invoke(invoke_request.capability, invoke_request.args)
    except InvocableError as exc:
        audit = complete_audit_entry(
            audit_id=audit.id,
            outcome=AUDIT_OUTCOME_ERROR,
            error=str(exc),
            latency_ms=None,
            now=now,
        )
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_ERROR,
            latency_ms=None,
            error=str(exc),
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=audit,
            result=result,
        )
    audit = complete_audit_entry(
        audit_id=audit.id,
        outcome=AUDIT_OUTCOME_OK,
        latency_ms=int(invocable_result.latency_ms),
        now=now,
    )
    record_decision_outcome(
        request_id=route_decision.request_id,
        outcome=AUDIT_OUTCOME_OK,
        latency_ms=int(invocable_result.latency_ms),
        success=True,
    )
    depth = classify_request_depth(
        side_effect=side_effect_name,
        trust_tier=trust_tier,
    )
    critic = critique_outcome(
        expected=OUTCOME_OK,
        actual=OUTCOME_OK,
        claims=tuple(request.metadata.get("claims", ()) or ()),
        evidence_ids=tuple(request.metadata.get("evidence_ids", ()) or ()),
        missing_evidence_codes=tuple(
            request.metadata.get("missing_evidence_codes", ()) or ()
        ),
        contradictions=tuple(request.metadata.get("contradictions", ()) or ()),
        notes=(f"depth={depth.name}",),
    )
    stop = should_stop(
        iteration=int(request.metadata.get("iteration", 0) or 0),
        steps=tuple(request.metadata.get("history", ()) or ()),
        success_criteria_met=not critic.has_blocker,
        critical_uncertainty=float(
            request.metadata.get("critical_uncertainty", 0.0) or 0.0
        ),
        min_iterations=int(request.metadata.get("min_iterations", 1) or 1),
        max_iterations=int(request.metadata.get("max_iterations", 8) or 8),
        anti_loop_window=int(request.metadata.get("anti_loop_window", 4) or 4),
    )
    if critic.verdict == CRITIC_VERDICT_FAIL:
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_CRITIC_FAIL,
            latency_ms=int(invocable_result.latency_ms),
            payload=invocable_result.payload,
            error="; ".join(d.message for d in critic.defects) or "critic failed",
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=audit,
            result=result,
            critic=critic,
            stop=stop,
            depth_name=depth.name,
        )
    if stop.outcome == STOP_REPLAN:
        result = InvocationResult(
            request_id=request.request_id,
            provider_id=chosen_provider_id,
            capability=chosen_capability,
            outcome=OUTCOME_REPLAN,
            latency_ms=int(invocable_result.latency_ms),
            payload=invocable_result.payload,
            error=stop.reason,
            audited=True,
        )
        return PipelineOutcome(
            invocation=invocation,
            route_decision=route_decision,
            policy=policy,
            audit=audit,
            result=result,
            critic=critic,
            stop=stop,
            depth_name=depth.name,
        )
    final_outcome = OUTCOME_OK
    if critic.verdict == CRITIC_VERDICT_WARN:
        final_outcome = "ok_with_warnings"
    if stop.outcome == STOP_HALT:
        final_outcome = "halted_after_success"
    result = InvocationResult(
        request_id=request.request_id,
        provider_id=chosen_provider_id,
        capability=chosen_capability,
        outcome=final_outcome,
        latency_ms=int(invocable_result.latency_ms),
        payload=invocable_result.payload,
        audited=True,
    )
    return PipelineOutcome(
        invocation=invocation,
        route_decision=route_decision,
        policy=policy,
        audit=audit,
        result=result,
        critic=critic,
        stop=stop,
        depth_name=depth.name,
    )


def execute_pipeline(
    requests: list[InvocationRequest],
    *,
    invocation_override: Invocable | None = None,
    now: str | None = None,
) -> list[PipelineOutcome]:
    return [execute_invocation(req, invocation_override=invocation_override, now=now) for req in requests]


def execute_pipeline_with_evaluation(
    requests: list[InvocationRequest],
    *,
    invocation_override: Invocable | None = None,
    now: str | None = None,
    security_indicators: tuple[str, ...] = (),
    min_confidence_to_learn: float = 0.7,
    cycle_owner: str = "system",
    cycle_id: str | None = None,
    bridge_to_learning: bool = True,
    min_failure_rate_to_propose: float = 0.25,
) -> dict[str, Any]:
    from xninetzy.context.evaluation.integration import (
        build_invocation_summary,
        evaluate_invocation_cycle,
    )
    outcomes = execute_pipeline(
        requests,
        invocation_override=invocation_override,
        now=now,
    )
    summaries = tuple(
        build_invocation_summary(
            request_id=outcome.audit.request_id,
            provider_id=outcome.audit.provider_id,
            capability=outcome.audit.capability,
            audit_outcome=outcome.audit.outcome,
            latency_ms=outcome.audit.latency_ms,
            error=outcome.audit.error,
        )
        for outcome in outcomes
    )
    cycle = evaluate_invocation_cycle(
        summaries=summaries,
        security_indicators=security_indicators,
        min_confidence_to_learn=min_confidence_to_learn,
    )
    bridge_result = None
    if bridge_to_learning and cycle.summaries:
        from xninetzy.context.evaluation.learning_bridge import (
            bridge_cycle_to_learning,
        )
        total = max(1, len(cycle.summaries))
        error_count = sum(
            1 for s in cycle.summaries if s.audit_outcome == "error"
        )
        block_count = sum(
            1
            for s in cycle.summaries
            if s.audit_outcome in ("blocked", "rejected_policy")
        )
        related = tuple(
            sorted({s.capability for s in cycle.summaries if s.audit_outcome not in ("ok", "replayed")})
        )
        import uuid as _uuid

        resolved_cycle_id = cycle_id or f"cycle-{_uuid.uuid4().hex[:12]}"
        bridge_result = bridge_cycle_to_learning(
            cycle_owner=cycle_owner,
            cycle_id=resolved_cycle_id,
            batch=cycle.learning_signals,
            error_rate=error_count / total,
            block_rate=block_count / total,
            overall_quality=cycle.quality_scores.overall,
            related_capabilities=related,
            min_failure_rate_to_propose=min_failure_rate_to_propose,
        )
    return {
        "outcomes": outcomes,
        "cycle": cycle,
        "bridge": bridge_result,
    }
