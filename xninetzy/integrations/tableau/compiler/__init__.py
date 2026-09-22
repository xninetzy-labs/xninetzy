from __future__ import annotations

import csv
import re
from pathlib import Path
from xml.sax.saxutils import escape

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    WORKBOOK_NS,
    Datasource,
    DatasourceField,
    DatasetProfile,
    VisualizationSpec,
    Workbook,
    Worksheet,
)


_TOKEN_INVALID = re.compile(r"[^A-Za-z0-9_]+")


def safe_field_token(name: str) -> str:
    cleaned = _TOKEN_INVALID.sub("_", str(name or "")).strip("_")
    if not cleaned:
        return "field"
    if cleaned[0].isdigit():
        cleaned = "f_" + cleaned
    return cleaned


def compile_datasource_from_csv(
    csv_path: str | Path,
    name: str,
    *,
    profile: "DatasetProfile | None" = None,
) -> Datasource:
    p = Path(csv_path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"DS_SOURCE_ERROR: CSV not found at {p}",
            code="INVALID_DATASET",
        )
    with p.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise TableauIntegrationError(
                f"INVALID_DATASET: empty CSV at {p}",
                code="INVALID_DATASET",
            ) from exc

    profile_columns = (
        {c.name: c for c in profile.columns} if profile is not None else {}
    )

    fields: list[DatasourceField] = []
    for idx, raw in enumerate(header):
        token = safe_field_token(raw)
        if not token:
            continue
        col = profile_columns.get(token) or profile_columns.get(raw)
        if col is not None:
            datatype = col.datatype
            role = col.role
            semantic_role = col.semantic_role
        else:
            datatype = "string"
            role = "dimension"
            semantic_role = None
        fields.append(
            DatasourceField(
                name=f"[{token}]",
                caption=raw,
                datatype=datatype,
                role=role,
                semantic_role=semantic_role,
            )
        )
    return Datasource(
        name=name,
        caption=name,
        connection_class="textscan",
        connection_path=str(p),
        connection_directory=str(p.parent),
        fields=fields,
    )


def _render_datasource_xml(ds: Datasource) -> str:
    cols = "\n".join(
        f'      <column name="{escape(f.name)}" caption="{escape(f.caption)}" '
        f'datatype="{escape(f.datatype)}" role="{escape(f.role)}"'
        + (f' semantic-role="{escape(f.semantic_role)}"' if f.semantic_role else "")
        + "/>"
        for f in ds.fields
    )
    directory_attr = (
        f' directory="{escape(ds.connection_directory)}"' if ds.connection_directory else ""
    )
    return (
        f'    <datasource name="{escape(ds.name)}" caption="{escape(ds.caption)}" version="18.1">\n'
        f'      <connection class="{escape(ds.connection_class)}"{directory_attr} '
        f'filename="{escape(ds.connection_path)}"/>\n'
        f"{cols}\n"
        f"    </datasource>"
    )


def _render_worksheet_xml(name: str, spec: VisualizationSpec, datasource_name: str) -> str:
    rows_field = (
        f'      <rows>[{safe_field_token(spec.rows[0])}]</rows>\n' if spec.rows else "  <rows/>\n"
    )
    cols_field = (
        f'      <cols>[{safe_field_token(spec.cols[0])}]</cols>\n' if spec.cols else "  <cols/>\n"
    )
    measure_xml = ""
    if spec.measure:
        measure_xml = (
            f'      <rows>[{safe_field_token(spec.measure)}:{spec.measure_aggregation.lower()}:nk]</rows>\n'
        )
    return (
        f'    <worksheet name="{escape(name)}">\n'
        f"      <title>{escape(name)}</title>\n"
        f"      <table>\n"
        f"        <view>\n"
        f'          <datasources><datasource name="{escape(datasource_name)}"/></datasources>\n'
        f"          {rows_field}{cols_field}{measure_xml}"
        f"        </view>\n"
        f'        <panes><pane><mark class="{escape(spec.mark_class())}"/></pane></panes>\n'
        f"      </table>\n"
        f"    </worksheet>"
    )


def compile_workbook(
    workbook: Workbook,
    *,
    worksheets_to_add: tuple[tuple[str, VisualizationSpec], ...] = (),
    story_points: tuple[str, ...] = (),
) -> bytes:
    seen_names: set[str] = set()
    for w in workbook.worksheets:
        if w.name in seen_names:
            raise TableauIntegrationError(
                f"WORKSHEET_CONFLICT: duplicate worksheet '{w.name}'",
                code="WORKSHEET_CONFLICT",
            )
        seen_names.add(w.name)

    primary_ds = workbook.datasources[0].name if workbook.datasources else "federated.primary"
    for name, spec in worksheets_to_add:
        if name in seen_names:
            raise TableauIntegrationError(
                f"WORKSHEET_CONFLICT: worksheet '{name}' already exists",
                code="WORKSHEET_CONFLICT",
            )
        seen_names.add(name)
        workbook.worksheets.append(Worksheet(name=name, raw_xml=""))
        workbook.worksheets_xml[name] = _render_worksheet_xml(name, spec, primary_ds)

    if story_points:
        workbook.story_points = [(caption, f"sp{idx + 1}") for idx, caption in enumerate(story_points)]

    metas = workbook.metadata
    head = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<workbook xmlns:user="{WORKBOOK_NS}" '
        f'original-version="{escape(metas.original_version)}" '
        f'source-build="{escape(metas.source_build)}" '
        f'source-platform="{escape(metas.source_platform)}" '
        f'version="{escape(metas.version)}">\n'
    )

    prefs = ""
    if workbook.preferences_xml:
        prefs = f"  {workbook.preferences_xml}\n"

    manifest = ""
    if workbook.document_format_xml:
        manifest = f"  {workbook.document_format_xml}\n"

    ds_section = ""
    if workbook.datasources:
        unique: dict[str, Datasource] = {}
        for ds in workbook.datasources:
            if ds.name in unique:
                continue
            unique[ds.name] = ds
        if len(unique) != len(workbook.datasources):
            workbook.datasources = list(unique.values())
        rendered = []
        for ds in workbook.datasources:
            xml = workbook.datasource_xml.get(ds.name) or _render_datasource_xml(ds)
            rendered.append(xml)
        ds_section = "  <datasources>\n" + "\n".join(rendered) + "\n  </datasources>\n"

    ws_section = ""
    if workbook.worksheets_xml:
        ws_section = "  <worksheets>\n" + "\n".join(workbook.worksheets_xml.values()) + "\n  </worksheets>\n"

    db_section = ""
    if workbook.dashboards_xml:
        db_section = "  <dashboards>\n" + "\n".join(workbook.dashboards_xml.values()) + "\n  </dashboards>\n"

    body = head + prefs + manifest + ds_section + ws_section + db_section + "</workbook>\n"
    return body.encode("utf-8")


__all__ = [
    "compile_workbook",
    "compile_datasource_from_csv",
    "safe_field_token",
]
