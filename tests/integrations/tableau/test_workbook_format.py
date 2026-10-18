from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from xninetzy.integrations.tableau import compiler as c
from xninetzy.integrations.tableau import xsd
from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import DOCUMENT_FEATURES, FORMAT_VERSION, Dashboard, Workbook, WorkbookMetadata
from xninetzy.integrations.tableau.profiling import profile_csv
from xninetzy.integrations.tableau.validator import validate_workbook
from xninetzy.integrations.tableau.visualizations import parse_visualization

pytestmark = pytest.mark.skipif(not xsd.available(), reason="lxml atau XSD resmi Tableau tidak tersedia")

CSV_TEXT = (
    "order_id,order_date,order_month,delivery_days_label,customer_state,price,review_score\n"
    "a1,2018-01-02,2018-01,08d,SP,10.5,4\n"
    "a2,2018-01-03,2018-01,09d,RJ,20.0,5\n"
    "a3,2018-02-04,2018-02,10d,SP,5.25,\n"
)


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "orders.csv"
    path.write_text(CSV_TEXT, encoding="utf-8")
    return path


@pytest.fixture
def datasource(csv_file: Path):
    return c.compile_datasource_from_csv(csv_file, name="orders", profile=profile_csv(csv_file))


def _compile(datasource, *specs: tuple[str, dict]) -> tuple[bytes, etree._Element]:
    workbook = Workbook(metadata=WorkbookMetadata())
    workbook.datasources.append(datasource)
    parsed = tuple((name, parse_visualization(spec)) for name, spec in specs)
    c.compile_workbook(workbook, worksheets_to_add=parsed)
    workbook.dashboards.append(Dashboard(name="Board"))
    workbook.dashboards_xml["Board"] = c.render_dashboard("Board", c.default_layout(workbook.worksheet_names()))
    data = c.compile_workbook(workbook)
    return data, etree.fromstring(data)


def _sheet(root: etree._Element, name: str) -> etree._Element:
    return next(ws for ws in root.iter("worksheet") if ws.get("name") == name)


def _instances(sheet: etree._Element) -> dict[str, str]:
    return {el.get("column"): el.get("derivation") for el in sheet.iter("column-instance")}


def test_profiler_types_follow_values_not_column_names(csv_file):
    columns = {col.caption: col.datatype for col in profile_csv(csv_file).columns}
    assert columns["order_date"] == "date"
    assert columns["order_month"] == "string"
    assert columns["delivery_days_label"] == "string"
    assert columns["price"] == "real"


def test_profiler_distinguishes_date_from_datetime(tmp_path):
    path = tmp_path / "t.csv"
    path.write_text("stamp,day\n2018-01-02 10:30:00,2018-01-02\n2018-01-03T08:00:00,2018-01-03\n", encoding="utf-8")
    columns = {col.caption: col.datatype for col in profile_csv(path).columns}
    assert columns == {"stamp": "datetime", "day": "date"}


def test_workbook_declares_real_document_format_and_manifest(datasource):
    _data, root = _compile(datasource, ("K", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}))
    assert root.get("version") == FORMAT_VERSION == "18.1"
    assert root.get("original-version") == "18.1"
    assert root.get("source-platform") == "win"
    assert root.get("source-build") != "0.0.0 (0000.0.0.0)"
    manifest = root.find("document-format-change-manifest")
    assert [child.tag for child in manifest] == list(DOCUMENT_FEATURES)
    assert {"SheetIdentifierTracking", "IntuitiveSorting", "IntuitiveSorting_SP2", "SortTagCleanup"} <= {child.tag for child in manifest}


def test_every_worksheet_uses_simple_id_and_never_legacy_worksheet_number(datasource):
    _data, root = _compile(
        datasource,
        ("A", {"type": "bar", "cols": ["customer_state"], "measure": "price"}),
        ("B", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}),
    )
    for sheet in root.iter("worksheet"):
        assert sheet.find("simple-id") is not None
        assert sheet.find("worksheet-number") is None
        assert sheet.get("number") is None


def test_validator_rejects_invented_manifest_and_incomplete_features(tmp_path, datasource):
    data, _root = _compile(datasource, ("K", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}))
    good = tmp_path / "good.twb"
    good.write_bytes(data)
    report = validate_workbook(good)
    assert report.valid and report.checks["manifest"] is True

    invented = tmp_path / "invented.twb"
    root = etree.fromstring(data)
    manifest = root.find("document-format-change-manifest")
    for child in list(manifest):
        manifest.remove(child)
    etree.SubElement(manifest, "ManifestByVersion")
    invented.write_bytes(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    bad = validate_workbook(invented)
    assert not bad.valid and bad.checks["manifest"] is False
    assert any(error.startswith("TWB_MANIFEST_INVALID") for error in bad.errors)
    assert any(error.startswith("TWB_MANIFEST_INCOMPLETE") for error in bad.errors)

    partial = tmp_path / "partial.twb"
    root = etree.fromstring(data)
    manifest = root.find("document-format-change-manifest")
    manifest.remove(manifest.find("SheetIdentifierTracking"))
    partial.write_bytes(etree.tostring(root, xml_declaration=True, encoding="utf-8"))
    report = validate_workbook(partial)
    assert not report.valid and any("SheetIdentifierTracking" in error for error in report.errors)


def test_generated_workbook_is_valid_for_the_official_schema(datasource):
    data, _root = _compile(
        datasource,
        ("Daily", {"type": "line", "rows": ["order_date"], "measure": "order_id", "measure_aggregation": "COUNTD", "date_level": "day"}),
        ("Months", {"type": "bar", "cols": ["order_month"], "measure": "order_id", "measure_aggregation": "COUNTD"}),
    )
    assert xsd.validate(data) == []
    assert xsd.validate(data, "26.2") == []


def test_countd_min_max_are_honoured_for_text_measures_and_sum_falls_back_to_count(datasource):
    _data, root = _compile(
        datasource,
        ("Distinct", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}),
        ("Maximum", {"type": "kpi", "measure": "order_id", "measure_aggregation": "MAX"}),
        ("Plain", {"type": "kpi", "measure": "order_id", "measure_aggregation": "SUM"}),
    )
    assert _instances(_sheet(root, "Distinct")) == {"[order_id]": "CountD"}
    assert _instances(_sheet(root, "Maximum")) == {"[order_id]": "Max"}
    assert _instances(_sheet(root, "Plain")) == {"[order_id]": "Count"}
    distinct = next(el for el in _sheet(root, "Distinct").iter("column-instance"))
    assert distinct.get("name") == "[ctd:order_id:qk]"


def test_date_level_selects_truncation_and_default_keeps_legacy_behaviour(datasource):
    _data, root = _compile(
        datasource,
        ("Day", {"type": "line", "rows": ["order_date"], "measure": "price", "date_level": "day"}),
        ("Month", {"type": "bar", "cols": ["order_date"], "measure": "price", "date_level": "month"}),
        ("Legacy", {"type": "line", "rows": ["order_date"], "measure": "price"}),
    )
    assert _instances(_sheet(root, "Day"))["[order_date]"] == "Day-Trunc"
    assert _instances(_sheet(root, "Month"))["[order_date]"] == "Month-Trunc"
    assert _instances(_sheet(root, "Legacy"))["[order_date]"] == "Month-Trunc"
    day = next(el for el in _sheet(root, "Day").iter("column-instance") if el.get("column") == "[order_date]")
    assert day.get("name") == "[tdy:order_date:qk]" and day.get("type") == "quantitative"


def test_invalid_date_level_is_rejected():
    with pytest.raises(TableauIntegrationError) as exc:
        parse_visualization({"type": "line", "rows": ["order_date"], "measure": "price", "date_level": "decade"})
    assert "date_level" in str(exc.value)


def test_text_dimensions_never_receive_date_derivations(datasource):
    _data, root = _compile(
        datasource,
        ("Months", {"type": "bar", "cols": ["order_month"], "measure": "order_id", "measure_aggregation": "COUNTD"}),
        ("Labels", {"type": "bar", "cols": ["delivery_days_label"], "measure": "order_id", "measure_aggregation": "COUNTD"}),
    )
    assert _instances(_sheet(root, "Months"))["[order_month]"] == "None"
    assert _instances(_sheet(root, "Labels"))["[delivery_days_label]"] == "None"


def test_time_series_keeps_time_on_columns_and_measure_on_rows(datasource):
    _data, root = _compile(datasource, ("Line", {"type": "line", "rows": ["order_date"], "measure": "price", "date_level": "day"}))
    table = _sheet(root, "Line").find("table")
    assert "tdy:order_date" in table.find("cols").text
    assert "sum:price" in table.find("rows").text


def test_bars_follow_requested_orientation(datasource):
    _data, root = _compile(
        datasource,
        ("Vertical", {"type": "bar", "cols": ["customer_state"], "measure": "price"}),
        ("Horizontal", {"type": "bar", "rows": ["customer_state"], "measure": "price"}),
    )
    vertical = _sheet(root, "Vertical").find("table")
    horizontal = _sheet(root, "Horizontal").find("table")
    assert "none:customer_state" in vertical.find("cols").text and "sum:price" in vertical.find("rows").text
    assert "none:customer_state" in horizontal.find("rows").text and "sum:price" in horizontal.find("cols").text


def test_datasource_follows_object_model_layout(datasource):
    _data, root = _compile(datasource, ("K", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}))
    ds = root.find("datasources/datasource")
    assert ds.get("version") == "18.1"
    relation = ds.find("connection/relation")
    date_column = next(col for col in relation.iter("column") if col.get("name") == "order_date")
    assert date_column.get("datatype") == "date" and date_column.get("date-parse-format") == "yyyy-MM-dd"
    records = ds.findall("connection/metadata-records/metadata-record")
    assert records[0].get("class") == "capability"
    columns = [r for r in records if r.get("class") == "column"]
    assert len(columns) == len(datasource.fields)
    object_ids = {r.findtext("object-id") for r in columns}
    assert len(object_ids) == 1
    object_id = next(iter(object_ids)).strip("[]")
    graph_object = ds.find("object-graph/objects/object")
    assert graph_object.get("id") == object_id
    assert graph_object.find("properties/relation").get("name") == "orders.csv"
    internal = [col for col in ds.findall("column") if col.get("datatype") == "table"]
    assert [col.get("name") for col in internal] == [f"[__tableau_internal_object_id__].[{object_id}]"]
    assert ds.find("layout") is not None


def test_dashboard_window_lists_its_worksheets_and_enables_tab_order(datasource):
    _data, root = _compile(
        datasource,
        ("Zeta", {"type": "bar", "cols": ["customer_state"], "measure": "price"}),
        ("Alpha", {"type": "kpi", "measure": "order_id", "measure_aggregation": "COUNTD"}),
    )
    assert root.find("dashboards/dashboard").get("enable-sort-zone-taborder") == "true"
    window = next(w for w in root.iter("window") if w.get("class") == "dashboard")
    assert [vp.get("name") for vp in window.findall("viewpoints/viewpoint")] == ["Alpha", "Zeta"]


def test_real_tableau_worksheet_layout_is_reproduced(datasource):
    _data, root = _compile(datasource, ("W", {"type": "bar", "cols": ["customer_state"], "measure": "price"}))
    sheet = _sheet(root, "W")
    assert [child.tag for child in sheet] == ["table", "simple-id"]
    assert [child.tag for child in sheet.find("table")] == ["view", "style", "panes", "rows", "cols"]
    assert [child.tag for child in sheet.find("table/view")] == ["datasources", "datasource-dependencies", "aggregation"]
