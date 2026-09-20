from __future__ import annotations

import hashlib
import time
from collections import OrderedDict
from threading import Lock


_CACHE_MAX_SIZE = 256
_CACHE_TTL_SECONDS = 30.0

_LOCK = Lock()
_CACHE: OrderedDict[str, tuple[float, str]] = OrderedDict()


def _hash_query(query: str, owner: str) -> str:
    blob = f"{owner}::{query}".encode("utf-8", errors="replace")
    return hashlib.sha256(blob).hexdigest()


def get_cached(query: str, owner: str) -> str | None:
    """Return cached memory context if present and fresh; else None."""
    key = _hash_query(query, owner)
    now = time.monotonic()
    with _LOCK:
        entry = _CACHE.get(key)
        if entry is None:
            return None
        stored_at, payload = entry
        if now - stored_at > _CACHE_TTL_SECONDS:
            _CACHE.pop(key, None)
            return None
        _CACHE.move_to_end(key)
        return payload


def put_cached(query: str, owner: str, payload: str) -> None:
    key = _hash_query(query, owner)
    now = time.monotonic()
    with _LOCK:
        if key in _CACHE:
            _CACHE.move_to_end(key)
        _CACHE[key] = (now, payload)
        while len(_CACHE) > _CACHE_MAX_SIZE:
            _CACHE.popitem(last=False)


def invalidate() -> int:
    with _LOCK:
        count = len(_CACHE)
        _CACHE.clear()
        return count


def stats() -> dict:
    with _LOCK:
        return {
            "size": len(_CACHE),
            "max_size": _CACHE_MAX_SIZE,
            "ttl_seconds": _CACHE_TTL_SECONDS,
        }
