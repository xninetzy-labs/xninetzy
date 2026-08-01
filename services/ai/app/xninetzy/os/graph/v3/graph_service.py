"""Orchestration façade over the GraphRAG V3 stores.

Business logic and tools call THIS module — never sqlite_store/neo4j_store/
faiss_store directly. It enforces the write path (canonical SQLite + outbox
only, never dual-write) and gives callers a small stable surface:

* ``upsert_node`` / ``upsert_edge`` — idempotent writes to canonical truth.
* ``search`` — hybrid FTS+FAISS+Neo4j retrieval → GraphContextPack.
* ``neighborhood`` / ``shortest_path`` — structural reads (best-effort).
* ``rebuild_projection`` — DESTRUCTIVE: wipe Neo4j + FAISS, then replay from
  canonical SQLite. Guarded behind HITL by the tool layer; never call from a
  request path without an approved action.
"""

from __future__ import annotations

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.graph.v3 import faiss_store, neo4j_store, sqlite_store
from app.xninetzy.os.graph.v3.hybrid_retriever import GraphContextPack, retrieve
from app.xninetzy.os.graph.v3.sqlite_store import EdgeUpsert, NodeUpsert, UpsertResult

logger = logging.getLogger(__name__)


def enabled() -> bool:
    return get_settings().GRAPHRAG_V3_ENABLED


# --- writes (canonical SQLite + outbox only) --------------------------------

def upsert_node(
    *,
    node_type: str,
    title: str,
    content: str | None = None,
    properties: dict | None = None,
    provenance: dict | None = None,
    identity: str | None = None,
    actor: str | None = None,
) -> UpsertResult:
    return sqlite_store.upsert_node(
        NodeUpsert(
            node_type=node_type,
            title=title,
            content=content,
            properties=properties or {},
            provenance=provenance or {},
            identity=identity,
        ),
        actor=actor,
    )


def upsert_edge(
    *,
    source_key: str,
    target_key: str,
    edge_type: str,
    weight: float = 1.0,
    properties: dict | None = None,
    provenance: dict | None = None,
    actor: str | None = None,
) -> UpsertResult:
    return sqlite_store.upsert_edge(
        EdgeUpsert(
            source_key=source_key,
            target_key=target_key,
            edge_type=edge_type,
            weight=weight,
            properties=properties or {},
            provenance=provenance or {},
        ),
        actor=actor,
    )


def soft_delete_node(key: str, *, actor: str | None = None) -> bool:
    return sqlite_store.soft_delete_node(key, actor=actor)


# --- reads ------------------------------------------------------------------

def search(query: str, *, top_k: int | None = None, expand_depth: int = 1) -> GraphContextPack:
    return retrieve(query, top_k=top_k, expand_depth=expand_depth)


def neighborhood(keys: list[str], *, depth: int = 1, limit: int = 60) -> list[dict]:
    return neo4j_store.neighborhood(keys, depth=depth, limit=limit)


def shortest_path(source_key: str, target_key: str, *, max_hops: int = 5) -> list[dict]:
    return neo4j_store.shortest_path(source_key, target_key, max_hops=max_hops)


def stats() -> dict:
    """Cheap health snapshot for tools/diagnostics."""
    return {
        "enabled": enabled(),
        "outbox_pending": sqlite_store.outbox_pending_count(),
        "neo4j_available": neo4j_store.is_available(),
        "active_nodes": len(sqlite_store.iter_active_nodes()),
        "active_edges": len(sqlite_store.iter_active_edges()),
    }


# --- destructive: rebuild the projections from canonical truth --------------

def rebuild_projection() -> dict:
    """Wipe the Neo4j + FAISS projections and replay them from canonical SQLite.

    DESTRUCTIVE to the *projections only* — the SQLite source of truth is never
    touched, so this is recoverable by definition. MUST be gated behind HITL:
    the tool layer routes here through an approved ``graph_rebuild`` action.
    """
    neo4j_ok = neo4j_store.wipe_all()
    faiss_count = faiss_store.rebuild_index()
    resynced = sqlite_store.enqueue_full_resync()
    logger.info(
        "Graph projection rebuild: neo4j_wiped=%s faiss_rows=%s outbox_enqueued=%s",
        neo4j_ok, faiss_count, resynced,
    )
    return {
        "neo4j_wiped": neo4j_ok,
        "faiss_rows": faiss_count,
        "outbox_enqueued": resynced,
    }
