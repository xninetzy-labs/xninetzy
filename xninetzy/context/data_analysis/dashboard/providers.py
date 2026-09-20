from __future__ import annotations

import hashlib
import json
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from xninetzy.context.data_analysis.dashboard.spec import DashboardSpec, Widget


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True, slots=True)
class DashboardArtifact:
    artifact_id: str
    provider_id: str
    dashboard_id: str
    format: str
    path: str
    checksum: str
    created_at: str = field(default_factory=_utcnow)
    validation_status: str = "pending"
    metadata: Mapping[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "artifact_id": self.artifact_id,
            "provider_id": self.provider_id,
            "dashboard_id": self.dashboard_id,
            "format": self.format,
            "path": self.path,
            "checksum": self.checksum,
            "created_at": self.created_at,
            "validation_status": self.validation_status,
            "metadata": dict(self.metadata),
        }


class DashboardProvider(ABC):
    provider_id: str
    supported_formats: tuple[str, ...] = ()
    supported_capabilities: tuple[str, ...] = ()

    @abstractmethod
    def render(self, spec: DashboardSpec, dataset_payload: Mapping[str, Any]) -> str:
        """Render the dashboard into a string payload (HTML / JSON / etc.)."""

    @abstractmethod
    def write(self, spec: DashboardSpec, dataset_payload: Mapping[str, Any], path: str | Path) -> DashboardArtifact:
        """Render and write to disk, returning the artifact metadata."""

    def validate(self, artifact: DashboardArtifact) -> DashboardArtifact:
        if not Path(artifact.path).exists():
            return DashboardArtifact(**{**artifact.to_dict(), "validation_status": "missing"})
        try:
            payload = Path(artifact.path).read_text(encoding="utf-8")
        except OSError:
            return DashboardArtifact(**{**artifact.to_dict(), "validation_status": "corrupt"})
        if spec_dashboard_id(artifact.path) != artifact.dashboard_id:
            return DashboardArtifact(**{**artifact.to_dict(), "validation_status": "id_mismatch"})
        if not payload.strip():
            return DashboardArtifact(**{**artifact.to_dict(), "validation_status": "empty"})
        return DashboardArtifact(**{**artifact.to_dict(), "validation_status": "valid"})


_ECHARTS_CDN = "https://cdn.jsdelivr.net/npm/echarts@5.5.0/dist/echarts.min.js"


def spec_dashboard_id(path: str | Path) -> str | None:
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    marker = 'data-dashboard-id="'
    idx = text.find(marker)
    if idx == -1:
        return None
    end = text.find('"', idx + len(marker))
    if end == -1:
        return None
    return text[idx + len(marker) : end]


def _checksum(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _widget_echarts_option(widget: Widget, dataset: Mapping[str, Any]) -> dict[str, Any]:
    dimensions = list(widget.dimensions)
    measures = list(widget.measures)
    rows = dataset.get("rows", [])
    x_key = dimensions[0] if dimensions else "x"
    y_key = measures[0] if measures else "y"
    series = [
        {
            "name": y_key,
            "type": (
                "bar"
                if widget.type.value in {"bar", "line"}
                else "pie" if widget.type.value == "pie" else "line"
            ),
            "data": [
                {"name": str(row.get(x_key)), "value": row.get(y_key)}
                for row in rows[: widget.limit]
            ],
        }
    ]
    return {
        "title": {"text": widget.title, "left": "center"},
        "tooltip": {"trigger": "axis"},
        "xAxis": (
            {"type": "category", "data": [str(r.get(x_key)) for r in rows[: widget.limit]]}
            if widget.type.value in {"bar", "line"}
            else {"type": "category"}
        ),
        "yAxis": {"type": "value"} if widget.type.value in {"bar", "line"} else {},
        "series": series,
    }


class NativeEChartsProvider(DashboardProvider):
    provider_id = "native_echarts"
    supported_formats = ("html",)
    supported_capabilities = ("dashboard_as_html", "interactive_chart", "standalone")

    def render(self, spec: DashboardSpec, dataset_payload: Mapping[str, Any]) -> str:
        blocks: list[str] = []
        dataset_id_attr = f' data-dataset-id="{spec.dataset_id}"'
        dashboard_attr = f' data-dashboard-id="{spec.dashboard_id}"'
        for idx, widget in enumerate(sorted(spec.widgets, key=lambda w: w.position)):
            option = _widget_echarts_option(widget, dataset_payload)
            chart_id = f"chart-{idx}-{widget.widget_id}"
            blocks.append(
                f'<section class="xninetzy-widget" data-widget-id="{widget.widget_id}">'
                f'<h3>{widget.title}</h3>'
                f'<div id="{chart_id}" class="xninetzy-chart" '
                f'data-widget-type="{widget.type.value}"'
                f' data-aggregation="{widget.aggregation.value}"'
                f' data-dimensions="{",".join(widget.dimensions)}"'
                f' data-measures="{",".join(widget.measures)}"'
                f'></div>'
                f'<script type="application/json" class="xninetzy-option" '
                f'data-target="{chart_id}">{json.dumps(option, ensure_ascii=False)}</script>'
                f'</section>'
            )
        body = "\n".join(blocks) if blocks else '<p class="xninetzy-empty">no widgets</p>'
        html = (
            f'<!doctype html>\n'
            f'<html lang="en">\n<head>\n'
            f'<meta charset="utf-8" />\n'
            f'<title>{spec.title}</title>\n'
            f'<meta name="description" content="{spec.description}" />\n'
            f'<meta name="generator" content="xninetzy-native-echarts" />\n'
            f'<meta name="theme-color" content="#020008" />\n'
            f'</head>\n<body{dashboard_attr}{dataset_id_attr}>\n'
            f'<header><h1>{spec.title}</h1>'
            f'<p>{spec.description}</p></header>\n'
            f'<main>{body}</main>\n'
            f'<script src="{_ECHARTS_CDN}" integrity="" crossorigin="anonymous"></script>\n'
            f'<script>(function(){{\n'
            f'  var charts = document.querySelectorAll(".xninetzy-chart");\n'
            f'  var opts = document.querySelectorAll(".xninetzy-option");\n'
            f'  for (var i = 0; i < charts.length; i++) {{\n'
            f'    var chart = echarts.init(charts[i]);\n'
            f'    var opt = opts[i];\n'
            f'    if (opt) {{ chart.setOption(JSON.parse(opt.textContent)); }}\n'
            f'  }}\n'
            f'}})();</script>\n'
            f'</body>\n</html>\n'
        )
        return html

    def write(
        self,
        spec: DashboardSpec,
        dataset_payload: Mapping[str, Any],
        path: str | Path,
    ) -> DashboardArtifact:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        rendered = self.render(spec, dataset_payload)
        p.write_text(rendered, encoding="utf-8")
        return DashboardArtifact(
            artifact_id=f"art-{uuid.uuid4().hex[:12]}",
            provider_id=self.provider_id,
            dashboard_id=spec.dashboard_id,
            format="html",
            path=str(p),
            checksum=_checksum(rendered),
            metadata={"widget_count": spec.widget_count},
        )


class DashboardProviderRegistry:
    def __init__(self) -> None:
        self._providers: dict[str, DashboardProvider] = {}

    def register(self, provider: DashboardProvider) -> None:
        self._providers[provider.provider_id] = provider

    def get(self, provider_id: str) -> DashboardProvider | None:
        return self._providers.get(provider_id)

    def list(self) -> tuple[str, ...]:
        return tuple(sorted(self._providers.keys()))

    def all(self) -> tuple[DashboardProvider, ...]:
        return tuple(self._providers[pid] for pid in sorted(self._providers))


_DEFAULT_REGISTRY = DashboardProviderRegistry()
_DEFAULT_REGISTRY.register(NativeEChartsProvider())


def get_default_registry() -> DashboardProviderRegistry:
    return _DEFAULT_REGISTRY
