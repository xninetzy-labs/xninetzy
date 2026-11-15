"""Projection worker for GraphRAG V3.

Drains existing outbox rows under their current lease. Projection delivery may
repeat; Neo4j writes use current canonical state and MERGE/idempotent deletion.
FAISS publishes checked snapshots and reuses identical text embeddings.
SQLite acknowledgement/markers are fenced to the claimed attempt and snapshot.
This is not external exactly-once delivery or a universal reconciliation proof.

The MCP lifespan can explicitly opt into this loop. Synchronous IO runs in a
worker thread; shutdown stops future steps, not an already running call.
"""

from __future__ import annotations

import asyncio
import json
import os
from contextlib import contextmanager, asynccontextmanager, suppress
from threading import Event

from xninetzy.core.config import get_settings
from xninetzy.core.logging import logging
from xninetzy.os.graph.v3 import faiss_store, neo4j_store, sqlite_store

logger = logging.getLogger(__name__)
_running_loops: set[asyncio.Task] = set()
_inflight_ticks: set[asyncio.Task] = set()


def _apply_one(row: dict) -> dict | None:
    """Apply an outbox op; enabled Neo4j must acknowledge before completion.

    Disabled Neo4j is skipped without claiming synchronization. Enabled but
    unavailable Neo4j retains the operation for bounded outbox retry, while
    canonical SQLite and the independent FAISS leg remain usable.
    """
    settings = get_settings()
    neo4j_enabled = bool(settings.GRAPHRAG_V3_ENABLED and settings.NEO4J_ENABLED)
    entity_type = row["entity_type"]
    key = row["entity_key"]
    op = row["op"]
    if (entity_type, op) not in {("node", "upsert"), ("node", "delete"), ("edge", "upsert")}:
        raise ValueError("graph_projection_operation_invalid")

    if op == "delete":
        if sqlite_store.get_node(key) is not None:
            return None  # An old deletion must not remove a reactivated node.
        if neo4j_enabled:
            if not neo4j_store.delete_node(key):
                raise RuntimeError("Neo4j node delete was not acknowledged")
        return

    if entity_type == "node":
        node = sqlite_store.get_node(key)
        if node is None:
            return  # soft-deleted or gone between enqueue and now; nothing to do
        props = json.loads(node.get("properties_json") or "{}")
        if not isinstance(props, dict):
            raise ValueError("graph_projection_properties_invalid")
        neo4j_synced = neo4j_enabled and neo4j_store.upsert_node(
            key=key, node_type=node["node_type"], title=node["title"], properties=props,
        )
        row_id = faiss_store.upsert_node_vector(key, node["title"], node.get("content"))
        if neo4j_enabled:
            if not neo4j_synced:
                raise RuntimeError("Neo4j node upsert was not acknowledged")
        return {"entity_type": "node", "key": key, "version": node["version"],
                "content_hash": node["content_hash"], "neo4j_synced": bool(neo4j_synced), "faiss_row": row_id}

    if entity_type == "edge":
        edge = sqlite_store.get_edge(key)
        if edge is None or not neo4j_enabled:
            return
        properties = json.loads(edge.get("properties_json") or "{}")
        if not isinstance(properties, dict):
            raise ValueError("graph_projection_properties_invalid")
        acknowledged = neo4j_store.upsert_edge(
            key=key,
            source_key=edge["source_key"], target_key=edge["target_key"],
            edge_type=edge["edge_type"], weight=float(edge["weight"]), properties=properties,
        )
        if not acknowledged:
            raise RuntimeError("Neo4j edge upsert was not acknowledged")
        return {"entity_type": "edge", "key": key, "version": edge["version"],
                "content_hash": edge["content_hash"], "neo4j_synced": True}


def _drain_tick(stop_event: Event | None = None) -> dict:
    settings = get_settings()
    claimed = sqlite_store.claim_outbox_batch(
        limit=settings.GRAPH_SYNC_BATCH_SIZE,
        lease_seconds=settings.GRAPH_SYNC_LEASE_SECONDS,
    )
    stats = {"claimed": len(claimed), "done": 0, "failed": 0}
    for row in claimed:
        if stop_event is not None and stop_event.is_set():
            if sqlite_store.release_unstarted_claim(row):
                stats["released"] = stats.get("released", 0) + 1
            continue
        if not sqlite_store.claim_is_current(row):
            stats["lease_lost"] = stats.get("lease_lost", 0) + 1
            continue
        try:
            receipt = _apply_one(row)
            if sqlite_store.mark_outbox_done(row["id"], claim=row, receipt=receipt):
                stats["done"] += 1
            else:
                stats["lease_lost"] = stats.get("lease_lost", 0) + 1
        except Exception as e:
            # Arbitrary provider messages may contain queries/private payloads.
            error = type(e).__name__
            if error == "RuntimeError" and str(e) in {
                "Neo4j node delete was not acknowledged", "Neo4j node upsert was not acknowledged",
                "Neo4j edge upsert was not acknowledged",
            }:
                error = str(e)
            logger.warning("Graph projection op failed (outbox #%s): %s", row["id"], error)
            updated = sqlite_store.mark_outbox_failed(
                row["id"],
                error=error, claim=row,
                max_attempts=settings.GRAPH_SYNC_MAX_ATTEMPTS,
                retry_base_seconds=settings.GRAPH_SYNC_RETRY_BASE_SECONDS,
            )
            if updated:
                stats["failed"] += 1
            else:
                stats["lease_lost"] = stats.get("lease_lost", 0) + 1
    return stats


@contextmanager
def _projection_lock():
    try:
        import fcntl
    except ImportError:
        raise RuntimeError("graph_projection_requires_posix_lock") from None
    from xninetzy.db.sqlite import get_db_path
    database = get_db_path()
    if not database.is_file():
        raise RuntimeError("graph_projection_database_unavailable")
    path = database.parent / ".graph-projection.lock"
    fd = os.open(path, os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            yield False
            return
        yield True
    finally:
        os.close(fd)


def _run_tick(stop_event: Event | None = None) -> dict:
    if stop_event is not None and stop_event.is_set():
        return {"claimed": 0, "done": 0, "failed": 0}
    with _projection_lock() as acquired:
        if not acquired:
            return {"claimed": 0, "done": 0, "failed": 0, "deferred": 1}
        return _drain_tick(stop_event)


async def run_projection_tick(stop_event: Event | None = None) -> dict:
    """One drain pass. Exposed for tests and manual triggering."""
    return await asyncio.to_thread(_run_tick, stop_event)


def _finish_tick(task: asyncio.Task) -> None:
    _inflight_ticks.discard(task)
    if not task.cancelled():
        task.exception()  # Retrieve errors even if the owning loop was cancelled.


def runtime_status() -> dict:
    settings = get_settings()
    return {"configured": bool(settings.GRAPHRAG_V3_ENABLED and settings.GRAPH_SYNC_WORKER_ENABLED),
            "running": sum(not task.done() for task in tuple(_running_loops)),
            "inflight": sum(not task.done() for task in tuple(_inflight_ticks))}


@asynccontextmanager
async def background_projection():
    settings = get_settings()
    if not (settings.GRAPHRAG_V3_ENABLED and settings.GRAPH_SYNC_WORKER_ENABLED):
        yield
        return
    stop = Event()
    task = asyncio.create_task(projection_worker_loop(stop), name="xninetzy-graph-projection")
    try:
        yield
    finally:
        stop.set()
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


async def projection_worker_loop(stop_event: Event | None = None) -> None:
    settings = get_settings()
    if not settings.GRAPHRAG_V3_ENABLED:
        return
    stop = stop_event or Event()
    task = asyncio.current_task()
    _running_loops.add(task)
    try:
        await asyncio.sleep(max(0, settings.GRAPH_SYNC_STARTUP_DELAY_SECONDS))
        logger.info("GraphRAG V3 projection worker started")
        while not stop.is_set():
            tick = asyncio.create_task(run_projection_tick(stop), name="xninetzy-graph-tick")
            _inflight_ticks.add(tick)
            tick.add_done_callback(_finish_tick)
            try:
                await asyncio.shield(tick)
            except asyncio.CancelledError:
                stop.set()
                raise
            except Exception as error:
                logger.warning("Graph projection worker tick failed (%s)", type(error).__name__)
            await asyncio.sleep(max(2, settings.GRAPH_SYNC_POLL_SECONDS))
    finally:
        stop.set()
        _running_loops.discard(task)
