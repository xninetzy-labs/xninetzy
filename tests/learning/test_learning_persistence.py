from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.context.learning.benchmark_engine import (
    LearningBenchmark,
    get_benchmark_registry,
    register_benchmark,
    run_learning_benchmark,
    reset_benchmark_registry,
)
from xninetzy.context.learning.evolution_engine import (
    EvolutionProposal,
    evolution_state,
    get_proposal,
    propose_evolution,
    reset_evolution,
    transition_proposal,
)
from xninetzy.context.learning.experiment_engine import (
    ABTest,
    ABTestResult,
    ExperimentOutcome,
    clear_tests,
    create_ab_test,
    finalize_test,
    get_test,
    list_tests,
    record_observation,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "learning.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    clear_tests()
    reset_evolution()
    reset_benchmark_registry()
    yield db_file
    clear_tests()
    reset_evolution()
    reset_benchmark_registry()


def test_ab_test_persists_across_module_reload(monkeypatch):
    test = create_ab_test(
        test_id="t1",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    assert test.test_id == "t1"
    get_benchmark_registry().clear()
    from xninetzy.context.learning import experiment_engine as ee
    ee._REGISTRY = None
    reloaded = get_test("t1")
    assert reloaded is not None
    assert reloaded.baseline == "a"


def test_record_observation_persists_to_db():
    create_ab_test(
        test_id="t2",
        baseline="a",
        candidate="b",
        metric_name="acc",
        owner_scope="local",
    )
    for v in (0.5, 0.6, 0.7):
        record_observation(
            test_id="t2",
            outcome=ExperimentOutcome(variant="a", metric_value=v, sample_size=1),
        )
    for v in (0.7, 0.8, 0.9):
        record_observation(
            test_id="t2",
            outcome=ExperimentOutcome(variant="b", metric_value=v, sample_size=1),
        )
    reloaded = get_test("t2")
    assert reloaded is not None
    assert len(reloaded.observations) == 6


def test_finalize_test_persists_status():
    create_ab_test(test_id="t3", baseline="a", candidate="b", metric_name="x", owner_scope="local")
    for v in (0.5, 0.6, 0.7):
        record_observation(test_id="t3", outcome=ExperimentOutcome(variant="a", metric_value=v, sample_size=1))
    for v in (0.7, 0.8, 0.9):
        record_observation(test_id="t3", outcome=ExperimentOutcome(variant="b", metric_value=v, sample_size=1))
    result = finalize_test(test_id="t3", min_samples=5)
    assert result.winner == "b"
    with connect() as conn:
        row = conn.execute(
            "SELECT status, winner FROM ab_tests WHERE test_id=?", ("t3",)
        ).fetchone()
    assert row["status"] == "accepted"
    assert row["winner"] == "b"


def test_list_tests_returns_persisted():
    create_ab_test(test_id="t4", baseline="a", candidate="b", metric_name="x", owner_scope="local")
    create_ab_test(test_id="t5", baseline="c", candidate="d", metric_name="y", owner_scope="local")
    tests = list_tests()
    assert "t4" in tests and "t5" in tests


def test_clear_tests_removes_db_rows():
    create_ab_test(test_id="t6", baseline="a", candidate="b", metric_name="x", owner_scope="local")
    clear_tests()
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) c FROM ab_tests").fetchone()["c"]
    assert count == 0


def test_propose_evolution_persists_to_db():
    proposal = propose_evolution(
        proposal_id="e1",
        title="improve x",
        problem="p",
        proposed_change="c",
        expected_impact="i",
        risk_level="low",
        confidence=0.8,
    )
    assert proposal.stage == "proposed"
    reloaded = get_proposal("e1")
    assert reloaded is not None
    assert reloaded.title == "improve x"


def test_transition_proposal_persists_stage():
    propose_evolution(
        proposal_id="e2",
        title="x",
        problem="p",
        proposed_change="c",
        expected_impact="i",
        risk_level="low",
        confidence=0.7,
    )
    decision = transition_proposal(proposal_id="e2", decision="validate")
    assert decision.next_stage == "validated"
    reloaded = get_proposal("e2")
    assert reloaded is not None
    assert reloaded.stage == "validated"


def test_evolution_state_aggregates_persisted_proposals():
    propose_evolution(
        proposal_id="e3",
        title="a",
        problem="p",
        proposed_change="c",
        expected_impact="i",
        risk_level="low",
        confidence=0.7,
    )
    propose_evolution(
        proposal_id="e4",
        title="b",
        problem="p",
        proposed_change="c",
        expected_impact="i",
        risk_level="low",
        confidence=0.7,
    )
    state = evolution_state()
    assert len(state.proposals) == 2


def test_register_benchmark_persists_to_db():
    register_benchmark(
        name="quality",
        category="system",
        description="x",
        target_metrics=("overall",),
        owner_scope="local",
    )
    with connect() as conn:
        row = conn.execute(
            "SELECT name, owner_scope FROM learning_benchmarks WHERE name=?",
            ("quality",),
        ).fetchone()
    assert row is not None
    assert row["owner_scope"] == "local"


def test_run_benchmark_persists_score_and_delta():
    register_benchmark(
        name="quality",
        category="system",
        description="x",
        target_metrics=("overall",),
        owner_scope="local",
    )
    benchmark = run_learning_benchmark(
        name="quality",
        score=0.8,
        last_run_at="2026-01-01T00:00:00Z",
        owner_scope="local",
    )
    assert benchmark.last_score == 0.8
    with connect() as conn:
        row = conn.execute(
            "SELECT last_score, baseline_score, delta FROM learning_benchmarks WHERE name=?",
            ("quality",),
        ).fetchone()
    assert row["last_score"] == 0.8
    assert row["delta"] == 0.0


def test_run_benchmark_second_run_updates_delta():
    register_benchmark(
        name="quality",
        category="system",
        description="x",
        target_metrics=("overall",),
        owner_scope="local",
    )
    run_learning_benchmark(name="quality", score=0.5, last_run_at="2026-01-01T00:00:00Z", owner_scope="local")
    benchmark = run_learning_benchmark(name="quality", score=0.7, last_run_at="2026-01-02T00:00:00Z", owner_scope="local")
    assert benchmark.delta == pytest.approx(0.2, abs=0.01)


def test_reset_evolution_removes_db_rows():
    propose_evolution(
        proposal_id="e5",
        title="x",
        problem="p",
        proposed_change="c",
        expected_impact="i",
        risk_level="low",
        confidence=0.7,
    )
    reset_evolution()
    assert get_proposal("e5") is None
    assert evolution_state().proposals == ()


def test_clear_ab_tests_then_get_returns_none():
    create_ab_test(test_id="t7", baseline="a", candidate="b", metric_name="x", owner_scope="local")
    clear_tests()
    assert get_test("t7") is None


def test_register_benchmark_returns_benchmark_dataclass():
    bm = register_benchmark(
        name="accuracy",
        category="eval",
        description="x",
        target_metrics=("a", "b"),
    )
    assert isinstance(bm, LearningBenchmark)
    assert get_benchmark_registry().get("accuracy") is not None
