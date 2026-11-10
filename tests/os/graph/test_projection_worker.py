from __future__ import annotations

import pytest

from xninetzy.core.config import get_settings
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect, init_db
from xninetzy.os.graph.v3 import projection_worker, sqlite_store


@pytest.fixture(autouse=True)
def isolated_projection(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "projection.sqlite3"))
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    monkeypatch.setenv("NEO4J_ENABLED", "true")
    monkeypatch.setenv("NEO4J_AUTOSTART_ENABLED", "false")
    monkeypatch.setenv("GRAPH_SYNC_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("GRAPH_SYNC_RETRY_BASE_SECONDS", "0")
    get_settings.cache_clear()
    init_db()
    run_migrations()
    monkeypatch.setattr(projection_worker.faiss_store, "upsert_node_vector", lambda *a: None)
    for name in ("upsert_node", "upsert_edge", "delete_node"):
        monkeypatch.setattr(projection_worker.neo4j_store, name, lambda *a, **kw: True)
    yield
    get_settings.cache_clear()


def _seed_operation(operation):
    node = sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title="Synthetic"))
    key, entity_type, op = node.key, "node", "upsert"
    if operation == "edge":
        target = sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title="Target"))
        edge = sqlite_store.upsert_edge(sqlite_store.EdgeUpsert(
            source_key=node.key, target_key=target.key, edge_type="related_to",
        ))
        key, entity_type = edge.key, "edge"
    elif operation == "delete":
        sqlite_store.soft_delete_node(node.key)
        op = "delete"
    with connect() as conn:
        row = conn.execute(
            "SELECT * FROM graph_sync_outbox WHERE entity_type=? AND entity_key=? AND op=?",
            (entity_type, key, op),
        ).fetchone()
        # Leave exactly this synthetic operation pending for tick bookkeeping.
        conn.execute("UPDATE graph_sync_outbox SET status='done' WHERE id<>?", (row["id"],))
    return dict(row)


def _canonical_row(row):
    table = "graph_nodes_v3" if row["entity_type"] == "node" else "graph_edges_v3"
    with connect() as conn:
        result = conn.execute(
            f"SELECT * FROM {table} WHERE canonical_key=?", (row["entity_key"],),
        ).fetchone()
    return dict(result)


@pytest.mark.parametrize("operation", ["node", "edge", "delete"])
def test_unacknowledged_enabled_projection_never_claims_success(monkeypatch, operation):
    row = _seed_operation(operation)
    function = {"node": "upsert_node", "edge": "upsert_edge", "delete": "delete_node"}[operation]
    monkeypatch.setattr(projection_worker.neo4j_store, function, lambda *a, **kw: False)
    canonical_before = _canonical_row(row)

    with pytest.raises(RuntimeError, match="Neo4j"):
        projection_worker._apply_one(row)

    assert _canonical_row(row) == canonical_before
    assert _canonical_row(row)["neo4j_synced_at"] is None


@pytest.mark.parametrize("operation", ["node", "edge", "delete"])
def test_projection_failure_retries_with_bound_and_preserves_canonical(monkeypatch, operation):
    row = _seed_operation(operation)
    function = {"node": "upsert_node", "edge": "upsert_edge", "delete": "delete_node"}[operation]
    calls = []

    def fail_projection(*args, **kwargs):
        calls.append(operation)
        return False

    monkeypatch.setattr(projection_worker.neo4j_store, function, fail_projection)
    canonical_before = _canonical_row(row)
    for expected_attempts in (1, 2):
        assert projection_worker._run_tick() == {"claimed": 1, "done": 0, "failed": 1}
        with connect() as conn:
            pending = conn.execute("SELECT * FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone()
        assert pending["status"] == "failed"
        assert pending["attempts"] == expected_attempts
        assert "Neo4j" in pending["last_error"]
        assert pending["lease_until"] is None
    assert projection_worker._run_tick() == {"claimed": 0, "done": 0, "failed": 0}
    assert len(calls) == 2
    assert _canonical_row(row) == canonical_before


@pytest.mark.parametrize("operation", ["node", "edge", "delete"])
@pytest.mark.parametrize("flag", ["NEO4J_ENABLED", "GRAPHRAG_V3_ENABLED"])
def test_disabled_projection_is_not_called_or_marked_synced(monkeypatch, operation, flag):
    row = _seed_operation(operation)
    monkeypatch.setenv(flag, "false")
    get_settings.cache_clear()

    def must_not_connect(*args, **kwargs):
        raise AssertionError("disabled Neo4j must not be invoked")

    for function in ("upsert_node", "upsert_edge", "delete_node"):
        monkeypatch.setattr(projection_worker.neo4j_store, function, must_not_connect)

    assert projection_worker._run_tick() == {"claimed": 1, "done": 1, "failed": 0}
    assert _canonical_row(row)["neo4j_synced_at"] is None


@pytest.mark.parametrize("operation", ["node", "edge"])
def test_acknowledged_projection_marks_synced(monkeypatch, operation):
    row = _seed_operation(operation)

    assert projection_worker._run_tick() == {"claimed": 1, "done": 1, "failed": 0}
    assert _canonical_row(row)["neo4j_synced_at"] is not None


def test_failed_attempt_can_recover_before_retry_limit(monkeypatch):
    row = _seed_operation("node")
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", lambda **kw: False)
    assert projection_worker._run_tick() == {"claimed": 1, "done": 0, "failed": 1}
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", lambda **kw: True)

    assert projection_worker._run_tick() == {"claimed": 1, "done": 1, "failed": 0}
    assert _canonical_row(row)["neo4j_synced_at"] is not None
    with connect() as conn:
        done = conn.execute("SELECT * FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone()
    assert done["attempts"] == 2
    assert done["last_error"] is None


@pytest.mark.parametrize("status", ["failed", "processing"])
def test_exhausted_outbox_row_is_not_claimed_again(status):
    row = _seed_operation("node")
    with connect() as conn:
        conn.execute(
            "UPDATE graph_sync_outbox SET status=?, attempts=2, next_retry_at=NULL WHERE id=?",
            (status, row["id"]),
        )

    assert sqlite_store.claim_outbox_batch(limit=10, lease_seconds=10) == []


def test_failure_retains_backoff_before_next_attempt(monkeypatch):
    row = _seed_operation("node")
    monkeypatch.setenv("GRAPH_SYNC_RETRY_BASE_SECONDS", "30")
    get_settings.cache_clear()
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", lambda **kw: False)

    assert projection_worker._run_tick() == {"claimed": 1, "done": 0, "failed": 1}
    assert projection_worker._run_tick() == {"claimed": 0, "done": 0, "failed": 0}
    with connect() as conn:
        failed = conn.execute("SELECT * FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone()
    assert failed["attempts"] == 1
    assert failed["next_retry_at"] is not None


def test_neo4j_failure_does_not_prevent_independent_vector_attempt(monkeypatch):
    row = _seed_operation("node")
    vectors = []
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", lambda **kw: False)
    monkeypatch.setattr(
        projection_worker.faiss_store, "upsert_node_vector", lambda *args: vectors.append(args),
    )

    with pytest.raises(RuntimeError, match="Neo4j"):
        projection_worker._apply_one(row)
    assert len(vectors) == 1
    assert vectors[0][0] == row["entity_key"]
