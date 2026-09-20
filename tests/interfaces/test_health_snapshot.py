from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def _isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "health.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.db.sqlite import init_db

    cfg.get_settings.cache_clear()
    init_db()
    run_migrations()
    yield db


def test_xninetzy_health_snapshot_returns_full_payload(_isolated_db):
    from xninetzy.tools.internal.evaluation import xninetzy_health_snapshot

    out = xninetzy_health_snapshot.invoke({})
    payload = json.loads(out)
    assert "provider_cache" in payload
    assert "memory_context_cache" in payload
    assert "retry_budget" in payload
    assert "perf_snapshot" in payload
    assert "settings" in payload
    assert "row_counts" in payload
    assert "memories_active" in payload["row_counts"]
    assert payload["row_counts"]["agent_episodes"] == 0


def test_xninetzy_health_snapshot_reflects_settings(_isolated_db, monkeypatch):
    from xninetzy.core import config as cfg

    monkeypatch.setenv("MEMORY_RETENTION_DAYS", "7")
    monkeypatch.setenv("MEMORY_PER_USER_CAP", "100")
    cfg.get_settings.cache_clear()

    from xninetzy.tools.internal.evaluation import xninetzy_health_snapshot

    out = xninetzy_health_snapshot.invoke({})
    payload = json.loads(out)
    assert payload["settings"]["memory_retention_days"] == 7
    assert payload["settings"]["memory_per_user_cap"] == 100
