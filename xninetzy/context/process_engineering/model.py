from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


NODE_KIND_TASK: str = "task"
NODE_KIND_START: str = "start"
NODE_KIND_END: str = "end"
NODE_KIND_GATEWAY: str = "gateway"
NODE_KIND_SUBPROCESS: str = "subprocess"

VALID_NODE_KINDS: frozenset[str] = frozenset(
    {
        NODE_KIND_TASK,
        NODE_KIND_START,
        NODE_KIND_END,
        NODE_KIND_GATEWAY,
        NODE_KIND_SUBPROCESS,
    }
)

NodeKind: str = str

ARTIFACT_STATUS_DRAFT: str = "draft"
ARTIFACT_STATUS_REVIEW: str = "review"
ARTIFACT_STATUS_APPROVED: str = "approved"
ARTIFACT_STATUS_RETIRED: str = "retired"

VALID_ARTIFACT_STATUSES: frozenset[str] = frozenset(
    {
        ARTIFACT_STATUS_DRAFT,
        ARTIFACT_STATUS_REVIEW,
        ARTIFACT_STATUS_APPROVED,
        ARTIFACT_STATUS_RETIRED,
    }
)

ArtifactStatus: str = str


@dataclass(frozen=True, slots=True)
class NodeDef:
    id: str
    kind: NodeKind
    name: str
    lane_id: str | None = None
    assignee: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class LaneDef:
    id: str
    name: str
    role: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessEdge:
    source_id: str
    target_id: str
    condition: str | None = None
    label: str | None = None


@dataclass(frozen=True, slots=True)
class ProcessNode:
    definition: NodeDef
    outgoing: tuple[ProcessEdge, ...] = ()


@dataclass(frozen=True, slots=True)
class ProcessLane:
    definition: LaneDef
    node_ids: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ProcessModel:
    id: str
    title: str
    description: str
    nodes: tuple[ProcessNode, ...]
    lanes: tuple[ProcessLane, ...]
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class ProcessArtifact:
    artifact_id: str
    model: ProcessModel
    status: ArtifactStatus
    format: str
    created_at: str
    updated_at: str
    version: int = 1


def node_kinds() -> tuple[str, ...]:
    return tuple(sorted(VALID_NODE_KINDS))


def artifact_statuses() -> tuple[str, ...]:
    return tuple(sorted(VALID_ARTIFACT_STATUSES))


def validate_process_model(model: ProcessModel) -> list[str]:
    issues: list[str] = []
    seen_node_ids: set[str] = set()
    for node in model.nodes:
        if node.definition.id in seen_node_ids:
            issues.append(f"duplicate node id: {node.definition.id}")
        seen_node_ids.add(node.definition.id)
        if node.definition.kind not in VALID_NODE_KINDS:
            issues.append(
                f"node {node.definition.id} has invalid kind {node.definition.kind!r}"
            )
        if not node.definition.name.strip():
            issues.append(f"node {node.definition.id} has empty name")
    for lane in model.lanes:
        for node_id in lane.node_ids:
            if node_id not in seen_node_ids:
                issues.append(f"lane {lane.definition.id} references missing node {node_id}")
    node_index = {n.definition.id: n for n in model.nodes}
    for node in model.nodes:
        for edge in node.outgoing:
            if edge.source_id != node.definition.id:
                issues.append(
                    f"edge source mismatch on node {node.definition.id}: {edge.source_id}"
                )
            if edge.target_id not in node_index:
                issues.append(
                    f"edge {edge.source_id}->{edge.target_id} targets missing node"
                )
    start_count = sum(
        1 for n in model.nodes if n.definition.kind == NODE_KIND_START
    )
    end_count = sum(1 for n in model.nodes if n.definition.kind == NODE_KIND_END
    )
    if start_count == 0:
        issues.append("process has no start node")
    if end_count == 0:
        issues.append("process has no end node")
    return issues