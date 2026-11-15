from __future__ import annotations

import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from xninetzy.os.hitl import approval_service as service


@pytest.fixture
def approval(tmp_path, monkeypatch):
    from xninetzy.core.config import Settings, get_settings
    from xninetzy.db.migrations import run_migrations
    from xninetzy.db.sqlite import init_db

    monkeypatch.setitem(Settings.model_config, "env_file", None)
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "approvals.sqlite3"))
    monkeypatch.setenv("MCP_RUNTIME_MODE", "container")
    monkeypatch.setenv("APP_TIMEZONE", "UTC")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    effects = []

    def execute(row):
        effects.append(row["id"])
        return "synthetic effect verified"

    monkeypatch.setattr(service, "_execute_approved_action", execute)
    identifier = service.request_approval(
        "fixture-chat", "fixture-owner", "synthetic-operation", "Fixture", "Fixture",
        {"target": "synthetic-target"},
    )
    yield identifier, effects
    get_settings.cache_clear()


def decide(identifier, status="approved"):
    # Atomic transition unit tests, not trusted-channel authentication tests.
    return service._apply_status_decision(identifier, status)


def test_simultaneous_approval_executes_only_once(approval, monkeypatch):
    identifier, effects = approval
    barrier = threading.Barrier(2, timeout=5)
    original = service._expired

    def synchronized_expiry(row):
        expired = original(row)
        barrier.wait()
        return expired

    monkeypatch.setattr(service, "_expired", synchronized_expiry)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(decide, [identifier, identifier]))

    assert effects == [identifier]
    assert sum(ok for ok, _ in results) == 1
    assert service.get_approval_status(identifier)["execution_result"] == "synthetic effect verified"


@pytest.mark.parametrize("stale_expired", [False, True])
def test_stale_decision_cannot_overwrite_winning_decision(approval, monkeypatch, stale_expired):
    identifier, effects = approval
    read = threading.Event()
    resume = threading.Event()
    original = service._expired

    def controlled_expiry(row):
        if threading.current_thread().name.startswith("stale-decision"):
            read.set()
            assert resume.wait(timeout=5)
            return stale_expired
        return original(row)

    monkeypatch.setattr(service, "_expired", controlled_expiry)
    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="stale-decision") as pool:
        pending = pool.submit(decide, identifier)
        try:
            assert read.wait(timeout=5)
            winner = "approved" if stale_expired else "rejected"
            assert decide(identifier, winner)[0]
        finally:
            resume.set()
        assert pending.result(timeout=5)[0] is False

    assert service.get_approval_status(identifier)["status"] == winner
    assert effects == ([identifier] if stale_expired else [])


def test_commit_rollback_prevents_side_effect(approval, monkeypatch):
    identifier, effects = approval
    original_connect = service.connect

    class RollbackBeforeExecution:
        def __enter__(self):
            self.connection = original_connect()
            return self.connection

        def __exit__(self, *_):
            self.connection.rollback()
            self.connection.close()
            raise sqlite3.OperationalError("synthetic commit failure")

    monkeypatch.setattr(service, "connect", RollbackBeforeExecution)
    with pytest.raises(sqlite3.OperationalError, match="synthetic commit failure"):
        decide(identifier)
    monkeypatch.setattr(service, "connect", original_connect)

    assert effects == []
    assert service.get_approval_status(identifier)["status"] == "pending"


def test_interrupted_effect_is_not_reported_complete_or_reexecuted(approval, monkeypatch):
    identifier, effects = approval

    def interrupted(row):
        effects.append(row["id"])
        raise SystemExit("synthetic interruption after effect")

    monkeypatch.setattr(service, "_execute_approved_action", interrupted)
    with pytest.raises(SystemExit):
        decide(identifier)
    ok, message = decide(identifier)

    assert not ok
    assert "approval_execution_unverified" in message
    assert effects == [identifier]
    assert service.get_approval_status(identifier)["execution_at"] is None
