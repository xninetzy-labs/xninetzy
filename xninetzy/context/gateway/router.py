from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Iterable

from xninetzy.context.capability_graph.semantic_match import (
    MatchResult,
    match_capability,
)
from xninetzy.context.gateway.registry import (
    ProviderRecord,
    list_providers,
    record_lifecycle_event,
)
from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_LOCAL,
    HEALTH_DOWN,
)
from xninetzy.db.sqlite import connect


MIN_TRUST_TIER_DEFAULT: int = TRUST_TIER_BLOCKED
HEALTH_PENALTY_DOWN: float = -1.0
HEALTH_PENALTY_DEGRADED: float = -0.25
HEALTH_BONUS_OK: float = 0.1


def _is_capability_enabled(capability: str) -> bool:
    """Check capability_toggles (TTL cached); default enabled if absent."""
    try:
        from xninetzy.os.lightning.capability_cache import capability_toggle_lookup
    except Exception:
        return True
    return capability_toggle_lookup(capability)


@dataclass(frozen=True, slots=True)
class RouterCandidate:
    provider_id: str
    capability: str
    transport: str
    trust_tier: int
    health_state: str
    score: float
    reasons: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class RouterDecision:
    request_id: str
    intent: str
    context_key: str
    chosen: RouterCandidate | None
    candidates: tuple[RouterCandidate, ...]
    fallback_used: bool
    stage_trace: tuple[dict, ...] = field(default_factory=tuple)


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _health_adjustment(health_state: str) -> float:
    if health_state == HEALTH_DOWN:
        return HEALTH_PENALTY_DOWN
    if health_state == "degraded":
        return HEALTH_PENALTY_DEGRADED
    if health_state == "ok":
        return HEALTH_BONUS_OK
    return 0.0


def _tier_score(trust_tier: int) -> float:
    return max(0.0, 1.0 - (0.25 * trust_tier))


def _score_candidate(
    *,
    provider: ProviderRecord,
    capability_match: MatchResult,
) -> RouterCandidate:
    reasons: list[str] = []
    base = capability_match.score
    reasons.append(f"match_score={base}")
    tier_component = _tier_score(provider.trust_tier)
    reasons.append(f"tier={provider.trust_tier} -> {round(tier_component, 3)}")
    health_component = _health_adjustment(provider.health_state)
    if health_component != 0.0:
        reasons.append(f"health={provider.health_state} -> {health_component}")
    trust_blocked = provider.trust_tier >= TRUST_TIER_BLOCKED
    final = base + tier_component + health_component
    if trust_blocked:
        final = min(final, 0.0)
        reasons.append("blocked tier clamps score to 0")
    return RouterCandidate(
        provider_id=provider.provider_id,
        capability=capability_match.capability,
        transport=provider.transport,
        trust_tier=provider.trust_tier,
        health_state=provider.health_state,
        score=round(final, 4),
        reasons=tuple(reasons),
    )


def _resolve_capability(query: str) -> tuple[MatchResult | None, list[MatchResult]]:
    matches = match_capability(query, top_k=5)
    if not matches:
        return None, []
    return matches[0], matches


def _eligible_providers(
    providers: Iterable[ProviderRecord],
    *,
    capability: str,
    min_trust_tier: int,
) -> list[ProviderRecord]:
    eligible: list[ProviderRecord] = []
    for provider in providers:
        if provider.trust_tier > min_trust_tier:
            continue
        if provider.trust_tier >= TRUST_TIER_BLOCKED:
            continue
        if provider.capabilities and capability not in provider.capabilities:
            continue
        eligible.append(provider)
    return eligible


def _bandit_boost(context_key: str, provider_id: str) -> tuple[float, int, int]:
    with connect() as conn:
        row = conn.execute(
            "SELECT sample_count, success_count FROM context_source_stats "
            "WHERE context_key = ? AND source_kind = ?",
            (context_key, f"mcp:{provider_id}"),
        ).fetchone()
    if row is None:
        return 0.0, 0, 0
    sample_count = int(row["sample_count"])
    success_count = int(row["success_count"])
    if sample_count <= 0:
        return 0.0, sample_count, success_count
    success_rate = success_count / sample_count
    exploration = math.sqrt(2.0 * math.log(max(sample_count + 1, 2)) / sample_count)
    return round(0.05 * success_rate + 0.05 * exploration, 4), sample_count, success_count


def _local_self_candidate(
    capability: str,
    capability_match: MatchResult,
) -> RouterCandidate:
    return RouterCandidate(
        provider_id="local:xninetzy",
        capability=capability,
        transport="local",
        trust_tier=TRUST_TIER_LOCAL,
        health_state="ok",
        score=round(1.0 + capability_match.score, 4),
        reasons=("local self always eligible", f"match_score={capability_match.score}"),
    )


def resolve_route(
    *,
    request_id: str,
    intent: str,
    query: str,
    context_key: str,
    providers: list[ProviderRecord] | None = None,
    min_trust_tier: int = MIN_TRUST_TIER_DEFAULT,
    include_local_self: bool = True,
    now: str | None = None,
) -> RouterDecision:
    stamp = now or _utcnow()
    primary, all_matches = _resolve_capability(query)
    stage_trace: list[dict] = [
        {"stage": "capability_match", "matches": [m.alias for m in all_matches]},
    ]
    if primary is None:
        chosen: RouterCandidate | None = None
        if include_local_self:
            chosen = RouterCandidate(
                provider_id="local:xninetzy",
                capability="unknown",
                transport="local",
                trust_tier=TRUST_TIER_LOCAL,
                health_state="ok",
                score=0.0,
                reasons=("no capability match, defaulting to local self",),
            )
        fallback_used = True if chosen is None else True
        record_lifecycle_event(
            capability="unknown",
            provider_id="none",
            stage="route_unresolved",
            notes=f"intent={intent}; context_key={context_key}; query={query}",
            actor="router",
            now=stamp,
        )
        decision = RouterDecision(
            request_id=request_id,
            intent=intent,
            context_key=context_key,
            chosen=chosen,
            candidates=(),
            fallback_used=fallback_used,
            stage_trace=tuple(stage_trace),
        )
        _persist_decision(decision, stamp)
        return decision
    pool = providers if providers is not None else list_providers()
    eligible = _eligible_providers(
        pool, capability=primary.capability, min_trust_tier=min_trust_tier
    )
    stage_trace.append(
        {
            "stage": "provider_filter",
            "eligible": [p.provider_id for p in eligible],
            "total_providers": len(pool),
        }
    )
    if not _is_capability_enabled(primary.capability):
        decision = RouterDecision(
            request_id=request_id,
            intent=intent,
            context_key=context_key,
            chosen=None,
            candidates=(),
            fallback_used=True,
            stage_trace=tuple(stage_trace) + (
                {
                    "stage": "capability_toggle",
                    "capability": primary.capability,
                    "enabled": False,
                },
            ),
        )
        _persist_decision(decision, stamp)
        return decision
    candidates: list[RouterCandidate] = []
    if include_local_self:
        candidates.append(_local_self_candidate(primary.capability, primary))
    for provider in eligible:
        scored = _score_candidate(provider=provider, capability_match=primary)
        boost, samples, successes = _bandit_boost(context_key, provider.provider_id)
        if boost != 0.0 or samples > 0:
            new_reasons = scored.reasons + (
                f"bandit sample={samples} success={successes} boost={boost}",
            )
            scored = RouterCandidate(
                provider_id=scored.provider_id,
                capability=scored.capability,
                transport=scored.transport,
                trust_tier=scored.trust_tier,
                health_state=scored.health_state,
                score=round(scored.score + boost, 4),
                reasons=new_reasons,
            )
        candidates.append(scored)
    candidates.sort(key=lambda cand: cand.score, reverse=True)
    chosen = candidates[0] if candidates else None
    fallback_used = False
    if chosen is None:
        fallback_used = True
        record_lifecycle_event(
            capability=primary.capability,
            provider_id="none",
            stage="route_unresolved",
            notes=f"intent={intent}; context_key={context_key}",
            actor="router",
            now=stamp,
        )
    elif chosen.provider_id == "local:xninetzy" and not eligible:
        fallback_used = True
    decision = RouterDecision(
        request_id=request_id,
        intent=intent,
        context_key=context_key,
        chosen=chosen,
        candidates=tuple(candidates),
        fallback_used=fallback_used,
        stage_trace=tuple(stage_trace),
    )
    _persist_decision(decision, stamp)
    return decision


def _persist_decision(decision: RouterDecision, now: str) -> None:
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO route_decisions
                (request_id, intent, context_key, chosen_provider_id,
                 chosen_capability, chosen_tool, candidate_count, stage_trace_json,
                 final_score, fallback_used, latency_ms, outcome, owner, created_at)
            VALUES (:request_id, :intent, :context_key, :chosen_provider_id,
                    :chosen_capability, :chosen_tool, :candidate_count, :stage_trace_json,
                    :final_score, :fallback_used, :latency_ms, :outcome, :owner, :created_at)
            """,
            {
                "request_id": decision.request_id,
                "intent": decision.intent,
                "context_key": decision.context_key,
                "chosen_provider_id": decision.chosen.provider_id if decision.chosen else None,
                "chosen_capability": decision.chosen.capability if decision.chosen else None,
                "chosen_tool": decision.chosen.transport if decision.chosen else None,
                "candidate_count": len(decision.candidates),
                "stage_trace_json": __import__("json").dumps(
                    [list(stage.values()) for stage in decision.stage_trace]
                ),
                "final_score": decision.chosen.score if decision.chosen else None,
                "fallback_used": 1 if decision.fallback_used else 0,
                "latency_ms": None,
                "outcome": None,
                "owner": None,
                "created_at": now,
            },
        )


def record_decision_outcome(
    *,
    request_id: str,
    outcome: str,
    latency_ms: int | None = None,
    success: bool = True,
) -> None:
    with connect() as conn:
        conn.execute(
            "UPDATE route_decisions SET outcome = ?, latency_ms = ? WHERE request_id = ?",
            (outcome, latency_ms, request_id),
        )
        chosen_row = conn.execute(
            "SELECT chosen_provider_id, context_key FROM route_decisions "
            "WHERE request_id = ? ORDER BY id DESC LIMIT 1",
            (request_id,),
        ).fetchone()
    if chosen_row is None or not chosen_row["chosen_provider_id"]:
        return
    provider_id = str(chosen_row["chosen_provider_id"])
    context_key = str(chosen_row["context_key"])
    if provider_id.startswith("local:"):
        return
    now = _utcnow()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO context_source_stats
                (context_key, source_kind, sample_count, success_count,
                 grounded_count, reward_sum, latency_sum_ms, last_used_at)
            VALUES (?, ?, 1, ?, 0, ?, ?, ?)
            ON CONFLICT(context_key, source_kind) DO UPDATE SET
                sample_count = sample_count + 1,
                success_count = success_count + ?,
                reward_sum = reward_sum + ?,
                latency_sum_ms = latency_sum_ms + ?,
                last_used_at = excluded.last_used_at
            """,
            (
                context_key,
                f"mcp:{provider_id}",
                1 if success else 0,
                1.0 if success else 0.0,
                latency_ms or 0,
                now,
                1 if success else 0,
                1.0 if success else 0.0,
                latency_ms or 0,
            ),
        )
