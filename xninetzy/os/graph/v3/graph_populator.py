"""GraphRAG V3 populator — a second ecosystem reducer.

Projects durable-fact lifecycle events (goals, tasks, ingested sources) into the
canonical graph. It is a SEPARATE reducer from ``closed_loop_v1`` and shares the
``ecosystem_event_consumptions`` table (composite PK on event_id+reducer lets
many reducers consume the same event exactly once each).

Design constraints honored:
* Deterministic only — NO LLM extraction here. Nodes/edges come straight from
  structured event payloads and canonical rows. (LLM enrichment, if ever added,
  must run outside any DB transaction and go through graph_service too.)
* Graph writes go through ``graph_service`` (canonical SQLite + outbox), never a
  direct Neo4j/FAISS write, and never nested inside the event's transaction —
  each upsert opens its own short transaction and is idempotent, so replay after
  a crash is harmless.
* Gated on GRAPHRAG_V3_ENABLED. When off, events are left UNCONSUMED so enabling
  the flag + startup replay backfills them.
* Every failure is swallowed: the graph must never break the closed loop.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect, init_db

logger = logging.getLogger(__name__)

REDUCER_NAME = "graph_populator_v1"


def _now() -> str:
    return datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()


def _ensure_consumption_schema(conn) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS ecosystem_event_consumptions (
            event_id INTEGER NOT NULL,
            reducer TEXT NOT NULL,
            consumed_at TEXT NOT NULL,
            PRIMARY KEY (event_id, reducer)
        )
        """
    )


def consume_event(event_id: int) -> bool:
    """Project one ecosystem event into the graph, exactly once.

    Returns True if this call performed the projection. When V3 is disabled the
    event is left unconsumed (returns False) so it can be replayed later.
    """
    if not get_settings().GRAPHRAG_V3_ENABLED:
        return False
    init_db()

    # Phase 1 — read (own short transaction, then release before graph writes).
    with connect() as conn:
        _ensure_consumption_schema(conn)
        already = conn.execute(
            "SELECT 1 FROM ecosystem_event_consumptions WHERE event_id=? AND reducer=?",
            (event_id, REDUCER_NAME),
        ).fetchone()
        if already:
            return False
        event = conn.execute(
            "SELECT * FROM ecosystem_events WHERE id=?", (event_id,)
        ).fetchone()
        if not event:
            return False
        event = dict(event)

    # Phase 2 — project into the graph (graph_service opens its own connections).
    try:
        _project(event)
    except Exception:
        logger.exception("graph_populator projection failed for event %s", event_id)
        return False  # leave unconsumed → retried on next replay

    # Phase 3 — mark consumed (idempotent; OR IGNORE covers a lost race).
    with connect() as conn:
        _ensure_consumption_schema(conn)
        conn.execute(
            "INSERT OR IGNORE INTO ecosystem_event_consumptions "
            "(event_id, reducer, consumed_at) VALUES (?,?,?)",
            (event_id, REDUCER_NAME, _now()),
        )
    return True


def replay_unconsumed_events(limit: int = 200) -> int:
    """Backfill events this reducer has not consumed yet (e.g. after enabling V3)."""
    if not get_settings().GRAPHRAG_V3_ENABLED:
        return 0
    init_db()
    with connect() as conn:
        _ensure_consumption_schema(conn)
        rows = conn.execute(
            """
            SELECT e.id FROM ecosystem_events e
            LEFT JOIN ecosystem_event_consumptions c
              ON c.event_id=e.id AND c.reducer=?
            WHERE c.event_id IS NULL
            ORDER BY e.id ASC LIMIT ?
            """,
            (REDUCER_NAME, limit),
        ).fetchall()
    return sum(1 for row in rows if consume_event(int(row["id"])))


# --- projection ------------------------------------------------------------

def _project(event: dict) -> None:
    from app.xninetzy.os.graph.v3 import graph_service

    etype = event["event_type"]
    entity_id = event.get("entity_id")
    payload = _payload(event)
    prov = {
        "event_id": event["id"],
        "event_type": etype,
        "source": event.get("source"),
        "chat_id": event.get("chat_id"),
    }

    if etype == "goal_created":
        title = payload.get("title") or f"goal:{entity_id}"
        graph_service.upsert_node(
            node_type="goal",
            title=title,
            properties={"goal_id": entity_id, "domain": payload.get("domain")},
            provenance=prov,
            actor=REDUCER_NAME,
        )
        return

    if etype in ("task_created", "task_completed"):
        title = payload.get("title") or f"task:{entity_id}"
        status = "completed" if etype == "task_completed" else "open"
        graph_service.upsert_node(
            node_type="task",
            title=title,
            properties={"task_id": entity_id, "status": status},
            provenance=prov,
            actor=REDUCER_NAME,
        )
        _link_task_to_goal(graph_service, entity_id, title, prov)
        return

    if etype == "pdf_ingested":
        title = payload.get("title") or f"source:{entity_id}"
        graph_service.upsert_node(
            node_type="source",
            title=title,
            properties={"source_id": entity_id, "chunks": payload.get("chunks")},
            provenance=prov,
            actor=REDUCER_NAME,
        )
        return

    # Other event types (habit/money/review/query) are transient — not projected.


def _link_task_to_goal(graph_service, task_entity_id, task_title: str, prov: dict) -> None:
    """Deterministically link a task node to its goal node, if the task has one.

    Reads the canonical ``tasks``/``life_goals`` rows (no LLM) to resolve the goal
    title, then upserts a ``belongs_to`` edge task→goal.
    """
    if not task_entity_id:
        return
    try:
        with connect() as conn:
            task = conn.execute(
                "SELECT goal_id FROM tasks WHERE id=?", (task_entity_id,)
            ).fetchone()
            if not task or not task["goal_id"]:
                return
            goal = conn.execute(
                "SELECT title FROM life_goals WHERE id=?", (task["goal_id"],)
            ).fetchone()
        if not goal or not goal["title"]:
            return
    except Exception:
        return

    from app.xninetzy.os.graph.v3.identity import node_key

    src = node_key("task", task_title)
    tgt = node_key("goal", goal["title"])
    graph_service.upsert_edge(
        source_key=src,
        target_key=tgt,
        edge_type="belongs_to",
        provenance=prov,
        actor=REDUCER_NAME,
    )


def _payload(event: dict) -> dict:
    import json

    try:
        return json.loads(event.get("payload_json") or "{}")
    except Exception:
        return {}
