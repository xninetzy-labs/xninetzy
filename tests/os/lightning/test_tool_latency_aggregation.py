from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.lightning.rl import start_episode, record_action, tool_latency_aggregation


@pytest.fixture
def _isolated_db(tmp_path, monkeypatch):
    db = tmp_path / "lat.db"
    monkeypatch.setenv("SQLITE_PATH", str(db))
    from xninetzy.core import config as cfg

    cfg.get_settings.cache_clear()
    init_db()
    run_migrations()
    yield db


def _seed_episode_with_latencies(owner: str, counts: dict[str, list[float]]):
    ep = start_episode(
        owner_scope=owner,
        interface="mcp",
        chat_id="chat-1",
        task_type="latency_aggregation",
        strategy_id="baseline",
    )
    ordinal = 1
    for tool_name, samples in counts.items():
        for ms in samples:
            record_action(
                episode_id=ep["episode_id"],
                owner_scope=owner,
                action_type="mcp_tool",
                action_name=tool_name,
                input_data={},
                output_data={},
                latency_ms=float(ms),
            )
            ordinal += 1


def test_tool_latency_aggregation_aggregates_p50_p95(_isolated_db):
    samples = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
    _seed_episode_with_latencies("owner-1", {"repo_search": samples})
    out = tool_latency_aggregation(owner_scope="owner-1", window_days=1)
    assert len(out) == 1
    row = out[0]
    assert row["tool"] == "repo_search"
    assert row["sample_count"] == 10
    assert row["latency_max_ms"] == 100.0
    assert row["latency_p50_ms"] == 50.0
    assert row["latency_p95_ms"] == 90.0


def test_tool_latency_aggregation_sorts_by_p95_desc(_isolated_db):
    _seed_episode_with_latencies(
        "owner-1",
        {
            "fast_tool": [5, 6, 7],
            "slow_tool": [200, 300, 400, 500],
        },
    )
    out = tool_latency_aggregation(owner_scope="owner-1", window_days=1)
    assert out[0]["tool"] == "slow_tool"
    assert out[1]["tool"] == "fast_tool"


def test_tool_latency_aggregation_top_n_cap(_isolated_db):
    counts = {f"tool_{i}": [float(i), float(i * 2)] for i in range(50)}
    _seed_episode_with_latencies("owner-1", counts)
    out = tool_latency_aggregation(owner_scope="owner-1", window_days=1, top_n=10)
    assert len(out) == 10


def test_tool_latency_aggregation_skips_zero_latency(_isolated_db):
    _seed_episode_with_latencies(
        "owner-1",
        {"zero_tool": [0.0, 0.0], "real_tool": [42.0, 84.0]},
    )
    out = tool_latency_aggregation(owner_scope="owner-1", window_days=1)
    names = [row["tool"] for row in out]
    assert "zero_tool" not in names
    assert "real_tool" in names
