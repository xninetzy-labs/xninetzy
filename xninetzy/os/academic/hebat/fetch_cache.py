from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass
class _Entry(Generic[V]):
    value: V
    expires_at: float


class TTLCache(Generic[K, V]):
    def __init__(self) -> None:
        self._store: dict[K, _Entry[V]] = {}
        self._lock = asyncio.Lock()

    def get(self, key: K) -> V | None:
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at <= time.monotonic():
            self._store.pop(key, None)
            return None
        return entry.value

    def set(self, key: K, value: V, *, ttl: float) -> None:
        if ttl <= 0:
            return
        self._store[key] = _Entry(value=value, expires_at=time.monotonic() + ttl)

    def pop(self, key: K, default: V | None = None) -> V | None:
        entry = self._store.pop(key, None)
        if entry is None or entry.expires_at <= time.monotonic():
            return default
        return entry.value

    def clear(self) -> None:
        self._store.clear()


fetch_assignment_detail_cache: TTLCache[tuple[str, str], dict[str, Any]] = TTLCache()
