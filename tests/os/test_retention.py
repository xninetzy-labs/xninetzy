from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.memory.memory_store import add_memory
from xninetzy.os.retention import prune_improvement_signals, prune_memories


@pytest.fixture
def _isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "retention.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    monkeypatch.setenv("MEMORY_RETENTION_DAYS", "30")
    monkeypatch.setenv("MEMORY_PER_USER_CAP", "3")
    monkeypatch.setenv("MEMORY_RETENTION_IMPORTANCE_FLOOR", "0.7")
    monkeypatch.setenv("IMPROVEMENT_RETENTION_DAYS", "30")
    from xninetzy.core import config as cfg

    cfg.get_settings.cache_clear()
    init_db()
    run_migrations()
    yield db


def _age_memory(memory_id: int, days_old: int) -> None:
    stamp = (datetime.now(timezone.utc) - timedelta(days=days_old)).isoformat()
    with connect() as conn:
        conn.execute(
            "UPDATE memories SET created_at=?, updated_at=? WHERE memory_id=?",
            (stamp, stamp, memory_id),
        )


def test_prune_memories_marks_old_low_importance_inactive(_isolated_db):
    for i in range(3):
        m = add_memory(user_id="u1", content=f"old entry {i}", importance=0.1)
        _age_memory(m["memory_id"], 60)
    add_memory(user_id="u1", content="recent important", importance=0.9)
    summary = prune_memories()
    assert summary["deactivated_old"] == 3
    with connect() as conn:
        active = conn.execute(
            "SELECT COUNT(*) c FROM memories WHERE user_id='u1' AND is_active=1"
        ).fetchone()["c"]
    assert active == 1


def test_prune_memories_enforces_per_user_cap(_isolated_db):
    for i in range(5):
        add_memory(user_id="u1", content=f"recent {i}", importance=0.5)
    summary = prune_memories()
    assert summary["capped"] == 2
    with connect() as conn:
        active = conn.execute(
            "SELECT COUNT(*) c FROM memories WHERE user_id='u1' AND is_active=1"
        ).fetchone()["c"]
    assert active == 3


def test_prune_improvement_signals_retires_resolved_old_rows(_isolated_db):
    with connect() as conn:
        conn.execute(
            """INSERT INTO improvement_proposals
               (proposal_id, scope, title, problem, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "p-old",
                "tool",
                "old",
                "old",
                "approved",
                (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
                (datetime.now(timezone.utc) - timedelta(days=120)).isoformat(),
            ),
        )
        conn.execute(
            """INSERT INTO improvement_proposals
               (proposal_id, scope, title, problem, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (
                "p-new",
                "tool",
                "new",
                "new",
                "approved",
                datetime.now(timezone.utc).isoformat(),
                datetime.now(timezone.utc).isoformat(),
            ),
        )
    summary = prune_improvement_signals()
    assert summary["retired"] == 1
    with connect() as conn:
        rows = {
            r["proposal_id"]: r["status"]
            for r in conn.execute("SELECT proposal_id, status FROM improvement_proposals").fetchall()
        }
    assert rows["p-old"] == "retired"
    assert rows["p-new"] == "approved"
