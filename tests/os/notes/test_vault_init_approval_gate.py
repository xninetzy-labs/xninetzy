from __future__ import annotations

import json

from xninetzy.tools.internal.obsidian_organization import (
    obsidian_moc_refresh,
    obsidian_vault_init,
)


def test_obsidian_vault_init_requires_sender_id(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_FOLDERING_ENABLED", "true")
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    monkeypatch.setenv("OBSIDIAN_BACKUP_BEFORE_WRITE", "false")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings
    from xninetzy.db.sqlite import init_db
    get_settings.cache_clear()
    init_db()

    result = obsidian_vault_init.invoke({})
    parsed = json.loads(result)
    assert "error" in parsed
    assert "sender_id" in parsed["error"].lower()
    assert not (tmp_path / "vault" / "Daily").exists()


def test_obsidian_moc_refresh_requires_sender_id(tmp_path, monkeypatch):
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_FOLDERING_ENABLED", "true")
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    monkeypatch.setenv("OBSIDIAN_BACKUP_BEFORE_WRITE", "false")
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings
    from xninetzy.db.sqlite import init_db
    get_settings.cache_clear()
    init_db()

    result = obsidian_moc_refresh.invoke({})
    parsed = json.loads(result)
    assert "error" in parsed
    assert "sender_id" in parsed["error"].lower()
