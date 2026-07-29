from pathlib import Path

import pytest
from cryptography.fernet import Fernet

from app.xninetzy.os.web_analysis.session_manager import (
    SessionDecryptionError,
    SessionEncryptionUnavailable,
    SessionManager,
)
from app.xninetzy.os.web_analysis.snapshot_manager import SnapshotManager


def test_session_is_encrypted_and_profile_name_not_in_path(tmp_path):
    key = Fernet.generate_key().decode()
    manager = SessionManager(root=tmp_path, key=key)
    state = {"cookies": [{"name": "MoodleSession", "value": "very-secret"}], "origins": []}
    path = manager.save_storage_state("hebat", state, profile_id="my-local-owner")
    raw = path.read_bytes()
    assert b"very-secret" not in raw
    assert "my-local-owner" not in str(path)
    assert path.stat().st_mode & 0o777 == 0o600
    assert manager.load_storage_state("hebat", "my-local-owner") == state


def test_session_persists_sanitized_landing_url(tmp_path):
    key = Fernet.generate_key().decode()
    manager = SessionManager(root=tmp_path, key=key)
    manager.save_storage_state(
        "mahasiswa",
        {"cookies": [], "origins": []},
        profile_id="owner",
        landing_url="https://mahasiswa.unair.ac.id/dashboard?token=secret#profile",
    )

    assert manager.load_landing_url("mahasiswa", "owner") == (
        "https://mahasiswa.unair.ac.id/dashboard"
    )


def test_session_rejects_cross_origin_landing_url(tmp_path):
    key = Fernet.generate_key().decode()
    manager = SessionManager(root=tmp_path, key=key)

    with pytest.raises(ValueError, match="luar origin"):
        manager.save_storage_state(
            "mahasiswa",
            {"cookies": [], "origins": []},
            landing_url="https://example.com/dashboard",
        )


def test_session_fails_closed_without_key(tmp_path):
    with pytest.raises(SessionEncryptionUnavailable):
        SessionManager(root=tmp_path, key="")


def test_corrupted_session_is_rejected(tmp_path):
    key = Fernet.generate_key().decode()
    manager = SessionManager(root=tmp_path, key=key)
    path = manager.save_storage_state("hebat", {"cookies": [], "origins": []}, "owner")
    path.write_bytes(b"not-a-fernet-token")
    with pytest.raises(SessionDecryptionError):
        manager.load_storage_state("hebat", "owner")


def test_personal_snapshot_is_separate_and_encrypted(tmp_path):
    key = Fernet.generate_key().decode()
    snapshots = SnapshotManager(root=tmp_path, key=key)
    path = snapshots.save(
        "mahasiswa",
        "schedule",
        [{"when": "Senin 08:00", "label": "APSI"}],
        "owner",
    )
    assert isinstance(path, Path)
    assert b"APSI" not in path.read_bytes()
    loaded = snapshots.load("mahasiswa", "schedule", profile_id="owner")
    assert loaded["items"][0]["label"] == "APSI"
