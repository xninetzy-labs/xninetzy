from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.context.capability_graph.graph import seed_from_registry
from xninetzy.context.gateway.registry import upsert_provider
from xninetzy.context.gateway.trust import (
    HEALTH_OK,
    TRANSPORT_STDIO,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_UNVERIFIED,
)
from xninetzy.context.invocation.classify import (
    SIDE_EFFECT_IDEMPOTENT_WRITE,
    SIDE_EFFECT_IRREVERSIBLE,
    SIDE_EFFECT_READ_ONLY,
)
from xninetzy.context.invocation.contract import InvocationRequest
from xninetzy.context.orchestrator.invokable import (
    Invocable,
    InvocableError,
    InvocableResult,
    clear_invokable_registry,
    register_invokable,
)
from xninetzy.context.orchestrator.pipeline import (
    OUTCOME_BLOCKED,
    OUTCOME_ERROR,
    OUTCOME_OK,
    OUTCOME_REJECTED_POLICY,
    OUTCOME_REPLAYED,
    execute_invocation,
    execute_pipeline,
)
from xninetzy.context.policy.audit import (
    AUDIT_OUTCOME_BLOCKED,
    AUDIT_OUTCOME_OK,
    find_audit_by_idempotency,
    list_audit_entries,
)
from xninetzy.db.migrations import run_migrations


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "orch.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    clear_invokable_registry()
    yield db_file
    clear_invokable_registry()


class _StubInvocable(Invocable):
    def __init__(self, provider_id, *, payload=None, raise_exc=None, latency=10):
        self.provider_id = provider_id
        self._payload = payload
        self._raise = raise_exc
        self._latency = latency
        self.calls: list[tuple[str, tuple]] = []

    def invoke(self, capability, args):
        self.calls.append((capability, args))
        if self._raise is not None:
            raise self._raise
        return InvocableResult(payload=self._payload, latency_ms=self._latency)

    def is_healthy(self):
        return True


def _seed_unverified_provider():
    upsert_provider(
        provider_id="unverified-x",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_UNVERIFIED,
        risk_class="unreviewed",
        capabilities=("do_thing",),
        health_state=HEALTH_OK,
    )


def _seed_known_provider():
    upsert_provider(
        provider_id="known-x",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("do_thing",),
        health_state=HEALTH_OK,
    )


def _request(**overrides):
    base = dict(
        request_id="req-1",
        intent="intent-x",
        capability="do_thing",
        context_key="ctx",
        query="",
        args=(("k", "v"),),
        side_effect=SIDE_EFFECT_READ_ONLY,
        idempotency_key=None,
        approval_id=None,
    )
    base.update(overrides)
    return InvocationRequest(**base)


def test_execute_invocation_routes_to_registered_invocable(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True})
    register_invokable("unverified-x", stub)
    outcome = execute_invocation(_request())
    assert outcome.result is not None
    assert outcome.result.outcome == OUTCOME_OK
    assert outcome.result.provider_id == "unverified-x"
    assert outcome.result.payload == {"ok": True}
    assert outcome.audit.outcome == AUDIT_OUTCOME_OK


def test_execute_invocation_returns_error_when_invokable_missing(_isolated_db):
    _seed_unverified_provider()
    outcome = execute_invocation(_request())
    assert outcome.result.outcome == OUTCOME_ERROR
    assert "no invocable registered" in (outcome.result.error or "")


def test_execute_invocation_returns_blocked_on_policy_block(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"k": "v"})
    register_invokable("unverified-x", stub)
    request = _request(side_effect="non_idempotent_write", idempotency_key="k1")
    outcome = execute_invocation(request)
    assert outcome.result.outcome == OUTCOME_BLOCKED
    assert not stub.calls
    assert outcome.audit.outcome == AUDIT_OUTCOME_BLOCKED


def test_execute_invocation_returns_rejected_policy_on_irreversible_without_approval(
    _isolated_db,
):
    _seed_known_provider()
    request = _request(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="k1",
        approval_id=None,
    )
    outcome = execute_invocation(request)
    assert outcome.result.outcome == OUTCOME_REJECTED_POLICY
    assert outcome.audit.id == 0


def test_execute_invocation_succeeds_for_irreversible_with_approval(_isolated_db):
    _seed_known_provider()
    stub = _StubInvocable("known-x", payload={"ok": True})
    register_invokable("known-x", stub)
    request = _request(
        side_effect=SIDE_EFFECT_IRREVERSIBLE,
        idempotency_key="k1",
        approval_id=99,
    )
    outcome = execute_invocation(request)
    assert outcome.result.outcome == OUTCOME_OK
    assert outcome.audit.outcome == AUDIT_OUTCOME_OK


def test_execute_invocation_replays_successful_idempotent_call(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True})
    register_invokable("unverified-x", stub)
    request = _request(
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        idempotency_key="replay-1",
    )
    first = execute_invocation(request)
    assert first.result.outcome == OUTCOME_OK
    second = execute_invocation(request)
    assert second.result.outcome == OUTCOME_REPLAYED
    assert second.audit.id == first.audit.id
    assert len(stub.calls) == 1


def test_execute_invocation_does_not_replay_blocked_outcome(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True})
    register_invokable("unverified-x", stub)
    request = _request(side_effect="non_idempotent_write", idempotency_key="k1")
    first = execute_invocation(request)
    assert first.result.outcome == OUTCOME_BLOCKED
    second = execute_invocation(request)
    assert second.result.outcome == OUTCOME_BLOCKED
    assert second.audit.id != first.audit.id


def test_execute_invocation_propagates_invocable_errors_to_audit(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable(
        "unverified-x",
        raise_exc=InvocableError("transport died"),
    )
    register_invokable("unverified-x", stub)
    outcome = execute_invocation(_request())
    assert outcome.result.outcome == OUTCOME_ERROR
    assert "transport died" in (outcome.result.error or "")
    assert outcome.audit.outcome == "error"
    assert outcome.audit.error == "transport died"


def test_execute_invocation_uses_override_invokable(_isolated_db):
    _seed_unverified_provider()
    override = _StubInvocable("override", payload={"override": True})
    outcome = execute_invocation(_request(), invocation_override=override)
    assert outcome.result.outcome == OUTCOME_OK
    assert outcome.result.payload == {"override": True}
    assert outcome.result.provider_id == "override"


def test_execute_pipeline_runs_requests_in_order(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"k": 1})
    register_invokable("unverified-x", stub)
    requests = [
        _request(request_id="req-a", idempotency_key="ka"),
        _request(request_id="req-b", idempotency_key="kb"),
    ]
    outcomes = execute_pipeline(requests)
    assert len(outcomes) == 2
    assert [o.result.outcome for o in outcomes] == [OUTCOME_OK, OUTCOME_OK]
    assert len(stub.calls) == 2


def test_execute_invocation_persists_audit_row(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True})
    register_invokable("unverified-x", stub)
    execute_invocation(_request(idempotency_key="audit-1"))
    entries = list_audit_entries(request_id="req-1")
    assert len(entries) == 1
    entry = entries[0]
    assert entry.outcome == AUDIT_OUTCOME_OK
    assert entry.context_key == "ctx"


def test_execute_invocation_records_bandit_feedback(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True}, latency=25)
    register_invokable("unverified-x", stub)
    execute_invocation(_request())
    from xninetzy.db.sqlite import connect
    with connect() as conn:
        row = conn.execute(
            "SELECT outcome, latency_ms FROM route_decisions WHERE request_id='req-1'"
        ).fetchone()
    assert row is not None
    assert row["outcome"] == AUDIT_OUTCOME_OK
    assert row["latency_ms"] == 25


def test_execute_invocation_supports_override_with_idempotent_replay(_isolated_db):
    _seed_unverified_provider()
    override_a = _StubInvocable("a", payload={"a": 1})
    override_b = _StubInvocable("b", payload={"b": 2})
    request = _request(
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        idempotency_key="replay-2",
    )
    first = execute_invocation(request, invocation_override=override_a)
    second = execute_invocation(request, invocation_override=override_b)
    assert first.result.outcome == OUTCOME_OK
    assert second.result.outcome == OUTCOME_REPLAYED
    assert second.result.provider_id == "a"
    assert len(override_a.calls) == 1
    assert len(override_b.calls) == 0


def test_find_audit_by_idempotency_returns_recorded_entry(_isolated_db):
    _seed_unverified_provider()
    stub = _StubInvocable("unverified-x", payload={"ok": True})
    register_invokable("unverified-x", stub)
    execute_invocation(_request(idempotency_key="audit-2"))
    entry = find_audit_by_idempotency("audit-2")
    assert entry is not None
    assert entry.outcome == AUDIT_OUTCOME_OK
