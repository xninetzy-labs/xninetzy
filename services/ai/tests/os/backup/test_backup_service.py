from __future__ import annotations

import sqlite3

import pytest

from app.xninetzy.os.backup.service import (
    BackupError,
    create_backup,
    restore_backup,
    verify_backup,
)


def test_backup_verifies_and_restores_sqlite_and_vectors(tmp_path):
    database = tmp_path / "state.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sample(value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('original')")
    vectors = tmp_path / "vectors"
    vectors.mkdir()
    (vectors / "faiss.index").write_bytes(b"index")
    (vectors / "faiss_map.json").write_text("[1]", encoding="utf-8")
    backups = tmp_path / "backups"

    created = create_backup(database, vectors, backups)
    assert verify_backup(backups, created["name"])["valid"] is True

    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE sample SET value='changed'")
    (vectors / "faiss_map.json").write_text("[]", encoding="utf-8")

    with pytest.raises(BackupError, match="confirmation"):
        restore_backup(backups, created["name"], database, vectors)
    restore_backup(backups, created["name"], database, vectors, confirmed=True)

    with sqlite3.connect(database) as connection:
        assert (
            connection.execute("SELECT value FROM sample").fetchone()[0] == "original"
        )
    assert (vectors / "faiss_map.json").read_text(encoding="utf-8") == "[1]"


def test_backup_verification_detects_tampering(tmp_path):
    database = tmp_path / "state.sqlite3"
    sqlite3.connect(database).close()
    vectors = tmp_path / "vectors"
    vectors.mkdir()
    backups = tmp_path / "backups"
    created = create_backup(database, vectors, backups)
    (backups / created["name"] / "xninetzy.sqlite3").write_bytes(b"tampered")

    result = verify_backup(backups, created["name"])

    assert result["valid"] is False
    assert result["errors"] == ["checksum:xninetzy.sqlite3"]
