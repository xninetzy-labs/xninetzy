from __future__ import annotations

from langchain_core.tools import tool

from xninetzy.context.data_analysis import (
    audit_quality,
    generate_xlsx_artifact,
    profile_dataset,
    validate_xlsx_artifact,
)


@tool
def data_profile(file_path: str, sheet_name: str | None = None) -> dict:
    """Profile a CSV or XLSX file. Returns row count, column count, per-column
    physical/semantic type, null counts, unique counts, and a SHA-256 checksum.

    Supported formats today: CSV, XLSX. Other formats return an error.
    """
    summary = profile_dataset(file_path, sheet_name=sheet_name)
    return summary.to_dict()


@tool
def data_quality_audit(file_path: str, sheet_name: str | None = None) -> dict:
    """Run a deterministic quality audit on a CSV or XLSX file. Reports
    completeness / validity / uniqueness / consistency scores plus any issues
    with severity and affected-row counts."""
    summary = profile_dataset(file_path, sheet_name=sheet_name)
    report = audit_quality(summary)
    return report.to_dict()


@tool
def data_generate_xlsx(
    output_path: str,
    name: str,
    rows: list[dict],
    source: str = "",
    transformation: str = "",
) -> dict:
    """Generate an XLSX artifact from a list of row dicts. Returns artifact
    metadata including path, checksum, schema, and row count. The file is
    written to ``output_path`` before this function returns."""
    artifact = generate_xlsx_artifact(
        path=output_path,
        name=name,
        rows=rows,
        source=source,
        transformation=transformation,
    )
    return artifact.to_dict()


@tool
def data_validate_xlsx(artifact: dict) -> dict:
    """Reopen an XLSX artifact on disk and verify its schema, row count, and
    readability. The artifact dict must include ``path``, ``schema``, and
    ``row_count``. Returns the artifact with updated ``validation_status``."""
    from xninetzy.context.data_analysis import TableArtifact

    art = TableArtifact(
        artifact_id=artifact["artifact_id"],
        name=artifact["name"],
        format=artifact["format"],
        schema=tuple(artifact["schema"]),
        row_count=artifact["row_count"],
        source=artifact.get("source", ""),
        transformation=artifact.get("transformation", ""),
        path=artifact["path"],
        checksum=artifact["checksum"],
    )
    validated = validate_xlsx_artifact(art)
    return validated.to_dict()


@tool
def dashboard_generate(
    output_path: str,
    title: str,
    description: str,
    dataset_id: str,
    widgets: list[dict],
    rows: list[dict] | None = None,
    provider_id: str = "native_echarts",
) -> dict:
    """Generate a dashboard from a DashboardSpec-like dict. ``widgets`` is a
    list of dicts with keys: ``widget_id``, ``type``, ``title``,
    ``dimensions`` (list), ``measures`` (list), ``aggregation``,
    ``position`` (int). Returns the DashboardArtifact metadata. The HTML
    file is written before this function returns."""
    from xninetzy.context.data_analysis.dashboard import (
        Aggregation,
        DashboardSpec,
        Widget,
        WidgetType,
        get_default_registry,
        new_dashboard_id,
        new_widget_id,
    )

    registry = get_default_registry()
    provider = registry.get(provider_id)
    if provider is None:
        return {"error": f"unknown provider: {provider_id}",
                "available": registry.list()}
    built_widgets = []
    for idx, raw in enumerate(widgets):
        wid = str(raw.get("widget_id") or new_widget_id())
        wtype = WidgetType(str(raw.get("type") or "bar"))
        agg = Aggregation(str(raw.get("aggregation") or "sum"))
        built_widgets.append(
            Widget(
                widget_id=wid,
                type=wtype,
                title=str(raw.get("title") or wid),
                dataset_id=dataset_id,
                dimensions=tuple(raw.get("dimensions") or ()),
                measures=tuple(raw.get("measures") or ()),
                aggregation=agg,
                position=int(raw.get("position", idx)),
            )
        )
    spec = DashboardSpec(
        dashboard_id=new_dashboard_id(),
        title=title,
        description=description,
        dataset_id=dataset_id,
        widgets=tuple(built_widgets),
    )
    art = provider.write(spec, {"rows": rows or []}, output_path)
    return art.to_dict()


@tool
def dashboard_validate(artifact: dict) -> dict:
    """Reopen a dashboard HTML artifact and verify its structure."""
    from xninetzy.context.data_analysis.dashboard import (
        DashboardArtifact,
        get_default_registry,
    )

    registry = get_default_registry()
    provider = registry.get(artifact.get("provider_id", ""))
    if provider is None:
        return {"error": "unknown provider"}
    art = DashboardArtifact(
        artifact_id=artifact["artifact_id"],
        provider_id=artifact["provider_id"],
        dashboard_id=artifact["dashboard_id"],
        format=artifact["format"],
        path=artifact["path"],
        checksum=artifact["checksum"],
    )
    validated = provider.validate(art)
    return validated.to_dict()


@tool
def dashboard_list_providers() -> dict:
    """List registered dashboard providers and their capabilities."""
    from xninetzy.context.data_analysis.dashboard import get_default_registry

    registry = get_default_registry()
    return {
        "providers": [
            {
                "provider_id": p.provider_id,
                "formats": list(p.supported_formats),
                "capabilities": list(p.supported_capabilities),
            }
            for p in registry.all()
        ]
    }
