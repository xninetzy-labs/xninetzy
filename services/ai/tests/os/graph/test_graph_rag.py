from __future__ import annotations

import pytest

from app.xninetzy.core.config import get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import init_db
from app.xninetzy.os.graph.graph_store import add_edge, add_node, search_nodes


@pytest.fixture
def graph_db(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    get_settings.cache_clear()
    init_db()
    run_migrations()
    yield
    get_settings.cache_clear()


def test_graph_node_edge_created():
    init_db()
    run_migrations()
    a = add_node("topic", "LangGraph")
    b = add_node("concept", "StateGraph")
    edge = add_edge(a, b, "related_to")
    assert edge > 0
    assert search_nodes("LangGraph")


def test_graph_search_multi_keyword_case_insensitive(graph_db):
    add_node("topic", "Evidence-Based Learning Techniques", "teknik belajar berbasis bukti")
    add_node("topic", "Skipped Topic", "tidak relevan")

    results = search_nodes("learning techniques")
    assert any("Learning Techniques" in row["title"] for row in results)
    assert not any("Skipped" in row["title"] for row in results)

    upper = search_nodes("EVIDENCE LEARNING")
    assert any("Learning Techniques" in row["title"] for row in upper)
