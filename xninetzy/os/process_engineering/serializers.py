from __future__ import annotations

import json
from typing import Any

from xninetzy.context.process_engineering.model import (
    ProcessArtifact,
    ProcessLane,
    ProcessModel,
    ProcessNode,
)


def serialize_model(model: ProcessModel) -> dict[str, Any]:
    return {
        "id": model.id,
        "title": model.title,
        "description": model.description,
        "nodes": [
            {
                "definition": {
                    "id": node.definition.id,
                    "kind": node.definition.kind,
                    "name": node.definition.name,
                    "lane_id": node.definition.lane_id,
                    "assignee": node.definition.assignee,
                    "metadata": dict(node.definition.metadata),
                },
                "outgoing": [
                    {
                        "source_id": edge.source_id,
                        "target_id": edge.target_id,
                        "condition": edge.condition,
                        "label": edge.label,
                    }
                    for edge in node.outgoing
                ],
            }
            for node in model.nodes
        ],
        "lanes": [
            {
                "definition": {
                    "id": lane.definition.id,
                    "name": lane.definition.name,
                    "role": lane.definition.role,
                },
                "node_ids": list(lane.node_ids),
            }
            for lane in model.lanes
        ],
        "metadata": dict(model.metadata),
    }


def deserialize_model(payload: dict[str, Any]) -> ProcessModel:
    from xninetzy.context.process_engineering.model import (
        LaneDef,
        NodeDef,
        ProcessEdge,
    )

    nodes = []
    for raw in payload.get("nodes", []):
        defn = raw["definition"]
        edges = tuple(
            ProcessEdge(
                source_id=e["source_id"],
                target_id=e["target_id"],
                condition=e.get("condition"),
                label=e.get("label"),
            )
            for e in raw.get("outgoing", [])
        )
        nodes.append(
            ProcessNode(
                definition=NodeDef(
                    id=defn["id"],
                    kind=defn["kind"],
                    name=defn["name"],
                    lane_id=defn.get("lane_id"),
                    assignee=defn.get("assignee"),
                    metadata=dict(defn.get("metadata") or {}),
                ),
                outgoing=edges,
            )
        )
    lanes = []
    for raw in payload.get("lanes", []):
        defn = raw["definition"]
        lanes.append(
            ProcessLane(
                definition=LaneDef(
                    id=defn["id"],
                    name=defn["name"],
                    role=defn.get("role"),
                ),
                node_ids=tuple(raw.get("node_ids", [])),
            )
        )
    return ProcessModel(
        id=payload["id"],
        title=payload.get("title", payload["id"]),
        description=payload.get("description", ""),
        nodes=tuple(nodes),
        lanes=tuple(lanes),
        metadata=dict(payload.get("metadata") or {}),
    )


def serialize_artifact(artifact: ProcessArtifact) -> str:
    payload = {
        "artifact_id": artifact.artifact_id,
        "status": artifact.status,
        "format": artifact.format,
        "created_at": artifact.created_at,
        "updated_at": artifact.updated_at,
        "version": artifact.version,
        "model": serialize_model(artifact.model),
    }
    return json.dumps(payload, ensure_ascii=False, sort_keys=True)


def deserialize_artifact(text: str) -> ProcessArtifact:
    payload = json.loads(text)
    return ProcessArtifact(
        artifact_id=payload["artifact_id"],
        model=deserialize_model(payload["model"]),
        status=payload["status"],
        format=payload.get("format", "json"),
        created_at=payload["created_at"],
        updated_at=payload["updated_at"],
        version=int(payload.get("version", 1)),
    )


def artifact_to_row(artifact: ProcessArtifact) -> tuple[str, str, str, str, str, int]:
    return (
        artifact.artifact_id,
        artifact.status,
        artifact.format,
        serialize_artifact(artifact),
        artifact.updated_at,
        artifact.version,
    )


def artifact_from_row(row: Any) -> ProcessArtifact:
    return deserialize_artifact(row["payload_json"])