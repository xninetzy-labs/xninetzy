from __future__ import annotations

import json
from pathlib import Path

import pytest

from xninetzy.context.gateway.registry import (
    list_lifecycle,
    list_providers,
    record_lifecycle_event,
    seed_providers_from_external,
    upsert_provider,
)
from xninetzy.context.gateway.router import (
    record_decision_outcome,
    resolve_route,
)
from xninetzy.context.gateway.trust import (
    HEALTH_DOWN,
    HEALTH_OK,
    RISK_CLASS_TO_TRUST,
    TRANSPORT_HTTP,
    TRANSPORT_LOCAL,
    TRANSPORT_STDIO,
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_LOCAL,
    TRUST_TIER_THIRD_PARTY,
    TRUST_TIER_UNVERIFIED,
    trust_for_risk,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "gateway.db"
    registry_file = tmp_path / "external-mcp.json"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as config_module
    config_module.get_settings.cache_clear()
    monkeypatch.setattr(
        "xninetzy.context.gateway.registry.get_settings",
        lambda: type(
            "S",
            (),
            {"EXTERNAL_MCP_REGISTRY_PATH": str(registry_file)},
        )(),
    )
    run_migrations()
    from xninetzy.context.capability_graph.graph import seed_from_registry
    seed_from_registry()
    yield {"db": db_file, "registry": registry_file}


def _write_registry(path: Path, servers: list[dict]) -> None:
    path.write_text(json.dumps({"servers": servers}), encoding="utf-8")


def test_trust_for_risk_maps_all_known_classes():
    assert trust_for_risk("low") == TRUST_TIER_KNOWN_EXTERNAL
    assert trust_for_risk("medium") == TRUST_TIER_THIRD_PARTY
    assert trust_for_risk("high") == TRUST_TIER_THIRD_PARTY
    assert trust_for_risk("unreviewed") == TRUST_TIER_UNVERIFIED
    assert trust_for_risk("unknown") == TRUST_TIER_UNVERIFIED
    assert trust_for_risk("not-a-real-class") == TRUST_TIER_UNVERIFIED


def test_trust_for_risk_full_table():
    for risk_class, expected in RISK_CLASS_TO_TRUST.items():
        assert trust_for_risk(risk_class) == expected


def test_upsert_provider_persists_row(_isolated_db):
    record = upsert_provider(
        provider_id="alpha",
        transport=TRANSPORT_STDIO,
        endpoint="python -m alpha_mcp",
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("repo_search", "repo_symbol"),
        metadata={"enabled": True},
    )
    assert record.provider_id == "alpha"
    assert record.transport == TRANSPORT_STDIO
    assert record.trust_tier == TRUST_TIER_KNOWN_EXTERNAL
    assert "repo_search" in record.capabilities
    rows = list_providers()
    assert any(item.provider_id == "alpha" for item in rows)


def test_upsert_provider_is_idempotent(_isolated_db):
    upsert_provider(
        provider_id="dup",
        transport=TRANSPORT_HTTP,
        endpoint="http://example",
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
    )
    upsert_provider(
        provider_id="dup",
        transport=TRANSPORT_HTTP,
        endpoint="http://example-v2",
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
        capabilities=("repo_search",),
    )
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM mcp_providers WHERE provider_id='dup'"
        ).fetchone()["n"]
    assert count == 1
    providers = list_providers()
    record = next(item for item in providers if item.provider_id == "dup")
    assert "repo_search" in record.capabilities


def test_seed_providers_from_external_skips_when_registry_missing(_isolated_db):
    result = seed_providers_from_external()
    assert result.upserted == ()
    assert result.skipped == ()
    assert result.total_rows == 0


def test_seed_providers_from_external_writes_rows_and_assigns_trust(
    _isolated_db,
):
    _write_registry(
        _isolated_db["registry"],
        [
            {
                "name": "alpha",
                "command": "python",
                "args": ["-m", "alpha"],
                "risk_level": "low",
                "enabled": True,
                "allowed_tools": ["repo_search"],
            },
            {
                "name": "beta",
                "command": "node",
                "args": ["beta.js"],
                "risk_level": "high",
                "enabled": False,
                "allowed_tools": [],
            },
            {
                "name": "gamma",
                "command": "node",
                "args": ["gamma.js"],
                "risk_level": "unreviewed",
                "enabled": True,
            },
        ],
    )
    result = seed_providers_from_external()
    assert set(result.upserted) == {"alpha", "beta", "gamma"}
    rows = {item.provider_id: item for item in list_providers()}
    assert rows["alpha"].trust_tier == TRUST_TIER_KNOWN_EXTERNAL
    assert rows["beta"].trust_tier == TRUST_TIER_THIRD_PARTY
    assert rows["gamma"].trust_tier == TRUST_TIER_UNVERIFIED
    assert "repo_search" in rows["alpha"].capabilities
    assert rows["beta"].metadata.get("enabled") is False


def test_seed_providers_is_idempotent(_isolated_db):
    _write_registry(
        _isolated_db["registry"],
        [{"name": "alpha", "command": "p", "args": [], "risk_level": "low"}],
    )
    first = seed_providers_from_external()
    second = seed_providers_from_external()
    assert first.upserted == ("alpha",)
    assert second.upserted == ()
    assert second.skipped == ("alpha",)


def test_record_lifecycle_event_appends_row(_isolated_db):
    initial = list_lifecycle("repo_search")
    record_lifecycle_event(
        capability="repo_search",
        provider_id="alpha",
        stage="discovered",
        notes="intake",
        actor="tester",
    )
    record_lifecycle_event(
        capability="repo_search",
        provider_id="alpha",
        stage="promoted",
        notes="low risk",
    )
    after = list_lifecycle("repo_search")
    assert len(after) == len(initial) + 2
    stages = [row["stage"] for row in after]
    assert stages[0] == "promoted"
    assert stages[1] == "discovered"


def test_resolve_route_uses_local_self_when_no_providers(_isolated_db):
    decision = resolve_route(
        request_id="req-1",
        intent="repo_search_symbol",
        query="find me repo_search symbol",
        context_key="ctx-default",
        include_local_self=True,
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == "local:xninetzy"
    assert decision.fallback_used is True
    assert decision.intent == "repo_search_symbol"


def test_resolve_route_prefers_lower_trust_tier_when_match_score_equal(
    _isolated_db,
):
    upsert_provider(
        provider_id="trusted",
        transport=TRANSPORT_STDIO,
        endpoint="cmd-a",
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    upsert_provider(
        provider_id="shady",
        transport=TRANSPORT_STDIO,
        endpoint="cmd-b",
        trust_tier=TRUST_TIER_LOCAL + 1,
        risk_class="medium",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    decision = resolve_route(
        request_id="req-2",
        intent="repo",
        query="repo_search please",
        context_key="ctx-a",
        include_local_self=False,
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == "trusted"


def test_resolve_route_blocks_tier_4(_isolated_db):
    upsert_provider(
        provider_id="blocked",
        transport=TRANSPORT_STDIO,
        endpoint="cmd",
        trust_tier=TRUST_TIER_BLOCKED,
        risk_class="high",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    decision = resolve_route(
        request_id="req-3",
        intent="repo",
        query="repo_search",
        context_key="ctx-block",
        include_local_self=False,
    )
    assert decision.chosen is None
    assert decision.fallback_used is True
    assert not any(
        cand.provider_id == "blocked" for cand in decision.candidates
    )


def test_resolve_route_penalises_down_provider(_isolated_db):
    upsert_provider(
        provider_id="healthy",
        transport=TRANSPORT_STDIO,
        endpoint="cmd-h",
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    upsert_provider(
        provider_id="down",
        transport=TRANSPORT_STDIO,
        endpoint="cmd-d",
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
        capabilities=("repo_search",),
        health_state=HEALTH_DOWN,
    )
    decision = resolve_route(
        request_id="req-4",
        intent="repo",
        query="repo_search",
        context_key="ctx-health",
        include_local_self=False,
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == "healthy"


def test_resolve_route_writes_decision_row(_isolated_db):
    upsert_provider(
        provider_id="p1",
        transport=TRANSPORT_LOCAL,
        endpoint=None,
        trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        risk_class="low",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    decision = resolve_route(
        request_id="req-write",
        intent="repo",
        query="repo_search symbols",
        context_key="ctx-write",
    )
    with connect() as conn:
        row = conn.execute(
            "SELECT request_id, intent, context_key, chosen_provider_id "
            "FROM route_decisions WHERE request_id=?",
            ("req-write",),
        ).fetchone()
    assert row is not None
    assert row["intent"] == "repo"
    assert row["context_key"] == "ctx-write"
    assert decision.chosen is not None
    assert row["chosen_provider_id"] == decision.chosen.provider_id


def test_record_decision_outcome_updates_bandit_stats(_isolated_db):
    upsert_provider(
        provider_id="p-bandit",
        transport=TRANSPORT_LOCAL,
        endpoint=None,
        trust_tier=TRUST_TIER_LOCAL,
        risk_class="low",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    decision = resolve_route(
        request_id="req-bandit",
        intent="repo",
        query="repo_search",
        context_key="ctx-bandit",
        include_local_self=False,
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == "p-bandit"
    record_decision_outcome(
        request_id="req-bandit",
        outcome="ok",
        latency_ms=120,
        success=True,
    )
    record_decision_outcome(
        request_id="req-bandit",
        outcome="error",
        latency_ms=300,
        success=False,
    )
    with connect() as conn:
        row = conn.execute(
            "SELECT sample_count, success_count, latency_sum_ms "
            "FROM context_source_stats WHERE source_kind='mcp:p-bandit'"
        ).fetchone()
    assert row is not None
    assert row["sample_count"] == 2
    assert row["success_count"] == 1
    assert row["latency_sum_ms"] == 420


def test_record_decision_outcome_ignores_local_self(_isolated_db):
    decision = resolve_route(
        request_id="req-local",
        intent="repo",
        query="repo_search",
        context_key="ctx-local",
        providers=[],
    )
    assert decision.chosen is not None
    assert decision.chosen.provider_id == "local:xninetzy"
    record_decision_outcome(
        request_id="req-local",
        outcome="ok",
        latency_ms=10,
        success=True,
    )
    with connect() as conn:
        count = conn.execute(
            "SELECT COUNT(*) AS n FROM context_source_stats WHERE source_kind='mcp:local:xninetzy'"
        ).fetchone()["n"]
    assert count == 0


def test_resolve_route_respects_min_trust_tier_filter(_isolated_db):
    upsert_provider(
        provider_id="unverified",
        transport=TRANSPORT_STDIO,
        endpoint="x",
        trust_tier=TRUST_TIER_UNVERIFIED,
        risk_class="unreviewed",
        capabilities=("repo_search",),
        health_state=HEALTH_OK,
    )
    decision = resolve_route(
        request_id="req-min",
        intent="repo",
        query="repo_search",
        context_key="ctx-min",
        providers=list_providers(),
        min_trust_tier=TRUST_TIER_KNOWN_EXTERNAL,
        include_local_self=False,
    )
    assert decision.chosen is None
    assert decision.fallback_used is True


def test_resolve_route_logs_lifecycle_event_when_unresolved(_isolated_db):
    providers: list = []
    decision = resolve_route(
        request_id="req-miss",
        intent="repo",
        query="zxcvbnm_random_unknown_query",
        context_key="ctx-miss",
        providers=providers,
        include_local_self=False,
    )
    assert decision.chosen is None
    assert decision.fallback_used is True
    rows = list_lifecycle()
    stages = [row["stage"] for row in rows]
    assert "route_unresolved" in stages
