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


def test_claim_returns_the_persisted_lease_not_the_old_pending_row():
    row = _seed_operation("node")
    claimed = sqlite_store.claim_outbox_batch(limit=1, lease_seconds=60)[0]
    with connect() as conn:
        stored = dict(conn.execute("SELECT * FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone())
    assert claimed == stored
    assert claimed["status"] == "processing" and claimed["attempts"] == 1
    assert claimed["lease_until"] is not None


def _reclaim(row):
    with connect() as conn:
        conn.execute("UPDATE graph_sync_outbox SET lease_until='2000-01-01T00:00:00+00:00' WHERE id=?", (row["id"],))
    return sqlite_store.claim_outbox_batch(limit=1, lease_seconds=60)[0]


@pytest.mark.parametrize("fail", [False, True])
def test_stale_worker_cannot_finalize_an_operation_reclaimed_during_effect(monkeypatch, fail):
    row = _seed_operation("node")
    successor = []

    def complete_after_takeover(**kwargs):
        successor.append(_reclaim(row))
        if fail:
            raise RuntimeError("private fixture payload")
        return True

    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", complete_after_takeover)
    stats = projection_worker._run_tick()
    with connect() as conn:
        after = dict(conn.execute("SELECT * FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone())
    assert after == successor[0]
    assert stats["done"] == stats["failed"] == 0
    assert stats["lease_lost"] == 1
    assert _canonical_row(row)["neo4j_synced_at"] is None


def test_expired_claim_is_not_dispatched_to_a_provider(monkeypatch):
    row = _seed_operation("node")
    claim = sqlite_store.claim_outbox_batch

    calls = []
    def expired_batch_without_recursion(**kwargs):
        batch = claim(**kwargs)
        with connect() as conn:
            conn.execute("UPDATE graph_sync_outbox SET lease_until='2000-01-01' WHERE id=?", (row["id"],))
        claim(limit=1, lease_seconds=60)
        return batch

    monkeypatch.setattr(sqlite_store, "claim_outbox_batch", expired_batch_without_recursion)
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", lambda **kw: calls.append(kw) or True)
    stats = projection_worker._run_tick()
    assert calls == []
    assert stats["done"] == 0 and stats["lease_lost"] == 1


@pytest.mark.parametrize("entity_type,operation", [("node", "unknown"), ("unknown", "upsert"), ("edge", "delete")])
def test_unknown_outbox_operations_fail_without_provider_calls(monkeypatch, entity_type, operation):
    row = _seed_operation("node")
    with connect() as conn:
        conn.execute("UPDATE graph_sync_outbox SET entity_type=?,op=? WHERE id=?", (entity_type, operation, row["id"]))
    calls = []
    for name in ("upsert_node", "upsert_edge", "delete_node"):
        monkeypatch.setattr(projection_worker.neo4j_store, name, lambda *a, **kw: calls.append(kw) or True)
    assert projection_worker._run_tick() == {"claimed": 1, "done": 0, "failed": 1}
    assert calls == []


def test_old_edge_event_projects_current_canonical_weight_and_properties(monkeypatch):
    row = _seed_operation("edge")
    import json
    payload = json.loads(row["payload_json"])
    sqlite_store.upsert_edge(sqlite_store.EdgeUpsert(
        source_key=payload["source_key"], target_key=payload["target_key"],
        edge_type=payload["edge_type"], weight=2.5, properties={"evidence": "canonical"},
    ))
    calls = []
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_edge", lambda **kw: calls.append(kw) or True)
    projection_worker._apply_one(row)
    assert calls[0]["weight"] == 2.5
    assert calls[0]["properties"] == {"evidence": "canonical"}


def test_edge_event_cannot_recreate_a_deleted_endpoint(monkeypatch):
    row = _seed_operation("edge")
    import json
    sqlite_store.soft_delete_node(json.loads(row["payload_json"])["source_key"])
    calls = []
    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_edge", lambda **kw: calls.append(kw) or True)
    projection_worker._apply_one(row)
    assert calls == []


def test_acknowledgement_cannot_mark_a_newer_canonical_version_synced(monkeypatch):
    row = _seed_operation("node")

    def update_during_projection(**kwargs):
        sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title="Synthetic", content="new version"))
        return True

    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", update_during_projection)
    projection_worker._run_tick()
    assert _canonical_row(row)["version"] == 2
    assert _canonical_row(row)["neo4j_synced_at"] is None


def test_canonical_update_invalidates_the_old_projection_marker():
    row = _seed_operation("node")
    projection_worker._run_tick()
    assert _canonical_row(row)["neo4j_synced_at"] is not None
    sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title="Synthetic", content="changed"))
    assert _canonical_row(row)["neo4j_synced_at"] is None


def test_provider_exception_payload_does_not_enter_outbox_or_logs(monkeypatch, caplog):
    row = _seed_operation("node")

    def private_failure(**kwargs):
        raise RuntimeError("synthetic-private-credential-value")

    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", private_failure)
    assert projection_worker._run_tick()["failed"] == 1
    with connect() as conn:
        error = conn.execute("SELECT last_error FROM graph_sync_outbox WHERE id=?", (row["id"],)).fetchone()[0]
    assert "synthetic-private-credential-value" not in error + caplog.text
    assert "RuntimeError" in error


def test_unleased_finalization_is_rejected():
    row = _seed_operation("node")
    claim = sqlite_store.claim_outbox_batch(limit=1, lease_seconds=60)[0]
    assert sqlite_store.mark_outbox_done(row["id"]) is False
    assert sqlite_store.mark_outbox_failed(row["id"], error="unsafe", max_attempts=2, retry_base_seconds=0) is False
    assert sqlite_store.claim_is_current(claim)


def test_concurrent_updated_projection_ticks_do_not_share_a_provider(monkeypatch):
    from concurrent.futures import ThreadPoolExecutor
    from threading import Event
    _seed_operation("node")
    entered, release = Event(), Event()
    calls = []

    def slow_projection(**kwargs):
        calls.append(kwargs)
        entered.set()
        assert release.wait(5)
        return True

    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_node", slow_projection)
    with ThreadPoolExecutor(max_workers=1) as pool:
        first = pool.submit(projection_worker._run_tick)
        try:
            assert entered.wait(5)
            assert projection_worker._run_tick() == {"claimed": 0, "done": 0, "failed": 0, "deferred": 1}
        finally:
            release.set()
        assert first.result(timeout=5)["done"] == 1
    assert len(calls) == 1


def test_projection_lock_symlink_is_not_followed(tmp_path):
    from xninetzy.db.sqlite import get_db_path
    target = tmp_path / "unrelated"
    target.write_text("keep")
    (get_db_path().parent / ".graph-projection.lock").symlink_to(target)
    with pytest.raises(OSError):
        projection_worker._run_tick()
    assert target.read_text() == "keep"


def test_deletion_during_edge_ack_does_not_mark_edge_current(monkeypatch):
    import json
    row = _seed_operation("edge")

    def delete_during_ack(**kwargs):
        sqlite_store.soft_delete_node(json.loads(row["payload_json"])["source_key"])
        return True

    monkeypatch.setattr(projection_worker.neo4j_store, "upsert_edge", delete_during_ack)
    projection_worker._run_tick()
    assert _canonical_row(row)["neo4j_synced_at"] is None


def test_projection_does_not_initialize_a_missing_canonical_database(monkeypatch, tmp_path):
    from xninetzy.db import sqlite as database
    missing = tmp_path / "unexpected-new.sqlite3"
    monkeypatch.setattr(database, "get_db_path", lambda: missing)
    monkeypatch.setattr(sqlite_store, "get_db_path", lambda: missing)
    with pytest.raises(Exception):
        projection_worker._run_tick()
    assert not missing.exists()
