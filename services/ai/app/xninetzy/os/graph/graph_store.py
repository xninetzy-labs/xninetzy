from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.sqlite import connect


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def add_node(node_type: str, title: str, content: str | None = None, metadata: dict | None = None) -> int:
    now = _now()
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO graph_nodes (node_type, title, content, metadata_json, created_at, updated_at)
            VALUES (?,?,?,?,?,?)
            """,
            (node_type, title, content, json.dumps(metadata or {}, ensure_ascii=False), now, now),
        )
        return int(cur.lastrowid)


def add_edge(source_node_id: int, target_node_id: int, edge_type: str, metadata: dict | None = None) -> int:
    with connect() as conn:
        cur = conn.execute(
            """
            INSERT INTO graph_edges (source_node_id, target_node_id, edge_type, metadata_json, created_at)
            VALUES (?,?,?,?,?)
            """,
            (source_node_id, target_node_id, edge_type, json.dumps(metadata or {}, ensure_ascii=False), _now()),
        )
        return int(cur.lastrowid)


def search_nodes(query: str, limit: int = 10) -> list[dict]:
    needle = f"%{query}%"
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT * FROM graph_nodes
            WHERE title LIKE ? OR content LIKE ? OR node_type LIKE ?
            ORDER BY updated_at DESC LIMIT ?
            """,
            (needle, needle, needle, limit),
        ).fetchall()
    return [dict(row) for row in rows]


def edges_for_node(node_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT e.*, s.title AS source_title, t.title AS target_title
            FROM graph_edges e
            JOIN graph_nodes s ON s.id=e.source_node_id
            JOIN graph_nodes t ON t.id=e.target_node_id
            WHERE e.source_node_id=? OR e.target_node_id=?
            LIMIT 30
            """,
            (node_id, node_id),
        ).fetchall()
    return [dict(row) for row in rows]
