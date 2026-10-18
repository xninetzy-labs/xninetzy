from __future__ import annotations

import copy
import re
from pathlib import Path

from lxml import etree

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

DOCTYPE_PATTERN = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)
_SAFE_PARSER = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
_PRESERVED_TAGS = (
    "repository-location",
    "style-theme",
    "local-data",
    "local-data-typed",
    "datasource-relationships",
    "mapsources",
    "shared-views",
    "actions",
    "datagraph",
    "external",
    "referenced-extensions",
    "explain-data",
    "data-orientation",
    "tab-agent-config",
    "accelerator-details",
    "workbook-optimizer",
)
_DATATYPES = frozenset({"integer", "real", "string", "datetime", "date", "boolean"})
_METADATA_TYPES = {"integer": "integer", "real": "real", "string": "string", "date": "date", "datetime": "datetime", "boolean": "boolean"}


def _local(tag: str) -> str:
    return tag.split("}", 1)[-1] if "}" in tag else tag


def _serialize(element: etree._Element) -> str:
    clone = copy.deepcopy(element)
    clone.tail = None
    etree.cleanup_namespaces(clone)
    return etree.tostring(clone, encoding="unicode")


def _text(element: etree._Element | None, tag: str) -> str:
    if element is None:
        return ""
    child = element.find(tag)
    return (child.text or "").strip() if child is not None else ""


def _connection_details(ds_el: etree._Element) -> tuple[str, str, str]:
    connection = ds_el.find("connection")
    if connection is None:
        return "textscan", "", ""
    inner = connection.find("named-connections/named-connection/connection")
    source = inner if inner is not None else connection
    connection_class = source.get("class", connection.get("class", "textscan"))
    directory = source.get("directory", "")
    filename = source.get("filename", "")
    if filename and directory and not Path(filename).is_absolute():
        filename = str(Path(directory) / filename)
    return connection_class, filename, directory


def _datasource_fields(ds_el: etree._Element) -> list[DatasourceField]:
    ordered: dict[str, DatasourceField] = {}
    for column in ds_el.iterfind("connection/relation/columns/column"):
        remote = column.get("name", "")
        if not remote:
            continue
        datatype = column.get("datatype", "string")
        datatype = datatype if datatype in _DATATYPES else "string"
        role = "measure" if datatype in {"integer", "real"} else "dimension"
        key = f"[{remote}]"
        ordered[key] = DatasourceField(
            name=key,
            caption=remote,
            datatype=datatype,
            role=role,
            remote_name=remote,
            ordinal=int(column.get("ordinal", len(ordered)) or 0),
        )
    for record in ds_el.iterfind("connection/metadata-records/metadata-record"):
        if record.get("class") != "column":
            continue
        local = _text(record, "local-name")
        if not local:
            continue
        datatype = _METADATA_TYPES.get(_text(record, "local-type"), "string")
        remote = _text(record, "remote-name")
        role = "measure" if datatype in {"integer", "real"} else "dimension"
        existing = ordered.get(local)
        if existing is None:
            ordered[local] = DatasourceField(
                name=local,
                caption=remote or local.strip("[]"),
                datatype=datatype,
                role=role,
                remote_name=remote,
                ordinal=int(_text(record, "ordinal") or len(ordered)),
            )
        elif not existing.remote_name:
            existing.remote_name = remote
    for column in ds_el.iterfind("column"):
        name = column.get("name", "")
        if not name:
            continue
        datatype = column.get("datatype", "string")
        datatype = datatype if datatype in _DATATYPES else "string"
        role = column.get("role", "measure" if datatype in {"integer", "real"} else "dimension")
        existing = ordered.get(name)
        remote = existing.remote_name if existing else ""
        ordinal = existing.ordinal if existing else len(ordered)
        ordered[name] = DatasourceField(
            name=name,
            caption=column.get("caption") or (existing.caption if existing else name.strip("[]")),
            datatype=datatype,
            role=role if role in {"dimension", "measure"} else "dimension",
            semantic_role=column.get("semantic-role"),
            remote_name=remote,
            ordinal=ordinal,
        )
    return list(ordered.values())


def _worksheet_title(ws_el: etree._Element, fallback: str) -> str:
    runs = ws_el.findall("layout-options/title/formatted-text/run")
    text = "".join((run.text or "") for run in runs).strip()
    return text or fallback


def parse_workbook_bytes(data: bytes, source: Path | None = None) -> Workbook:
    if DOCTYPE_PATTERN.search(data[:4096].decode("utf-8", errors="ignore")):
        raise TableauIntegrationError("TWB_PARSE_ERROR: DOCTYPE/ENTITY tidak diizinkan di workbook")
    try:
        root = etree.fromstring(data, _SAFE_PARSER)
    except etree.XMLSyntaxError as exc:
        label = source.name if source is not None else "workbook"
        raise TableauIntegrationError(f"TWB_PARSE_ERROR: cannot parse {label}: {exc}") from exc
    if _local(root.tag) != "workbook":
        raise TableauIntegrationError(
            f"TWB_PARSE_ERROR: root element must be <workbook>, got <{_local(root.tag)}>"
        )

    metadata = WorkbookMetadata.from_root(root)

    datasources: list[Datasource] = []
    datasource_xml: dict[str, str] = {}
    container = root.find("datasources")
    for ds_el in (container if container is not None else []):
        if _local(ds_el.tag) != "datasource":
            continue
        name = ds_el.get("name") or ds_el.get("caption") or f"ds_{len(datasources)}"
        connection_class, connection_path, connection_dir = _connection_details(ds_el)
        datasources.append(
            Datasource(
                name=name,
                caption=ds_el.get("caption", name),
                connection_class=connection_class,
                connection_path=connection_path,
                connection_directory=connection_dir,
                fields=_datasource_fields(ds_el),
            )
        )
        datasource_xml[name] = _serialize(ds_el)

    worksheets: list[Worksheet] = []
    worksheets_xml: dict[str, str] = {}
    container = root.find("worksheets")
    for ws_el in (container if container is not None else []):
        if _local(ws_el.tag) != "worksheet":
            continue
        name = ws_el.get("name", f"Sheet{len(worksheets) + 1}")
        mark_el = ws_el.find(".//panes/pane/mark")
        if mark_el is None:
            mark_el = ws_el.find(".//mark")
        worksheets.append(
            Worksheet(
                name=name,
                title=_worksheet_title(ws_el, name),
                mark_class=mark_el.get("class", "Automatic") if mark_el is not None else "Automatic",
            )
        )
        worksheets_xml[name] = _serialize(ws_el)

    dashboards: list[Dashboard] = []
    dashboards_xml: dict[str, str] = {}
    story_points: list[tuple[str, str]] = []
    container = root.find("dashboards")
    for db_el in (container if container is not None else []):
        if _local(db_el.tag) != "dashboard":
            continue
        name = db_el.get("name", f"Dashboard{len(dashboards) + 1}")
        storyboard = db_el.get("type") == "storyboard"
        dashboards.append(Dashboard(name=name, is_storyboard=storyboard))
        dashboards_xml[name] = _serialize(db_el)
        if storyboard:
            for point in db_el.iter("story-point"):
                story_points.append((point.get("caption", ""), point.get("id", "")))

    def top_level(tag: str) -> str:
        element = root.find(tag)
        return _serialize(element) if element is not None else ""

    preserved = {tag: top_level(tag) for tag in _PRESERVED_TAGS if root.find(tag) is not None}

    return Workbook(
        metadata=metadata,
        datasources=datasources,
        worksheets=worksheets,
        dashboards=dashboards,
        worksheets_xml=worksheets_xml,
        dashboards_xml=dashboards_xml,
        datasource_xml=datasource_xml,
        preferences_xml=top_level("preferences"),
        document_format_xml=top_level("document-format-change-manifest"),
        style_xml=top_level("style"),
        windows_xml=top_level("windows"),
        preserved_xml=preserved,
        story_points=story_points,
        source_path=source,
    )


def parse_workbook(path: Path | str) -> Workbook:
    p = Path(path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"TWB_PARSE_ERROR: workbook not found at {p}"
        )
    return parse_workbook_bytes(p.read_bytes(), p)


def serialize_workbook(workbook: Workbook) -> bytes:
    from xninetzy.integrations.tableau.compiler import compile_workbook

    return compile_workbook(workbook)


__all__ = [
    "parse_workbook",
    "parse_workbook_bytes",
    "serialize_workbook",
    "WORKBOOK_NS",
]
