from __future__ import annotations

from xninetzy.tools.ecosystem.knowledge_tools import (
    knowledge_ingest_file,
    knowledge_list_sources,
)


def test_knowledge_ingest_file_supports_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    md = tmp_path / "note.md"
    md.write_text("# Judul\nisi catatan penting tentang learning", encoding="utf-8")
    result = knowledge_ingest_file.invoke({"file_path": str(md)})
    assert "Diingest" in result

    again = knowledge_ingest_file.invoke({"file_path": str(md)})
    assert "sudah ada" in again


def test_knowledge_ingest_file_reports_missing_file(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    result = knowledge_ingest_file.invoke({"file_path": str(tmp_path / "missing.md")})
    assert "tidak ditemukan" in result


def test_knowledge_ingest_file_idempotent_with_key(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    md = tmp_path / "idem.md"
    md.write_text("# Idem content", encoding="utf-8")
    key = "idem-key-abc123"
    first = knowledge_ingest_file.invoke({
        "file_path": str(md),
        "title": "IdemDoc",
        "idempotency_key": key,
    })
    second = knowledge_ingest_file.invoke({
        "file_path": str(md),
        "title": "IdemDoc",
        "idempotency_key": key,
    })
    assert first == second


def test_knowledge_list_sources_clamps_negative_limit(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    md = tmp_path / "clamp.md"
    md.write_text("# clamp content", encoding="utf-8")
    knowledge_ingest_file.invoke({"file_path": str(md), "title": "Clamp"})

    result = knowledge_list_sources.invoke({"limit": 0})
    assert "Knowledge Sources" in result or "Belum ada sumber" in result

    result = knowledge_list_sources.invoke({"limit": -5})
    assert "Knowledge Sources" in result or "Belum ada sumber" in result
