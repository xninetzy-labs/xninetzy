from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.context.capability_graph.graph import seed_from_registry
from xninetzy.context.evaluation.learning_bridge import bridge_cycle_to_learning
from xninetzy.context.evaluation.signal_gen import extract_signals
from xninetzy.context.gateway.registry import upsert_provider
from xninetzy.context.gateway.trust import (
    HEALTH_OK,
    TRANSPORT_STDIO,
    TRUST_TIER_KNOWN_EXTERNAL,
)
from xninetzy.context.invocation.contract import InvocationRequest
from xninetzy.context.orchestrator.invokable import (
    Invocable,
    InvocableResult,
    clear_invokable_registry,
    register_invokable,
)
from xninetzy.context.orchestrator.pipeline import execute_pipeline_with_evaluation
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "poison.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    seed_from_registry()
    clear_invokable_registry()
    yield db_file
    clear_invokable_registry()


class _OkInvocable(Invocable):
    def invoke(self, capability, args):
        return InvocableResult(payload={"ok": True}, latency_ms=5)

    def is_healthy(self):
        return True


def _seed_provider(provider_id: str = "goodprov"):
    upsert_provider(
        provider_id=provider_id,
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("do_thing",),
        health_state=HEALTH_OK,
    )
    register_invokable(provider_id, _OkInvocable())


def test_poisoned_signal_does_not_persist_as_learning():
    """Bad outcomes get confidence 0.3 → IGNORE → not persisted."""
    summaries = (
        build_summary("r1", "ok"),
        build_summary("r2", "error"),
    )
    batch = extract_signals(
        findings=(
            {"source": "do_thing", "summary": "ok", "confidence": 0.9, "evidence_refs": ("r1",)},
            {"source": "do_thing", "summary": "bad", "confidence": 0.3, "evidence_refs": ("r2",)},
        )
    )
    assert batch.learn_count == 1
    assert batch.ignore_count == 1


def test_bridge_does_not_propose_when_no_failures():
    summaries = (build_summary("r1", "ok"),)
    batch = extract_signals(
        findings=({"source": "do_thing", "summary": "ok", "confidence": 0.9, "evidence_refs": ("r1",)},)
    )
    result = bridge_cycle_to_learning(
        cycle_owner="local",
        cycle_id="poison-clean",
        batch=batch,
        error_rate=0.0,
        block_rate=0.0,
        overall_quality=0.95,
        related_capabilities=("do_thing",),
    )
    assert result.lightning_proposal_ids == ()


def test_bridge_proposes_only_on_real_failure():
    summaries = (build_summary("r1", "error"),)
    batch = extract_signals(
        findings=({"source": "do_thing", "summary": "err", "confidence": 0.3, "evidence_refs": ("r1",)},)
    )
    result = bridge_cycle_to_learning(
        cycle_owner="local",
        cycle_id="poison-fail",
        batch=batch,
        error_rate=1.0,
        block_rate=0.0,
        overall_quality=0.1,
        related_capabilities=("do_thing",),
    )
    assert len(result.lightning_proposal_ids) == 1


def test_replay_returns_replayed_outcome_not_double_audit():
    """Replaying a successful audit returns outcome=replayed, not duplicate ok."""
    _seed_provider()
    req = InvocationRequest(
        request_id="r-replay",
        intent="x",
        capability="do_thing",
        context_key="ctx",
        query="",
        args=(("k", "v"),),
        side_effect="read_only",
        idempotency_key="replay-key",
        approval_id=None,
    )
    first = execute_pipeline_with_evaluation(requests=[req])
    second = execute_pipeline_with_evaluation(requests=[req])
    assert first["outcomes"][0].result.outcome == "ok"
    assert second["outcomes"][0].result.outcome == "replayed"
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) c FROM audit_invocations WHERE request_id=?",
            ("r-replay",),
        ).fetchone()["c"]
    assert count == 1


def test_audit_skippable_does_not_audit():
    """audit_skippable flag prevents DB write for read_only self."""
    req = InvocationRequest(
        request_id="r-skip",
        intent="x",
        capability="do_thing",
        context_key="ctx",
        query="",
        args=(("k", "v"),),
        side_effect="read_only",
        idempotency_key="skip-key",
        approval_id=None,
        metadata={"audit_skippable": True},
    )
    execute_pipeline_with_evaluation(requests=[req])
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) c FROM audit_invocations WHERE request_id=?",
            ("r-skip",),
        ).fetchone()["c"]
    assert count == 0


def build_summary(request_id: str, outcome: str, error: str | None = None):
    from xninetzy.context.evaluation.integration import build_invocation_summary
    return build_invocation_summary(
        request_id=request_id,
        provider_id="p",
        capability="do_thing",
        audit_outcome=outcome,
        latency_ms=10,
        error=error,
    )
