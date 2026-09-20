from __future__ import annotations

import time
from pathlib import Path

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.os.lightning.capability_cache import (
    DEFAULT_TTL_SECONDS,
    capability_toggle_lookup,
    clear_capability_toggle,
    disabled_capabilities,
    invalidate_capability_cache,
    write_capability_toggle,
)


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "capcache.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    invalidate_capability_cache()
    yield db_file
    invalidate_capability_cache()


def test_capability_default_enabled():
    assert capability_toggle_lookup("never_toggled") is True


def test_write_capability_toggle_persists():
    write_capability_toggle("do_thing", False)
    invalidate_capability_cache()
    assert capability_toggle_lookup("do_thing") is False


def test_capability_cache_hit_returns_immediately(monkeypatch):
    write_capability_toggle("do_thing", False)
    invalidate_capability_cache()
    capability_toggle_lookup("do_thing")
    calls: list[str] = []

    def _spy(*args, **kwargs):
        calls.append("connect")
        from xninetzy.db.sqlite import connect as _real
        return _real()

    monkeypatch.setattr(
        "xninetzy.os.lightning.capability_cache.connect", _spy
    )
    capability_toggle_lookup("do_thing")
    assert calls == []


def test_clear_capability_toggle_removes_row():
    write_capability_toggle("do_thing", False)
    invalidate_capability_cache()
    assert capability_toggle_lookup("do_thing") is False
    clear_capability_toggle("do_thing")
    assert capability_toggle_lookup("do_thing") is True


def test_disabled_capabilities_returns_tuple():
    write_capability_toggle("a", False)
    write_capability_toggle("b", False)
    invalidate_capability_cache()
    disabled = disabled_capabilities()
    assert "a" in disabled
    assert "b" in disabled


def test_disabled_capabilities_caches():
    write_capability_toggle("a", False)
    invalidate_capability_cache()
    first = disabled_capabilities()
    write_capability_toggle("c", False)
    second = disabled_capabilities()
    assert first == second


def test_invalidate_capability_cache_clears_all():
    write_capability_toggle("a", False)
    invalidate_capability_cache()
    assert capability_toggle_lookup("a") is False
    invalidate_capability_cache()
    assert capability_toggle_lookup("a") is False


def test_ttl_default_is_reasonable():
    assert DEFAULT_TTL_SECONDS > 0
    assert DEFAULT_TTL_SECONDS <= 300
