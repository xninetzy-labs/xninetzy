from __future__ import annotations

from typing import Any

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


def _ensure() -> None:
    run_migrations()


def learning_benchmark_snapshot(*, owner_scope: str) -> tuple[dict[str, float], ...]:
    _ensure()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT name, last_score, baseline_score, delta, last_run_at
            FROM learning_benchmarks
            WHERE owner_scope=? OR owner_scope='system'
            ORDER BY last_run_at DESC LIMIT 25
            """,
            (owner_scope,),
        ).fetchall()
    return tuple(
        {
            "name": str(row["name"]),
            "last_score": float(row["last_score"] or 0.0),
            "baseline_score": float(row["baseline_score"] or 0.0),
            "delta": float(row["delta"] or 0.0),
            "last_run_at": str(row["last_run_at"] or ""),
        }
        for row in rows
    )


def ab_test_snapshot(*, owner_scope: str) -> tuple[dict[str, Any], ...]:
    _ensure()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT test_id, baseline, candidate, status, winner,
                   baseline_avg, candidate_avg, confidence, sample_total
            FROM ab_tests
            WHERE owner_scope=? OR owner_scope='system'
            ORDER BY created_at DESC LIMIT 25
            """,
            (owner_scope,),
        ).fetchall()
    return tuple(
        {
            "test_id": str(row["test_id"]),
            "baseline": str(row["baseline"]),
            "candidate": str(row["candidate"]),
            "status": str(row["status"]),
            "winner": row["winner"],
            "baseline_avg": float(row["baseline_avg"] or 0.0),
            "candidate_avg": float(row["candidate_avg"] or 0.0),
            "confidence": float(row["confidence"] or 0.0),
            "sample_total": int(row["sample_total"] or 0),
        }
        for row in rows
    )


def evolution_proposal_snapshot(*, owner_scope: str) -> tuple[dict[str, Any], ...]:
    _ensure()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT proposal_id, title, target_area, status, confidence,
                   baseline_metrics_json, candidate_metrics_json, rollback_json
            FROM improvement_proposals
            WHERE user_id=? OR user_id='system'
            ORDER BY id DESC LIMIT 25
            """,
            (owner_scope,),
        ).fetchall()
    return tuple(
        {
            "proposal_id": str(row["proposal_id"]),
            "title": str(row["title"]),
            "target_area": str(row["target_area"]),
            "status": str(row["status"]),
            "confidence": float(row["confidence"] or 0.0),
            "baseline_metrics": str(row["baseline_metrics_json"] or "{}"),
            "candidate_metrics": str(row["candidate_metrics_json"] or "{}"),
            "rollback": str(row["rollback_json"] or "{}"),
        }
        for row in rows
    )


def enrich_strategy_rank(
    *,
    owner_scope: str,
    rank_result: dict[str, Any],
    boost_weight: float = 0.25,
) -> dict[str, Any]:
    """Augment strategy_rank output with learning engine state so bandit can use it."""
    benchmarks = learning_benchmark_snapshot(owner_scope=owner_scope)
    tests = ab_test_snapshot(owner_scope=owner_scope)
    proposals = evolution_proposal_snapshot(owner_scope=owner_scope)
    benchmark_deltas = [b["delta"] for b in benchmarks]
    benchmark_signal = (
        sum(benchmark_deltas) / len(benchmark_deltas) if benchmark_deltas else 0.0
    )
    accepted_winners = sum(
        1 for t in tests if t["status"] == "accepted" and t["winner"]
    )
    pending_proposals = sum(1 for p in proposals if p["status"] == "pending")
    rank_result["learning_state"] = {
        "benchmark_count": len(benchmarks),
        "benchmark_avg_delta": round(benchmark_signal, 4),
        "ab_test_count": len(tests),
        "ab_accepted_winners": accepted_winners,
        "pending_proposals": pending_proposals,
        "boost_weight": boost_weight,
        "benchmarks": list(benchmarks)[:5],
        "ab_tests": list(tests)[:5],
    }
    strategies = rank_result.get("strategies", [])
    for strategy in strategies:
        sid = strategy["strategy_id"]
        boost = 0.0
        for test in tests:
            if test["winner"] == sid and test["status"] == "accepted":
                boost = max(boost, float(test["candidate_avg"]) - float(test["baseline_avg"]))
        strategy["learning_boost"] = boost
        if boost != 0.0:
            adjusted = float(strategy.get("ucb_score", 0.0)) + (boost_weight * boost)
            strategy["ucb_score_adjusted"] = round(adjusted, 6)
    if any(s.get("learning_boost", 0.0) != 0.0 for s in strategies):
        strategies.sort(
            key=lambda s: (-s.get("ucb_score_adjusted", s.get("ucb_score", 0.0)), s["strategy_id"])
        )
    return rank_result
