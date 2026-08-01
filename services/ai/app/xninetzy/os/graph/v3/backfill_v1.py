"""One-shot migration: legacy V1 graph (graph_nodes/graph_edges) → GraphRAG V3.

The V1 store (``app.xninetzy.os.graph.graph_store``) writes flat integer-keyed
rows with no idempotency, provenance, or projection. This backfill replays those
rows through ``graph_service`` so they gain canonical keys, content hashing,
provenance, and outbox-driven projection into Neo4j/FAISS — without touching or
deleting the V1 tables (they stay as-is for rollback).

Idempotent by construction: every write goes through the V3 upsert path, so
re-running the backfill converges (unchanged rows are no-ops, no version bump).
Legacy integer ids are resolved to V3 canonical keys via the same deterministic
``node_key`` the upsert uses, so edges land on the right endpoints on any run.
"""

from __future__ import annotations

import json

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect, init_db

logger = logging.getLogger(__name__)

ACTOR = "backfill_v1"


def _metadata(raw: str | None) -> dict:
    try:
        data = json.loads(raw or "{}")
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def backfill_legacy_graph(*, limit: int | None = None) -> dict:
    """Migrate every legacy node then edge into V3. Returns a stats dict.

    ``limit`` caps nodes AND edges independently (mostly for tests). Writing to
    canonical SQLite is safe even when GRAPHRAG_V3_ENABLED is off — the rows just
    wait in the outbox until the projection worker is turned on.
    """
    from app.xninetzy.os.graph.v3 import graph_service

    init_db()
    stats = {"nodes": 0, "edges": 0, "nodes_skipped": 0, "edges_skipped": 0}

    with connect() as conn:
        node_rows = conn.execute(
            "SELECT id, node_type, title, content, metadata_json FROM graph_nodes ORDER BY id"
            + (f" LIMIT {int(limit)}" if limit else "")
        ).fetchall()
        edge_rows = conn.execute(
            "SELECT source_node_id, target_node_id, edge_type, metadata_json "
            "FROM graph_edges ORDER BY id"
            + (f" LIMIT {int(limit)}" if limit else "")
        ).fetchall()

    # Legacy integer id → V3 canonical key, so edges can be re-pointed.
    key_by_legacy_id: dict[int, str] = {}
    for row in node_rows:
        title = (row["title"] or "").strip()
        if not title:
            stats["nodes_skipped"] += 1
            continue
        result = graph_service.upsert_node(
            node_type=row["node_type"] or "note",
            title=title,
            content=row["content"],
            properties=_metadata(row["metadata_json"]),
            provenance={"backfill": "v1", "legacy_node_id": row["id"]},
            actor=ACTOR,
        )
        key_by_legacy_id[int(row["id"])] = result.key
        stats["nodes"] += 1

    for row in edge_rows:
        src = key_by_legacy_id.get(int(row["source_node_id"]))
        tgt = key_by_legacy_id.get(int(row["target_node_id"]))
        if not src or not tgt:
            # Endpoint was skipped (blank title) or outside this limited batch.
            stats["edges_skipped"] += 1
            continue
        graph_service.upsert_edge(
            source_key=src,
            target_key=tgt,
            edge_type=row["edge_type"] or "related_to",
            properties=_metadata(row["metadata_json"]),
            provenance={"backfill": "v1"},
            actor=ACTOR,
        )
        stats["edges"] += 1

    logger.info(
        "Backfill V1→V3: %d nodes, %d edges (skipped %d nodes, %d edges)",
        stats["nodes"], stats["edges"], stats["nodes_skipped"], stats["edges_skipped"],
    )
    return stats
