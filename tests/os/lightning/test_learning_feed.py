from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.os.lightning.learning_feed import (
    ab_test_snapshot,
    enrich_strategy_rank,
    evolution_proposal_snapshot,
    learning_benchmark_snapshot,
)
from xninetzy.os.lightning.rl import (
    start_episode,
)
from xninetzy.os.lightning.service import (
    apply_proposal,
    reject_proposal,
    rollback_proposal,
)
from xninetzy.os.lightning.store import (
    create_proposal,
    list_proposals,
    set_proposal_status,
)


OWNER = "owner-jid"
NAME = "Misbahul"


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "lightning.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    yield db_file


def test_learning_benchmark_snapshot_empty():
    snap = learning_benchmark_snapshot(owner_scope=OWNER)
    assert snap == ()


def test_learning_benchmark_snapshot_after_insert():
    from xninetzy.db.sqlite import connect
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO learning_benchmarks
              (name, owner_scope, category, description, target_metrics_json,
               last_score, baseline_score, delta, last_run_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "quality",
                OWNER,
                "system",
                "x",
                "[]",
                0.8,
                0.5,
                0.3,
                "2026-01-01T00:00:00Z",
            ),
        )
    snap = learning_benchmark_snapshot(owner_scope=OWNER)
    assert len(snap) == 1
    assert snap[0]["delta"] == 0.3


def test_ab_test_snapshot_after_insert():
    from xninetzy.db.sqlite import connect
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ab_tests
              (test_id, owner_scope, baseline, candidate, metric_name, status,
               winner, baseline_avg, candidate_avg, confidence, sample_total,
               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "t1",
                OWNER,
                "a",
                "b",
                "acc",
                "accepted",
                "b",
                0.5,
                0.9,
                0.95,
                20,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
    snap = ab_test_snapshot(owner_scope=OWNER)
    assert snap[0]["winner"] == "b"
    assert snap[0]["candidate_avg"] == 0.9


def test_evolution_proposal_snapshot_after_insert():
    create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="hello",
        problem="p",
        proposed_change="c",
        target_area="rule",
        baseline_metrics={"overall_quality": 0.4},
        candidate_metrics={"overall_quality": 0.8},
        rollback={"action": "revert"},
        risk_level="low",
        confidence=0.5,
    )
    snap = evolution_proposal_snapshot(owner_scope=OWNER)
    assert len(snap) == 1
    assert snap[0]["target_area"] == "rule"


def test_enrich_strategy_rank_attaches_learning_state():
    enriched = enrich_strategy_rank(
        owner_scope=OWNER,
        rank_result={"strategies": [], "context_key": "x"},
    )
    assert "learning_state" in enriched
    assert enriched["learning_state"]["benchmark_count"] == 0


def test_apply_proposal_rejects_when_candidate_not_better():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="no improvement",
        problem="p",
        proposed_change="c",
        target_area="tool_routing",
        baseline_metrics={"overall_quality": 0.9},
        candidate_metrics={"overall_quality": 0.8},
        risk_level="low",
        confidence=0.5,
    )
    result = apply_proposal(
        proposal_pk=int(proposal["id"]),
        sender_id=OWNER,
        sender_name=NAME,
        min_candidate_improvement=0.05,
    )
    assert "⛔" in result
    rows = list_proposals(status=None, limit=50)
    pk = int(proposal["id"])
    row = next(r for r in rows if int(r["id"]) == pk)
    assert row["status"] == "rejected"


def test_apply_proposal_accepts_when_candidate_better():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="real improvement",
        problem="p",
        proposed_change="c",
        target_area="rule",
        patch={"rule_content": "always greet user", "user_id": OWNER},
        baseline_metrics={"overall_quality": 0.4},
        candidate_metrics={"overall_quality": 0.9},
        risk_level="low",
        confidence=0.7,
    )
    result = apply_proposal(
        proposal_pk=int(proposal["id"]),
        sender_id=OWNER,
        sender_name=NAME,
    )
    assert "✅" in result


def test_rollback_proposal_logs_and_marks_status():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="r1",
        problem="p",
        proposed_change="c",
        target_area="rule",
        patch={"rule_content": "test rollback rule", "user_id": OWNER},
        baseline_metrics={"x": 0.3},
        candidate_metrics={"x": 0.9},
        risk_level="low",
        confidence=0.7,
    )
    pk = int(proposal["id"])
    apply_proposal(proposal_pk=pk, sender_id=OWNER, sender_name=NAME)
    result = rollback_proposal(proposal_pk=pk, sender_id=OWNER, sender_name=NAME)
    assert "↩️" in result
    row = next(r for r in list_proposals(status=None, limit=50) if int(r["id"]) == pk)
    assert row["status"] == "rolled_back"


def test_reject_proposal_works():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="r2",
        problem="p",
        proposed_change="c",
        target_area="tool_routing",
        risk_level="low",
        confidence=0.5,
    )
    result = reject_proposal(
        proposal_pk=int(proposal["id"]),
        sender_id=OWNER,
        sender_name=NAME,
    )
    assert "ditolak" in result.lower()


def test_start_episode_creates_bandit_episode():
    ep = start_episode(
        owner_scope=OWNER,
        interface="test",
        chat_id=None,
        context={"k": "v"},
        strategy_id="a",
        task_type="t",
        state={},
        idempotency_key="k1",
    )
    assert ep["episode_id"].startswith("E-")


def test_rollback_log_records_execution():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="r3",
        problem="p",
        proposed_change="c",
        target_area="tool_routing",
        baseline_metrics={"x": 0.1},
        candidate_metrics={"x": 0.9},
        risk_level="low",
        confidence=0.7,
    )
    pk = int(proposal["id"])
    apply_proposal(proposal_pk=pk, sender_id=OWNER, sender_name=NAME)
    rollback_proposal(proposal_pk=pk, sender_id=OWNER, sender_name=NAME)
    from xninetzy.db.sqlite import connect
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) c FROM lightning_rollback_log WHERE proposal_pk=?",
            (pk,),
        ).fetchone()["c"]
    assert count >= 2


def test_enrich_strategy_rank_boosts_winning_test():
    from xninetzy.db.sqlite import connect
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO ab_tests
              (test_id, owner_scope, baseline, candidate, metric_name, status,
               winner, baseline_avg, candidate_avg, confidence, sample_total,
               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "tboost",
                OWNER,
                "winning-strategy",
                "loser",
                "acc",
                "accepted",
                "winning-strategy",
                0.4,
                0.85,
                0.95,
                20,
                "2026-01-01T00:00:00Z",
                "2026-01-01T00:00:00Z",
            ),
        )
    enriched = enrich_strategy_rank(
        owner_scope=OWNER,
        rank_result={
            "strategies": [{"strategy_id": "winning-strategy", "ucb_score": 0.5}],
            "context_key": "x",
        },
    )
    target = next(s for s in enriched["strategies"] if s["strategy_id"] == "winning-strategy")
    assert target["learning_boost"] > 0


def test_set_proposal_status_can_rollback_to_active():
    proposal = create_proposal(
        source_type="test",
        source_id="t1",
        user_id=OWNER,
        title="manual",
        problem="p",
        proposed_change="c",
        target_area="tool_routing",
        risk_level="low",
        confidence=0.5,
    )
    pk = int(proposal["id"])
    set_proposal_status(pk, "active", reviewed_by=NAME, rollout_state="active")
    row = next(r for r in list_proposals(status=None, limit=50) if int(r["id"]) == pk)
    assert row["status"] == "active"
