from __future__ import annotations

from xninetzy.os.academic.hebat.fetch_cache import TTLCache


def test_pop_returns_and_removes_live_entry():
    cache = TTLCache[tuple[str, str], dict]()
    key = ("chat", "170006")
    cache.set(key, {"title": "x"}, ttl=60)

    assert cache.pop(key, None) == {"title": "x"}
    assert cache.get(key) is None


def test_pop_missing_key_returns_default():
    cache = TTLCache[tuple[str, str], dict]()

    assert cache.pop(("chat", "missing"), None) is None


def test_pop_expired_entry_returns_default():
    cache = TTLCache[tuple[str, str], dict]()
    key = ("chat", "170006")
    cache.set(key, {"title": "x"}, ttl=0.001)

    import time

    time.sleep(0.01)
    assert cache.pop(key, None) is None
    assert cache.get(key) is None
