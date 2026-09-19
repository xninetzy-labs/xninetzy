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


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class PipelineOutcome:
    invocation: InvocationContext
    route_decision: Any
    policy: PolicyDecision
    audit: AuditLedgerEntry
    result: InvocationResult | None


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
    result = InvocationResult(
        request_id=request.request_id,
        provider_id=chosen_provider_id,
        capability=chosen_capability,
        outcome=OUTCOME_OK,
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
    )


def execute_pipeline(
    requests: list[InvocationRequest],
    *,
    invocation_override: Invocable | None = None,
    now: str | None = None,
) -> list[PipelineOutcome]:
    return [execute_invocation(req, invocation_override=invocation_override, now=now) for req in requests]
