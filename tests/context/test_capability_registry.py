from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.context.capability_graph.graph import (
    CapabilityNode,
    _aliases_for_group,
    _nodes_from_registry,
    seed_from_registry,
)
from xninetzy.context.capability_graph.semantic_match import (
    _tokenize,
    match_capability,
)
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "capability_registry.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    monkeypatch.delenv("XNINETZY_SQLITE_PATH", raising=False)
    from xninetzy.core import config as config_module
    config_module.get_settings.cache_clear()
    run_migrations()
    yield db_file


def test_migration_creates_capability_tables(_isolated_db: Path):
    with connect() as conn:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'capability_%' OR name IN ('mcp_providers', 'route_decisions', 'context_source_stats')"
        ).fetchall()
    names = {row["name"] for row in rows}
    assert {
        "capability_aliases",
        "mcp_providers",
        "route_decisions",
        "context_source_stats",
        "capability_lifecycle",
    }.issubset(names)


def test_migration_creates_indexes(_isolated_db: Path):
    with connect() as conn:
        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'"
            ).fetchall()
        }
    expected = {
        "idx_capability_aliases_capability",
        "idx_capability_aliases_alias",
        "idx_mcp_providers_trust_tier",
        "idx_route_decisions_intent",
        "idx_context_source_stats_context",
        "idx_capability_lifecycle_capability",
    }
    missing = expected - indexes
    assert not missing, f"missing indexes: {sorted(missing)}"


def test_alias_normalization_drops_duplicates_and_strips_case():
    aliases = _aliases_for_group("code", "repo_search")
    assert all(alias == alias.lower() for alias in aliases)
    assert len(aliases) == len(set(aliases))
    assert "repo_search" in aliases
    assert "repo search" in aliases
    assert "code:repo_search" in aliases


def test_seed_is_idempotent(_isolated_db: Path):
    first = seed_from_registry()
    assert first.inserted > 0
    second = seed_from_registry()
    assert second.inserted == 0
    assert second.skipped >= first.inserted
    with connect() as conn:
        count = conn.execute("SELECT COUNT(*) AS n FROM capability_aliases").fetchone()["n"]
    assert count == first.inserted


def test_seed_covers_every_tool_group(_isolated_db: Path):
    result = seed_from_registry()
    assert set(result.capabilities).issuperset({"core", "repo", "academic", "it_learning"})


def test_seed_records_surface_per_capability(_isolated_db: Path):
    seed_from_registry()
    with connect() as conn:
        rows = conn.execute(
            "SELECT DISTINCT surface FROM capability_aliases ORDER BY surface"
        ).fetchall()
    surfaces = {row["surface"] for row in rows}
    assert any(surface.startswith("tool_group:") for surface in surfaces)
    assert any(surface.startswith("tool:") for surface in surfaces)


def test_seed_uses_custom_nodes_when_supplied(_isolated_db: Path):
    nodes = [
        CapabilityNode(
            capability="custom_alpha",
            surface="tool_group:custom_alpha",
            aliases=("alpha", "alfa"),
        )
    ]
    result = seed_from_registry(nodes=nodes)
    assert result.inserted == 2
    assert "custom_alpha" in result.capabilities


def test_nodes_from_registry_uses_get_tool_groups():
    nodes = _nodes_from_registry()
    capabilities = {node.capability for node in nodes}
    surfaces = {node.surface for node in nodes}
    assert "core" in capabilities
    assert "tool_group:core" in surfaces
    assert any(surface.startswith("tool:repo_search") for surface in surfaces)


def test_tokenize_drops_stopwords_and_strips_punctuation():
    tokens = _tokenize("Please tolong carikan repo_search untuk saya")
    assert "repo_search" in tokens
    assert "tolong" not in tokens
    assert "saya" not in tokens
    assert "carikan" in tokens


def test_match_capability_finds_known_tool(_isolated_db: Path):
    seed_from_registry()
    results = match_capability("repo_search find me symbol")
    assert results, "expected at least one match for repo_search query"
    top = results[0]
    assert top.capability == "repo_search"
    assert top.surface == "tool:repo_search"


def test_match_capability_supports_phrase_query(_isolated_db: Path):
    seed_from_registry()
    results = match_capability("academic course list")
    assert results
    capabilities = {result.capability for result in results}
    assert "academic" in capabilities


def test_match_capability_returns_empty_for_stopwords_only(_isolated_db: Path):
    seed_from_registry()
    assert match_capability("please tolong the a an") == []


def test_match_capability_respects_top_k(_isolated_db: Path):
    seed_from_registry()
    results = match_capability("learn study", top_k=3)
    assert len(results) <= 3


def test_match_capability_ranks_higher_score_first(_isolated_db: Path):
    seed_from_registry()
    results = match_capability("repo search code")
    scores = [match.score for match in results]
    assert scores == sorted(scores, reverse=True)


def test_match_capability_records_method(_isolated_db: Path):
    seed_from_registry()
    results = match_capability("repo_search")
    assert results
    assert {result.method for result in results} <= {"jaccard", "contains"}
