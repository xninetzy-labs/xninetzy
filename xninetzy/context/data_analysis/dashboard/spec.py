from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Mapping


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class WidgetType(str, Enum):
    KPI = "kpi"
    BAR = "bar"
    LINE = "line"
    TABLE = "table"
    PIE = "pie"
    SCATTER = "scatter"
    HEATMAP = "heatmap"


class Aggregation(str, Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    COUNT_DISTINCT = "count_distinct"
    MIN = "min"
    MAX = "max"
    MEDIAN = "median"


@dataclass(frozen=True, slots=True)
class Widget:
    widget_id: str
    type: WidgetType
    title: str
    dataset_id: str
    dimensions: tuple[str, ...] = ()
    measures: tuple[str, ...] = ()
    aggregation: Aggregation = Aggregation.SUM
    filters: tuple[Mapping[str, Any], ...] = ()
    limit: int = 100
    position: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "widget_id": self.widget_id,
            "type": self.type.value,
            "title": self.title,
            "dataset_id": self.dataset_id,
            "dimensions": list(self.dimensions),
            "measures": list(self.measures),
            "aggregation": self.aggregation.value,
            "filters": [dict(f) for f in self.filters],
            "limit": self.limit,
            "position": self.position,
        }


@dataclass(frozen=True, slots=True)
class DashboardSpec:
    dashboard_id: str
    title: str
    description: str
    dataset_id: str
    widgets: tuple[Widget, ...] = ()
    theme: str = "light"
    refresh_policy: str = "manual"
    created_at: str = field(default_factory=_utcnow)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dashboard_id": self.dashboard_id,
            "title": self.title,
            "description": self.description,
            "dataset_id": self.dataset_id,
            "widgets": [w.to_dict() for w in self.widgets],
            "theme": self.theme,
            "refresh_policy": self.refresh_policy,
            "created_at": self.created_at,
            "provenance": dict(self.provenance),
        }

    @property
    def widget_count(self) -> int:
        return len(self.widgets)


def new_dashboard_id() -> str:
    return f"dash-{uuid.uuid4().hex[:12]}"


def new_widget_id() -> str:
    return f"w-{uuid.uuid4().hex[:8]}"
