from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class LineageEdge:
    parent_id: str
    child_id: str
    operation: str
    parameters: dict[str, Any] = field(default_factory=dict)
    recorded_at: str = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "parent_id": self.parent_id,
            "child_id": self.child_id,
            "operation": self.operation,
            "parameters": dict(self.parameters),
            "recorded_at": self.recorded_at,
        }


@dataclass
class LineageRecord:
    dataset_id: str
    source_uri: str
    operations: list[LineageEdge] = field(default_factory=list)

    def add(
        self,
        *,
        parent_id: str,
        child_id: str,
        operation: str,
        parameters: dict[str, Any] | None = None,
    ) -> LineageEdge:
        edge = LineageEdge(
            parent_id=parent_id,
            child_id=child_id,
            operation=operation,
            parameters=parameters or {},
        )
        self.operations.append(edge)
        return edge

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_uri": self.source_uri,
            "operations": [op.to_dict() for op in self.operations],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)
