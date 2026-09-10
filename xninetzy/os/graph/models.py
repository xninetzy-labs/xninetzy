from __future__ import annotations

from pydantic import BaseModel


class GraphNode(BaseModel):
    id: int | None = None
    node_type: str
    title: str
    content: str | None = None
    metadata: dict = {}


class GraphEdge(BaseModel):
    id: int | None = None
    source_node_id: int
    target_node_id: int
    edge_type: str
    metadata: dict = {}
