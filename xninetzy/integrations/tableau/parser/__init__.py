from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree as ET

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    WORKBOOK_NS,
    Dashboard,
    Datasource,
    DatasourceField,
    Workbook,
    WorkbookMetadata,
    Worksheet,
)


_TAG_STRIP = re.compile(r"<(/?)[a-zA-Z][^>]*>")


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def parse_workbook(path: Path | str) -> Workbook:
    p = Path(path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"TWB_PARSE_ERROR: workbook not found at {p}"
        )
    try:
        tree = ET.parse(p)
    except ET.ParseError as exc:
        raise TableauIntegrationError(
            f"TWB_PARSE_ERROR: cannot parse {p.name}: {exc}"
        ) from exc

    root = tree.getroot()
    if _local(root.tag) != "workbook":
        raise TableauIntegrationError(
            f"TWB_PARSE_ERROR: root element must be <workbook>, got <{_local(root.tag)}>"
        )

    metadata = WorkbookMetadata.from_root(root)

    raw = p.read_text(encoding="utf-8", errors="replace")

    datasources: list[Datasource] = []
    datasource_xml: dict[str, str] = {}
    for ds_el in root.findall(".//datasources/datasource") or root.findall(".//datasource"):
        name = ds_el.get("name") or ds_el.get("caption") or f"ds_{len(datasources)}"
        conn = ds_el.find("connection")
        conn_class = conn.get("class", "textscan") if conn is not None else "textscan"
        conn_path = conn.get("filename", "") if conn is not None else ""
        conn_dir = conn.get("directory", "") if conn is not None else ""
        fields: list[DatasourceField] = []
        for col in ds_el.findall("column"):
            fields.append(
                DatasourceField(
                    name=col.get("name", ""),
                    caption=col.get("caption", "") or col.get("name", ""),
                    datatype=col.get("datatype", "string"),
                    role=col.get("role", "dimension"),
                    semantic_role=col.get("semantic-role"),
                )
            )
        ds = Datasource(
            name=name,
            caption=ds_el.get("caption", name),
            connection_class=conn_class,
            connection_path=conn_path,
            connection_directory=conn_dir,
            fields=fields,
        )
        datasources.append(ds)
        snippet = _extract_element(raw, "datasource", ds_el.get("name"))
        datasource_xml[name] = snippet

    worksheets: list[Worksheet] = []
    worksheets_xml: dict[str, str] = {}
    for ws_el in root.findall(".//worksheets/worksheet") or root.findall(".//worksheet"):
        name = ws_el.get("name", f"Sheet{len(worksheets) + 1}")
        title_el = ws_el.find("title")
        mark_el = ws_el.find(".//panes/pane/mark") or ws_el.find(".//mark")
        mark_class = mark_el.get("class", "Automatic") if mark_el is not None else "Automatic"
        ws = Worksheet(
            name=name,
            title=title_el.text or "" if title_el is not None else "",
            mark_class=mark_class,
        )
        worksheets.append(ws)
        worksheets_xml[name] = _extract_element(raw, "worksheet", name)

    dashboards: list[Dashboard] = []
    dashboards_xml: dict[str, str] = {}
    db_root = root.find("dashboards")
    if db_root is not None:
        for db_el in db_root:
            name = db_el.get("name", f"Dashboard{len(dashboards) + 1}")
            dashboards.append(
                Dashboard(
                    name=name,
                    is_storyboard=(db_el.get("type") == "storyboard"),
                )
            )
            dashboards_xml[name] = _extract_element(raw, _local(db_el.tag), name)

    story_points: list[tuple[str, str]] = []
    story_root = db_root.find("story") if db_root is not None else None
    if story_root is not None:
        for sp in story_root.findall("story-points/story-point"):
            story_points.append((sp.get("caption", ""), sp.get("id", "")))

    preferences_xml = _extract_top_level(raw, "preferences")
    manifest_xml = _extract_top_level(raw, "document-format-change-manifest")

    workbook = Workbook(
        metadata=metadata,
        datasources=datasources,
        worksheets=worksheets,
        dashboards=dashboards,
        worksheets_xml=worksheets_xml,
        dashboards_xml=dashboards_xml,
        datasource_xml=datasource_xml,
        preferences_xml=preferences_xml,
        document_format_xml=manifest_xml,
        story_points=story_points,
        source_path=p,
    )
    return workbook


def _extract_element(xml: str, tag: str, name: str | None) -> str:
    if not name:
        idx = xml.find(f"<{tag}")
        if idx < 0:
            return ""
        end = xml.find(f"</{tag}>", idx)
        if end < 0:
            return ""
        return xml[idx : end + len(f"</{tag}>")]
    open_re = re.compile(rf"<{re.escape(tag)}\b[^>]*\bname=\"{re.escape(name)}\"")
    m = open_re.search(xml)
    if not m:
        return ""
    end = xml.find(f"</{tag}>", m.start())
    if end < 0:
        return ""
    return xml[m.start() : end + len(f"</{tag}>")]


def _extract_top_level(xml: str, tag: str) -> str:
    start = xml.find(f"<{tag}")
    if start < 0:
        return ""
    end = xml.find(f"</{tag}>", start)
    if end < 0:
        return ""
    return xml[start : end + len(f"</{tag}>")]


def serialize_workbook(workbook: Workbook) -> bytes:
    from xninetzy.integrations.tableau.compiler import compile_workbook

    return compile_workbook(workbook)


__all__ = [
    "parse_workbook",
    "serialize_workbook",
    "WORKBOOK_NS",
]
