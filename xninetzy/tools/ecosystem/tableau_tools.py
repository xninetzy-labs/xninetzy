from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from xninetzy.integrations.tableau.compiler import (
    add_story,
    compile_datasource_from_csv,
    compile_workbook,
    default_layout,
    render_dashboard,
    render_datasource,
    render_worksheet,
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
from xninetzy.integrations.tableau import xsd
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


def _persist_workbook(workbook: Workbook, target: Path, schema_version: str | None = None) -> dict[str, Any]:
    from xninetzy.core.paths import resolve_artifact_output

    target = resolve_artifact_output(target, create_parents=True)
    body = compile_workbook(workbook)
    target.write_bytes(body)
    return {
        "path": str(target),
        "bytes": len(body),
        "datasources": workbook.datasource_names(),
        "worksheets": workbook.worksheet_names(),
        "dashboards": workbook.dashboard_names(),
        "validation": _validation_summary(target, schema_version),
    }


def _validation_summary(path: Path, schema_version: str | None = None) -> dict[str, Any]:
    report = validate_workbook(path, schema_version)
    return {
        "valid": report.valid,
        "xsd": report.checks.get("xsd"),
        "xsd_version": report.metadata.get("xsd_version"),
        "error_count": len(report.errors),
        "errors": report.errors[:5],
        "warnings": report.warnings[:5],
    }


def _failure(exc: TableauIntegrationError) -> dict[str, Any]:
    return {"error": exc.code, "message": str(exc)}


def _clean_sheet_name(raw: object, fallback: str) -> str:
    name = "".join(ch for ch in str(raw or "") if ch.isprintable()).strip()[:100]
    return name or fallback


def _rename_field_tokens(fragment: str, mapping: dict[str, str]) -> str:
    from lxml import etree

    element = etree.fromstring(fragment.encode("utf-8"))
    patterns = [
        (re.compile(r"\[((?:[A-Za-z]+:)?)" + re.escape(old) + r"((?::[a-z]{2})?)\]"), new)
        for old, new in mapping.items()
    ]

    def apply(value: str) -> str:
        for pattern, new in patterns:
            value = pattern.sub(lambda m, n=new: f"[{m.group(1)}{n}{m.group(2)}]", value)
        return value

    for node in element.iter():
        for key, value in list(node.attrib.items()):
            updated = apply(value)
            if updated != value:
                node.set(key, updated)
        if node.text and node.text.strip():
            node.text = apply(node.text)
    return etree.tostring(element, encoding="unicode")


def _referenced_fields(workbook: Workbook, datasource: str) -> set[str]:
    from lxml import etree

    names: set[str] = set()
    for fragment in workbook.worksheets_xml.values():
        element = etree.fromstring(fragment.encode("utf-8"))
        for dependencies in element.iter("datasource-dependencies"):
            if dependencies.get("datasource") == datasource:
                names.update(column.get("name", "") for column in dependencies.findall("column"))
    names.discard("")
    return names


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


@tool(description=(
    "Generate a fresh Tableau workbook (.twb) from CSVs and visualization specs. "
    "The CSV is profiled so numeric columns become measures; output is validated against the official Tableau TWB XSD. "
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
    tableau_version: str = "26.2",
) -> dict[str, Any]:
    if tableau_version not in xsd.supported_versions():
        return {"error": "unsupported_version", "supported": list(xsd.supported_versions()), "requested": tableau_version}
    workspace = workspace_root()
    sub = safe_workspace_subdir(output_subdir or name)
    target_dir = workspace / "workbooks" / sub
    target_dir.mkdir(parents=True, exist_ok=True)

    workbook = Workbook(metadata=WorkbookMetadata())
    for csv_path in csv_paths:
        cp = Path(csv_path)
        if not cp.is_file():
            return {"error": "missing_csv", "csv_path": str(cp)}
        ds_name = name if len(csv_paths) == 1 else f"federated.{safe_field_token(cp.stem)}"
        try:
            ds = compile_datasource_from_csv(cp, name=ds_name, profile=profile_csv(cp))
        except TableauIntegrationError as exc:
            return _failure(exc)
        workbook.datasources.append(ds)

    if template_name:
        try:
            tmpl = resolve_template_path(template_name)
            template_wb = _load_workbook(tmpl)
            for ds in template_wb.datasources[1:]:
                workbook.datasources.append(ds)
                workbook.datasource_xml[ds.name] = template_wb.datasource_xml.get(ds.name, "")
        except FileNotFoundError:
            pass

    try:
        specs = [
            (_clean_sheet_name(viz.get("name"), f"ws_{idx + 1}"), parse_visualization(viz))
            for idx, viz in enumerate(visualizations or [])
        ]
        names: set[str] = set()
        ordered: list[tuple[str, Any]] = []
        for idx, (ws_name, spec) in enumerate(specs):
            if ws_name in names:
                ws_name = f"{ws_name}_{idx + 1}"
            names.add(ws_name)
            ordered.append((ws_name, spec))
        compile_workbook(workbook, worksheets_to_add=tuple(ordered))
        if workbook.worksheets:
            db_name = _clean_sheet_name(dashboard_title, "Dashboard")
            if db_name in names:
                db_name = f"{db_name} Dashboard"
            workbook.dashboards.append(Dashboard(name=db_name))
            workbook.dashboards_xml[db_name] = render_dashboard(db_name, default_layout(workbook.worksheet_names()))
        if story_points:
            add_story(workbook, "Story 1", list(story_points))
    except TableauIntegrationError as exc:
        return _failure(exc)

    target = target_dir / f"{safe_field_token(name) or 'workbook'}.twb"
    info = _persist_workbook(workbook, target, tableau_version)
    info["idempotency_key"] = f"{name}:{','.join(str(p) for p in csv_paths)}"
    return info


@tool(description=(
    "Replace a workbook's primary datasource with a new CSV. field_map renames fields (old -> new) in every worksheet; "
    "the write is refused when worksheets still reference fields the new CSV does not have (unless allow_missing_fields=true)."
))
def tableau_datasource_replace(
    workbook_path: str,
    csv_path: str,
    field_map: dict[str, str] | None = None,
    allow_missing_fields: bool = False,
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if not workbook.datasources:
        return {"error": "no_datasource", "path": str(path)}
    old = workbook.datasources[0]
    try:
        new_ds = compile_datasource_from_csv(csv_path, name=old.name, profile=profile_csv(csv_path))
    except TableauIntegrationError as exc:
        return _failure(exc)
    new_ds.caption = old.caption or new_ds.caption
    mapping = {str(k).strip("[]"): str(v).strip("[]") for k, v in (field_map or {}).items() if k and v}
    unknown_targets = sorted(v for v in mapping.values() if new_ds.find_field(v) is None)
    if unknown_targets:
        return {"error": "field_map_target_missing", "fields": unknown_targets, "available": [f.caption for f in new_ds.fields]}
    if mapping:
        for key in list(workbook.worksheets_xml):
            workbook.worksheets_xml[key] = _rename_field_tokens(workbook.worksheets_xml[key], mapping)
        for key in list(workbook.dashboards_xml):
            workbook.dashboards_xml[key] = _rename_field_tokens(workbook.dashboards_xml[key], mapping)
    missing = sorted(name for name in _referenced_fields(workbook, old.name) if new_ds.find_field(name) is None)
    if missing and not allow_missing_fields:
        return {"error": "fields_missing_in_new_datasource", "fields": missing, "hint": "berikan field_map atau allow_missing_fields=true"}
    workbook.datasources[0] = new_ds
    workbook.datasource_xml[new_ds.name] = render_datasource(new_ds)
    result = _persist_workbook(workbook, path)
    result["missing_fields"] = missing
    result["renamed_fields"] = mapping
    return result


@tool(description="Append a new worksheet to an existing workbook based on a visualization spec.")
def tableau_worksheet_create(
    workbook_path: str, worksheet_name: str, visualization: dict[str, Any]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if any(w.name == worksheet_name for w in workbook.worksheets):
        return {"error": "duplicate_worksheet", "name": worksheet_name}
    if not workbook.datasources:
        return {"error": "no_datasource", "path": str(path)}
    try:
        spec = parse_visualization(visualization)
        workbook.worksheets.append(
            Worksheet(name=worksheet_name, title=worksheet_name, mark_class=spec.mark_class())
        )
        workbook.worksheets_xml[worksheet_name] = render_worksheet(worksheet_name, spec, workbook.datasources[0])
    except TableauIntegrationError as exc:
        return _failure(exc)
    return _persist_workbook(workbook, path)


@tool(description="Modify an existing worksheet in a workbook.")
def tableau_worksheet_modify(
    workbook_path: str, worksheet_name: str, visualization: dict[str, Any]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if not any(w.name == worksheet_name for w in workbook.worksheets):
        return {"error": "not_found", "worksheet": worksheet_name}
    if not workbook.datasources:
        return {"error": "no_datasource", "path": str(path)}
    try:
        spec = parse_visualization(visualization)
        workbook.worksheets_xml[worksheet_name] = render_worksheet(worksheet_name, spec, workbook.datasources[0])
    except TableauIntegrationError as exc:
        return _failure(exc)
    for ws in workbook.worksheets:
        if ws.name == worksheet_name:
            ws.mark_class = spec.mark_class()
            break
    return _persist_workbook(workbook, path)


@tool(description=(
    "Create a new dashboard referencing existing worksheets. layout is optional: entries "
    "{worksheet, x, y, w, h} in percent (0-100) of the dashboard; default stacks the worksheets vertically."
))
def tableau_dashboard_create(
    workbook_path: str,
    dashboard_name: str,
    worksheets: list[str],
    layout: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    if any(d.name == dashboard_name for d in workbook.dashboards) or dashboard_name in workbook.worksheet_names():
        return {"error": "duplicate_dashboard", "name": dashboard_name}
    if not worksheets or any(ws not in workbook.worksheet_names() for ws in worksheets):
        return {"error": "unknown_worksheet", "requested": worksheets}
    try:
        xml = render_dashboard(dashboard_name, layout or default_layout(worksheets))
    except TableauIntegrationError as exc:
        return _failure(exc)
    workbook.dashboards.append(Dashboard(name=dashboard_name))
    workbook.dashboards_xml[dashboard_name] = xml
    return _persist_workbook(workbook, path)


@tool(description="Update the zone layout (percent 0-100) for an existing dashboard; dashboard size is preserved.")
def tableau_dashboard_layout(
    workbook_path: str, dashboard_name: str, layout: list[dict[str, Any]]
) -> dict[str, Any]:
    from lxml import etree

    path = Path(workbook_path)
    workbook = _load_workbook(path)
    target = next((d for d in workbook.dashboards if d.name == dashboard_name), None)
    if target is None:
        return {"error": "not_found", "dashboard": dashboard_name}
    if target.is_storyboard:
        return {"error": "storyboard_has_no_layout", "dashboard": dashboard_name}
    unknown = sorted({str(e.get("worksheet")) for e in layout} - set(workbook.worksheet_names()) - set(workbook.dashboard_names()))
    if unknown:
        return {"error": "unknown_worksheet", "requested": unknown}
    size = (1200, 800)
    existing = workbook.dashboards_xml.get(dashboard_name)
    if existing:
        node = etree.fromstring(existing.encode("utf-8")).find("size")
        if node is not None and node.get("maxwidth") and node.get("maxheight"):
            size = (int(node.get("maxwidth")), int(node.get("maxheight")))
    try:
        workbook.dashboards_xml[dashboard_name] = render_dashboard(dashboard_name, layout, size)
    except TableauIntegrationError as exc:
        return _failure(exc)
    return _persist_workbook(workbook, path)


@tool(description=(
    "Add a story (storyboard) to a workbook. points are captions or {caption, sheet}; "
    "a point without sheet captures the workbook's dashboards/worksheets in order."
))
def tableau_story_create(
    workbook_path: str, story_name: str, points: list[Any]
) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    try:
        created = add_story(workbook, story_name, list(points))
    except TableauIntegrationError as exc:
        return _failure(exc)
    result = _persist_workbook(workbook, path)
    result["story"] = created
    result["story_points"] = [caption for caption, _ in workbook.story_points]
    return result


@tool(description="Re-serialize a workbook to a clean .twb file.")
def tableau_twb_export(workbook_path: str, target_path: str | None = None) -> dict[str, Any]:
    path = Path(workbook_path)
    workbook = _load_workbook(path)
    from xninetzy.core.paths import resolve_artifact_output

    target = resolve_artifact_output(target_path if target_path else path, create_parents=True)
    body = compile_workbook(workbook)
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
    from xninetzy.core.paths import resolve_artifact_output

    if output_path is None:
        out = workspace / "twbx" / f"{safe_field_token(path.stem)}.twbx"
    else:
        out = Path(output_path)
    out = resolve_artifact_output(out, create_parents=True)
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
