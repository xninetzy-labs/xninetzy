from __future__ import annotations

from app.xninetzy.tools.ecosystem.helper_tools import (
    helper_generate_obsidian_docs,
    helper_get,
)


def test_helper_get_overview_when_no_topic():
    result = helper_get.invoke({"topic": None})
    assert "Xninetzy AI" in result
    assert "Capability Map" in result


def test_helper_get_known_topic_returns_guide():
    result = helper_get.invoke({"topic": "learning"})
    assert "Learning OS" in result
    assert "roadmap" in result


def test_helper_get_topic_is_case_insensitive():
    result = helper_get.invoke({"topic": "HEBAT"})
    assert "HEBAT / E-Learning UNAIR" in result


def test_helper_get_unknown_topic_returns_fallback():
    result = helper_get.invoke({"topic": "unknown-topic"})
    assert "Kategori tidak dikenal" in result
    assert "learning" in result


def test_helper_get_registered_in_registry():
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    assert "helper_get" in names
    assert "helper_generate_obsidian_docs" in names


def test_helper_generate_obsidian_docs_writes_to_isolated_vault(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "host-vault"))
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    monkeypatch.setenv("OBSIDIAN_BACKUP_BEFORE_WRITE", "false")
    vault = tmp_path / "vault"
    vault.mkdir()

    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

    init_db()
    from app.xninetzy.db.migrations import run_migrations

    run_migrations()

    result = helper_generate_obsidian_docs.invoke({})
    assert "Dokumentasi dibuat" in result
    assert (vault / "System" / "Help" / "README.md").is_file()
    assert (vault / "System" / "Help" / "Commands.md").is_file()
    readme = (vault / "System" / "Help" / "README.md").read_text(encoding="utf-8")
    assert "Xninetzy AI" in readme
