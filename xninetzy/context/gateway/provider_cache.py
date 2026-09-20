from __future__ import annotations

import time
from typing import Any

from xninetzy.context.gateway.registry import (
    ProviderRecord,
    list_providers,
)


_CACHE_TTL_SECONDS: float = 60.0
_CACHE_MAX_SIZE: int = 256


_CACHE: dict[str, tuple[float, tuple[ProviderRecord, ...]]] = {}
_METRICS: dict[str, int] = {"hits": 0, "misses": 0, "evictions": 0}


def _now() -> float:
    return time.monotonic()


def cached_list_providers(
    *,
    cache_key: str = "default",
    ttl_seconds: float = _CACHE_TTL_SECONDS,
) -> tuple[ProviderRecord, ...]:
    entry = _CACHE.get(cache_key)
    now = _now()
    if entry is not None:
        stored_at, payload = entry
        if now - stored_at < ttl_seconds:
            _METRICS["hits"] += 1
            return payload
        _CACHE.pop(cache_key, None)
    _METRICS["misses"] += 1
    records = list_providers()
    frozen = tuple(records)
    if cache_key not in _CACHE and len(_CACHE) >= _CACHE_MAX_SIZE:
        _CACHE.clear()
        _METRICS["evictions"] += 1
    _CACHE[cache_key] = (now, frozen)
    return frozen


def invalidate_cache(cache_key: str | None = None) -> None:
    if cache_key is None:
        _CACHE.clear()
    else:
        _CACHE.pop(cache_key, None)


def cache_stats() -> dict[str, Any]:
    return {
        "entries": len(_CACHE),
        "max_size": _CACHE_MAX_SIZE,
        "ttl_seconds": _CACHE_TTL_SECONDS,
        "hits": _METRICS["hits"],
        "misses": _METRICS["misses"],
        "evictions": _METRICS["evictions"],
    }
