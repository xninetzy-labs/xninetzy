from __future__ import annotations

from xninetzy.os.research.sources.base import SourceAdapter
from xninetzy.os.research.sources.rate_limit import (
    CircuitBreakerGuard,
    RateLimiter,
)

SOURCE_REGISTRY: dict[str, SourceAdapter] = {}


def register_adapter(adapter: SourceAdapter) -> None:
    SOURCE_REGISTRY[adapter.id] = adapter


def get_adapter(source_id: str) -> SourceAdapter | None:
    return SOURCE_REGISTRY.get(source_id)


def list_adapters() -> list[str]:
    return sorted(SOURCE_REGISTRY.keys())


def clear_registry() -> None:
    SOURCE_REGISTRY.clear()


def build_rate_limiter(adapter: SourceAdapter) -> RateLimiter:
    return RateLimiter(
        requests_per_minute=adapter.rate_limit.requests_per_minute,
        burst=adapter.rate_limit.burst,
    )


def build_breaker(adapter: SourceAdapter) -> CircuitBreakerGuard:
    return CircuitBreakerGuard(adapter.circuit_breaker)
