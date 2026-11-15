"""Exercise the existing optional Neo4j projection in an owned disposable container.

Requires an already pulled official image and the existing graph extra. No
owner database, graph, credential, network endpoint or Docker volume is reused.
"""
from __future__ import annotations

import json
import ipaddress
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
from uuid import uuid4


def docker(*args: str) -> str:
    result = subprocess.run(["docker", *args], capture_output=True, text=True, timeout=40)
    if result.returncode:
        raise RuntimeError(f"graph_smoke_docker_{args[0]}_failed")
    return result.stdout.strip()


def check(root: Path, uri: str, password: str, name: str) -> dict:
    os.environ.update(
        MCP_RUNTIME_MODE="container", SQLITE_PATH=str(root / "state.sqlite3"), DATA_DIR=str(root),
        GRAPHRAG_V3_ENABLED="true", NEO4J_ENABLED="true", NEO4J_AUTOSTART_ENABLED="false",
        NEO4J_URI=uri, NEO4J_HOST_URI=uri, NEO4J_USERNAME="neo4j", NEO4J_PASSWORD=password,
        NEO4J_AUTH_FILE="", NEO4J_CONNECT_TIMEOUT_SECONDS="0.5", NEO4J_FAILURE_COOLDOWN_SECONDS="1",
        GRAPH_SYNC_MAX_ATTEMPTS="6", GRAPH_SYNC_RETRY_BASE_SECONDS="0", GRAPH_SYNC_LEASE_SECONDS="120",
        HF_HUB_OFFLINE="1", TRANSFORMERS_OFFLINE="1", AUTO_GRAPH_ENABLED="false", AUTO_MEMORY_ENABLED="false",
        AUTO_IMPROVE_ENABLED="false", LIGHTNING_ENABLED="false", OS_SCHEDULER_ENABLED="false",
    )
    for setting in ("BACKUP_DIR", "OUTPUT_DIR", "HEBAT_DATA_DIR", "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_PATH",
                    "VECTOR_DATA_DIR", "GRAPH_VECTOR_DATA_DIR", "XNINETZY_SKILLS_DIR"):
        os.environ[setting] = str(root / setting.lower())
    for setting in ("MCP_HOST_DATA_DIR", "MCP_HOST_SQLITE_PATH"):
        os.environ.pop(setting, None)
    from xninetzy.core.config import Settings, get_settings
    Settings.model_config["env_file"] = None
    get_settings.cache_clear()
    from neo4j import GraphDatabase
    from xninetzy.db.sqlite import init_db, connect
    from xninetzy.db.migrations import run_migrations
    from xninetzy.os.graph.v3 import graph_service, neo4j_store, projection_worker, sqlite_store
    from unittest.mock import patch
    init_db()
    run_migrations()

    def ready():
        until = time.monotonic() + 90
        while time.monotonic() < until:
            try:
                with GraphDatabase.driver(uri, auth=("neo4j", password), connection_timeout=0.5, max_transaction_retry_time=0) as client:
                    client.verify_connectivity()
                    return
            except Exception:
                time.sleep(0.25)
        raise RuntimeError("graph_smoke_neo4j_readiness_timeout")

    def query(statement, **parameters):
        with GraphDatabase.driver(uri, auth=("neo4j", password), connection_timeout=1, max_transaction_retry_time=1) as client:
            return [row.data() for row in client.execute_query(statement, database_="neo4j", **parameters).records]

    # Only Neo4j is the live integration under test; no embedding/model is run.
    vector_stub = patch.object(projection_worker.faiss_store, "upsert_node_vector", return_value=None)
    vector_stub.start()
    try:
        ready()
        first = graph_service.upsert_node(node_type="topic", title="Local graph fixture", content="original")
        second = graph_service.upsert_node(node_type="topic", title="Related fixture")
        edge = graph_service.upsert_edge(source_key=first.key, target_key=second.key, edge_type="related_to", weight=2.75, properties={"evidence": "fixture"})
        assert projection_worker._run_tick() == {"claimed": 3, "done": 3, "failed": 0}
        relationship = query("MATCH ()-[r:GRAPH_EDGE {key:$key}]->() RETURN r.weight AS weight, r.props AS props", key=edge.key)
        assert len(relationship) == 1 and relationship[0]["weight"] == 2.75
        assert json.loads(relationship[0]["props"]) == {"evidence": "fixture"}
        # Duplicate deliveries must not create duplicate relationships.
        sqlite_store.enqueue_full_resync()
        assert projection_worker._run_tick()["failed"] == 0
        assert query("MATCH ()-[r:GRAPH_EDGE {key:$key}]->() RETURN count(r) AS n", key=edge.key) == [{"n": 1}]

        docker("stop", "--time", "5", name)
        changed = graph_service.upsert_node(node_type="topic", title="Local graph fixture", content="changed offline")
        assert changed.version == 2
        # Closing a broken pool gives the next request a real bounded connectivity probe.
        # The stop is real, not a mocked failure; no owner service is involved.
        neo4j_store.close_driver()
        neo4j_store.clear_unavailable()
        assert projection_worker._run_tick() == {"claimed": 1, "done": 0, "failed": 1}
        assert sqlite_store.get_node(first.key)["content"] == "changed offline"
        assert sqlite_store.fts_search_nodes("changed")
        with connect() as conn:
            row = conn.execute("SELECT status,attempts FROM graph_sync_outbox ORDER BY id DESC LIMIT 1").fetchone()
        assert tuple(row) == ("failed", 1)

        docker("start", name)
        ready()
        neo4j_store.close_driver()
        neo4j_store.clear_unavailable()
        assert projection_worker._run_tick() == {"claimed": 1, "done": 1, "failed": 0}
        assert sqlite_store.get_node(first.key)["neo4j_synced_at"] is not None
        assert graph_service.soft_delete_node(first.key)
        assert projection_worker._run_tick()["done"] == 1
        assert query("MATCH (n:GraphNode {key:$key}) RETURN count(n) AS n", key=first.key) == [{"n": 0}]
        assert query("MATCH ()-[r:GRAPH_EDGE {key:$key}]->() RETURN count(r) AS n", key=edge.key) == [{"n": 0}]
        return {"live_neo4j": "passed", "canonical_edge_weight_properties": "passed",
                "duplicate_delivery": "passed", "backend_stop_retry_restart": "passed",
                "sqlite_lexical_fallback": "passed", "node_delete_and_relationship_removal": "passed",
                "owner_data_used": False, "faiss": "NOT_TESTED", "limitations": "Controlled local backend fixture; no all-client worker startup, owner reconciliation or multi-host guarantee."}
    finally:
        neo4j_store.close_driver()
        vector_stub.stop()


def main() -> int:
    image = "neo4j:5.26-community"
    image_id = docker("image", "inspect", image, "--format", "{{.Id}}")
    name = f"xninetzy-graph-smoke-{uuid4().hex[:10]}"
    network = name + "-net"
    with tempfile.TemporaryDirectory(prefix="xn-graph-smoke-") as directory:
        root = Path(directory)
        password = secrets.token_hex(16)
        auth = root / "auth.env"
        auth.touch(mode=0o600)
        auth.write_text(f"NEO4J_AUTH=neo4j/{password}\n")
        network_id = docker("network", "create", "--internal", "--label", "xninetzy.test=graph-projection", network)
        container_id = None
        try:
            container_id = docker("create", "--name", name, "--network", network_id,
                   "--label", "xninetzy.test=graph-projection",
                   "--user", "7474:7474", "--cap-drop", "ALL",
                   "--security-opt", "no-new-privileges:true", "--memory", "1536m", "--cpus", "1.5",
                   "--pids-limit", "256", "--env-file", str(auth),
                   "--env", "NEO4J_server_memory_heap_initial__size=256m", "--env", "NEO4J_server_memory_heap_max__size=256m",
                   "--env", "NEO4J_server_memory_pagecache_size=128m", image_id)
            docker("start", container_id)
            state = json.loads(docker("inspect", container_id))[0]
            networks = state["NetworkSettings"]["Networks"]
            assert len(networks) == 1
            address = next(iter(networks.values()))["IPAddress"]
            assert ipaddress.ip_address(address).is_private
            assert all(value is None for value in state["NetworkSettings"]["Ports"].values())
            # Internal bridge publishing is unsupported on this host. Reach only
            # this exact owned fixture's private address; no host port is opened.
            result = check(root, f"bolt://{address}:7687", password, container_id)
            result.update(neo4j_image=image, neo4j_image_id=image_id, network="temporary internal bridge / no published host ports")
            print(json.dumps(result, indent=2))
        finally:
            try:
                if container_id:
                    docker("rm", "--force", "--volumes", container_id)
            finally:
                docker("network", "rm", network_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
