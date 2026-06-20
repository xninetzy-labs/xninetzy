from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.graph.graph_context import get_graph_context
from app.xninetzy.os.graph.graph_store import add_edge, add_node, search_nodes


@tool
def graph_add_node(node_type: str, title: str, content: str = "", metadata: dict | None = None) -> str:
    """Tambah node Graph RAG SQLite."""
    node_id = add_node(node_type, title, content, metadata)
    return f"✅ Graph node #{node_id} dibuat: {node_type} - {title}"


@tool
def graph_add_edge(source_node_id: int, target_node_id: int, edge_type: str, metadata: dict | None = None) -> str:
    """Tambah edge Graph RAG SQLite."""
    edge_id = add_edge(source_node_id, target_node_id, edge_type, metadata)
    return f"✅ Graph edge #{edge_id} dibuat: {source_node_id} {edge_type} {target_node_id}"


@tool
def graph_search(query: str, limit: int = 10) -> str:
    """Search node Graph RAG."""
    nodes = search_nodes(query, limit)
    if not nodes:
        return "Tidak ada node graph yang cocok."
    lines = [f"*Graph Search: {query}*"]
    for node in nodes:
        lines.append(f"#{node['id']} {node['node_type']} - {node['title']}")
    return "\n".join(lines)


@tool
def graph_get_context(query: str) -> str:
    """Ambil konteks graph terkait query."""
    return get_graph_context(query)


@tool
def graph_explain_topic_map(query: str) -> str:
    """Jelaskan topic map dari graph."""
    return get_graph_context(query)


@tool
def graph_link_research_to_roadmap(research_node_id: int, roadmap_node_id: int) -> str:
    """Link research brief ke roadmap."""
    edge_id = add_edge(roadmap_node_id, research_node_id, "created_from", {})
    return f"✅ Research dihubungkan ke roadmap via edge #{edge_id}."


@tool
def graph_link_note_to_topic(note_node_id: int, topic_node_id: int) -> str:
    """Link Obsidian note ke topic."""
    edge_id = add_edge(note_node_id, topic_node_id, "stored_in", {})
    return f"✅ Note dihubungkan ke topic via edge #{edge_id}."
