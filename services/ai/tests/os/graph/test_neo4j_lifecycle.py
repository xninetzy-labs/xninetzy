"""Tests for on-demand Neo4j lifecycle (host-mode autostart).

No Docker and no real Neo4j are touched: subprocess and socket probes are
monkeypatched. We assert the host/URI decision, the bolt probe wiring, and that
``ensure_running`` early-returns (no ``docker compose up``) when the port is
already open.
"""

from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.graph.v3 import neo4j_lifecycle, neo4j_store


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    get_settings.cache_clear()
    monkeypatch.setattr(neo4j_lifecycle, "_idle_thread_started", False, raising=False)
    monkeypatch.setattr(neo4j_lifecycle, "_last_access", 0.0, raising=False)
    yield
    get_settings.cache_clear()


def test_resolve_uri_host_uses_loopback(monkeypatch):
    monkeypatch.setattr(neo4j_lifecycle, "is_host_runtime", lambda: True)
    settings = get_settings()
    assert neo4j_store._resolve_uri(settings) == settings.NEO4J_HOST_URI


def test_resolve_uri_container_uses_compose_dns(monkeypatch):
    monkeypatch.setattr(neo4j_lifecycle, "is_host_runtime", lambda: False)
    settings = get_settings()
    assert neo4j_store._resolve_uri(settings) == settings.NEO4J_URI


def test_bolt_endpoint_parses_host_uri():
    settings = get_settings()
    host, port = neo4j_lifecycle._bolt_endpoint(settings)
    assert host == "127.0.0.1"
    assert port == 7687


def test_bolt_ready_true_when_socket_connects(monkeypatch):
    class _Sock:
        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

    monkeypatch.setattr(
        neo4j_lifecycle.socket, "create_connection", lambda *a, **k: _Sock()
    )
    assert neo4j_lifecycle._bolt_ready("127.0.0.1", 7687) is True


def test_bolt_ready_false_on_oserror(monkeypatch):
    def _boom(*a, **k):
        raise OSError("refused")

    monkeypatch.setattr(neo4j_lifecycle.socket, "create_connection", _boom)
    assert neo4j_lifecycle._bolt_ready("127.0.0.1", 7687) is False


def test_ensure_running_early_returns_when_port_open(monkeypatch):
    monkeypatch.setenv("NEO4J_AUTOSTART_ENABLED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(neo4j_lifecycle, "is_host_runtime", lambda: True)
    monkeypatch.setattr(neo4j_lifecycle, "_bolt_ready", lambda *a, **k: True)

    called = {"n": 0}

    def _no_run(*a, **k):
        called["n"] += 1

    monkeypatch.setattr(neo4j_lifecycle.subprocess, "run", _no_run)
    monkeypatch.setattr(neo4j_lifecycle, "_start_idle_watch", lambda: None)

    assert neo4j_lifecycle.ensure_running() is True
    assert called["n"] == 0  # no docker compose up when already reachable


def test_ensure_running_noop_when_not_host(monkeypatch):
    monkeypatch.setenv("NEO4J_AUTOSTART_ENABLED", "true")
    get_settings.cache_clear()
    monkeypatch.setattr(neo4j_lifecycle, "is_host_runtime", lambda: False)
    assert neo4j_lifecycle.ensure_running() is False


def test_ensure_running_noop_when_autostart_disabled(monkeypatch):
    monkeypatch.setenv("NEO4J_AUTOSTART_ENABLED", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(neo4j_lifecycle, "is_host_runtime", lambda: True)
    assert neo4j_lifecycle.ensure_running() is False


def test_clear_unavailable_resets_sticky_flag(monkeypatch):
    monkeypatch.setattr(neo4j_store, "_unavailable", True, raising=False)
    neo4j_store.clear_unavailable()
    assert neo4j_store._unavailable is False
