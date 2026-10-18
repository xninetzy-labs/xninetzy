from __future__ import annotations

import csv
import re
import uuid
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    DOCUMENT_FEATURES,
    FORMAT_VERSION,
    PLACEHOLDER_BUILD,
    PRODUCT_BUILD,
    WORKBOOK_NS,
    Dashboard,
    Datasource,
    DatasourceField,
    DatasetProfile,
    VisualizationSpec,
    Workbook,
    Worksheet,
)


_TOKEN_INVALID = re.compile(r"[^A-Za-z0-9_]+")
_SEMANTIC_ROLE = re.compile(r"^\[[A-Za-z]+\]\.\[[A-Za-z0-9_]+\]$")
_UUID_NAMESPACE = uuid.UUID("6f0f8d5e-2d0a-4c5b-9d2b-3f5a1b7c9e11")
_FRAGMENT_PARSER = etree.XMLParser(remove_blank_text=True, resolve_entities=False, no_network=True, load_dtd=False)

TOP_LEVEL_ORDER: tuple[str, ...] = (
    "document-format-change-manifest",
    "repository-location",
    "preferences",
    "style-theme",
    "style",
    "local-data",
    "local-data-typed",
    "datasources",
    "datasource-relationships",
    "mapsources",
    "shared-views",
    "actions",
    "worksheets",
    "dashboards",
    "windows",
    "datagraph",
    "thumbnails",
    "external",
    "referenced-extensions",
    "explain-data",
    "data-orientation",
    "tab-agent-config",
    "accelerator-details",
    "workbook-optimizer",
)
DROPPED_SECTIONS = frozenset({"thumbnails"})
SUPPORTED_PLATFORMS = frozenset({"win", "mac"})
DATE_PARSE_FORMAT = "yyyy-MM-dd"
FIELD_REMOTE_TYPES: dict[str, int] = {"string": 129, "integer": 20, "real": 5, "date": 7, "datetime": 135, "boolean": 11}
FIELD_AGGREGATIONS: dict[str, str] = {
    "string": "Count",
    "integer": "Sum",
    "real": "Sum",
    "date": "Year",
    "datetime": "Year",
    "boolean": "Count",
}
TEXT_AGGREGATIONS = frozenset({"COUNT", "COUNTD", "MIN", "MAX"})
TRUNC_LEVELS: dict[str, tuple[str, str]] = {
    "year": ("Year-Trunc", "tyr"),
    "quarter": ("Quarter-Trunc", "tqr"),
    "month": ("Month-Trunc", "tmn"),
    "week": ("Week-Trunc", "twk"),
    "day": ("Day-Trunc", "tdy"),
}
DEFAULT_PREFERENCES: tuple[tuple[str, str], ...] = (
    ("ui.encoding.shelf.height", "24"),
    ("ui.shelf.height", "26"),
)
NUMERIC_DATATYPES = frozenset({"integer", "real"})
TEMPORAL_DATATYPES = frozenset({"date", "datetime"})
VALID_DATATYPES = frozenset({"integer", "real", "string", "datetime", "date", "boolean"})
AGGREGATIONS: dict[str, tuple[str, str]] = {
    "SUM": ("Sum", "sum"),
    "AVG": ("Avg", "avg"),
    "AVERAGE": ("Avg", "avg"),
    "MEAN": ("Avg", "avg"),
    "COUNT": ("Count", "cnt"),
    "COUNTD": ("CountD", "ctd"),
    "MIN": ("Min", "min"),
    "MAX": ("Max", "max"),
    "MEDIAN": ("Median", "med"),
}
TRENDLINE_MARKS = frozenset({"scatter", "line", "circle", "area"})
DASHBOARD_UNITS = 100000
DEFAULT_DASHBOARD_SIZE = (1200, 800)


def safe_field_token(name: str) -> str:
    cleaned = _TOKEN_INVALID.sub("_", str(name or "")).strip("_")
    if not cleaned:
        return "field"
    if cleaned[0].isdigit():
        cleaned = "f_" + cleaned
    return cleaned


def _bracket(name: str) -> str:
    return "[" + str(name).replace("]", "]]") + "]"


def _stable_uuid(kind: str, name: str) -> str:
    return "{" + str(uuid.uuid5(_UUID_NAMESPACE, f"{kind}:{name}")).upper() + "}"


def _node(parent: etree._Element | None, tag: str, attrs: dict[str, object] | None = None, text: str | None = None) -> etree._Element:
    values = {key: str(value) for key, value in (attrs or {}).items() if value is not None}
    element = etree.Element(tag, values) if parent is None else etree.SubElement(parent, tag, values)
    if text is not None:
        element.text = text
    return element


def _to_string(element: etree._Element) -> str:
    clone = etree.fromstring(etree.tostring(element))
    etree.cleanup_namespaces(clone)
    return etree.tostring(clone, encoding="unicode", pretty_print=True).rstrip("\n")


def _from_string(fragment: str) -> etree._Element:
    return etree.fromstring(fragment.strip().encode("utf-8"), _FRAGMENT_PARSER)


def datatype_defaults(datatype: str) -> tuple[str, str]:
    if datatype in NUMERIC_DATATYPES:
        return "measure", "quantitative"
    if datatype in TEMPORAL_DATATYPES:
        return "dimension", "ordinal"
    return "dimension", "nominal"


def _field_type(field: DatasourceField) -> str:
    if field.role == "measure":
        return "quantitative"
    if field.datatype in TEMPORAL_DATATYPES or field.datatype in NUMERIC_DATATYPES:
        return "ordinal"
    return "nominal"


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
    with p.open("r", encoding="utf-8-sig", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise TableauIntegrationError(
                f"INVALID_DATASET: empty CSV at {p}",
                code="INVALID_DATASET",
            ) from exc

    profile_columns: dict[str, object] = {}
    if profile is not None:
        for column in profile.columns:
            profile_columns[column.name] = column
            profile_columns.setdefault(column.caption, column)

    fields: list[DatasourceField] = []
    seen: set[str] = set()
    for index, raw in enumerate(header):
        remote = str(raw).strip() or f"F{index + 1}"
        if remote in seen:
            continue
        seen.add(remote)
        column = profile_columns.get(remote) or profile_columns.get(safe_field_token(remote))
        if column is not None:
            datatype = column.datatype if column.datatype in VALID_DATATYPES else "string"
            role = column.role if column.role in {"dimension", "measure"} else datatype_defaults(datatype)[0]
            semantic_role = column.semantic_role if column.semantic_role and _SEMANTIC_ROLE.match(column.semantic_role) else None
        else:
            datatype, role, semantic_role = "string", "dimension", None
        fields.append(
            DatasourceField(
                name=_bracket(remote),
                caption=remote,
                datatype=datatype,
                role=role,
                semantic_role=semantic_role,
                remote_name=remote,
                ordinal=index,
            )
        )
    identifier = name if name.startswith("federated.") else f"federated.{safe_field_token(name)}"
    return Datasource(
        name=identifier,
        caption=name.removeprefix("federated.") if name.startswith("federated.") else name,
        connection_class="textscan",
        connection_path=str(p),
        connection_directory=str(p.parent),
        fields=fields,
    )


def _column_element(parent: etree._Element, field: DatasourceField, *, with_caption: bool) -> etree._Element:
    attrs: dict[str, object] = {
        "datatype": field.datatype if field.datatype in VALID_DATATYPES else "string",
        "name": field.name,
        "role": field.role if field.role in {"dimension", "measure"} else datatype_defaults(field.datatype)[0],
        "type": _field_type(field),
    }
    if with_caption and field.caption and field.caption != field.local_name():
        attrs["caption"] = field.caption
    if field.semantic_role and _SEMANTIC_ROLE.match(field.semantic_role):
        attrs["semantic-role"] = field.semantic_role
    return _node(parent, "column", attrs)


def _relation_element(connection_name: str, relation_name: str, fields: list[DatasourceField]) -> etree._Element:
    relation = etree.Element("relation", {
        "connection": connection_name,
        "name": relation_name,
        "table": "[" + relation_name.replace(".", "#").replace("]", "]]") + "]",
        "type": "table",
    })
    columns = _node(relation, "columns", {"character-set": "UTF-8", "header": "yes", "locale": "en_US", "separator": ","})
    for index, field in enumerate(fields):
        datatype = field.datatype if field.datatype in VALID_DATATYPES else "string"
        attrs: dict[str, object] = {"datatype": datatype}
        if datatype == "date":
            attrs["date-parse-format"] = DATE_PARSE_FORMAT
        attrs["name"] = field.remote_name or field.local_name()
        attrs["ordinal"] = field.ordinal if field.remote_name else index
        _node(columns, "column", attrs)
    return relation


def _metadata_records(parent: etree._Element, fields: list[DatasourceField], relation_name: str, object_id: str) -> None:
    parent_name = _bracket(relation_name)
    records = _node(parent, "metadata-records")
    capability = _node(records, "metadata-record", {"class": "capability"})
    _node(capability, "remote-name")
    _node(capability, "remote-type", text="0")
    _node(capability, "parent-name", text=parent_name)
    _node(capability, "remote-alias")
    _node(capability, "aggregation", text="Count")
    _node(capability, "contains-null", text="true")
    for index, field in enumerate(fields):
        datatype = field.datatype if field.datatype in VALID_DATATYPES else "string"
        remote = field.remote_name or field.local_name()
        record = _node(records, "metadata-record", {"class": "column"})
        _node(record, "remote-name", text=remote)
        _node(record, "remote-type", text=str(FIELD_REMOTE_TYPES[datatype]))
        _node(record, "local-name", text=field.name)
        _node(record, "parent-name", text=parent_name)
        _node(record, "remote-alias", text=remote)
        _node(record, "ordinal", text=str(field.ordinal if field.remote_name else index))
        _node(record, "local-type", text=datatype)
        _node(record, "aggregation", text=FIELD_AGGREGATIONS[datatype])
        _node(record, "contains-null", text="true")
        _node(record, "object-id", text=f"[{object_id}]")


def render_datasource(ds: Datasource) -> str:
    source = Path(ds.connection_path) if ds.connection_path else None
    directory = ds.connection_directory or (str(source.parent) if source else "")
    filename = source.name if source else ""
    relation_name = filename or ds.name
    identifier = uuid.uuid5(_UUID_NAMESPACE, f"textscan:{ds.connection_path or ds.name}").hex[:27]
    connection_name = f"textscan.{identifier}"
    object_id = f"{relation_name}_{uuid.uuid5(_UUID_NAMESPACE, f'object:{ds.connection_path or ds.name}').hex.upper()}"
    root = _node(None, "datasource", {"caption": ds.caption or ds.name, "inline": "true", "name": ds.name, "version": FORMAT_VERSION})
    connection = _node(root, "connection", {"class": "federated"})
    named = _node(_node(connection, "named-connections"), "named-connection", {"caption": relation_name, "name": connection_name})
    _node(named, "connection", {"class": ds.connection_class or "textscan", "directory": directory, "filename": filename, "password": "", "server": ""})
    connection.append(_relation_element(connection_name, relation_name, ds.fields))
    _metadata_records(connection, ds.fields, relation_name, object_id)
    _node(root, "aliases", {"enabled": "yes"})
    _node(root, "column", {
        "caption": relation_name,
        "datatype": "table",
        "name": f"[__tableau_internal_object_id__].[{object_id}]",
        "role": "measure",
        "type": "quantitative",
    })
    for field in ds.fields:
        _column_element(root, field, with_caption=False)
    _node(root, "layout", {"dim-ordering": "alphabetic", "measure-ordering": "alphabetic", "show-structure": "true"})
    graph = _node(root, "object-graph")
    node = _node(_node(_node(graph, "objects"), "object", {"caption": relation_name, "id": object_id}), "properties", {"context": ""})
    node.append(_relation_element(connection_name, relation_name, ds.fields))
    return _to_string(root)


@dataclass(slots=True)
class _Instance:
    field: DatasourceField
    column: str
    name: str
    derivation: str
    kind: str

    def reference(self, datasource: str) -> str:
        return f"[{datasource}].{self.name}"


def _resolve(ds: Datasource, reference: str, *, role: str) -> DatasourceField:
    found = ds.find_field(reference)
    if found is None:
        available = ", ".join(f.caption or f.local_name() for f in ds.fields[:30])
        raise TableauIntegrationError(
            f"FIELD_NOT_FOUND: {role} '{reference}' tidak ada di datasource '{ds.name}'. Field tersedia: {available}",
            code="FIELD_NOT_FOUND",
        )
    return found


def _aggregation(spec: VisualizationSpec) -> tuple[str, str]:
    key = str(spec.measure_aggregation or "SUM").upper()
    if key not in AGGREGATIONS:
        raise TableauIntegrationError(
            f"VIZ_AGG_ERROR: agregasi '{spec.measure_aggregation}' tidak didukung. Didukung: {sorted(set(AGGREGATIONS))}",
            code="VIZ_TYPE_ERROR",
        )
    return AGGREGATIONS[key]


def _instance(field: DatasourceField, spec: VisualizationSpec, *, as_measure: bool | None = None) -> _Instance:
    local = field.local_name()
    column = _bracket(local)
    measure = field.role == "measure" if as_measure is None else as_measure
    if measure:
        if field.datatype in {"string", "boolean"}:
            requested = str(spec.measure_aggregation or "").upper()
            derivation, abbreviation = AGGREGATIONS[requested] if requested in TEXT_AGGREGATIONS else AGGREGATIONS["COUNT"]
        else:
            derivation, abbreviation = _aggregation(spec)
        return _Instance(field, column, _bracket(f"{abbreviation}:{local}:qk"), derivation, "quantitative")
    if field.datatype in TEMPORAL_DATATYPES:
        if spec.date_level:
            derivation, abbreviation = TRUNC_LEVELS[spec.date_level]
            return _Instance(field, column, _bracket(f"{abbreviation}:{local}:qk"), derivation, "quantitative")
        if spec.type in {"line", "area"}:
            return _Instance(field, column, _bracket(f"tmn:{local}:qk"), "Month-Trunc", "quantitative")
        return _Instance(field, column, _bracket(f"yr:{local}:ok"), "Year", "ordinal")
    if field.datatype in NUMERIC_DATATYPES:
        return _Instance(field, column, _bracket(f"none:{local}:ok"), "None", "ordinal")
    return _Instance(field, column, _bracket(f"none:{local}:nk"), "None", "nominal")


def _is_dimension(instance: _Instance) -> bool:
    return instance.kind != "quantitative" or instance.derivation.endswith("-Trunc")


def _plan_worksheet(spec: VisualizationSpec, ds: Datasource) -> dict[str, list[_Instance]]:
    if spec.top_n is not None:
        raise TableauIntegrationError(
            "VIZ_OPTION_UNSUPPORTED: top_n belum didukung oleh generator; pasang Top N filter di Tableau Desktop",
            code="VIZ_TYPE_ERROR",
        )
    if spec.trend_line and spec.type not in TRENDLINE_MARKS:
        raise TableauIntegrationError(
            f"VIZ_OPTION_UNSUPPORTED: trend_line hanya untuk {sorted(TRENDLINE_MARKS)}, bukan '{spec.type}'",
            code="VIZ_TYPE_ERROR",
        )
    rows = [_instance(_resolve(ds, ref, role="rows"), spec) for ref in spec.rows]
    cols = [_instance(_resolve(ds, ref, role="cols"), spec) for ref in spec.cols]
    plan: dict[str, list[_Instance]] = {"rows": [], "cols": [], "color": [], "size": [], "text": [], "wedge-size": []}
    measure = _instance(_resolve(ds, spec.measure, role="measure"), spec, as_measure=True) if spec.measure else None
    dimensions = [i for i in rows + cols if _is_dimension(i)]
    if spec.type == "pie":
        plan["color"] = dimensions[:1]
        plan["wedge-size"] = [measure] if measure else []
    elif spec.type in {"kpi", "table"}:
        plan["rows"] = [i for i in rows + cols if not _is_aggregate(i)]
        plan["text"] = [measure] if measure else [i for i in rows + cols if _is_aggregate(i)]
    else:
        plan["rows"], plan["cols"] = rows, cols
        if measure is not None:
            has_col_dimension = any(_is_dimension(i) for i in cols)
            has_row_dimension = any(_is_dimension(i) for i in rows)
            if spec.type in {"line", "area"} and has_row_dimension and not has_col_dimension:
                plan["rows"], plan["cols"] = [measure], rows
            elif has_row_dimension and not has_col_dimension and not cols:
                plan["cols"] = cols + [measure]
            else:
                plan["rows"] = rows + [measure]
    for key, reference in (("color", spec.color), ("size", spec.size), ("text", spec.label)):
        if reference:
            plan[key] = plan[key] + [_instance(_resolve(ds, reference, role=key), spec)]
    return plan


def _is_aggregate(instance: _Instance) -> bool:
    return instance.derivation in {"Sum", "Avg", "Count", "CountD", "Min", "Max", "Median"}


def _shelf_text(instances: list[_Instance], datasource: str) -> str:
    text = instances[0].reference(datasource)
    if len(instances) == 1:
        return text
    for previous, current in zip(instances, instances[1:]):
        joiner = " + " if _is_aggregate(previous) and _is_aggregate(current) else " * "
        text += joiner + current.reference(datasource)
    return "(" + text + ")"


def render_worksheet(name: str, spec: VisualizationSpec, ds: Datasource) -> str:
    plan = _plan_worksheet(spec, ds)
    used: dict[str, _Instance] = {}
    for instances in plan.values():
        for instance in instances:
            used.setdefault(instance.name, instance)
    fields: dict[str, DatasourceField] = {}
    for instance in used.values():
        fields.setdefault(instance.field.name, instance.field)
    worksheet = _node(None, "worksheet", {"name": name})
    table = _node(worksheet, "table")
    view = _node(table, "view")
    _node(_node(view, "datasources"), "datasource", {"caption": ds.caption or ds.name, "name": ds.name})
    dependencies = _node(view, "datasource-dependencies", {"datasource": ds.name})
    for field in fields.values():
        _column_element(dependencies, field, with_caption=False)
    for instance in used.values():
        _node(dependencies, "column-instance", {
            "column": instance.column,
            "derivation": instance.derivation,
            "name": instance.name,
            "pivot": "key",
            "type": instance.kind,
        })
    _node(view, "aggregation", {"value": "true"})
    _node(table, "style")
    pane = _node(_node(table, "panes"), "pane", {"selection-relaxation-option": "selection-relaxation-allow"})
    _node(_node(pane, "view"), "breakdown", {"value": "auto"})
    _node(pane, "mark", {"class": spec.mark_class()})
    encodings = [(tag, inst) for tag in ("color", "size", "text", "wedge-size") for inst in plan[tag]]
    if encodings:
        container = _node(pane, "encodings")
        for tag, inst in encodings:
            _node(container, tag, {"column": inst.reference(ds.name)})
    if spec.trend_line:
        _node(pane, "trendline", {
            "enabled": "true",
            "fit": "linear",
            "exclude-intercept": "false",
            "enable-confidence-bands": "false",
            "exclude-color": "false",
        })
    _node(table, "rows", text=_shelf_text(plan["rows"], ds.name) if plan["rows"] else None)
    _node(table, "cols", text=_shelf_text(plan["cols"], ds.name) if plan["cols"] else None)
    _node(worksheet, "simple-id", {"uuid": _stable_uuid("worksheet", name)})
    return _to_string(worksheet)


def _percent_units(value: float, label: str) -> int:
    number = float(value)
    if not 0 <= number <= 100:
        raise TableauIntegrationError(
            f"DASHBOARD_LAYOUT_ERROR: {label}={value} di luar 0..100 (persen dari dashboard)",
            code="INVALID_LAYOUT",
        )
    return int(round(number * DASHBOARD_UNITS / 100))


def default_layout(sheet_names: list[str]) -> list[dict[str, float | str]]:
    count = max(1, len(sheet_names))
    height = 100 / count
    return [{"worksheet": sheet, "x": 0, "y": index * height, "w": 100, "h": height} for index, sheet in enumerate(sheet_names)]


def render_dashboard(
    name: str,
    layout: list[dict[str, float | str]],
    size: tuple[int, int] = DEFAULT_DASHBOARD_SIZE,
) -> str:
    dashboard = _node(None, "dashboard", {"enable-sort-zone-taborder": "true", "name": name})
    _node(dashboard, "style")
    _node(dashboard, "size", {"maxheight": size[1], "maxwidth": size[0], "minheight": size[1], "minwidth": size[0]})
    zones = _node(dashboard, "zones")
    outer = _node(zones, "zone", {"h": DASHBOARD_UNITS, "id": 1, "type-v2": "layout-basic", "w": DASHBOARD_UNITS, "x": 0, "y": 0})
    for index, entry in enumerate(layout):
        sheet = str(entry.get("worksheet") or "")
        if not sheet:
            raise TableauIntegrationError("DASHBOARD_LAYOUT_ERROR: setiap zona butuh 'worksheet'", code="INVALID_LAYOUT")
        x, y = float(entry.get("x", 0)), float(entry.get("y", 0))
        w, h = float(entry.get("w", 100)), float(entry.get("h", 100))
        if x + w > 100.0001 or y + h > 100.0001:
            raise TableauIntegrationError(
                f"DASHBOARD_LAYOUT_ERROR: zona '{sheet}' keluar dari batas dashboard (x+w={x + w}, y+h={y + h}; maks 100)",
                code="INVALID_LAYOUT",
            )
        _node(outer, "zone", {
            "h": _percent_units(h, "h"),
            "id": index + 2,
            "name": sheet,
            "w": _percent_units(w, "w"),
            "x": _percent_units(x, "x"),
            "y": _percent_units(y, "y"),
        })
    _node(dashboard, "simple-id", {"uuid": _stable_uuid("dashboard", name)})
    return _to_string(dashboard)


def render_story(name: str, points: list[tuple[str, str]], size: tuple[int, int] = DEFAULT_DASHBOARD_SIZE) -> str:
    if not points:
        raise TableauIntegrationError("STORY_ERROR: story butuh minimal satu point", code="INVALID_LAYOUT")
    dashboard = _node(None, "dashboard", {"name": name, "type": "storyboard"})
    _node(dashboard, "style")
    _node(dashboard, "size", {"maxheight": size[1], "maxwidth": size[0], "minheight": size[1], "minwidth": size[0], "sizing-mode": "fixed"})
    zones = _node(dashboard, "zones")
    outer = _node(zones, "zone", {"h": DASHBOARD_UNITS, "id": 1, "type-v2": "layout-basic", "w": DASHBOARD_UNITS, "x": 0, "y": 0})
    flip = _node(outer, "zone", {"h": DASHBOARD_UNITS, "id": 2, "type-v2": "flipboard", "w": DASHBOARD_UNITS, "x": 0, "y": 0})
    board = _node(flip, "flipboard", {"active-id": 1, "nav-type": "caption", "show-nav-arrows": "true"})
    story_points = _node(board, "story-points")
    for index, (caption, sheet) in enumerate(points):
        _node(story_points, "story-point", {"caption": caption, "captured-sheet": sheet, "id": index + 1})
    _node(dashboard, "simple-id", {"uuid": _stable_uuid("dashboard", name)})
    return _to_string(dashboard)


def _dashboard_sheets(fragment: str | None) -> list[str]:
    if not fragment:
        return []
    element = _from_string(fragment)
    if element.get("type") == "storyboard":
        return []
    return sorted({zone.get("name") for zone in element.iter("zone") if zone.get("name")})


def _window(name: str, kind: str, sheets: list[str] | None = None) -> etree._Element:
    window = _node(None, "window", {"class": kind, "name": name})
    if kind == "worksheet":
        cards = _node(window, "cards")
        left = _node(_node(cards, "edge", {"name": "left"}), "strip", {"size": "160"})
        for card in ("pages", "filters", "marks"):
            _node(left, "card", {"type": card})
        top = _node(cards, "edge", {"name": "top"})
        for size, card in (("2147483647", "columns"), ("2147483647", "rows"), ("31", "title")):
            _node(_node(top, "strip", {"size": size}), "card", {"type": card})
    else:
        viewpoints = _node(window, "viewpoints")
        for sheet in sheets or []:
            _node(viewpoints, "viewpoint", {"name": sheet})
        _node(window, "active", {"id": "-1"})
    _node(window, "simple-id", {"uuid": _stable_uuid("window", f"{kind}:{name}")})
    return window


def _windows_element(workbook: Workbook) -> etree._Element | None:
    sheets = [(w.name, "worksheet") for w in workbook.worksheets] + [(d.name, "dashboard") for d in workbook.dashboards]
    if not sheets:
        return None
    wanted = {name for name, _kind in sheets}
    container = _node(None, "windows", {"source-height": "30"})
    seen: set[str] = set()
    if workbook.windows_xml:
        previous = _from_string(workbook.windows_xml)
        if previous.get("source-height"):
            container.set("source-height", previous.get("source-height"))
        for existing in previous.findall("window"):
            name = existing.get("name", "")
            if name in wanted and name not in seen:
                container.append(existing)
                seen.add(name)
    dashboard_sheets = {d.name: _dashboard_sheets(workbook.dashboards_xml.get(d.name)) for d in workbook.dashboards}
    for name, kind in sheets:
        if name not in seen:
            container.append(_window(name, kind, dashboard_sheets.get(name)))
            seen.add(name)
    return container


def _default_story_sheets(workbook: Workbook) -> list[str]:
    return [d.name for d in workbook.dashboards if not d.is_storyboard] + [w.name for w in workbook.worksheets]


def _unique_name(existing: set[str], base: str) -> str:
    if base not in existing:
        return base
    index = 2
    while f"{base} {index}" in existing:
        index += 1
    return f"{base} {index}"


def add_story(workbook: Workbook, name: str, points: list[str | dict[str, str]]) -> str:
    sheets = _default_story_sheets(workbook)
    if not sheets:
        raise TableauIntegrationError("STORY_ERROR: workbook belum punya worksheet/dashboard untuk di-capture", code="INVALID_LAYOUT")
    known = set(sheets)
    resolved: list[tuple[str, str]] = []
    for index, point in enumerate(points):
        if isinstance(point, dict):
            caption = str(point.get("caption") or f"Point {index + 1}")
            sheet = str(point.get("sheet") or sheets[index % len(sheets)])
        else:
            caption, sheet = str(point), sheets[index % len(sheets)]
        if sheet not in known:
            raise TableauIntegrationError(f"STORY_ERROR: sheet '{sheet}' tidak ada di workbook", code="INVALID_LAYOUT")
        resolved.append((caption, sheet))
    taken = {w.name for w in workbook.worksheets} | {d.name for d in workbook.dashboards}
    story_name = _unique_name(taken, name)
    workbook.dashboards.append(Dashboard(name=story_name, is_storyboard=True))
    workbook.dashboards_xml[story_name] = render_story(story_name, resolved)
    workbook.story_points = [(caption, str(i + 1)) for i, (caption, _sheet) in enumerate(resolved)]
    return story_name


def _manifest_element(workbook: Workbook) -> etree._Element:
    if workbook.document_format_xml:
        preserved = _from_string(workbook.document_format_xml)
        if any(isinstance(child.tag, str) and child.tag != "ManifestByVersion" for child in preserved):
            return preserved
    manifest = _node(None, "document-format-change-manifest")
    for feature in DOCUMENT_FEATURES:
        _node(manifest, feature)
    return manifest


def _preferences_element(workbook: Workbook) -> etree._Element:
    if workbook.preferences_xml:
        return _from_string(workbook.preferences_xml)
    preferences = _node(None, "preferences")
    for key, value in DEFAULT_PREFERENCES:
        _node(preferences, "preference", {"name": key, "value": value})
    return preferences


def _default_explain_data() -> etree._Element:
    explain = _node(None, "explain-data", {"enabled-for-viewer": "false", "extreme-values-enabled-for-all": "false"})
    _node(explain, "explanation-types")
    return explain


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

    for name, spec in worksheets_to_add:
        if name in seen_names:
            raise TableauIntegrationError(
                f"WORKSHEET_CONFLICT: worksheet '{name}' already exists",
                code="WORKSHEET_CONFLICT",
            )
        if not workbook.datasources:
            raise TableauIntegrationError(
                "DS_SOURCE_ERROR: workbook belum punya datasource untuk worksheet baru",
                code="INVALID_DATASET",
            )
        seen_names.add(name)
        fragment = render_worksheet(name, spec, workbook.datasources[0])
        workbook.worksheets.append(Worksheet(name=name, title=name, mark_class=spec.mark_class()))
        workbook.worksheets_xml[name] = fragment

    if story_points:
        add_story(workbook, "Story 1", list(story_points))

    unique: dict[str, Datasource] = {}
    for ds in workbook.datasources:
        unique.setdefault(ds.name, ds)
    if len(unique) != len(workbook.datasources):
        workbook.datasources = list(unique.values())

    meta = workbook.metadata
    build = meta.source_build if meta.source_build and meta.source_build != PLACEHOLDER_BUILD else PRODUCT_BUILD
    platform = meta.source_platform if meta.source_platform in SUPPORTED_PLATFORMS else "win"
    root = etree.Element(
        "workbook",
        {
            "original-version": FORMAT_VERSION,
            "source-build": build,
            "source-platform": platform,
            "version": FORMAT_VERSION,
        },
        nsmap={"user": WORKBOOK_NS},
    )
    sections: dict[str, list[etree._Element]] = {tag: [] for tag in TOP_LEVEL_ORDER}

    sections["document-format-change-manifest"].append(_manifest_element(workbook))

    sections["preferences"].append(_preferences_element(workbook))
    if workbook.style_xml:
        sections["style"].append(_from_string(workbook.style_xml))
    for tag, fragment in workbook.preserved_xml.items():
        if tag in sections and tag not in DROPPED_SECTIONS and fragment:
            sections[tag].append(_from_string(fragment))

    if workbook.datasources:
        container = _node(None, "datasources")
        for ds in workbook.datasources:
            container.append(_from_string(workbook.datasource_xml.get(ds.name) or render_datasource(ds)))
        sections["datasources"].append(container)

    worksheet_fragments = [workbook.worksheets_xml[w.name] for w in workbook.worksheets if workbook.worksheets_xml.get(w.name)]
    if worksheet_fragments:
        container = _node(None, "worksheets")
        for fragment in worksheet_fragments:
            container.append(_from_string(fragment))
        sections["worksheets"].append(container)

    dashboard_fragments = [workbook.dashboards_xml[d.name] for d in workbook.dashboards if workbook.dashboards_xml.get(d.name)]
    if dashboard_fragments:
        container = _node(None, "dashboards")
        for fragment in dashboard_fragments:
            container.append(_from_string(fragment))
        sections["dashboards"].append(container)

    windows = _windows_element(workbook)
    if windows is not None:
        sections["windows"].append(windows)
    if not sections["explain-data"]:
        sections["explain-data"].append(_default_explain_data())

    for tag in TOP_LEVEL_ORDER:
        for element in sections[tag]:
            root.append(element)
    etree.cleanup_namespaces(root, keep_ns_prefixes=["user"])
    return etree.tostring(root, xml_declaration=True, encoding="utf-8", pretty_print=True)


__all__ = [
    "compile_workbook",
    "compile_datasource_from_csv",
    "render_datasource",
    "render_worksheet",
    "render_dashboard",
    "render_story",
    "add_story",
    "default_layout",
    "safe_field_token",
]
