from __future__ import annotations

from app.xninetzy.tools.ecosystem.knowledge_tools import knowledge_ingest_file


def test_knowledge_ingest_file_supports_markdown(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("EMBEDDING_PROVIDER", "numpy_tfidf")
    monkeypatch.setenv("VECTOR_DATA_DIR", str(tmp_path / "vector"))
    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

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
    from app.xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from app.xninetzy.db.sqlite import init_db

    init_db()

    result = knowledge_ingest_file.invoke({"file_path": str(tmp_path / "missing.md")})
    assert "tidak ditemukan" in result
