from app.xninetzy.core.config import get_settings
from app.xninetzy.os.lightning.rl import (
    record_action,
    record_outcome,
    reward_summary,
    start_episode,
    strategy_rank,
)
from app.xninetzy.tools.registry import get_tool_names


def test_episode_reward_and_idempotency(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "lightning.sqlite3"))
    get_settings.cache_clear()

    episode = start_episode(
        owner_scope="owner-a",
        interface="test",
        context={"domain": "learning", "intent": "explain"},
        strategy_id="route:a",
        idempotency_key="request-1",
    )
    repeated = start_episode(
        owner_scope="owner-a",
        interface="test",
        context={"domain": "learning", "intent": "explain"},
        strategy_id="route:a",
        idempotency_key="request-1",
    )
    assert repeated["episode_id"] == episode["episode_id"]

    action = record_action(
        episode_id=episode["episode_id"],
        owner_scope="owner-a",
        action_type="tool",
        action_name="knowledge_answer",
        idempotency_key="request-1:action",
    )
    repeated_action = record_action(
        episode_id=episode["episode_id"],
        owner_scope="owner-a",
        action_type="tool",
        action_name="knowledge_answer",
        idempotency_key="request-1:action",
    )
    assert repeated_action["action_id"] == action["action_id"]
    finished = record_outcome(
        episode_id=episode["episode_id"],
        owner_scope="owner-a",
        success=True,
        evidence_status="sufficient",
        latency_ms=25,
        idempotency_key="request-1:outcome",
    )
    assert finished["status"] == "completed"
    assert -1 <= finished["reward"] <= 1

    summary = reward_summary(owner_scope="owner-a", window_days=7)
    assert summary["episodes"] == 1
    assert summary["success_rate"] == 1


def test_strategy_ranking_and_owner_scope(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "ranking.sqlite3"))
    get_settings.cache_clear()

    for index in range(2):
        episode = start_episode(
            owner_scope="owner-a",
            interface="test",
            context={"domain": "research", "intent": "search"},
            strategy_id="route:good",
            idempotency_key=f"good-{index}",
        )
        record_outcome(
            episode_id=episode["episode_id"],
            owner_scope="owner-a",
            success=True,
            evidence_status="sufficient",
        )

    episode = start_episode(
        owner_scope="owner-a",
        interface="test",
        context={"domain": "research", "intent": "search"},
        strategy_id="route:bad",
        idempotency_key="bad-1",
    )
    record_outcome(
        episode_id=episode["episode_id"],
        owner_scope="owner-a",
        success=False,
        evidence_status="insufficient",
    )

    ranked = strategy_rank(
        owner_scope="owner-a",
        context={"domain": "research", "intent": "search"},
    )
    assert ranked["strategies"][0]["strategy_id"] == "route:good"
    assert reward_summary(owner_scope="owner-b", window_days=7)["episodes"] == 0


def test_registry_contains_shared_lightning_tools():
    names = set(get_tool_names())
    assert {
        "lightning_episode_start",
        "lightning_record_action",
        "lightning_record_outcome",
        "lightning_episode_finish",
        "lightning_reward_summary",
        "lightning_strategy_rank",
        "lightning_regression_check",
        "lightning_propose_improvement",
    } <= names
