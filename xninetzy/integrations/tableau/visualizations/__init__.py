from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import VisualizationSpec


SUPPORTED_VISUALIZATIONS = frozenset(
    {
        "bar",
        "line",
        "area",
        "circle",
        "square",
        "map",
        "kpi",
        "pie",
        "scatter",
        "heatmap",
        "table",
    }
)


def parse_visualization(spec: dict[str, Any]) -> VisualizationSpec:
    if not isinstance(spec, dict):
        raise TableauIntegrationError(
            f"VIZ_TYPE_ERROR: spec must be dict, got {type(spec).__name__}"
        )
    viz_type = str(spec.get("type", "")).lower().strip()
    if not viz_type:
        raise TableauIntegrationError("VIZ_TYPE_ERROR: visualization 'type' is required")
    if viz_type not in SUPPORTED_VISUALIZATIONS:
        raise TableauIntegrationError(
            f"VIZ_TYPE_ERROR: unsupported visualization type '{viz_type}'. "
            f"Supported: {sorted(SUPPORTED_VISUALIZATIONS)}"
        )
    return VisualizationSpec(
        type=viz_type,
        rows=list(spec.get("rows") or []),
        cols=list(spec.get("cols") or spec.get("columns") or []),
        measure=spec.get("measure"),
        measure_aggregation=str(spec.get("measure_aggregation") or "SUM").upper(),
        color=spec.get("color"),
        size=spec.get("size"),
        label=spec.get("label"),
        top_n=int(spec["top_n"]) if spec.get("top_n") is not None else None,
        trend_line=bool(spec.get("trend_line", False)),
    )


def compile_visualization(spec: VisualizationSpec) -> VisualizationSpec:
    if spec.type not in SUPPORTED_VISUALIZATIONS:
        raise TableauIntegrationError(
            f"VIZ_TYPE_ERROR: unsupported visualization type '{spec.type}'"
        )
    return spec


__all__ = [
    "parse_visualization",
    "compile_visualization",
    "SUPPORTED_VISUALIZATIONS",
]
