"""Projection worker for GraphRAG V3.

Drains ``graph_sync_outbox`` and applies each op to the Neo4j and FAISS
projections. At-least-once delivery: ops are idempotent (MERGE / content_hash
gated), so a redelivered op is harmless. Neo4j/FAISS failures are non-fatal —
they mark the row failed with backoff and move on; the canonical SQLite row is
untouched, so nothing is ever lost.

Runs as a single asyncio background task started in ``main.startup`` only when
GRAPHRAG_V3_ENABLED. The DB work is synchronous SQLite/driver calls executed in
a thread so the event loop is never blocked.
"""

from __future__ import annotations

import asyncio

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.os.graph.v3 import faiss_store, neo4j_store, sqlite_store

logger = logging.getLogger(__name__)


def _apply_one(row: dict) -> None:
    """Apply a single outbox op to both projections. Raises on hard failure so
    the caller records a retry; returns normally when the op is satisfied (even
    if a projection is merely unavailable — that's not a per-row failure)."""
    entity_type = row["entity_type"]
    key = row["entity_key"]
    op = row["op"]

    if op == "delete":
        if entity_type == "node":
            neo4j_store.delete_node(key)
        return

    if entity_type == "node":
        node = sqlite_store.get_node(key)
        if node is None:
            return  # soft-deleted or gone between enqueue and now; nothing to do
        import json as _json

        props = {}
        try:
            props = _json.loads(node.get("properties_json") or "{}")
        except Exception:
            props = {}
        neo4j_store.upsert_node(
            key=key, node_type=node["node_type"], title=node["title"], properties=props
        )
        row_id = faiss_store.upsert_node_vector(key, node["title"], node.get("content"))
        if row_id is not None:
            sqlite_store.set_faiss_row(key, row_id)
        sqlite_store.mark_neo4j_synced("node", key)
        return

    if entity_type == "edge":
        import json as _json

        payload = {}
        try:
            payload = _json.loads(row.get("payload_json") or "{}")
        except Exception:
            payload = {}
        neo4j_store.upsert_edge(
            key=key,
            source_key=payload.get("source_key"),
            target_key=payload.get("target_key"),
            edge_type=payload.get("edge_type", "related_to"),
            weight=float(payload.get("weight", 1.0)),
        )
        sqlite_store.mark_neo4j_synced("edge", key)
        return


def _run_tick() -> dict:
    settings = get_settings()
    claimed = sqlite_store.claim_outbox_batch(
        limit=settings.GRAPH_SYNC_BATCH_SIZE,
        lease_seconds=settings.GRAPH_SYNC_LEASE_SECONDS,
    )
    stats = {"claimed": len(claimed), "done": 0, "failed": 0}
    for row in claimed:
        try:
            _apply_one(row)
            sqlite_store.mark_outbox_done(row["id"])
            stats["done"] += 1
        except Exception as e:
            logger.warning("Graph projection op failed (outbox #%s): %s", row["id"], e)
            sqlite_store.mark_outbox_failed(
                row["id"],
                error=str(e),
                max_attempts=settings.GRAPH_SYNC_MAX_ATTEMPTS,
                retry_base_seconds=settings.GRAPH_SYNC_RETRY_BASE_SECONDS,
            )
            stats["failed"] += 1
    return stats


async def run_projection_tick() -> dict:
    """One drain pass. Exposed for tests and manual triggering."""
    return await asyncio.to_thread(_run_tick)


async def projection_worker_loop() -> None:
    settings = get_settings()
    if not settings.GRAPHRAG_V3_ENABLED:
        return
    await asyncio.sleep(max(0, settings.GRAPH_SYNC_STARTUP_DELAY_SECONDS))
    logger.info("GraphRAG V3 projection worker started")
    while True:
        try:
            await run_projection_tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Graph projection worker tick failed")
        await asyncio.sleep(max(2, settings.GRAPH_SYNC_POLL_SECONDS))
