from __future__ import annotations

import time

from xninetzy.context.gateway.provider_cache import (
    cache_stats,
    cached_list_providers,
    invalidate_cache,
)


def setup_function(_fn):
    invalidate_cache()


def teardown_function(_fn):
    invalidate_cache()


def test_cache_returns_empty_when_no_providers(tmp_path, monkeypatch):
    db = tmp_path / "pcache.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    cfg.get_settings.cache_clear()
    run_migrations()
    invalidate_cache()
    records = cached_list_providers()
    assert records == ()


def test_cache_hit_reuses_records(tmp_path, monkeypatch):
    db = tmp_path / "pcache.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.context.gateway.registry import upsert_provider
    from xninetzy.context.gateway.trust import (
        HEALTH_OK,
        TRANSPORT_STDIO,
        TRUST_TIER_KNOWN_EXTERNAL,
    )
    cfg.get_settings.cache_clear()
    run_migrations()
    upsert_provider(
        provider_id="p1",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("cap1",),
        health_state=HEALTH_OK,
    )
    invalidate_cache()
    first = cached_list_providers()
    second = cached_list_providers()
    assert len(first) == 1
    assert len(second) == 1
    assert first is not second or first == second


def test_upsert_invalidates_cache(tmp_path, monkeypatch):
    db = tmp_path / "pcache.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.context.gateway.registry import upsert_provider
    from xninetzy.context.gateway.trust import (
        HEALTH_OK,
        TRANSPORT_STDIO,
        TRUST_TIER_KNOWN_EXTERNAL,
    )
    cfg.get_settings.cache_clear()
    run_migrations()
    upsert_provider(
        provider_id="p1",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("cap1",),
        health_state=HEALTH_OK,
    )
    invalidate_cache()
    first = cached_list_providers()
    assert len(first) == 1
    upsert_provider(
        provider_id="p2",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("cap2",),
        health_state=HEALTH_OK,
    )
    after = cached_list_providers()
    assert len(after) == 2


def test_cache_expires_after_ttl(tmp_path, monkeypatch):
    db = tmp_path / "pcache.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.db.sqlite import connect
    from xninetzy.context.gateway.trust import (
        HEALTH_OK,
        TRUST_TIER_KNOWN_EXTERNAL,
    )
    cfg.get_settings.cache_clear()
    run_migrations()
    invalidate_cache()
    invalidate_cache("test")
    from xninetzy.db.sqlite import connect as _c
    with _c() as conn:
        conn.execute(
            """
            INSERT INTO mcp_providers
                (provider_id, transport, endpoint, trust_tier, risk_class,
                 capabilities_json, health_state, last_seen_at,
                 metadata_json, created_at, updated_at)
            VALUES (?, 'stdio', 'cmd', ?, 'low', '["cap1"]', ?, ?, '{}', ?, ?)
            """,
            (
                "p1",
                int(TRUST_TIER_KNOWN_EXTERNAL),
                HEALTH_OK,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
    cached_list_providers(ttl_seconds=0.0)
    time.sleep(0.01)
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO mcp_providers
                (provider_id, transport, endpoint, trust_tier, risk_class,
                 capabilities_json, health_state, last_seen_at,
                 metadata_json, created_at, updated_at)
            VALUES (?, 'stdio', 'cmd', ?, 'low', '["cap2"]', ?, ?, '{}', ?, ?)
            """,
            (
                "p2",
                int(TRUST_TIER_KNOWN_EXTERNAL),
                HEALTH_OK,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
    out = cached_list_providers(ttl_seconds=0.0)
    assert len(out) == 2


def test_invalidate_cache_clears_entries():
    invalidate_cache()
    cached_list_providers(cache_key="test")
    invalidate_cache("test")
    invalidate_cache()


def test_cache_stats_returns_dict():
    stats = cache_stats()
    for key in ("entries", "max_size", "ttl_seconds"):
        assert key in stats
