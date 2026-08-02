from __future__ import annotations

from app.xninetzy.tools.ecosystem.unified_search_tools import unified_search


def test_unified_search_returns_empty_for_unknown_query(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing-container-mount"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    (tmp_path / "vault").mkdir()

    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

    init_db()
    from app.xninetzy.db.migrations import run_migrations

    run_migrations()

    result = unified_search.invoke({"query": "xyzzy"})
    assert "Unified Search" in result
    assert "Tidak ada hasil" in result


def test_unified_search_finds_vault_note(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    monkeypatch.setenv("OBSIDIAN_VAULT_PATH", str(tmp_path / "missing-container-mount"))
    monkeypatch.setenv("OBSIDIAN_VAULT_HOST_PATH", str(tmp_path / "vault"))
    monkeypatch.setenv("OBSIDIAN_ALLOW_WRITE", "true")
    vault = tmp_path / "vault"
    vault.mkdir()
    (vault / "Note.md").write_text(
        "Evidence-Based Learning Techniques untuk Xninetzy", encoding="utf-8"
    )

    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

    init_db()
    from app.xninetzy.db.migrations import run_migrations

    run_migrations()

    result = unified_search.invoke({"query": "learning techniques", "limit": 5})
    assert "Vault" in result
    assert "Note.md" in result


def test_unified_search_registered_in_registry():
    from app.xninetzy.tools.registry import get_all_tools

    names = {t.name for t in get_all_tools()}
    assert "unified_search" in names
