from __future__ import annotations

from typing import Final


TRUST_TIER_LOCAL: Final[int] = 0
TRUST_TIER_KNOWN_EXTERNAL: Final[int] = 1
TRUST_TIER_THIRD_PARTY: Final[int] = 2
TRUST_TIER_UNVERIFIED: Final[int] = 3
TRUST_TIER_BLOCKED: Final[int] = 4


RISK_CLASS_TO_TRUST: Final[dict[str, int]] = {
    "low": TRUST_TIER_KNOWN_EXTERNAL,
    "medium": TRUST_TIER_THIRD_PARTY,
    "high": TRUST_TIER_THIRD_PARTY,
    "unreviewed": TRUST_TIER_UNVERIFIED,
    "unknown": TRUST_TIER_UNVERIFIED,
}


def trust_for_risk(risk_class: str) -> int:
    return RISK_CLASS_TO_TRUST.get(risk_class, TRUST_TIER_UNVERIFIED)


HEALTH_OK: Final[str] = "ok"
HEALTH_DEGRADED: Final[str] = "degraded"
HEALTH_DOWN: Final[str] = "down"
HEALTH_UNKNOWN: Final[str] = "unknown"

TRANSPORT_STDIO: Final[str] = "stdio"
TRANSPORT_HTTP: Final[str] = "http"
TRANSPORT_LOCAL: Final[str] = "local"
