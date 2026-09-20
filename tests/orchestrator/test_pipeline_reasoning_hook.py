from __future__ import annotations

import json
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
    SIDE_EFFECT_READ_ONLY,
)
from xninetzy.context.invocation.contract import InvocationRequest
from xninetzy.context.orchestrator.invokable import (
    Invocable,
    InvocableResult,
    clear_invokable_registry,
    register_invokable,
)
from xninetzy.context.orchestrator.pipeline import (
    OUTCOME_CRITIC_FAIL,
    OUTCOME_OK,
    OUTCOME_REPLAN,
    execute_invocation,
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
    def __init__(self, provider_id, payload=None):
        self.provider_id = provider_id
        self._payload = payload

    def invoke(self, capability, args):
        return InvocableResult(payload=self._payload, latency_ms=10)

    def is_healthy(self):
        return True


def _seed_provider(provider_id: str, trust_tier: int):
    upsert_provider(
        provider_id=provider_id,
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=trust_tier,
        risk_class="low" if trust_tier == TRUST_TIER_KNOWN_EXTERNAL else "unreviewed",
        capabilities=("do_thing",),
        health_state=HEALTH_OK,
    )


def _request(**overrides) -> InvocationRequest:
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


def test_pipeline_attaches_critic_and_stop_on_success():
    _seed_provider("known-x", TRUST_TIER_KNOWN_EXTERNAL)
    register_invokable("known-x", _StubInvocable("known-x", payload={"ok": True}))
    outcome = execute_invocation(_request())
    assert outcome.result.outcome == OUTCOME_OK
    assert outcome.critic is not None
    assert outcome.stop is not None
    assert outcome.depth_name == "trivial"


def test_pipeline_returns_critic_fail_when_evidence_missing():
    _seed_provider("unverified-x", TRUST_TIER_UNVERIFIED)
    register_invokable("unverified-x", _StubInvocable("unverified-x", payload={"ok": True}))
    req = _request(
        metadata={
            "missing_evidence_codes": ["PRIMARY_SOURCE"],
            "claims": [],
        },
    )
    outcome = execute_invocation(req)
    assert outcome.result.outcome == OUTCOME_CRITIC_FAIL
    assert outcome.critic.verdict == "fail"
    assert outcome.stop is not None


def test_pipeline_returns_replan_on_anti_loop():
    _seed_provider("unverified-x", TRUST_TIER_UNVERIFIED)
    register_invokable("unverified-x", _StubInvocable("unverified-x", payload={"ok": True}))
    history = [
        {"hypothesis": "h", "tool": "t", "outcome": "fail"},
        {"hypothesis": "h", "tool": "t", "outcome": "fail"},
        {"hypothesis": "h", "tool": "t", "outcome": "fail"},
        {"hypothesis": "h", "tool": "t", "outcome": "fail"},
    ]
    req = _request(
        metadata={"history": history, "iteration": 4, "anti_loop_window": 4},
    )
    outcome = execute_invocation(req)
    assert outcome.result.outcome == OUTCOME_REPLAN
    assert outcome.stop.outcome == "replan"
    assert outcome.stop.anti_loop is not None


def test_pipeline_warns_on_unsupported_claim_but_passes_outcome():
    _seed_provider("unverified-x", TRUST_TIER_UNVERIFIED)
    register_invokable("unverified-x", _StubInvocable("unverified-x", payload={"ok": True}))
    req = _request(
        metadata={"claims": ["the system probably works"]},
    )
    outcome = execute_invocation(req)
    assert outcome.critic.verdict == "warn"
    assert outcome.result.outcome == "ok_with_warnings"


def test_pipeline_classifies_routine_depth_for_idempotent_write():
    _seed_provider("known-x", TRUST_TIER_KNOWN_EXTERNAL)
    register_invokable("known-x", _StubInvocable("known-x", payload={"ok": True}))
    req = _request(
        side_effect=SIDE_EFFECT_IDEMPOTENT_WRITE,
        idempotency_key="idem-1",
    )
    outcome = execute_invocation(req)
    assert outcome.depth_name == "routine"


def test_pipeline_anti_loop_signal_serializable_to_json():
    _seed_provider("unverified-x", TRUST_TIER_UNVERIFIED)
    register_invokable("unverified-x", _StubInvocable("unverified-x", payload={"ok": True}))
    history = [{"hypothesis": "h", "tool": "t", "outcome": "fail"}] * 4
    req = _request(metadata={"history": history, "iteration": 4, "anti_loop_window": 4})
    outcome = execute_invocation(req)
    payload = outcome.stop.to_dict()
    assert json.dumps(payload)
