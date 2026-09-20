from __future__ import annotations

from xninetzy.context.data_analysis.dashboard.spec import (
    Aggregation,
    DashboardSpec,
    Widget,
    WidgetType,
)
from xninetzy.context.data_analysis.dashboard.providers import (
    DashboardArtifact,
    DashboardProvider,
    DashboardProviderRegistry,
    NativeEChartsProvider,
    get_default_registry,
)

__all__ = [
    "Aggregation",
    "DashboardArtifact",
    "DashboardProvider",
    "DashboardProviderRegistry",
    "DashboardSpec",
    "NativeEChartsProvider",
    "Widget",
    "WidgetType",
    "get_default_registry",
]
