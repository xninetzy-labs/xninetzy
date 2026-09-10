"""Community detection for GraphRAG V3 — a periodic, deterministic enrichment.

Runs Louvain community detection (NetworkX) over the *canonical* SQLite graph
and writes the result back as first-class graph entities:

* one ``community`` node per detected cluster, and
* an ``in_community`` edge from every member node → its community node.

Everything is written through ``graph_service`` (canonical SQLite + outbox),
never straight to Neo4j/FAISS. Writes are idempotent: a community's identity is
its *stable representative* (the lexicographically-smallest member key), so a
stable graph re-detected on the next run lands on the same community node with
no version bump and no outbox churn.

Constraints honored:
* Deterministic — Louvain is seeded, so the same graph yields the same
  partition run-to-run.
* Structural only — communities come from edges that already exist, never from
  semantic similarity. Similarity is not evidence of a relationship.
* Non-fatal — NetworkX missing, an empty graph, or any failure degrades to a
  no-op; chat/knowledge/reminders are never affected.
* Gated on GRAPHRAG_V3_ENABLED *and* GRAPH_COMMUNITY_ENABLED (both default off).
"""

from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.graph.v3 import sqlite_store

logger = logging.getLogger(__name__)

ACTOR = "community_builder_v1"
_SEED = 42  # fixed so Louvain is reproducible across runs
_MAX_MEMBERS_IN_PROPS = 50


def enabled() -> bool:
    s = get_settings()
    return s.GRAPHRAG_V3_ENABLED and s.GRAPH_COMMUNITY_ENABLED


def _build_graph(nodes: list[dict], edges: list[dict]):
    """Assemble an undirected NetworkX graph from canonical active rows.

    Returns ``(graph, title_by_key)`` or ``(None, {})`` when NetworkX is absent.
    Only edges whose *both* endpoints are active nodes are added, so a dangling
    edge (target soft-deleted between reads) can't invent a phantom member.

    Community nodes and ``in_community`` edges from a previous sweep are excluded
    — detection runs over the *base* graph only, never over its own output, so a
    stable base graph re-detects to the same partition (idempotent).
    """
    try:
        import networkx as nx
    except ImportError:
        logger.warning("networkx not available — community detection disabled")
        return None, {}

    graph = nx.Graph()
    title_by_key: dict[str, str] = {}
    for node in nodes:
        if node["node_type"] == "community":
            continue
        key = node["canonical_key"]
        graph.add_node(key)
        title_by_key[key] = node["title"]
    for edge in edges:
        if edge["edge_type"] == "in_community":
            continue
        src, tgt = edge["source_key"], edge["target_key"]
        if src in title_by_key and tgt in title_by_key and src != tgt:
            # Accumulate weight on parallel/duplicate edges rather than overwrite.
            w = float(edge.get("weight") or 1.0)
            if graph.has_edge(src, tgt):
                graph[src][tgt]["weight"] += w
            else:
                graph.add_edge(src, tgt, weight=w)
    return graph, title_by_key


def _detect(graph) -> list[set[str]]:
    """Seeded Louvain partition, largest community first. Empty on any failure."""
    try:
        from networkx.algorithms.community import louvain_communities

        communities = louvain_communities(graph, weight="weight", seed=_SEED)
    except Exception as e:  # pragma: no cover - defensive
        logger.warning("Louvain community detection failed (non-fatal): %s", e)
        return []
    return sorted((set(c) for c in communities), key=len, reverse=True)


def _project_community(members: set[str], title_by_key: dict[str, str], run_marker: str) -> bool:
    """Upsert one community node + its member edges. Idempotent.

    Skips trivial communities (<2 members) — a lone node is not a cluster.
    """
    from app.xninetzy.os.graph.v3 import graph_service
    if len(members) < 2:
        return False

    ordered = sorted(members)  # stable ordering → stable representative + title
    representative = ordered[0]
    rep_title = title_by_key.get(representative, representative[:8])
    title = f"Cluster: {rep_title}"
    prov = {"algorithm": "louvain", "actor": ACTOR, "run": run_marker}

    result = graph_service.upsert_node(
        node_type="community",
        title=title,
        properties={
            "size": len(members),
            "algorithm": "louvain",
            "members": ordered[:_MAX_MEMBERS_IN_PROPS],
            "truncated": len(members) > _MAX_MEMBERS_IN_PROPS,
        },
        provenance=prov,
        identity=representative,  # membership drift can't fork the community node
        actor=ACTOR,
    )
    community_key = result.key

    for member in ordered:
        graph_service.upsert_edge(
            source_key=member,
            target_key=community_key,
            edge_type="in_community",
            provenance=prov,
            actor=ACTOR,
        )
    return True


def _run() -> dict:
    """One detection pass over the canonical graph. Safe to call directly."""
    if not enabled():
        return {"enabled": False, "communities": 0, "members_linked": 0}

    nodes = sqlite_store.iter_active_nodes()
    edges = sqlite_store.iter_active_edges()
    graph, title_by_key = _build_graph(nodes, edges)
    if graph is None or graph.number_of_edges() == 0:
        return {"enabled": True, "communities": 0, "members_linked": 0}

    # A monotonic-ish run marker keyed off the graph size — no wall clock needed
    # for determinism, and provenance still records which sweep touched a node.
    run_marker = f"n{len(nodes)}-e{len(edges)}"
    communities = _detect(graph)

    built = 0
    members_linked = 0
    for members in communities:
        if _project_community(members, title_by_key, run_marker):
            built += 1
            members_linked += len(members)
    logger.info(
        "Community detection: %d nodes, %d edges → %d communities (%d members linked)",
        len(nodes), len(edges), built, members_linked,
    )
    return {"enabled": True, "communities": built, "members_linked": members_linked}


async def run_community_tick() -> dict:
    """One detection pass off the event loop. Exposed for tests + manual runs."""
    return await asyncio.to_thread(_run)


async def community_loop() -> None:
    settings = get_settings()
    if not enabled():
        return
    interval = max(5, settings.GRAPH_COMMUNITY_INTERVAL_MINUTES) * 60
    # Let the projection worker settle before the first heavy sweep.
    await asyncio.sleep(min(interval, max(0, settings.GRAPH_SYNC_STARTUP_DELAY_SECONDS) + 30))
    logger.info("GraphRAG V3 community builder started (every %d min)", interval // 60)
    while True:
        try:
            await run_community_tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Community detection tick failed")
        await asyncio.sleep(interval)
