from __future__ import annotations

import sqlite3
import hashlib
import json
from pathlib import Path

import pytest

from xninetzy.os.backup.service import (
    BackupError,
    create_backup,
    restore_backup,
    verify_backup,
    list_backups,
    prune_backups,
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


def _fixture_backup(tmp_path):
    database = tmp_path / "state.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE sample(value TEXT)")
        connection.execute("INSERT INTO sample VALUES ('original')")
    vectors = tmp_path / "vectors"
    vectors.mkdir()
    backups = tmp_path / "backups"
    created = create_backup(database, vectors, backups)
    return database, vectors, backups, created


@pytest.mark.parametrize("manifest", [
    {}, {"version": 1, "files": {}}, {"version": 2, "files": {}},
    {"version": 1, "files": []}, [], None,
    {"version": 1, "files": {"../outside": {"sha256": "0" * 64, "size": 1}}},
])
def test_invalid_manifest_cannot_validate_or_replace_state(tmp_path, manifest):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    (backups / created["name"] / "manifest.json").write_text(json.dumps(manifest))
    before = database.read_bytes()
    assert verify_backup(backups, created["name"])["valid"] is False
    with pytest.raises(BackupError):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert database.read_bytes() == before


def test_checksum_matching_corrupt_sqlite_is_not_a_valid_backup(tmp_path):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    directory = backups / created["name"]
    invalid = b"not a sqlite database"
    (directory / "xninetzy.sqlite3").write_bytes(invalid)
    manifest = json.loads((directory / "manifest.json").read_text())
    manifest["files"]["xninetzy.sqlite3"] = {
        "sha256": hashlib.sha256(invalid).hexdigest(), "size": len(invalid),
    }
    (directory / "manifest.json").write_text(json.dumps(manifest))
    before = database.read_bytes()
    assert verify_backup(backups, created["name"])["valid"] is False
    with pytest.raises(BackupError):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert database.read_bytes() == before


def test_manifest_size_is_enforced(tmp_path):
    _, _, backups, created = _fixture_backup(tmp_path)
    path = backups / created["name"] / "manifest.json"
    manifest = json.loads(path.read_text())
    manifest["files"]["xninetzy.sqlite3"]["size"] += 1
    path.write_text(json.dumps(manifest))
    assert verify_backup(backups, created["name"])["valid"] is False


def test_retention_never_uses_manifest_path_or_name(tmp_path):
    _, _, backups, first = _fixture_backup(tmp_path)
    outside = tmp_path / "unrelated-owner-files"
    outside.mkdir()
    (outside / "keep").write_text("preserve")
    manifest = backups / first["name"] / "manifest.json"
    value = json.loads(manifest.read_text())
    value.update(path=str(outside), name="forged")
    manifest.write_text(json.dumps(value))
    # Use deterministic names for retention order; no owner directory is involved.
    old = backups / "xninetzy-20000101T000000Z-old"
    manifest.parent.rename(old)
    newer = backups / "xninetzy-20990101T000000Z-new"
    newer.mkdir()
    (newer / "manifest.json").write_text(json.dumps(value))
    assert all(Path(x["path"]).parent == backups for x in list_backups(backups))
    prune_backups(backups, 1)
    assert (outside / "keep").read_text() == "preserve"


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_restore_refuses_sidecars_without_modifying_them(tmp_path, suffix):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    sidecar = database.with_name(database.name + suffix)
    sidecar.write_bytes(b"uncertain sqlite state")
    before = database.read_bytes()
    with pytest.raises(BackupError, match="offline"):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert database.read_bytes() == before
    assert sidecar.read_bytes() == b"uncertain sqlite state"


def test_restore_retains_current_state_as_verified_safety_snapshot(tmp_path):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE sample SET value='current'")
    result = restore_backup(backups, created["name"], database, vectors, confirmed=True)
    safety_name = result["pre_restore_backup"]
    assert safety_name != created["name"]
    assert verify_backup(backups, safety_name)["valid"] is True
    with sqlite3.connect(backups / safety_name / "xninetzy.sqlite3") as connection:
        assert connection.execute("SELECT value FROM sample").fetchone()[0] == "current"


@pytest.mark.parametrize("member", ["manifest.json", "xninetzy.sqlite3"])
def test_snapshot_symlink_members_are_rejected(tmp_path, member):
    _, _, backups, created = _fixture_backup(tmp_path)
    path = backups / created["name"] / member
    real = path.with_name("saved-" + member)
    path.rename(real)
    path.symlink_to(real)
    assert verify_backup(backups, created["name"])["valid"] is False


def test_unlisted_vectors_are_never_restored(tmp_path):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    injected = backups / created["name"] / "vector"
    injected.mkdir()
    (injected / "faiss.index").write_bytes(b"not verified")
    (injected / "faiss_map.json").write_text("[]")
    before = database.read_bytes()
    with pytest.raises(BackupError):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert not (vectors / "faiss.index").exists()
    assert database.read_bytes() == before


def test_restore_holds_instead_of_leaving_a_stale_target_vector_pair(tmp_path):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    (vectors / "faiss.index").write_bytes(b"newer unrelated projection")
    (vectors / "faiss_map.json").write_text("[9]")
    with pytest.raises(BackupError, match="vector"):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert (vectors / "faiss_map.json").read_text() == "[9]"


def test_online_wal_backup_captures_committed_data_without_uncommitted_rows(tmp_path):
    database = tmp_path / "state.sqlite3"
    with sqlite3.connect(database) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE sample(value TEXT)")
        writer.execute("INSERT INTO sample VALUES ('committed')")
        writer.commit()
        writer.execute("INSERT INTO sample VALUES ('uncommitted')")
        backups = tmp_path / "backups"
        created = create_backup(database, tmp_path / "vectors", backups)
        assert verify_backup(backups, created["name"])["valid"]
        with sqlite3.connect(backups / created["name"] / "xninetzy.sqlite3") as snapshot:
            assert snapshot.execute("SELECT value FROM sample").fetchall() == [("committed",)]


@pytest.mark.parametrize("target", ["database", "vector_directory", "snapshot_directory"])
def test_restore_symlink_targets_or_snapshot_are_held(tmp_path, target):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    path = {"database": database, "vector_directory": vectors,
            "snapshot_directory": backups / created["name"]}[target]
    real = path.with_name("real-" + path.name)
    path.rename(real)
    path.symlink_to(real, target_is_directory=real.is_dir())
    before = (real if target == "database" else database).read_bytes()
    with pytest.raises(BackupError):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert (real if target == "database" else database).read_bytes() == before


def test_missing_source_never_creates_empty_database(tmp_path):
    database = tmp_path / "missing.sqlite3"
    with pytest.raises(BackupError):
        create_backup(database, tmp_path / "vectors", tmp_path / "backups")
    assert not database.exists()


def test_incomplete_vector_pair_cannot_publish_or_prune_a_snapshot(tmp_path):
    database, vectors, backups, created = _fixture_backup(tmp_path)
    (vectors / "faiss.index").write_bytes(b"unpaired")
    with pytest.raises(BackupError, match="vector"):
        create_backup(database, vectors, backups, retention=1)
    assert [x["name"] for x in list_backups(backups)] == [created["name"]]


def test_staging_rechecks_bytes_after_initial_verification(tmp_path, monkeypatch):
    from xninetzy.os.backup import service
    database, vectors, backups, created = _fixture_backup(tmp_path)
    original = service._atomic_copy

    def changed_copy(source, target):
        original(source, target)
        if source == backups / created["name"] / "xninetzy.sqlite3":
            target.write_bytes(b"changed after initial verification")

    monkeypatch.setattr(service, "_atomic_copy", changed_copy)
    before = database.read_bytes()
    with pytest.raises(BackupError, match="staged"):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert database.read_bytes() == before


def test_restore_copy_failure_keeps_safety_snapshot_and_reports_interruption(tmp_path, monkeypatch):
    from xninetzy.os.backup import service
    database, vectors, backups, created = _fixture_backup(tmp_path)
    with sqlite3.connect(database) as connection:
        connection.execute("UPDATE sample SET value='current'")
    original = service._atomic_copy

    def failed_copy(source, target):
        if target == database:
            raise OSError("synthetic private failure")
        original(source, target)

    monkeypatch.setattr(service, "_atomic_copy", failed_copy)
    before = database.read_bytes()
    with pytest.raises(BackupError, match="restore_interrupted") as error:
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert "private" not in str(error.value)
    assert database.read_bytes() == before
    snapshots = list_backups(backups)
    assert len(snapshots) == 2
    assert all(verify_backup(backups, item["name"])["valid"] for item in snapshots)


def test_restore_excludes_another_cooperating_restore(tmp_path):
    from xninetzy.os.backup.service import _restore_lock
    database, vectors, backups, created = _fixture_backup(tmp_path)
    before = database.read_bytes()
    with _restore_lock(database), pytest.raises(BackupError, match="restore_in_progress"):
        restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert database.read_bytes() == before


def test_backup_does_not_claim_private_database_is_secret_free(tmp_path):
    _, _, backups, created = _fixture_backup(tmp_path)
    assert created["contains_secrets"] is None
    directory = backups / created["name"]
    assert directory.stat().st_mode & 0o077 == 0
    assert (directory / "xninetzy.sqlite3").stat().st_mode & 0o077 == 0


def test_backup_with_foreign_key_violations_is_not_published(tmp_path):
    database = tmp_path / "invalid.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.executescript("CREATE TABLE parent(id INTEGER PRIMARY KEY); CREATE TABLE child(id REFERENCES parent(id)); INSERT INTO child VALUES(42);")
    backups = tmp_path / "backups"
    with pytest.raises(BackupError):
        create_backup(database, tmp_path / "vectors", backups)
    assert list_backups(backups) == []


def test_same_second_retention_never_prunes_the_new_snapshot(tmp_path, monkeypatch):
    from datetime import datetime, timezone
    from uuid import UUID
    from xninetzy.os.backup import service
    database, vectors, backups, _ = _fixture_backup(tmp_path)
    identifiers = iter([UUID(int=2**128 - 1), UUID(int=0)])
    monkeypatch.setattr(service, "uuid4", lambda: next(identifiers))
    timestamp = datetime(2099, 1, 1, tzinfo=timezone.utc)
    first = create_backup(database, vectors, backups, retention=1, now=timestamp)
    second = create_backup(database, vectors, backups, retention=1, now=timestamp)
    assert (backups / second["name"]).is_dir()
    assert verify_backup(backups, second["name"])["valid"]
    assert not (backups / first["name"]).exists()


def test_offline_wal_restore_does_not_create_sidecars_on_the_target(tmp_path):
    from contextlib import closing
    database = tmp_path / "wal.sqlite3"
    vectors, backups = tmp_path / "vectors", tmp_path / "backups"
    with closing(sqlite3.connect(database)) as writer:
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("CREATE TABLE sample(value TEXT)")
        writer.execute("INSERT INTO sample VALUES ('original')")
        writer.commit()
        created = create_backup(database, vectors, backups)
        writer.execute("UPDATE sample SET value='current'")
        writer.commit()
    assert not Path(str(database) + "-wal").exists()
    result = restore_backup(backups, created["name"], database, vectors, confirmed=True)
    assert result["restored"]
    with closing(sqlite3.connect(database)) as reader:
        assert reader.execute("SELECT value FROM sample").fetchone()[0] == "original"


@pytest.mark.parametrize("suffix", ["-wal", "-shm", "-journal"])
def test_snapshot_with_unlisted_sqlite_sidecar_is_not_standalone(tmp_path, suffix):
    _, _, backups, created = _fixture_backup(tmp_path)
    (backups / created["name"] / ("xninetzy.sqlite3" + suffix)).write_bytes(b"unverified sidecar")
    assert verify_backup(backups, created["name"])["valid"] is False
