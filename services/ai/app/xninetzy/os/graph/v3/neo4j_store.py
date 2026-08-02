"""Neo4j structural projection for GraphRAG V3 — rebuildable, never canonical.

Hard safety rules baked in:
* Exactly ONE node label ``GraphNode`` and ONE relationship type ``GRAPH_EDGE``.
  The domain node_type / edge_type live as *properties*, never as labels or
  rel-types, so model-generated strings can never inject schema.
* Every query is parameterized. No string interpolation of values.
* Idempotent MERGE on ``canonical_key``.
* Every failure is swallowed and logged. Neo4j being down must never break
  chat, knowledge, reminders, or workflows — it is a projection, not truth.

The driver is a lazy singleton closed at process exit. Connectivity is verified
once; if it fails the store degrades to a no-op and the SQLite/FAISS legs carry
retrieval on their own.
"""

from __future__ import annotations

import atexit
import threading
import time
from pathlib import Path

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging

logger = logging.getLogger(__name__)

_driver = None
_driver_lock = threading.Lock()
_unavailable = False
_unavailable_until = 0.0


def _resolve_password(settings) -> str:
    """Prefer the mounted secret file (Docker secret) over env. The file may
    hold either a bare password or the ``neo4j/<password>`` NEO4J_AUTH format."""
    auth_file = (settings.NEO4J_AUTH_FILE or "").strip()
    if auth_file:
        try:
            raw = Path(auth_file).read_text().strip()
            if raw:
                return raw.split("/", 1)[1] if "/" in raw else raw
        except Exception as e:
            logger.warning("Could not read NEO4J_AUTH_FILE (%s): %s", auth_file, e)
    return settings.NEO4J_PASSWORD


def _resolve_uri(settings) -> str:
    """Host MCP cannot resolve the docker-DNS hostname ``neo4j``; swap to the
    published loopback bolt port. Inside the container we keep the compose URI."""
    from app.xninetzy.os.graph.v3 import neo4j_lifecycle

    if neo4j_lifecycle.is_host_runtime():
        return settings.NEO4J_HOST_URI or settings.NEO4J_URI
    return settings.NEO4J_URI


def clear_unavailable() -> None:
    global _unavailable, _unavailable_until
    _unavailable = False
    _unavailable_until = 0.0


def _failure_active(settings) -> bool:
    global _unavailable, _unavailable_until
    if not _unavailable:
        return False
    if _unavailable_until <= 0.0:
        return True
    if time.monotonic() < _unavailable_until:
        return True
    _unavailable = False
    _unavailable_until = 0.0
    return False


def _latch_unavailable(settings) -> None:
    global _unavailable, _unavailable_until
    _unavailable = True
    cooldown = max(0.0, float(settings.NEO4J_FAILURE_COOLDOWN_SECONDS))
    _unavailable_until = time.monotonic() + cooldown if cooldown else 0.0


def _touch_access() -> None:
    try:
        from app.xninetzy.os.graph.v3 import neo4j_lifecycle

        neo4j_lifecycle.touch_access()
    except Exception:
        pass


def _get_driver():
    global _driver, _unavailable, _unavailable_until
    settings = get_settings()
    if _failure_active(settings):
        return None
    if _driver is not None:
        _touch_access()
        return _driver
    with _driver_lock:
        if _driver is not None:
            _touch_access()
            return _driver
        if _failure_active(settings):
            return None
        if not (settings.GRAPHRAG_V3_ENABLED and settings.NEO4J_ENABLED):
            _unavailable = True
            _unavailable_until = 0.0
            return None
        if settings.NEO4J_AUTOSTART_ENABLED:
            try:
                from app.xninetzy.os.graph.v3 import neo4j_lifecycle

                neo4j_lifecycle.ensure_running()
            except Exception as e:
                logger.warning('Neo4j ensure_running failed (non-fatal): %s', e)
        driver = None
        try:
            from neo4j import GraphDatabase

            driver = GraphDatabase.driver(
                _resolve_uri(settings),
                auth=(settings.NEO4J_USERNAME, _resolve_password(settings)),
                connection_timeout=max(
                    0.5, float(settings.NEO4J_CONNECT_TIMEOUT_SECONDS)
                ),
            )
            driver.verify_connectivity()
            _driver = driver
            _unavailable = False
            _unavailable_until = 0.0
            atexit.register(close_driver)
            _ensure_constraints()
            logger.info('Neo4j projection connected: %s', _resolve_uri(settings))
            return _driver
        except Exception as e:
            if driver is not None:
                try:
                    driver.close()
                except Exception:
                    pass
            _latch_unavailable(settings)
            logger.warning('Neo4j unavailable — projection disabled: %s', e)
            return None


def close_driver() -> None:
    global _driver
    if _driver is not None:
        try:
            _driver.close()
        except Exception:
            pass
        _driver = None


def _database() -> str:
    return get_settings().NEO4J_DATABASE or "neo4j"


def _ensure_constraints() -> None:
    """One uniqueness constraint on GraphNode.key so MERGE is O(1) and idempotent."""
    try:
        from neo4j import RoutingControl

        _driver.execute_query(
            "CREATE CONSTRAINT graph_node_key IF NOT EXISTS "
            "FOR (n:GraphNode) REQUIRE n.key IS UNIQUE",
            database_=_database(),
            routing_=RoutingControl.WRITE,
        )
    except Exception as e:
        logger.warning("Neo4j constraint setup failed (non-fatal): %s", e)


def upsert_node(*, key: str, node_type: str, title: str, properties: dict | None = None) -> bool:
    driver = _get_driver()
    if driver is None:
        return False
    try:
        from neo4j import RoutingControl

        driver.execute_query(
            """
            MERGE (n:GraphNode {key: $key})
            SET n.node_type = $node_type,
                n.title = $title,
                n.props = $props
            """,
            key=key,
            node_type=node_type,
            title=title,
            props=_flatten(properties),
            database_=_database(),
            routing_=RoutingControl.WRITE,
        )
        return True
    except Exception as e:
        logger.warning("Neo4j node upsert failed (non-fatal): %s", e)
        return False


def upsert_edge(
    *, key: str, source_key: str, target_key: str, edge_type: str,
    weight: float = 1.0, properties: dict | None = None,
) -> bool:
    driver = _get_driver()
    if driver is None:
        return False
    try:
        from neo4j import RoutingControl

        driver.execute_query(
            """
            MERGE (s:GraphNode {key: $source_key})
            MERGE (t:GraphNode {key: $target_key})
            MERGE (s)-[r:GRAPH_EDGE {key: $key}]->(t)
            SET r.edge_type = $edge_type,
                r.weight = $weight,
                r.props = $props
            """,
            key=key,
            source_key=source_key,
            target_key=target_key,
            edge_type=edge_type,
            weight=float(weight),
            props=_flatten(properties),
            database_=_database(),
            routing_=RoutingControl.WRITE,
        )
        return True
    except Exception as e:
        logger.warning("Neo4j edge upsert failed (non-fatal): %s", e)
        return False


def delete_node(key: str) -> bool:
    driver = _get_driver()
    if driver is None:
        return False
    try:
        from neo4j import RoutingControl

        driver.execute_query(
            "MATCH (n:GraphNode {key: $key}) DETACH DELETE n",
            key=key,
            database_=_database(),
            routing_=RoutingControl.WRITE,
        )
        return True
    except Exception as e:
        logger.warning("Neo4j node delete failed (non-fatal): %s", e)
        return False


def neighborhood(keys: list[str], depth: int = 1, limit: int = 60) -> list[dict]:
    """Structural leg of hybrid retrieval: expand up to ``depth`` hops from the
    seed keys. Returns neighbor node keys with the shortest hop distance seen.
    Empty list on any failure (caller falls back to SQLite edges)."""
    driver = _get_driver()
    if driver is None or not keys:
        return []
    depth = max(1, min(depth, 3))
    try:
        from neo4j import RoutingControl

        records, _, _ = driver.execute_query(
            f"""
            MATCH (s:GraphNode) WHERE s.key IN $keys
            MATCH p = (s)-[:GRAPH_EDGE*1..{depth}]-(m:GraphNode)
            WITH m.key AS key, m.node_type AS node_type, m.title AS title,
                 min(length(p)) AS hops
            RETURN key, node_type, title, hops
            ORDER BY hops ASC
            LIMIT $limit
            """,
            keys=keys,
            limit=limit,
            database_=_database(),
            routing_=RoutingControl.READ,
        )
        return [
            {"key": r["key"], "node_type": r["node_type"],
             "title": r["title"], "hops": r["hops"]}
            for r in records
        ]
    except Exception as e:
        logger.warning("Neo4j neighborhood query failed (non-fatal): %s", e)
        return []


def shortest_path(source_key: str, target_key: str, max_hops: int = 5) -> list[dict]:
    driver = _get_driver()
    if driver is None:
        return []
    max_hops = max(1, min(max_hops, 8))
    try:
        from neo4j import RoutingControl

        records, _, _ = driver.execute_query(
            f"""
            MATCH (s:GraphNode {{key: $source_key}}), (t:GraphNode {{key: $target_key}})
            MATCH p = shortestPath((s)-[:GRAPH_EDGE*1..{max_hops}]-(t))
            RETURN [n IN nodes(p) | {{key: n.key, title: n.title, node_type: n.node_type}}] AS hops
            """,
            source_key=source_key,
            target_key=target_key,
            database_=_database(),
            routing_=RoutingControl.READ,
        )
        if not records:
            return []
        return records[0]["hops"] or []
    except Exception as e:
        logger.warning("Neo4j shortest_path failed (non-fatal): %s", e)
        return []


def wipe_all() -> bool:
    """Drop every projected node/edge. Used by the HITL rebuild before replay."""
    driver = _get_driver()
    if driver is None:
        return False
    try:
        from neo4j import RoutingControl

        driver.execute_query(
            "MATCH (n:GraphNode) DETACH DELETE n",
            database_=_database(),
            routing_=RoutingControl.WRITE,
        )
        return True
    except Exception as e:
        logger.warning("Neo4j wipe failed (non-fatal): %s", e)
        return False


def availability_status() -> dict:
    settings = get_settings()
    configured = bool(settings.GRAPHRAG_V3_ENABLED and settings.NEO4J_ENABLED)
    remaining = 0.0
    if _unavailable_until > 0.0:
        remaining = max(0.0, _unavailable_until - time.monotonic())
    latched = _failure_active(settings) if configured else False
    return {
        "configured": configured,
        "available": _driver is not None,
        "failure_latched": latched,
        "cooldown_seconds": round(remaining, 3),
    }


def is_available() -> bool:
    return _get_driver() is not None


def _flatten(properties: dict | None) -> str:
    """Neo4j property values must be primitives; store nested props as JSON."""
    import json

    return json.dumps(properties or {}, ensure_ascii=False)
