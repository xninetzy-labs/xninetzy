"""Tests for GraphRAG V3: canonical writes, idempotency, retrieval, populator,
community detection, and the V1→V3 backfill.

All tests run against a temp SQLite DB with GRAPHRAG_V3_ENABLED forced on and
NEO4J_ENABLED off — the Neo4j/FAISS projections are best-effort and non-fatal, so
the canonical (SQLite) leg is what we assert on. FAISS embedding is heavy and
network-ish, so retrieval is exercised through the FTS (lexical) leg only.
"""

from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db


@pytest.fixture(autouse=True)
def isolated_graph(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "graph_v3.sqlite3"))
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    monkeypatch.setenv("NEO4J_ENABLED", "false")
    monkeypatch.setenv("GRAPH_COMMUNITY_ENABLED", "true")
    monkeypatch.setenv("GRAPH_VECTOR_DATA_DIR", str(tmp_path / "graph_vector"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    # Neo4j store keeps a process-sticky "_unavailable" flag; reset it so a prior
    # test's failed connectivity attempt doesn't mask this test's config.
    from app.xninetzy.os.graph.v3 import neo4j_store

    monkeypatch.setattr(neo4j_store, "_unavailable", False, raising=False)
    monkeypatch.setattr(neo4j_store, "_driver", None, raising=False)
    yield
    get_settings.cache_clear()


def _active_node_count(node_type: str | None = None) -> int:
    with connect() as conn:
        if node_type:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM graph_nodes_v3 WHERE status='active' AND node_type=?",
                (node_type,),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM graph_nodes_v3 WHERE status='active'"
            ).fetchone()
    return int(row["c"])


# --- canonical write path + idempotency ------------------------------------

def test_upsert_node_is_idempotent_and_enqueues_outbox():
    from app.xninetzy.os.graph.v3 import graph_service

    first = graph_service.upsert_node(node_type="topic", title="LangGraph")
    assert first.created is True
    assert first.version == 1

    # Same identity + same content ⇒ no change, no version bump, no new outbox row.
    again = graph_service.upsert_node(node_type="topic", title="LangGraph")
    assert again.created is False
    assert again.changed is False
    assert again.version == 1
    assert again.key == first.key

    # Case/whitespace variants collapse to the same canonical node.
    variant = graph_service.upsert_node(node_type="topic", title="  langgraph ")
    assert variant.key == first.key
    assert _active_node_count("topic") == 1


def test_content_change_bumps_version_and_outbox():
    from app.xninetzy.os.graph.v3 import graph_service

    r1 = graph_service.upsert_node(node_type="topic", title="StateGraph", content="v1")
    r2 = graph_service.upsert_node(node_type="topic", title="StateGraph", content="v2")
    assert r2.changed is True
    assert r2.version == 2
    assert r2.key == r1.key

    with connect() as conn:
        pending = conn.execute(
            "SELECT COUNT(*) AS c FROM graph_sync_outbox WHERE entity_type='node' AND entity_key=?",
            (r1.key,),
        ).fetchone()["c"]
    # One row for the create, one for the content change.
    assert pending == 2


def test_edge_upsert_and_soft_delete():
    from app.xninetzy.os.graph.v3 import graph_service
    from app.xninetzy.os.graph.v3.identity import node_key

    a = graph_service.upsert_node(node_type="topic", title="Neo4j")
    b = graph_service.upsert_node(node_type="concept", title="Cypher")
    edge = graph_service.upsert_edge(
        source_key=a.key, target_key=b.key, edge_type="related_to"
    )
    assert edge.created is True
    assert edge.key == graph_service.upsert_edge(
        source_key=a.key, target_key=b.key, edge_type="related_to"
    ).key  # idempotent

    assert graph_service.soft_delete_node(a.key) is True
    assert graph_service.soft_delete_node(a.key) is False  # already deleted
    assert node_key("topic", "Neo4j") == a.key
    assert _active_node_count() == 1  # only Cypher remains active


# --- retrieval (FTS leg) ----------------------------------------------------

def test_search_returns_pack_via_fts():
    from app.xninetzy.os.graph.v3 import graph_service

    graph_service.upsert_node(
        node_type="topic", title="Reciprocal Rank Fusion",
        content="RRF fuses lexical and dense retrieval rankings",
    )
    pack = graph_service.search("reciprocal rank fusion", expand_depth=1)
    assert pack.is_empty() is False
    assert any("Reciprocal Rank Fusion" in n.title for n in pack.nodes)
    md = pack.to_markdown()
    assert "Graph context" in md


# --- populator (ecosystem event → graph) -----------------------------------

def test_populator_projects_goal_and_task_with_edge():
    from app.xninetzy.ecosystem.event_bus import record_event
    from app.xninetzy.os.graph.v3 import graph_populator
    from app.xninetzy.os.graph.v3.identity import node_key

    now = "2026-08-01T09:00:00+07:00"
    with connect() as conn:
        cur = conn.execute(
            "INSERT INTO life_goals (title, domain, horizon, status, priority, "
            "created_at, updated_at) VALUES (?,?,?,?,?,?,?)",
            ("Master GraphRAG", "learning", "monthly", "active", "high", now, now),
        )
        goal_id = cur.lastrowid
        cur = conn.execute(
            "INSERT INTO tasks (title, status, goal_id, created_at, updated_at) "
            "VALUES (?,?,?,?,?)",
            ("Read the RRF paper", "inbox", goal_id, now, now),
        )
        task_id = cur.lastrowid

    # record_event dispatches to the populator synchronously (non-fatal wrapper).
    record_event(
        "system", "goal_created", "test", entity_type="goal",
        entity_id=str(goal_id), payload={"title": "Master GraphRAG", "domain": "learning"},
    )
    record_event(
        "system", "task_created", "test", entity_type="task",
        entity_id=str(task_id), payload={"title": "Read the RRF paper"},
    )

    goal_key = node_key("goal", "Master GraphRAG")
    task_key = node_key("task", "Read the RRF paper")
    with connect() as conn:
        assert conn.execute(
            "SELECT 1 FROM graph_nodes_v3 WHERE canonical_key=? AND status='active'",
            (goal_key,),
        ).fetchone()
        edge = conn.execute(
            "SELECT edge_type FROM graph_edges_v3 WHERE source_key=? AND target_key=? "
            "AND status='active'",
            (task_key, goal_key),
        ).fetchone()
    assert edge is not None
    assert edge["edge_type"] == "belongs_to"

    # Replaying an already-consumed event is a no-op.
    assert graph_populator.replay_unconsumed_events() == 0


def test_populator_left_unconsumed_when_disabled(monkeypatch):
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "false")
    get_settings.cache_clear()
    from app.xninetzy.ecosystem.event_bus import record_event
    from app.xninetzy.os.graph.v3 import graph_populator

    event_id = record_event(
        "system", "goal_created", "test", entity_type="goal",
        entity_id="99", payload={"title": "Disabled Goal", "domain": "personal"},
    )
    assert graph_populator.consume_event(event_id) is False  # gated off

    # Re-enable → backfill replays the previously-unconsumed event.
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    get_settings.cache_clear()
    assert graph_populator.replay_unconsumed_events() >= 1


# --- community detection ----------------------------------------------------

def test_community_builder_clusters_connected_nodes():
    pytest.importorskip("networkx")
    from app.xninetzy.os.graph.v3 import community_builder, graph_service

    # Two triangles sharing no edge → two communities.
    triangles = [("a", "b", "c"), ("x", "y", "z")]
    keys = {}
    for tri in triangles:
        for name in tri:
            keys[name] = graph_service.upsert_node(node_type="topic", title=name).key
    for u, v, w in triangles:
        graph_service.upsert_edge(source_key=keys[u], target_key=keys[v], edge_type="related_to")
        graph_service.upsert_edge(source_key=keys[v], target_key=keys[w], edge_type="related_to")
        graph_service.upsert_edge(source_key=keys[w], target_key=keys[u], edge_type="related_to")

    stats = community_builder._run()
    assert stats["enabled"] is True
    assert stats["communities"] == 2
    assert _active_node_count("community") == 2

    # Re-running is idempotent: same partition, no new community nodes.
    community_builder._run()
    assert _active_node_count("community") == 2


def test_community_builder_noop_when_no_edges():
    pytest.importorskip("networkx")
    from app.xninetzy.os.graph.v3 import community_builder, graph_service

    graph_service.upsert_node(node_type="topic", title="Lonely")
    stats = community_builder._run()
    assert stats["communities"] == 0


# --- V1 → V3 backfill -------------------------------------------------------

def test_backfill_v1_migrates_nodes_and_edges():
    from app.xninetzy.os.graph.graph_store import add_edge, add_node
    from app.xninetzy.os.graph.v3 import backfill_v1
    from app.xninetzy.os.graph.v3.identity import node_key

    a = add_node("topic", "LangChain")
    b = add_node("concept", "Runnable")
    add_edge(a, b, "related_to")

    stats = backfill_v1.backfill_legacy_graph()
    assert stats["nodes"] == 2
    assert stats["edges"] == 1

    src = node_key("topic", "LangChain")
    tgt = node_key("concept", "Runnable")
    with connect() as conn:
        assert conn.execute(
            "SELECT 1 FROM graph_nodes_v3 WHERE canonical_key=?", (src,)
        ).fetchone()
        assert conn.execute(
            "SELECT 1 FROM graph_edges_v3 WHERE source_key=? AND target_key=? AND edge_type='related_to'",
            (src, tgt),
        ).fetchone()

    # Idempotent: a second backfill re-upserts without creating duplicates.
    again = backfill_v1.backfill_legacy_graph()
    assert again["nodes"] == 2
    assert _active_node_count() == 2



def test_stats_is_passive_when_neo4j_is_disabled(monkeypatch):
    from app.xninetzy.os.graph.v3 import graph_service, neo4j_store

    def fail_if_called():
        raise AssertionError("stats must not connect to Neo4j")

    monkeypatch.setattr(neo4j_store, "_get_driver", fail_if_called)
    snapshot = graph_service.stats()
    assert snapshot["neo4j_available"] is False
    assert snapshot["neo4j"]["configured"] is False
