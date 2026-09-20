from __future__ import annotations

import json
from pathlib import Path

import pytest


@pytest.fixture
def _isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "diag.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    monkeypatch.setenv("MEMORY_RETENTION_DAYS", "30")
    monkeypatch.setenv("MEMORY_PER_USER_CAP", "3")
    monkeypatch.setenv("MEMORY_RETENTION_IMPORTANCE_FLOOR", "0.7")
    monkeypatch.setenv("IMPROVEMENT_RETENTION_DAYS", "30")
    from xninetzy.core import config as cfg
    from xninetzy.db.migrations import run_migrations
    from xninetzy.db.sqlite import init_db

    cfg.get_settings.cache_clear()
    init_db()
    run_migrations()
    yield db


def test_xninetzy_self_test_returns_structured_report(_isolated_db):
    from xninetzy.tools.internal.evaluation import xninetzy_self_test

    out = xninetzy_self_test.invoke({})
    payload = json.loads(out)
    assert payload["status"] == "ok"
    assert payload["tools_total"] >= 250
    assert "feature_pack" in payload
    assert "risk" in payload
    assert "core" in payload["feature_pack"]
    assert "skill_health" in payload


def test_retention_prune_now_runs_and_reports(_isolated_db):
    from xninetzy.os.memory.memory_store import add_memory
    from xninetzy.tools.ecosystem.life_tools import retention_prune_now

    add_memory(user_id="u1", content="hello world this is long enough", importance=0.1)
    add_memory(user_id="u1", content="another long enough memory entry", importance=0.1)
    out = retention_prune_now.invoke({})
    assert "Retention prune selesai" in out
    assert "deactivated_old" in out


def test_retention_prune_now_handles_empty_db(_isolated_db):
    from xninetzy.tools.ecosystem.life_tools import retention_prune_now

    out = retention_prune_now.invoke({})
    assert "Retention prune selesai" in out
    assert "deactivated_old=0" in out


def test_retention_prune_now_idempotent_replay(_isolated_db):
    from xninetzy.tools.ecosystem.life_tools import retention_prune_now

    key = "retention-prune-test-1"
    first = retention_prune_now.invoke({"idempotency_key": key})
    assert "Retention prune selesai" in first
    second = retention_prune_now.invoke({"idempotency_key": key})
    assert "replay" in second.lower() or "sudah dijalankan" in second.lower()
