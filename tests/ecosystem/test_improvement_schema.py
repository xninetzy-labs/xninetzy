from __future__ import annotations

import sqlite3



def test_improvement_proposals_table_has_scope_column(tmp_path, monkeypatch):
    db_path = tmp_path / "test_improvement.sqlite3"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "false")

    from xninetzy.core.config import get_settings
    get_settings.cache_clear()

    from xninetzy.db.sqlite import init_db
    init_db()

    conn = sqlite3.connect(str(db_path))
    cols = {row[1] for row in conn.execute("PRAGMA table_info(improvement_proposals)").fetchall()}
    required = {
        "scope",
        "target_kind",
        "target_id",
        "proposed_change",
        "rationale",
        "metrics_json",
        "rollout",
        "metadata_json",
        "updated_at",
    }
    missing = required - cols
    assert not missing, f"improvement_proposals table missing required columns: {missing}"
    conn.close()


def test_improvement_proposals_alter_migration_runs_cleanly(tmp_path, monkeypatch):
    db_path = tmp_path / "test_migration.sqlite3"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "false")

    from xninetzy.core.config import get_settings
    get_settings.cache_clear()

    conn_pre = sqlite3.connect(str(db_path))
    conn_pre.execute(
        """
        CREATE TABLE improvement_proposals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            proposal_id TEXT NOT NULL UNIQUE,
            user_id TEXT,
            title TEXT,
            problem TEXT,
            status TEXT NOT NULL DEFAULT 'pending',
            created_at TEXT NOT NULL DEFAULT ''
        )
        """
    )
    conn_pre.commit()
    conn_pre.close()

    from xninetzy.db.sqlite import init_db
    init_db()

    conn = sqlite3.connect(str(db_path))
    cols = {row[1] for row in conn.execute("PRAGMA table_info(improvement_proposals)").fetchall()}
    for required in (
        "scope",
        "target_kind",
        "target_id",
        "proposed_change",
        "rationale",
        "metrics_json",
        "rollout",
        "metadata_json",
        "updated_at",
        "confidence",
        "risk_score",
    ):
        assert required in cols, f"init_db/schema failed to ensure column {required!r}"
    conn.close()


def test_improvement_list_tool_does_not_crash_on_missing_scope(tmp_path, monkeypatch):
    db_path = tmp_path / "test_tool.sqlite3"
    monkeypatch.setenv("SQLITE_PATH", str(db_path))
    monkeypatch.setenv("ARTIFACT_ALLOWLIST", "false")

    from xninetzy.core.config import get_settings
    get_settings.cache_clear()

    from xninetzy.tools.ecosystem.improvement_tools import improvement_list

    result = improvement_list.invoke(
        {"owner": "system", "status": "", "scope": "", "limit": 10, "sender_id": ""}
    )
    assert "no such column" not in result.lower(), (
        f"improvement_list crashed with schema error: {result[:300]}"
    )
