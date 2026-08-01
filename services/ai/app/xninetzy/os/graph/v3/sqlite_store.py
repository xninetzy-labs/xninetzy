"""Canonical SQLite store for GraphRAG V3 — the single source of truth.

Every mutation is idempotent and happens in ONE transaction that also writes
the ``graph_sync_outbox`` row (the only channel to the Neo4j/FAISS projections)
and an append-only ``graph_audit`` entry. Business logic must go through here —
never write Neo4j or FAISS directly.

Design rules honored:
* No dual-write: SQLite + outbox only, atomically.
* Idempotent: identity via canonical_key (UUID5), change-detection via
  content_hash. Unchanged upsert ⇒ no version bump, no outbox row.
* Provenance-first: every node/edge carries provenance_json.
* Reversible: soft-delete flips status to 'deleted' and emits a delete op.
"""

from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import get_db_path
from app.xninetzy.os.graph.v3.identity import (
    edge_content_hash,
    edge_key,
    node_content_hash,
    node_key,
)


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _connect() -> sqlite3.Connection:
    """Graph-local connection with a busy_timeout so the projection worker and
    the request path don't collide on the WAL under concurrent writes."""
    conn = sqlite3.connect(get_db_path(), timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


@dataclass
class NodeUpsert:
    node_type: str
    title: str
    content: str | None = None
    properties: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)
    identity: str | None = None


@dataclass
class EdgeUpsert:
    source_key: str
    target_key: str
    edge_type: str
    weight: float = 1.0
    properties: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)


@dataclass
class UpsertResult:
    key: str
    changed: bool
    version: int
    created: bool


def _enqueue_outbox(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_key: str,
    op: str,
    payload: dict,
    now: str,
) -> None:
    dedupe = f"{entity_type}:{entity_key}:{payload.get('content_hash', op)}"
    conn.execute(
        """
        INSERT INTO graph_sync_outbox
          (entity_type, entity_key, op, payload_json, dedupe_key, status,
           attempts, next_retry_at, created_at, updated_at)
        VALUES (?,?,?,?,?, 'pending', 0, ?, ?, ?)
        """,
        (entity_type, entity_key, op, json.dumps(payload, ensure_ascii=False),
         dedupe, now, now, now),
    )


def _audit(
    conn: sqlite3.Connection,
    *,
    entity_type: str,
    entity_key: str,
    op: str,
    actor: str | None,
    version: int | None,
    detail: dict,
    now: str,
) -> None:
    conn.execute(
        """
        INSERT INTO graph_audit
          (entity_type, entity_key, op, actor, version, detail_json, created_at)
        VALUES (?,?,?,?,?,?,?)
        """,
        (entity_type, entity_key, op, actor, version,
         json.dumps(detail, ensure_ascii=False), now),
    )


def upsert_node(spec: NodeUpsert, *, actor: str | None = None) -> UpsertResult:
    key = node_key(spec.node_type, spec.title, identity=spec.identity)
    chash = node_content_hash(
        node_type=spec.node_type,
        title=spec.title,
        content=spec.content,
        properties=spec.properties,
    )
    now = _now()
    props = json.dumps(spec.properties or {}, ensure_ascii=False)
    prov = json.dumps(spec.provenance or {}, ensure_ascii=False)

    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, content_hash, version FROM graph_nodes_v3 WHERE canonical_key=?",
            (key,),
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO graph_nodes_v3
                  (canonical_key, node_type, title, content, properties_json,
                   provenance_json, content_hash, version, status,
                   created_at, updated_at)
                VALUES (?,?,?,?,?,?,?, 1, 'active', ?, ?)
                """,
                (key, spec.node_type, spec.title, spec.content, props, prov,
                 chash, now, now),
            )
            conn.execute(
                "INSERT INTO graph_nodes_v3_fts (node_key, title, content) VALUES (?,?,?)",
                (key, spec.title, spec.content or ""),
            )
            _enqueue_outbox(
                conn, entity_type="node", entity_key=key, op="upsert",
                payload={"content_hash": chash, "version": 1}, now=now,
            )
            _audit(conn, entity_type="node", entity_key=key, op="create",
                   actor=actor, version=1, detail={"title": spec.title}, now=now)
            return UpsertResult(key=key, changed=True, version=1, created=True)

        if row["content_hash"] == chash:
            # Refresh provenance without a version bump; not a projection change.
            conn.execute(
                "UPDATE graph_nodes_v3 SET provenance_json=?, updated_at=? WHERE id=?",
                (prov, now, row["id"]),
            )
            return UpsertResult(key=key, changed=False, version=int(row["version"]), created=False)

        new_version = int(row["version"]) + 1
        conn.execute(
            """
            UPDATE graph_nodes_v3
               SET node_type=?, title=?, content=?, properties_json=?,
                   provenance_json=?, content_hash=?, version=?, status='active',
                   updated_at=?
             WHERE id=?
            """,
            (spec.node_type, spec.title, spec.content, props, prov, chash,
             new_version, now, row["id"]),
        )
        conn.execute(
            "UPDATE graph_nodes_v3_fts SET title=?, content=? WHERE node_key=?",
            (spec.title, spec.content or "", key),
        )
        _enqueue_outbox(
            conn, entity_type="node", entity_key=key, op="upsert",
            payload={"content_hash": chash, "version": new_version}, now=now,
        )
        _audit(conn, entity_type="node", entity_key=key, op="update",
               actor=actor, version=new_version, detail={"title": spec.title}, now=now)
        return UpsertResult(key=key, changed=True, version=new_version, created=False)


def upsert_edge(spec: EdgeUpsert, *, actor: str | None = None) -> UpsertResult:
    key = edge_key(spec.source_key, spec.edge_type, spec.target_key)
    chash = edge_content_hash(
        edge_type=spec.edge_type, weight=spec.weight, properties=spec.properties
    )
    now = _now()
    props = json.dumps(spec.properties or {}, ensure_ascii=False)
    prov = json.dumps(spec.provenance or {}, ensure_ascii=False)

    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, content_hash, version FROM graph_edges_v3 WHERE canonical_key=?",
            (key,),
        ).fetchone()

        if row is None:
            conn.execute(
                """
                INSERT INTO graph_edges_v3
                  (canonical_key, source_key, target_key, edge_type, weight,
                   properties_json, provenance_json, content_hash, version,
                   status, created_at, updated_at)
                VALUES (?,?,?,?,?,?,?,?, 1, 'active', ?, ?)
                """,
                (key, spec.source_key, spec.target_key, spec.edge_type,
                 float(spec.weight), props, prov, chash, now, now),
            )
            _enqueue_outbox(
                conn, entity_type="edge", entity_key=key, op="upsert",
                payload={
                    "content_hash": chash, "version": 1,
                    "source_key": spec.source_key, "target_key": spec.target_key,
                    "edge_type": spec.edge_type,
                }, now=now,
            )
            _audit(conn, entity_type="edge", entity_key=key, op="create",
                   actor=actor, version=1,
                   detail={"edge_type": spec.edge_type}, now=now)
            return UpsertResult(key=key, changed=True, version=1, created=True)

        if row["content_hash"] == chash:
            conn.execute(
                "UPDATE graph_edges_v3 SET provenance_json=?, updated_at=? WHERE id=?",
                (prov, now, row["id"]),
            )
            return UpsertResult(key=key, changed=False, version=int(row["version"]), created=False)

        new_version = int(row["version"]) + 1
        conn.execute(
            """
            UPDATE graph_edges_v3
               SET edge_type=?, weight=?, properties_json=?, provenance_json=?,
                   content_hash=?, version=?, status='active', updated_at=?
             WHERE id=?
            """,
            (spec.edge_type, float(spec.weight), props, prov, chash,
             new_version, now, row["id"]),
        )
        _enqueue_outbox(
            conn, entity_type="edge", entity_key=key, op="upsert",
            payload={
                "content_hash": chash, "version": new_version,
                "source_key": spec.source_key, "target_key": spec.target_key,
                "edge_type": spec.edge_type,
            }, now=now,
        )
        _audit(conn, entity_type="edge", entity_key=key, op="update",
               actor=actor, version=new_version,
               detail={"edge_type": spec.edge_type}, now=now)
        return UpsertResult(key=key, changed=True, version=new_version, created=False)


def soft_delete_node(key: str, *, actor: str | None = None) -> bool:
    now = _now()
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT id, status FROM graph_nodes_v3 WHERE canonical_key=?", (key,)
        ).fetchone()
        if row is None or row["status"] == "deleted":
            return False
        conn.execute(
            "UPDATE graph_nodes_v3 SET status='deleted', updated_at=? WHERE id=?",
            (now, row["id"]),
        )
        conn.execute("DELETE FROM graph_nodes_v3_fts WHERE node_key=?", (key,))
        _enqueue_outbox(conn, entity_type="node", entity_key=key, op="delete",
                        payload={"op": "delete"}, now=now)
        _audit(conn, entity_type="node", entity_key=key, op="delete",
               actor=actor, version=None, detail={}, now=now)
    return True


# --- read helpers used by the hybrid retriever -----------------------------

def get_node(key: str) -> dict | None:
    with _connect() as conn:
        row = conn.execute(
            "SELECT * FROM graph_nodes_v3 WHERE canonical_key=? AND status='active'",
            (key,),
        ).fetchone()
    return dict(row) if row else None


def get_nodes(keys: list[str]) -> dict[str, dict]:
    if not keys:
        return {}
    placeholders = ",".join("?" for _ in keys)
    with _connect() as conn:
        rows = conn.execute(
            f"SELECT * FROM graph_nodes_v3 WHERE canonical_key IN ({placeholders}) "
            "AND status='active'",
            keys,
        ).fetchall()
    return {row["canonical_key"]: dict(row) for row in rows}


def fts_search_nodes(query: str, limit: int = 10) -> list[dict]:
    """FTS5 leg of hybrid retrieval. Returns nodes ranked by bm25 (best first)."""
    cleaned = query.strip()
    if not cleaned:
        return []
    match = " OR ".join(
        f'"{token}"' for token in cleaned.split() if token
    ) or f'"{cleaned}"'
    with _connect() as conn:
        try:
            rows = conn.execute(
                """
                SELECT n.canonical_key, n.node_type, n.title, n.content,
                       bm25(graph_nodes_v3_fts) AS score
                  FROM graph_nodes_v3_fts f
                  JOIN graph_nodes_v3 n ON n.canonical_key = f.node_key
                 WHERE graph_nodes_v3_fts MATCH ?
                   AND n.status='active'
                 ORDER BY score
                 LIMIT ?
                """,
                (match, limit),
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return [dict(row) for row in rows]


def edges_for_keys(keys: list[str], limit: int = 60) -> list[dict]:
    if not keys:
        return []
    placeholders = ",".join("?" for _ in keys)
    with _connect() as conn:
        rows = conn.execute(
            f"""
            SELECT canonical_key, source_key, target_key, edge_type, weight,
                   properties_json
              FROM graph_edges_v3
             WHERE status='active'
               AND (source_key IN ({placeholders}) OR target_key IN ({placeholders}))
             LIMIT ?
            """,
            [*keys, *keys, limit],
        ).fetchall()
    return [dict(row) for row in rows]


def set_faiss_row(key: str, faiss_row: int) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "UPDATE graph_nodes_v3 SET faiss_row=?, faiss_synced_at=? WHERE canonical_key=?",
            (faiss_row, now, key),
        )


def mark_neo4j_synced(entity_type: str, key: str) -> None:
    now = _now()
    table = "graph_nodes_v3" if entity_type == "node" else "graph_edges_v3"
    with _connect() as conn:
        conn.execute(
            f"UPDATE {table} SET neo4j_synced_at=? WHERE canonical_key=?",
            (now, key),
        )


def iter_active_nodes() -> list[dict]:
    """Full active-node scan for FAISS/Neo4j rebuilds."""
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM graph_nodes_v3 WHERE status='active' ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def iter_active_edges() -> list[dict]:
    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM graph_edges_v3 WHERE status='active' ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


# --- outbox: the only channel to the Neo4j/FAISS projections ----------------

def claim_outbox_batch(*, limit: int, lease_seconds: int) -> list[dict]:
    """Atomically lease up to ``limit`` ready outbox rows. A row is ready when
    pending/failed and its next_retry_at has passed, or its lease has expired.
    Mirrors the JobStore claim idiom (BEGIN IMMEDIATE + lease_until)."""
    from datetime import timedelta

    now_dt = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    now = now_dt.isoformat()
    lease_until = (now_dt + timedelta(seconds=max(1, lease_seconds))).isoformat()
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        rows = conn.execute(
            """
            SELECT * FROM graph_sync_outbox
             WHERE (
                     status IN ('pending','failed')
                     AND (next_retry_at IS NULL OR next_retry_at <= ?)
                   )
                OR (
                     status='processing'
                     AND (lease_until IS NULL OR lease_until <= ?)
                   )
             ORDER BY id
             LIMIT ?
            """,
            (now, now, limit),
        ).fetchall()
        claimed: list[dict] = []
        for row in rows:
            conn.execute(
                """
                UPDATE graph_sync_outbox
                   SET status='processing', attempts=attempts+1,
                       lease_until=?, updated_at=?
                 WHERE id=?
                """,
                (lease_until, now, row["id"]),
            )
            claimed.append(dict(row))
    return claimed


def mark_outbox_done(outbox_id: int) -> None:
    now = _now()
    with _connect() as conn:
        conn.execute(
            "UPDATE graph_sync_outbox SET status='done', last_error=NULL, "
            "lease_until=NULL, updated_at=? WHERE id=?",
            (now, outbox_id),
        )


def mark_outbox_failed(
    outbox_id: int, *, error: str, max_attempts: int, retry_base_seconds: int
) -> None:
    """Exponential backoff on failure; give up after ``max_attempts`` (status
    stays 'failed' with no next_retry so it stops being claimed)."""
    from datetime import timedelta

    now_dt = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE))
    now = now_dt.isoformat()
    with _connect() as conn:
        row = conn.execute(
            "SELECT attempts FROM graph_sync_outbox WHERE id=?", (outbox_id,)
        ).fetchone()
        attempts = int(row["attempts"]) if row else max_attempts
        if attempts >= max_attempts:
            conn.execute(
                "UPDATE graph_sync_outbox SET status='failed', last_error=?, "
                "lease_until=NULL, next_retry_at=NULL, updated_at=? WHERE id=?",
                (error[:2000], now, outbox_id),
            )
        else:
            delay = retry_base_seconds * (2 ** (attempts - 1))
            next_retry = (now_dt + timedelta(seconds=delay)).isoformat()
            conn.execute(
                "UPDATE graph_sync_outbox SET status='failed', last_error=?, "
                "lease_until=NULL, next_retry_at=?, updated_at=? WHERE id=?",
                (error[:2000], next_retry, now, outbox_id),
            )


def outbox_pending_count() -> int:
    with _connect() as conn:
        row = conn.execute(
            "SELECT COUNT(*) AS c FROM graph_sync_outbox WHERE status IN ('pending','failed','processing')"
        ).fetchone()
    return int(row["c"]) if row else 0


def enqueue_full_resync() -> int:
    """Push an upsert op for every active node then edge — used after a rebuild
    to repopulate an empty Neo4j/FAISS projection from canonical truth."""
    now = _now()
    count = 0
    with _connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        for node in conn.execute(
            "SELECT canonical_key, content_hash, version FROM graph_nodes_v3 WHERE status='active'"
        ).fetchall():
            _enqueue_outbox(
                conn, entity_type="node", entity_key=node["canonical_key"],
                op="upsert",
                payload={"content_hash": node["content_hash"], "version": node["version"]},
                now=now,
            )
            count += 1
        for edge in conn.execute(
            "SELECT canonical_key, content_hash, version, source_key, target_key, edge_type "
            "FROM graph_edges_v3 WHERE status='active'"
        ).fetchall():
            _enqueue_outbox(
                conn, entity_type="edge", entity_key=edge["canonical_key"],
                op="upsert",
                payload={
                    "content_hash": edge["content_hash"], "version": edge["version"],
                    "source_key": edge["source_key"], "target_key": edge["target_key"],
                    "edge_type": edge["edge_type"],
                },
                now=now,
            )
            count += 1
    return count

