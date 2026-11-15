"""Mocked error-serialization checks; these do not establish backend availability."""
from __future__ import annotations

import sys
from types import SimpleNamespace

import pytest

from xninetzy.os.graph.v3 import neo4j_store


def _fail(*args, **kwargs):
    raise RuntimeError("synthetic-private-provider-payload")


@pytest.mark.parametrize("function,arguments", [
    ("upsert_node", {"key": "fixture", "node_type": "topic", "title": "Fixture"}),
    ("upsert_edge", {"key": "edge", "source_key": "a", "target_key": "b", "edge_type": "related_to"}),
    ("delete_node", {"key": "fixture"}),
    ("neighborhood", {"keys": ["fixture"]}),
    ("shortest_path", {"source_key": "a", "target_key": "b"}),
    ("wipe_all", {}),
    ("_ensure_constraints", {}),
])
def test_query_errors_expose_type_without_private_payload(monkeypatch, caplog, function, arguments):
    driver = SimpleNamespace(execute_query=_fail)
    monkeypatch.setattr(neo4j_store, "_get_driver", lambda: driver)
    monkeypatch.setattr(neo4j_store, "_driver", driver)
    monkeypatch.setitem(sys.modules, "neo4j", SimpleNamespace(RoutingControl=SimpleNamespace(READ="read", WRITE="write")))
    getattr(neo4j_store, function)(**arguments)
    assert "synthetic-private-provider-payload" not in caplog.text
    assert "RuntimeError" in caplog.text


def test_auth_file_read_error_does_not_log_path_or_exception_payload(monkeypatch, caplog):
    monkeypatch.setattr(neo4j_store.Path, "read_text", _fail)
    settings = SimpleNamespace(NEO4J_AUTH_FILE="/synthetic-private-path/auth", NEO4J_PASSWORD="fixture-fallback")
    assert neo4j_store._resolve_password(settings) == "fixture-fallback"
    assert "synthetic-private-provider-payload" not in caplog.text
    assert "synthetic-private-path" not in caplog.text


def test_connectivity_exception_does_not_log_private_payload(monkeypatch, caplog):
    from xninetzy.core.config import get_settings
    monkeypatch.setenv("GRAPHRAG_V3_ENABLED", "true")
    monkeypatch.setenv("NEO4J_ENABLED", "true")
    monkeypatch.setenv("NEO4J_AUTOSTART_ENABLED", "false")
    get_settings.cache_clear()
    monkeypatch.setattr(neo4j_store, "_driver", None)
    monkeypatch.setattr(neo4j_store, "_unavailable", False)
    monkeypatch.setattr(neo4j_store, "_unavailable_until", 0.0)
    driver = SimpleNamespace(verify_connectivity=_fail, close=lambda: None)
    monkeypatch.setitem(sys.modules, "neo4j", SimpleNamespace(GraphDatabase=SimpleNamespace(driver=lambda *a, **kw: driver)))
    try:
        assert neo4j_store._get_driver() is None
        assert "synthetic-private-provider-payload" not in caplog.text
        assert "RuntimeError" in caplog.text
    finally:
        get_settings.cache_clear()
