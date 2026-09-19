from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from xninetzy.context.capability_graph.graph import seed_from_registry
from xninetzy.context.gateway.registry import (
    list_providers,
    record_lifecycle_event,
    upsert_provider,
)
from xninetzy.context.gateway.trust import (
    HEALTH_UNKNOWN,
    RISK_CLASS_TO_TRUST,
    TRANSPORT_HTTP,
    TRANSPORT_LOCAL,
    TRANSPORT_STDIO,
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_LOCAL,
    TRUST_TIER_UNVERIFIED,
    trust_for_risk,
)
from xninetzy.context.intake.classify import ClassificationResult
from xninetzy.context.intake.urls import URLKind, canonicalize_github_url, sha256_hex


STAGE_DISCOVERED: str = "discovered"
STAGE_CLASSIFIED: str = "classified"
STAGE_REGISTERED: str = "registered"
STAGE_PROMOTED: str = "promoted"
STAGE_REJECTED: str = "rejected"

INTAKE_RISK_CLASS: str = "unreviewed"
INTAKE_DEFAULT_TIER: int = TRUST_TIER_UNVERIFIED

PROMOTION_MAX_TIER: int = TRUST_TIER_KNOWN_EXTERNAL

_VALID_TRANSPORTS: frozenset[str] = frozenset(
    {TRANSPORT_STDIO, TRANSPORT_HTTP, TRANSPORT_LOCAL}
)


@dataclass(frozen=True, slots=True)
class IntakeRegistrationResult:
    provider_id: str
    trust_tier: int
    risk_class: str
    idempotency_key: str
    stage_sequence: tuple[str, ...]
    reused: bool
    capabilities: tuple[str, ...]


def _coerce_transport(value: str | None) -> str:
    if value is None:
        return TRANSPORT_LOCAL
    candidate = str(value).strip().lower()
    if candidate in _VALID_TRANSPORTS:
        return candidate
    return TRANSPORT_LOCAL


def _clamp_promotion_tier(target_tier: int) -> int:
    if target_tier < TRUST_TIER_LOCAL:
        return TRUST_TIER_LOCAL
    if target_tier > PROMOTION_MAX_TIER:
        return PROMOTION_MAX_TIER
    return target_tier


def _provider_id_for_url(url: URLKind, fallback: str) -> str:
    if url.owner and url.repo:
        slug = f"{url.owner}/{url.repo}".lower()
    else:
        slug = (fallback or url.raw or "intake").strip().lower()
    digest = sha256_hex(slug)[:12]
    safe = re.sub(r"[^a-z0-9_.-]", "-", slug)
    return f"ext:{safe}:{digest}"


def _existing_provider(provider_id: str) -> bool:
    return any(record.provider_id == provider_id for record in list_providers())


def _capability_node(capability: str):
    from xninetzy.context.capability_graph.graph import CapabilityNode
    return CapabilityNode(
        capability=capability,
        surface=f"tool:{capability}",
        aliases=(capability, capability.replace("_", " ")),
    )


def _ensure_capability_aliases(capabilities: tuple[str, ...]) -> tuple[str, ...]:
    if not capabilities:
        return ()
    seed_from_registry(nodes=[_capability_node(capability) for capability in capabilities])
    return capabilities


def register_from_classification(
    *,
    source: URLKind,
    classification: ClassificationResult,
    endpoint: str | None = None,
    actor: str = "intake",
    idempotency_key: str | None = None,
    override_tier: int | None = None,
    override_capabilities: tuple[str, ...] | None = None,
    risk_class: str | None = None,
) -> IntakeRegistrationResult:
    canonical = canonicalize_github_url(source)
    key_source = idempotency_key or sha256_hex(f"{canonical}|{classification.kind}")
    provider_id = _provider_id_for_url(source, fallback=classification.kind)
    capabilities = override_capabilities or classification.suggested_capabilities
    transport = _coerce_transport(classification.suggested_transport)
    chosen_risk = risk_class or INTAKE_RISK_CLASS
    base_tier = trust_for_risk(chosen_risk)
    if override_tier is None:
        chosen_tier = max(int(base_tier), INTAKE_DEFAULT_TIER)
    else:
        chosen_tier = int(override_tier)
    record_lifecycle_event(
        capability=capabilities[0] if capabilities else classification.kind,
        provider_id=provider_id,
        stage=STAGE_DISCOVERED,
        notes=f"url={source.raw}; kind={classification.kind}",
        actor=actor,
    )
    record_lifecycle_event(
        capability=capabilities[0] if capabilities else classification.kind,
        provider_id=provider_id,
        stage=STAGE_CLASSIFIED,
        notes=f"transport={transport}; risk={chosen_risk}; tier={chosen_tier}",
        actor=actor,
    )
    reused = _existing_provider(provider_id)
    upsert_provider(
        provider_id=provider_id,
        transport=transport,
        endpoint=endpoint,
        trust_tier=chosen_tier,
        risk_class=chosen_risk,
        capabilities=capabilities,
        health_state=HEALTH_UNKNOWN,
        metadata={
            "source_url": source.raw,
            "canonical_url": canonical,
            "intake_kind": classification.kind,
            "idempotency_key": key_source,
            "actor": actor,
        },
    )
    record_lifecycle_event(
        capability=capabilities[0] if capabilities else classification.kind,
        provider_id=provider_id,
        stage=STAGE_REGISTERED,
        notes=f"reused={reused}; idempotency_key={key_source}",
        actor=actor,
    )
    ensure_capability_aliases_safe(capabilities)
    return IntakeRegistrationResult(
        provider_id=provider_id,
        trust_tier=chosen_tier,
        risk_class=chosen_risk,
        idempotency_key=key_source,
        stage_sequence=(STAGE_DISCOVERED, STAGE_CLASSIFIED, STAGE_REGISTERED),
        reused=reused,
        capabilities=capabilities,
    )


def ensure_capability_aliases_safe(capabilities: tuple[str, ...]) -> tuple[str, ...]:
    if not capabilities:
        return ()
    return _ensure_capability_aliases(capabilities)


def promote_provider_tier(
    *,
    provider_id: str,
    new_tier: int,
    actor: str,
    rationale: str,
) -> int:
    if not actor:
        raise ValueError("actor required for promotion")
    if not rationale:
        raise ValueError("rationale required for promotion")
    if new_tier >= TRUST_TIER_BLOCKED:
        raise ValueError("promotion target tier must be below blocked")
    target_tier = _clamp_promotion_tier(int(new_tier))
    existing = [
        record for record in list_providers() if record.provider_id == provider_id
    ]
    if not existing:
        raise ValueError(f"unknown provider: {provider_id}")
    record = existing[0]
    if record.trust_tier <= target_tier:
        return record.trust_tier
    upsert_provider(
        provider_id=provider_id,
        transport=record.transport,
        endpoint=record.endpoint,
        trust_tier=target_tier,
        risk_class=record.risk_class,
        capabilities=record.capabilities,
        health_state=record.health_state,
        metadata={**record.metadata, "promotion_rationale": rationale, "promoted_by": actor},
    )
    record_lifecycle_event(
        capability=record.capabilities[0] if record.capabilities else provider_id,
        provider_id=provider_id,
        stage=STAGE_PROMOTED,
        notes=f"from_tier={record.trust_tier}; to_tier={target_tier}; rationale={rationale}",
        actor=actor,
    )
    return target_tier


def reject_provider(
    *,
    provider_id: str,
    actor: str,
    rationale: str,
) -> int:
    if not actor or not rationale:
        raise ValueError("actor and rationale required for rejection")
    existing = [
        record for record in list_providers() if record.provider_id == provider_id
    ]
    if not existing:
        raise ValueError(f"unknown provider: {provider_id}")
    record = existing[0]
    upsert_provider(
        provider_id=provider_id,
        transport=record.transport,
        endpoint=record.endpoint,
        trust_tier=TRUST_TIER_BLOCKED,
        risk_class=record.risk_class,
        capabilities=record.capabilities,
        health_state=record.health_state,
        metadata={**record.metadata, "rejection_rationale": rationale, "rejected_by": actor},
    )
    record_lifecycle_event(
        capability=record.capabilities[0] if record.capabilities else provider_id,
        provider_id=provider_id,
        stage=STAGE_REJECTED,
        notes=f"rationale={rationale}",
        actor=actor,
    )
    return TRUST_TIER_BLOCKED


def intake_constants() -> dict[str, Any]:
    return {
        "RISK_CLASS_TO_TRUST": dict(RISK_CLASS_TO_TRUST),
        "INTAKE_DEFAULT_TIER": INTAKE_DEFAULT_TIER,
        "PROMOTION_MAX_TIER": PROMOTION_MAX_TIER,
        "STAGES": (
            STAGE_DISCOVERED,
            STAGE_CLASSIFIED,
            STAGE_REGISTERED,
            STAGE_PROMOTED,
            STAGE_REJECTED,
        ),
    }
