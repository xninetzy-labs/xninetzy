from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect
from xninetzy.context.policy.audit import (
    AUDIT_OUTCOME_BLOCKED,
    AUDIT_OUTCOME_ERROR,
    AUDIT_OUTCOME_OK,
    complete_audit_entry,
    find_audit_by_idempotency,
    get_audit_entry,
    list_audit_entries,
    record_audit_start,
)


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "audit.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    yield db_file


def test_record_audit_start_creates_row(_isolated_db):
    entry = record_audit_start(
        request_id="req-1",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="idem-1",
        approval_id=None,
        args_hash="hash-a",
        args_bytes=10,
        context_key="ctx",
    )
    assert entry.id > 0
    assert entry.outcome is None
    assert entry.finished_at is None


def test_record_audit_start_is_replayable_for_same_key(_isolated_db):
    first = record_audit_start(
        request_id="req-1",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key="idem-same",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    second = record_audit_start(
        request_id="req-1",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key="idem-same",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    assert first.id == second.id


def test_record_audit_start_uses_distinct_keys_for_non_idempotent(
    _isolated_db,
):
    first = record_audit_start(
        request_id="req-a",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key=None,
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    second = record_audit_start(
        request_id="req-b",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key=None,
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    assert first.id != second.id


def test_complete_audit_entry_updates_outcome(_isolated_db):
    entry = record_audit_start(
        request_id="req-c",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="idem-c",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    finished = complete_audit_entry(
        audit_id=entry.id,
        outcome=AUDIT_OUTCOME_OK,
        latency_ms=42,
    )
    assert finished.outcome == AUDIT_OUTCOME_OK
    assert finished.latency_ms == 42
    assert finished.finished_at is not None


def test_complete_audit_entry_rejects_invalid_outcome(_isolated_db):
    entry = record_audit_start(
        request_id="req-d",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="idem-d",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    with pytest.raises(ValueError):
        complete_audit_entry(audit_id=entry.id, outcome="bogus")


def test_get_audit_entry_returns_none_for_missing(_isolated_db):
    assert get_audit_entry(999999) is None


def test_find_audit_by_idempotency_returns_latest(_isolated_db):
    record_audit_start(
        request_id="req-e1",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key="shared",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    record_audit_start(
        request_id="req-e2",
        provider_id="beta",
        capability="do_thing",
        side_effect_class="idempotent_write",
        idempotency_key="shared",
        approval_id=None,
        args_hash="hash",
        args_bytes=10,
        context_key="ctx",
    )
    found = find_audit_by_idempotency("shared")
    assert found is not None
    assert found.provider_id in {"alpha", "beta"}


def test_find_audit_by_idempotency_returns_none_when_unset():
    assert find_audit_by_idempotency(None) is None


def test_list_audit_entries_filters_by_request_id(_isolated_db):
    record_audit_start(
        request_id="req-f1",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="f1",
        approval_id=None,
        args_hash="h",
        args_bytes=1,
        context_key="ctx",
    )
    record_audit_start(
        request_id="req-f2",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="f2",
        approval_id=None,
        args_hash="h",
        args_bytes=1,
        context_key="ctx",
    )
    entries = list_audit_entries(request_id="req-f1")
    assert len(entries) == 1
    assert entries[0].request_id == "req-f1"


def test_audit_invocations_table_indexes_exist(_isolated_db):
    with connect() as conn:
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_audit_%'"
            ).fetchall()
        }
    assert {
        "idx_audit_invocations_request",
        "idx_audit_invocations_provider",
        "idx_audit_invocations_idempotency",
    }.issubset(indexes)


def test_record_then_complete_blocked_outcome_persists_error(_isolated_db):
    entry = record_audit_start(
        request_id="req-g",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="irreversible",
        idempotency_key="g1",
        approval_id=None,
        args_hash="h",
        args_bytes=1,
        context_key="ctx",
    )
    finished = complete_audit_entry(
        audit_id=entry.id,
        outcome=AUDIT_OUTCOME_BLOCKED,
        error="missing approval",
    )
    assert finished.outcome == AUDIT_OUTCOME_BLOCKED
    assert finished.error == "missing approval"


def test_record_then_complete_error_outcome_persists(_isolated_db):
    entry = record_audit_start(
        request_id="req-h",
        provider_id="alpha",
        capability="do_thing",
        side_effect_class="read_only",
        idempotency_key="h1",
        approval_id=None,
        args_hash="h",
        args_bytes=1,
        context_key="ctx",
    )
    finished = complete_audit_entry(
        audit_id=entry.id,
        outcome=AUDIT_OUTCOME_ERROR,
        error="timeout",
    )
    assert finished.outcome == AUDIT_OUTCOME_ERROR
    assert finished.error == "timeout"
