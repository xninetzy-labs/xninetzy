from __future__ import annotations

from dataclasses import dataclass

from xninetzy.context.gateway.provider_cache import cached_list_providers
from xninetzy.context.gateway.registry import ProviderRecord
from xninetzy.context.gateway.router import (
    RouterDecision,
    resolve_route,
)
from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_UNVERIFIED,
)
from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_NON_IDEMPOTENT_WRITE,
    SIDE_EFFECT_EXTERNAL,
    classify_side_effect,
)
from xninetzy.context.invocation.contract import InvocationRequest


INVOCATION_FORBIDDEN_KINDS: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class InvocationRoute:
    request: InvocationRequest
    decision: RouterDecision
    min_trust_tier: int
    eligible_providers: tuple[ProviderRecord, ...]


def _min_trust_for_side_effect(side_effect_name: str | None) -> int:
    cls = classify_side_effect(side_effect_name)
    if cls.name in (SIDE_EFFECT_NON_IDEMPOTENT_WRITE, SIDE_EFFECT_EXTERNAL):
        return TRUST_TIER_KNOWN_EXTERNAL
    if cls.name == SIDE_EFFECT_IRREVERSIBLE:
        return TRUST_TIER_KNOWN_EXTERNAL
    return TRUST_TIER_UNVERIFIED


def _eligible_providers(
    providers: list[ProviderRecord], capability: str
) -> list[ProviderRecord]:
    eligible: list[ProviderRecord] = []
    for provider in providers:
        if provider.trust_tier >= TRUST_TIER_BLOCKED:
            continue
        if provider.capabilities and capability not in provider.capabilities:
            continue
        eligible.append(provider)
    return eligible


def resolve_invocation_route(
    request: InvocationRequest,
    *,
    providers: list[ProviderRecord] | None = None,
    include_local_self: bool = False,
) -> InvocationRoute:
    pool = providers if providers is not None else list(cached_list_providers())
    policy_min_tier = _min_trust_for_side_effect(request.side_effect)
    requested_min_tier = (
        request.min_trust_tier if request.min_trust_tier is not None else policy_min_tier
    )
    effective_min_tier = min(policy_min_tier, requested_min_tier)
    decision = resolve_route(
        request_id=request.request_id,
        intent=request.intent,
        query=f"{request.capability} {request.query}".strip(),
        context_key=request.context_key,
        providers=pool,
        min_trust_tier=effective_min_tier,
        include_local_self=include_local_self,
    )
    eligible = _eligible_providers(
        pool, capability=request.capability
    )
    return InvocationRoute(
        request=request,
        decision=decision,
        min_trust_tier=effective_min_tier,
        eligible_providers=tuple(eligible),
    )
