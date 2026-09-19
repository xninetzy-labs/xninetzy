from __future__ import annotations

from xninetzy.context.gateway.registry import (
    ProviderRecord,
    SeedProviderResult,
    list_lifecycle,
    list_providers,
    record_lifecycle_event,
    seed_providers_from_external,
    upsert_provider,
)
from xninetzy.context.gateway.router import (
    RouterCandidate,
    RouterDecision,
    record_decision_outcome,
    resolve_route,
)
from xninetzy.context.gateway.trust import (
    HEALTH_DEGRADED,
    HEALTH_DOWN,
    HEALTH_OK,
    HEALTH_UNKNOWN,
    RISK_CLASS_TO_TRUST,
    TRANSPORT_HTTP,
    TRANSPORT_LOCAL,
    TRANSPORT_STDIO,
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_LOCAL,
    TRUST_TIER_THIRD_PARTY,
    TRUST_TIER_UNVERIFIED,
    trust_for_risk,
)

PACKAGE_MARKER: str = "xninetzy.context.gateway"

__all__ = [
    "HEALTH_DEGRADED",
    "HEALTH_DOWN",
    "HEALTH_OK",
    "HEALTH_UNKNOWN",
    "PACKAGE_MARKER",
    "ProviderRecord",
    "RISK_CLASS_TO_TRUST",
    "RouterCandidate",
    "RouterDecision",
    "SeedProviderResult",
    "TRANSPORT_HTTP",
    "TRANSPORT_LOCAL",
    "TRANSPORT_STDIO",
    "TRUST_TIER_BLOCKED",
    "TRUST_TIER_KNOWN_EXTERNAL",
    "TRUST_TIER_LOCAL",
    "TRUST_TIER_THIRD_PARTY",
    "TRUST_TIER_UNVERIFIED",
    "list_lifecycle",
    "list_providers",
    "record_decision_outcome",
    "record_lifecycle_event",
    "resolve_route",
    "seed_providers_from_external",
    "trust_for_risk",
    "upsert_provider",
]
