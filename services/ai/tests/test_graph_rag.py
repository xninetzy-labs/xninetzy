from app.db.migrations import run_migrations
from app.db.sqlite import init_db
from app.graph_rag.graph_store import add_edge, add_node, search_nodes


def test_graph_node_edge_created():
    init_db()
    run_migrations()
    a = add_node("topic", "LangGraph")
    b = add_node("concept", "StateGraph")
    edge = add_edge(a, b, "related_to")
    assert edge > 0
    assert search_nodes("LangGraph")
