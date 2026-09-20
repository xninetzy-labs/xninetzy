from __future__ import annotations

from pathlib import Path

from xninetzy.context.data_analysis.dashboard import (
    Aggregation,
    DashboardArtifact,
    DashboardSpec,
    NativeEChartsProvider,
    Widget,
    WidgetType,
    get_default_registry,
)


def _spec() -> DashboardSpec:
    return DashboardSpec(
        dashboard_id="dash-test",
        title="Sales",
        description="Q1 revenue",
        dataset_id="ds-orders",
        widgets=(
            Widget(
                widget_id="w1",
                type=WidgetType.BAR,
                title="Revenue by region",
                dataset_id="ds-orders",
                dimensions=("region",),
                measures=("revenue",),
                aggregation=Aggregation.SUM,
                position=0,
            ),
        ),
    )


def test_default_registry_has_native_echarts() -> None:
    reg = get_default_registry()
    assert "native_echarts" in reg.list()
    assert reg.get("native_echarts") is not None


def test_render_contains_echarts_and_dataset_marker() -> None:
    provider = NativeEChartsProvider()
    html = provider.render(_spec(), {"rows": [{"region": "East", "revenue": 100}]})
    assert "echarts.min.js" in html
    assert 'data-dashboard-id="dash-test"' in html
    assert 'data-dataset-id="ds-orders"' in html
    assert "Revenue by region" in html


def test_write_then_validate_round_trip(tmp_path: Path) -> None:
    provider = NativeEChartsProvider()
    art = provider.write(_spec(), {"rows": []}, tmp_path / "dash.html")
    assert art.validation_status == "pending"
    validated = provider.validate(art)
    assert validated.validation_status == "valid"


def test_validate_missing(tmp_path: Path) -> None:
    provider = NativeEChartsProvider()
    art = DashboardArtifact(
        artifact_id="art-x",
        provider_id="native_echarts",
        dashboard_id="dash-x",
        format="html",
        path=str(tmp_path / "missing.html"),
        checksum="",
    )
    assert provider.validate(art).validation_status == "missing"


def test_render_empty_widgets() -> None:
    spec = DashboardSpec(
        dashboard_id="d-empty",
        title="empty",
        description="",
        dataset_id="ds-x",
        widgets=(),
    )
    html = NativeEChartsProvider().render(spec, {})
    assert "no widgets" in html
