from __future__ import annotations

import asyncio
from threading import Event

import pytest

from xninetzy.core.config import get_settings
from xninetzy.interfaces import mcp_server
from xninetzy.os.graph.v3 import projection_worker


@pytest.fixture(autouse=True)
def worker_configuration(monkeypatch, tmp_path):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "lifespan.sqlite3"))
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    monkeypatch.setenv("GRAPH_SYNC_WORKER_ENABLED", "true")
    monkeypatch.setenv("GRAPH_SYNC_STARTUP_DELAY_SECONDS", "0")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_mcp_lifespan_owns_and_stops_the_opted_in_worker(monkeypatch):
    entered, stopped = asyncio.Event(), asyncio.Event()

    async def loop(*args, **kwargs):
        entered.set()
        try:
            await asyncio.Event().wait()
        finally:
            stopped.set()

    monkeypatch.setattr(projection_worker, "projection_worker_loop", loop)
    lifespan = mcp_server.mcp.settings.lifespan
    assert lifespan is not None
    async with lifespan(mcp_server.mcp):
        await asyncio.wait_for(entered.wait(), 1)
        assert not stopped.is_set()
    assert stopped.is_set()


@pytest.mark.asyncio
@pytest.mark.parametrize("flag", ["GRAPHRAG_V3_ENABLED", "GRAPH_SYNC_WORKER_ENABLED"])
async def test_disabled_worker_stays_off_without_loading_providers(monkeypatch, flag):
    monkeypatch.setenv(flag, "false")
    get_settings.cache_clear()
    calls = []

    async def must_not_start(*args, **kwargs):
        calls.append(True)

    monkeypatch.setattr(projection_worker, "projection_worker_loop", must_not_start)
    lifespan = mcp_server.mcp.settings.lifespan
    assert lifespan is not None
    async with lifespan(mcp_server.mcp):
        await asyncio.sleep(0)
    assert calls == []


def test_stop_before_tick_does_not_claim_or_execute(monkeypatch):
    stop = Event()
    stop.set()
    calls = []
    monkeypatch.setattr(projection_worker.sqlite_store, "claim_outbox_batch", lambda **kw: calls.append(True) or [])
    result = projection_worker._run_tick(stop_event=stop)
    assert calls == []
    assert result["claimed"] == 0


def test_shutdown_releases_only_unstarted_claims(monkeypatch):
    from xninetzy.db.sqlite import init_db, connect
    from xninetzy.db.migrations import run_migrations
    from xninetzy.os.graph.v3 import sqlite_store
    init_db()
    run_migrations()
    for title in ("first fixture", "unstarted fixture"):
        sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title=title))
    stop, calls = Event(), []

    def finish_current(row):
        calls.append(row["id"])
        stop.set()

    monkeypatch.setattr(projection_worker, "_apply_one", finish_current)
    result = projection_worker._run_tick(stop_event=stop)
    assert result["done"] == 1
    assert len(calls) == 1
    with connect() as conn:
        rows = conn.execute("SELECT status,attempts FROM graph_sync_outbox ORDER BY id").fetchall()
    assert [tuple(row) for row in rows] == [("done", 1), ("pending", 0)]


@pytest.mark.asyncio
async def test_shutdown_retains_inflight_tick_until_current_call_finishes(monkeypatch):
    entered, release, finished = Event(), Event(), Event()
    stops = []

    def blocked_tick(stop):
        stops.append(stop)
        entered.set()
        assert release.wait(5), "Test handler was not released"
        finished.set()
        return {"claimed": 1, "done": 1, "failed": 0}

    monkeypatch.setattr(projection_worker, "_run_tick", blocked_tick)
    try:
        async with projection_worker.background_projection():
            assert await asyncio.to_thread(entered.wait, 2)
            assert projection_worker.runtime_status()["running"] == 1
        assert stops[0].is_set()
        assert not finished.is_set()
        assert projection_worker.runtime_status()["running"] == 0
        assert projection_worker.runtime_status()["inflight"] == 1
    finally:
        release.set()
        assert await asyncio.to_thread(finished.wait, 2)
        async with asyncio.timeout(2):
            while projection_worker.runtime_status()["inflight"]:
                await asyncio.sleep(0.01)


def test_stale_shutdown_cannot_release_successor_claim():
    from xninetzy.db.sqlite import init_db, connect
    from xninetzy.db.migrations import run_migrations
    from xninetzy.os.graph.v3 import sqlite_store

    init_db()
    run_migrations()
    sqlite_store.upsert_node(sqlite_store.NodeUpsert(node_type="topic", title="Lease fixture"))
    first = sqlite_store.claim_outbox_batch(limit=1, lease_seconds=120)[0]
    with connect() as conn:
        conn.execute("UPDATE graph_sync_outbox SET lease_until='2000-01-01T00:00:00+00:00'")
    successor = sqlite_store.claim_outbox_batch(limit=1, lease_seconds=120)[0]
    assert successor["attempts"] == first["attempts"] + 1
    assert not sqlite_store.release_unstarted_claim(first)
    assert sqlite_store.claim_is_current(successor)
    assert sqlite_store.release_unstarted_claim(successor)
    assert not sqlite_store.release_unstarted_claim(successor)
