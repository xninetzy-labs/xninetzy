from __future__ import annotations

from xninetzy.os.memory._context_cache import (
    get_cached,
    invalidate,
    put_cached,
    stats,
)


def test_get_cached_returns_none_when_empty():
    invalidate()
    assert get_cached("missing", "owner-1") is None


def test_put_then_get_round_trips():
    invalidate()
    put_cached("hello", "owner-1", "result-A")
    assert get_cached("hello", "owner-1") == "result-A"


def test_cache_keyed_by_owner():
    invalidate()
    put_cached("hello", "owner-A", "for-A")
    put_cached("hello", "owner-B", "for-B")
    assert get_cached("hello", "owner-A") == "for-A"
    assert get_cached("hello", "owner-B") == "for-B"


def test_invalidate_clears_cache():
    put_cached("k", "owner-1", "v")
    cleared = invalidate()
    assert cleared >= 1
    assert get_cached("k", "owner-1") is None


def test_stats_returns_metadata():
    invalidate()
    put_cached("a", "o", "x")
    s = stats()
    assert s["size"] == 1
    assert s["max_size"] >= 1
    assert s["ttl_seconds"] > 0
