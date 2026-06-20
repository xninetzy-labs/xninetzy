from __future__ import annotations

from app.xninetzy.os.graph.graph_store import edges_for_node, search_nodes


def get_graph_context(query: str) -> str:
    nodes = search_nodes(query, limit=5)
    if not nodes:
        return "Belum ada node graph yang cocok."
    lines = [f"*Topic Map: {query}*"]
    for node in nodes:
        lines.append(f"• {node['node_type']}: {node['title']}")
        for edge in edges_for_node(node["id"])[:3]:
            lines.append(f"  - {edge['source_title']} {edge['edge_type']} {edge['target_title']}")
    return "\n".join(lines)
