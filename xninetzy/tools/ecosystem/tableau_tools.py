from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.integrations.tableau.compiler import (
    compile_datasource_from_csv,
    compile_workbook,
    safe_field_token,
)
from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.hyper import (
    extract_csv_to_hyper,
    hyper_available,
    validate_hyper,
)
from xninetzy.integrations.tableau.ir import (
    Dashboard,
    PublishTarget,
    Workbook,
    WorkbookMetadata,
    Worksheet,
)
from xninetzy.integrations.tableau.packager import package_twbx
from xninetzy.integrations.tableau.parser import parse_workbook
from xninetzy.integrations.tableau.profiling import profile_csv, profile_schema_hash
from xninetzy.integrations.tableau.server import (
    list_workbooks as _list_workbooks_server,
    publish_workbook as _publish_workbook_server,
    refresh_workbook as _refresh_workbook_server,
)
from xninetzy.integrations.tableau.validator import validate_workbook
from xninetzy.integrations.tableau.visualizations import (
    SUPPORTED_VISUALIZATIONS,
    parse_visualization,
)
from xninetzy.integrations.tableau.workspace import (
    resolve_template_path,
    safe_workspace_subdir,
    templates_root,
    workspace_root,
)


SUPPORTED_VISUALIZATIONS_LIST = sorted(SUPPORTED_VISUALIZATIONS)


def _load_workbook(path: Path) -> Workbook:
    return parse_workbook(path)


def _persist_workbook(workbook: Workbook, target: Path) -> dict[str, Any]:
    target.parent.mkdir(parents=True, exist_ok=True)
    body = compile_workbook(workbook)
    target.write_bytes(body)
    return {
        "path": str(target),
        "bytes": len(body),
        "datasources": workbook.datasource_names(),
        "worksheets": workbook.worksheet_names(),
        "dashboards": workbook.dashboard_names(),
    }


def _render_datasource_xml(ds, csv_path: str) -> str:
    cols = "\n".join(
        f'      <column name="{f.name}" caption="{f.caption}" '
        f'datatype="{f.datatype}" role="{f.role}"/>'
        for f in ds.fields
    )
    return (
        f'    <datasource name="{ds.name}" caption="{ds.caption}" version="18.1">\n'
        f'      <connection class="textscan" filename="{csv_path}"/>\n'
        f"{cols}\n"
        f"    </datasource>"
    )


@tool(description="List Tableau integration capabilities and supported visualization types.")
def tableau_capabilities() -> dict[str, Any]:
    return {
        "supported_visualizations": SUPPORTED_VISUALIZATIONS_LIST,
        "operations": [
            "parse_workbook",
            "compile_workbook",
            "validate_workbook",
            "package_twbx",
            "compile_datasource_from_csv",
        ],
        "tier_2_3_tools": [
            "tableau_workbook_generate",
            "tableau_twb_export",
            "tableau_twbx_package",
        ],
    }


@tool(description="List available Tableau .twb templates in the templates directory.")
def tableau_template_list() -> dict[str, Any]:
    root = templates_root()
    files = sorted(p.name for p in root.glob("*.twb"))
    return {"templates": files, "root": str(root), "count": len(files)}


@tool(description="Inspect a Tableau template (.twb) without producing side effects.")
def tableau_template_inspect(template_name: str) -> dict[str, Any]:
    path = resolve_template_path(template_name)
    workbook = _load_workbook(path)
    return {
        "path": str(path),
        "metadata": workbook.metadata.__dict__,
        "datasources": workbook.datasource_names(),
        "worksheets": workbook.worksheet_names(),
        "dashboards": workbook.dashboard_names(),
        "story_points": [c for c, _ in workbook.story_points],
    }


@tool(description="Inspect a generated workbook from disk and summarize its structure.")
def tableau_workbook_inspect(workbook_path: str) -> dict[str, Any]:
    path = Path(workbook_path)
    if not path.is_file():
        return {"error": "not_found", "path": str(path)}
    workbook = _load_workbook(path)
    return {
        "path": str(path),
        "datasources": workbook.datasource_names(),
        "worksheets": workbook.worksheet_names(),
        "dashboards": workbook.dashboard_names(),
    }


@tool(description="Validate a workbook file and return a structured report.")
def tableau_workbook_validate(workbook_path: str) -> dict[str, Any]:
    path = Path(workbook_path)
    report = validate_workbook(path)
    return report.to_dict()


def _render_worksheet_xml(name: str, spec, ds_name: str) -> str:
    rows_field = (
        f'      <rows>[{safe_field_token(spec.rows[0])}]</rows>\n' if spec.rows else "  <rows/>\n"
    )
    cols_field = (
        f'      <cols>[{safe_field_token(spec.cols[0])}]</cols>\n' if spec.cols else "  <cols/>\n"
    )
    return (
        f'    <worksheet name="{name}"><title>{name}</title>'
        f"<table><view>"
        f'<datasources><datasource name="{ds_name}"/></datasources>'
        f"{rows_field}{cols_field}"
        f"</view>"
        f'<panes><pane><mark class="{spec.mark_class()}"/></pane></panes>'
        f"</table></worksheet>"
    )


@tool(description=(
    "Generate a fresh Tableau workbook (.twb) from CSVs and visualization specs. "
    "Idempotent when given the same name and content."
))
def tableau_workbook_generate(
    csv_paths: list[str],
    name: str,
    visualizations: list[dict[str, Any]],
    dashboard_title: str = "Auto Dashboard",
    output_subdir: str | None = None,
    story_points: list[str] | None = None,
    template_name: str | None = None,
) -> dict[str, Any]:
    workspace = workspace_root()
    sub = safe_workspace_subdir(output_subdir or name)
    target_dir = workspace / "workbooks" / sub
    target_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook(metadata=WorkbookMetadata(source_platform="linux"))
    ds_specs: list[tuple[str, Path]] = []
    for csv_path in csv_paths:
        cp = Path(csv_path)
        if not cp.is_file():
            return {"error": "missing_csv", "csv_path": str(cp)}
        ds_name = f"federated.{safe_field_token(cp.stem)}"
        if len(csv_paths) == 1:
            ds_name = name or ds_name
        ds = compile_datasource_from_csv(cp, name=ds_name)
        workbook.datasources.append(ds)
        workbook.datasource_xml[ds.name] = _render_datasource_xml(ds, str(cp))
        ds_specs.append((ds_name, cp))

    if template_name:
        try:
            tmpl = resolve_template_path(template_name)
            template_wb = _load_workbook(tmpl)
            for ds in template_wb.datasources[1:]:
                workbook.datasources.append(ds)
                workbook.datasource_xml[ds.name] = template_wb.datasource_xml.get(ds.name, "")
        except FileNotFoundError:
            pass

    for idx, viz_dict in enumerate(visualizations or []):
        spec = parse_visualization(viz_dict)
        ws_name = safe_field_token(viz_dict.get("name") or f"ws_{idx + 1}")
        if any(w.name == ws_name for w in workbook.worksheets):
            ws_name = f"{ws_name}_{idx + 1}"
        ds_name = (
            ds_specs[0][0]
            if ds_specs
            else (workbook.datasources[0].name if workbook.datasources else "federated.primary")
        )
        workbook.worksheets.append(
            Worksheet(name=ws_name, title=ws_name, mark_class=spec.mark_class())
        )
        workbook.worksheets_xml[ws_name] = _render_worksheet_xml(ws_name, spec, ds_name)

    db_name = safe_field_token(dashboard_title) or "Dashboard"
    workbook.dashboards.append(Dashboard(name=db_name))
    workbook.dashboards_xml[db_name] = (
        f'    <dashboard name="{db_name}"><zones>'
        + "".join(
            f'<zone name="{ws.name}" x="0" y="{i * 100}" w="200" h="100"/>'
            for i, ws in enumerate(workbook.worksheets)
        )
        + "</zones></dashboard>"
    )
    workbook.story_points = [(caption, f"sp{i + 1}") for i, caption in enumerate(story_points or [])]

    target = target_dir / f"{safe_field_token(name) or 'workbook'}.twb"
    info = _persist_workbook(workbook, target)
    info["idempotency_key"] = f"{name}:{','.join(str(p) for p in csv_paths)}"
    return info


@tool(description="Replace a workbook's primary datasource with a new CSV, mapping fields.")
def tableau_datasource_replace(
    workbook_path: str, csv_path: str, field_map: dict[str, str] | None = None
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    new_ds = compile_datasource_from_csv(csv_path, name=workbook.datasources[0].name)
    workbook.datasources[0] = new_ds
    workbook.datasource_xml[new_ds.name] = _render_datasource_xml(new_ds, csv_path)
    return _persist_workbook(workbook, path)


@tool(description="Append a new worksheet to an existing workbook based on a visualization spec.")
def tableau_worksheet_create(
    workbook_path: str, worksheet_name: str, visualization: dict[str, Any]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    spec = parse_visualization(visualization)
    if any(w.name == worksheet_name for w in workbook.worksheets):
        return {"error": "duplicate_worksheet", "name": worksheet_name}
    ds_name = workbook.datasources[0].name
    workbook.worksheets.append(
        Worksheet(name=worksheet_name, title=worksheet_name, mark_class=spec.mark_class())
    )
    workbook.worksheets_xml[worksheet_name] = _render_worksheet_xml(worksheet_name, spec, ds_name)
    return _persist_workbook(workbook, path)


@tool(description="Modify an existing worksheet in a workbook.")
def tableau_worksheet_modify(
    workbook_path: str, worksheet_name: str, visualization: dict[str, Any]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if not any(w.name == worksheet_name for w in workbook.worksheets):
        return {"error": "not_found", "worksheet": worksheet_name}
    spec = parse_visualization(visualization)
    ds_name = workbook.datasources[0].name
    workbook.worksheets_xml[worksheet_name] = _render_worksheet_xml(
        worksheet_name, spec, ds_name
    )
    for ws in workbook.worksheets:
        if ws.name == worksheet_name:
            ws.mark_class = spec.mark_class()
            break
    return _persist_workbook(workbook, path)


@tool(description="Create a new dashboard referencing existing worksheets.")
def tableau_dashboard_create(
    workbook_path: str, dashboard_name: str, worksheets: list[str]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if any(d.name == dashboard_name for d in workbook.dashboards):
        return {"error": "duplicate_dashboard", "name": dashboard_name}
    if any(ws not in workbook.worksheet_names() for ws in worksheets):
        return {"error": "unknown_worksheet", "requested": worksheets}
    workbook.dashboards.append(Dashboard(name=dashboard_name))
    workbook.dashboards_xml[dashboard_name] = (
        f'    <dashboard name="{dashboard_name}"><zones>'
        + "".join(
            f'<zone name="{ws}" x="0" y="{i * 100}" w="200" h="100"/>'
            for i, ws in enumerate(worksheets)
        )
        + "</zones></dashboard>"
    )
    return _persist_workbook(workbook, path)


@tool(description="Update the zone layout for an existing dashboard.")
def tableau_dashboard_layout(
    workbook_path: str, dashboard_name: str, layout: list[dict[str, Any]]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if dashboard_name not in workbook.dashboard_names():
        return {"error": "not_found", "dashboard": dashboard_name}
    zones = "".join(
        f'<zone name="{entry["worksheet"]}" x="{entry.get("x", 0)}" '
        f'y="{entry.get("y", 0)}" w="{entry.get("w", 200)}" h="{entry.get("h", 100)}"/>'
        for entry in layout
    )
    workbook.dashboards_xml[dashboard_name] = (
        f'    <dashboard name="{dashboard_name}"><zones>{zones}</zones></dashboard>'
    )
    return _persist_workbook(workbook, path)


@tool(description="Attach story points (caption list) to a workbook.")
def tableau_story_create(
    workbook_path: str, story_name: str, points: list[str]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    workbook.story_points = [(caption, f"sp{i + 1}") for i, caption in enumerate(points)]
    body = compile_workbook(workbook)
    path.write_bytes(body)
    return {"path": str(path), "story_points": points, "name": story_name}


@tool(description="Re-serialize a workbook to a clean .twb file.")
def tableau_twb_export(workbook_path: str, target_path: str | None = None) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    target = Path(target_path) if target_path else path
    body = compile_workbook(workbook)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(body)
    return {"path": str(target), "bytes": len(body)}


@tool(description="Package the workbook and any extra resources into a .twbx archive.")
def tableau_twbx_package(
    workbook_path: str,
    resources: list[str] | None = None,
    output_path: str | None = None,
) -> dict[str, Any]:
    workspace = workspace_root()
    path = Path(workbook_path)
    res_paths = [Path(r) for r in (resources or [])]
    if output_path is None:
        out = workspace / "twbx" / f"{safe_field_token(path.stem)}.twbx"
    else:
        out = Path(output_path)
    result = package_twbx(twb_path=path, resources=res_paths, output_path=out)
    return {
        "package_path": str(result.package_path),
        "workbook_present": result.workbook_present,
        "entries": result.entries,
        "extras_included": result.extras_included,
    }


@tool(description=(
    "CSV → Hyper extract with profiling + typed schema. "
    "Writes a real .hyper file when tableauhyperapi is installed; "
    "otherwise returns a typed manifest alongside a clean error so the agent "
    "can fall back. Tier 1 (write, idempotent)."
))
def tableau_hyper_create(
    csv_path: str, name: str, output_path: str | None = None
) -> dict[str, Any]:
    p = Path(csv_path)
    workspace = workspace_root()
    out = Path(output_path) if output_path else (
        workspace / "hyper" / f"{safe_field_token(name)}.hyper"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        record = extract_csv_to_hyper(p, out)
    except TableauIntegrationError as exc:
        return {
            "error": exc.code,
            "message": str(exc),
            "path": str(out),
            "manifest_path": str(out.with_suffix(out.suffix + ".txt")),
            "hyper_available": hyper_available(),
        }
    return {
        "path": str(record.extract_path),
        "rows": record.row_count,
        "schema_hash": record.schema_hash,
        "columns": [c.name for c in record.columns],
        "size_bytes": record.size_bytes,
    }


@tool(description="Profile a CSV dataset and return typed schema with semantic roles.")
def tableau_profile_dataset(csv_path: str) -> dict[str, Any]:
    profile = profile_csv(csv_path)
    out = profile.to_dict()
    out["schema_hash"] = profile_schema_hash(profile)
    return out


@tool(description="Validate a Hyper extract: open .hyper, list tables, size + schema_hash.")
def tableau_validate_hyper(extract_path: str) -> dict[str, Any]:
    try:
        info = validate_hyper(extract_path)
    except TableauIntegrationError as exc:
        return {"error": exc.code, "message": str(exc), "path": str(extract_path)}
    info["path"] = info.pop("extract_path")
    return info


@tool(description="Infer Tableau datasource schema from a CSV without persisting it. Tier 0.")
def tableau_infer_schema(csv_path: str) -> dict[str, Any]:
    profile = profile_csv(csv_path)
    fields = [
        {
            "name": c.name,
            "caption": c.caption,
            "datatype": c.datatype,
            "role": c.role,
            "semantic_role": c.semantic_role,
        }
        for c in profile.columns
    ]
    return {
        "source_path": profile.source_path,
        "row_count": profile.row_count,
        "column_count": profile.column_count,
        "duplicate_columns": list(profile.duplicate_columns),
        "fields": fields,
        "measures": [c.name for c in profile.measure_columns()],
        "dimensions": [c.name for c in profile.dimension_columns()],
        "temporal": [c.name for c in profile.temporal_columns()],
    }


def _target_from_dict(target: dict[str, Any]) -> PublishTarget:
    return PublishTarget(
        server_url=str(target.get("server_url", "")),
        site_id=str(target.get("site_id", "")),
        project=str(target.get("project", "default")),
        token_name=str(target.get("token_name", "")),
        token_secret=str(target.get("token_secret", "")),
    )


@tool(description=(
    "Publish a workbook to a Tableau server. Tier 3 (FINAL, HITL required). "
    "Requires target.server_url, token_name, token_secret, project."
))
def tableau_publish_workbook(
    workbook_path: str,
    target: dict[str, Any],
    *,
    project_id: str = "",
    mode: str = "Append",
) -> dict[str, Any]:
    try:
        result = _publish_workbook_server(
            workbook_path,
            _target_from_dict(target),
            project_id=project_id,
            mode=mode,
        )
    except TableauIntegrationError as exc:
        return {"error": exc.code, "message": str(exc)}
    return result.to_dict()


@tool(description="Refresh a published workbook's extract on a Tableau server. Tier 1 (idempotent).")
def tableau_refresh_workbook(
    workbook_id: str,
    target: dict[str, Any],
) -> dict[str, Any]:
    try:
        result = _refresh_workbook_server(workbook_id, _target_from_dict(target))
    except TableauIntegrationError as exc:
        return {"error": exc.code, "message": str(exc), "workbook_id": workbook_id}
    return result.to_dict()


@tool(description="List published workbooks on a Tableau server. Tier 0 (read-only).")
def tableau_list_workbooks(
    target: dict[str, Any],
    *,
    limit: int = 100,
) -> dict[str, Any]:
    try:
        result = _list_workbooks_server(_target_from_dict(target), limit=limit)
    except TableauIntegrationError as exc:
        return {"error": exc.code, "message": str(exc)}
    return result


TABLEAU_TOOLS = [
    tableau_capabilities,
    tableau_template_list,
    tableau_template_inspect,
    tableau_workbook_inspect,
    tableau_workbook_validate,
    tableau_workbook_generate,
    tableau_datasource_replace,
    tableau_worksheet_create,
    tableau_worksheet_modify,
    tableau_dashboard_create,
    tableau_dashboard_layout,
    tableau_story_create,
    tableau_twb_export,
    tableau_twbx_package,
    tableau_hyper_create,
    tableau_profile_dataset,
    tableau_validate_hyper,
    tableau_infer_schema,
    tableau_publish_workbook,
    tableau_refresh_workbook,
    tableau_list_workbooks,
]
