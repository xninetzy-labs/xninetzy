from __future__ import annotations

from pathlib import Path

import pytest
from lxml import etree

from xninetzy.integrations.tableau import compiler as c
from xninetzy.integrations.tableau import xsd
from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import DOCUMENT_FEATURES, Dashboard, Workbook, WorkbookMetadata
from xninetzy.integrations.tableau.parser import parse_workbook, parse_workbook_bytes
from xninetzy.integrations.tableau.profiling import profile_csv
from xninetzy.integrations.tableau.validator import validate_workbook
from xninetzy.integrations.tableau.visualizations import SUPPORTED_VISUALIZATIONS, parse_visualization
from xninetzy.tools.ecosystem import tableau_tools as tools

pytestmark = pytest.mark.skipif(not xsd.available(), reason="lxml atau XSD resmi Tableau tidak tersedia")

TEMPLATE = Path(__file__).resolve().parents[3] / "xninetzy" / "templates" / "tableau" / "Progres1ya.twb"

TABLEAU_STYLE = """<?xml version='1.0' encoding='utf-8' ?>
<workbook original-version='26.1' source-build='0.0.0 (0000.0.0.0)' source-platform='win' version='26.1' xmlns:user='http://www.tableausoftware.com/xml/user'>
  <document-format-change-manifest><ManifestByVersion /></document-format-change-manifest>
  <preferences><preference name='ui.shelf.height' value='26' /></preferences>
  <datasources>
    <datasource caption='orders' inline='true' name='federated.abc' version='26.1'>
      <connection class='federated'>
        <named-connections>
          <named-connection caption='orders' name='textscan.abc'>
            <connection class='textscan' directory='/data' filename='orders.csv' password='' server='' />
          </named-connection>
        </named-connections>
        <relation connection='textscan.abc' name='orders.csv' table='[orders#csv]' type='table'>
          <columns character-set='UTF-8' header='yes' locale='en_US' separator=','>
            <column datatype='string' name='category' ordinal='0' />
            <column datatype='real' name='sales' ordinal='1' />
          </columns>
        </relation>
        <metadata-records>
          <metadata-record class='column'>
            <remote-name>category</remote-name>
            <local-name>[category]</local-name>
            <local-type>string</local-type>
            <ordinal>0</ordinal>
          </metadata-record>
          <metadata-record class='column'>
            <remote-name>sales</remote-name>
            <local-name>[sales]</local-name>
            <local-type>real</local-type>
            <ordinal>1</ordinal>
          </metadata-record>
        </metadata-records>
      </connection>
      <aliases enabled='yes' />
    </datasource>
  </datasources>
  <worksheets>
    <worksheet name='Sheet 1'>
      <table>
        <view>
          <datasources><datasource caption='orders' name='federated.abc' /></datasources>
          <datasource-dependencies datasource='federated.abc'>
            <column datatype='string' name='[category]' role='dimension' type='nominal' />
            <column datatype='real' name='[sales]' role='measure' type='quantitative' />
            <column-instance column='[category]' derivation='None' name='[none:category:nk]' pivot='key' type='nominal' />
            <column-instance column='[sales]' derivation='Sum' name='[sum:sales:qk]' pivot='key' type='quantitative' />
          </datasource-dependencies>
          <aggregation value='true' />
        </view>
        <style />
        <panes>
          <pane selection-relaxation-option='selection-relaxation-allow'>
            <view><breakdown value='auto' /></view>
            <mark class='Bar' />
          </pane>
        </panes>
        <rows>[federated.abc].[sum:sales:qk]</rows>
        <cols>[federated.abc].[none:category:nk]</cols>
      </table>
      <simple-id uuid='{11111111-1111-4111-8111-111111111111}' />
    </worksheet>
  </worksheets>
  <windows source-height='30'>
    <window class='worksheet' name='Sheet 1'>
      <cards><edge name='left'><strip size='160'><card type='pages' /></strip></edge></cards>
      <simple-id uuid='{33333333-3333-4333-8333-333333333333}' />
    </window>
  </windows>
  <thumbnails><thumbnail height='192' name='Sheet 1' width='192'>AAAA</thumbnail></thumbnails>
  <explain-data enabled-for-viewer='true' extreme-values-enabled-for-all='false'><explanation-types /></explain-data>
</workbook>
"""


@pytest.fixture
def csv_file(tmp_path: Path) -> Path:
    path = tmp_path / "orders.csv"
    path.write_text("category,sales,order_date,Order Note\nA,10.5,2024-01-01,x\nB,20.0,2024-01-02,y\n", encoding="utf-8")
    return path


@pytest.fixture
def workspace(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    for name in ("OUTPUT_DIR", "UNTRACKED_OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR", "RESEARCH_OUTPUT_DIR"):
        monkeypatch.setenv(name, str(tmp_path / "out"))
    monkeypatch.setenv("XNINETZY_TABLEAU_WORKSPACE", str(tmp_path / "out" / "tableau"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()


def _datasource(csv_file: Path):
    return c.compile_datasource_from_csv(csv_file, "Orders", profile=profile_csv(csv_file))


def _workbook(csv_file: Path, version: str = "26.1") -> Workbook:
    workbook = Workbook(metadata=WorkbookMetadata(version=version, original_version=version))
    workbook.datasources.append(_datasource(csv_file))
    return workbook


def _valid(data: bytes, version: str = "26.1") -> list[str]:
    return xsd.validate(data, version)


def test_official_schemas_are_vendored_and_load():
    assert set(xsd.supported_versions()) == {"26.1", "26.2"}
    assert (xsd.SCHEMA_DIR / "LICENSE.tableau-document-schemas.txt").is_file()
    assert xsd.validate(TEMPLATE.read_bytes(), "26.1") == []


def test_shipped_template_is_schema_valid_for_both_versions():
    data = TEMPLATE.read_bytes()
    assert _valid(data, "26.1") == [] and _valid(data, "26.2") == []
    report = validate_workbook(TEMPLATE)
    assert report.valid and report.checks["xsd"] is True


def test_measures_are_typed_from_csv_profile(csv_file):
    ds = _datasource(csv_file)
    fields = {f.caption: f for f in ds.fields}
    assert (fields["sales"].datatype, fields["sales"].role) == ("real", "measure")
    assert (fields["category"].datatype, fields["category"].role) == ("string", "dimension")
    assert fields["Order Note"].name == "[Order Note]" and fields["Order Note"].remote_name == "Order Note"
    assert ds.name == "federated.Orders" and ds.caption == "Orders"


def test_datasource_and_worksheet_carry_required_type_attributes(csv_file):
    workbook = _workbook(csv_file)
    c.compile_workbook(workbook, worksheets_to_add=(("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    data = c.compile_workbook(workbook)
    root = etree.fromstring(data)
    for column in root.iter("column"):
        if column.get("role"):
            assert column.get("type") and column.get("datatype")
    for instance in root.iter("column-instance"):
        assert instance.get("pivot") == "key" and instance.get("type") and instance.get("derivation")
    assert _valid(data) == []


@pytest.mark.parametrize("viz_type", sorted(SUPPORTED_VISUALIZATIONS))
def test_every_supported_visualization_compiles_to_valid_twb(csv_file, viz_type):
    workbook = _workbook(csv_file)
    spec = parse_visualization({"type": viz_type, "cols": ["category"], "measure": "sales"})
    data = c.compile_workbook(workbook, worksheets_to_add=(("Chart", spec),))
    assert _valid(data) == [], viz_type
    assert _valid(data, "26.2") == []


def test_worksheet_options_color_size_label_trendline_and_aggregation(csv_file):
    workbook = _workbook(csv_file)
    spec = parse_visualization({"type": "line", "cols": ["order_date"], "measure": "sales", "measure_aggregation": "AVG", "color": "category", "size": "sales", "label": "category", "trend_line": True})
    data = c.compile_workbook(workbook, worksheets_to_add=(("Trend", spec),))
    assert _valid(data) == []
    root = etree.fromstring(data)
    assert [e.tag for e in root.find(".//pane/encodings")] == ["color", "size", "text"]
    assert root.find(".//pane/trendline").get("enabled") == "true"
    names = {i.get("name") for i in root.iter("column-instance")}
    assert {"[avg:sales:qk]", "[tmn:order_date:qk]", "[none:category:nk]"} <= names
    assert root.find(".//table/rows").text == "[federated.Orders].[avg:sales:qk]"


def test_measure_goes_to_columns_for_horizontal_bar(csv_file):
    data = c.compile_workbook(_workbook(csv_file), worksheets_to_add=(("H", parse_visualization({"type": "bar", "rows": ["category"], "measure": "sales"})),))
    root = etree.fromstring(data)
    assert root.find(".//table/rows").text == "[federated.Orders].[none:category:nk]"
    assert root.find(".//table/cols").text == "[federated.Orders].[sum:sales:qk]"
    assert _valid(data) == []


def test_unknown_fields_and_unsupported_options_are_rejected_not_dropped(csv_file):
    workbook = _workbook(csv_file)
    with pytest.raises(TableauIntegrationError) as missing:
        c.render_worksheet("S", parse_visualization({"type": "bar", "rows": ["nope"], "measure": "sales"}), workbook.datasources[0])
    assert missing.value.code == "FIELD_NOT_FOUND" and "category" in str(missing.value)
    with pytest.raises(TableauIntegrationError):
        c.render_worksheet("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales", "top_n": 5}), workbook.datasources[0])
    with pytest.raises(TableauIntegrationError):
        c.render_worksheet("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales", "trend_line": True}), workbook.datasources[0])
    with pytest.raises(TableauIntegrationError):
        c.render_worksheet("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales", "measure_aggregation": "STDEV"}), workbook.datasources[0])


def test_fields_resolve_by_caption_token_or_bracketed_name(csv_file):
    ds = _datasource(csv_file)
    assert ds.find_field("Order Note") is ds.find_field("[Order Note]") is ds.find_field("order_note")
    assert ds.find_field("missing") is None


def test_names_with_xml_special_characters_stay_well_formed(csv_file):
    workbook = _workbook(csv_file)
    nasty = 'Sales "Q1" & <Q2> \'x\''
    c.compile_workbook(workbook, worksheets_to_add=((nasty, parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    workbook.dashboards.append(Dashboard(name='Dash "A" & B'))
    workbook.dashboards_xml['Dash "A" & B'] = c.render_dashboard('Dash "A" & B', c.default_layout([nasty]))
    data = c.compile_workbook(workbook)
    root = etree.fromstring(data)
    assert root.find(".//worksheet").get("name") == nasty
    assert root.find(".//dashboard/zones/zone/zone").get("name") == nasty
    assert _valid(data) == []


def test_document_structure_follows_schema_order_and_required_sections(csv_file):
    workbook = _workbook(csv_file)
    data = c.compile_workbook(workbook, worksheets_to_add=(("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    root = etree.fromstring(data)
    tags = [child.tag for child in root]
    assert tags == ["document-format-change-manifest", "preferences", "datasources", "worksheets", "windows", "explain-data"]
    assert root.get("version") == "18.1" and root.get("original-version") == "18.1"
    assert root.find("document-format-change-manifest/ManifestByVersion") is None
    assert [child.tag for child in root.find("document-format-change-manifest")] == list(DOCUMENT_FEATURES)
    assert root.nsmap["user"] == "http://www.tableausoftware.com/xml/user"


def test_compile_is_idempotent_and_roundtrips_byte_for_byte(csv_file):
    workbook = _workbook(csv_file)
    c.compile_workbook(workbook, worksheets_to_add=(("S", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    workbook.dashboards.append(Dashboard(name="D"))
    workbook.dashboards_xml["D"] = c.render_dashboard("D", c.default_layout(["S"]))
    c.add_story(workbook, "Story", ["One"])
    first = c.compile_workbook(workbook)
    second = c.compile_workbook(parse_workbook_bytes(first))
    assert first == second
    assert c.compile_workbook(workbook) == first


def test_document_format_version_resolves_to_latest_official_schema(csv_file):
    data = c.compile_workbook(_workbook(csv_file, "26.2"))
    assert etree.fromstring(data).get("version") == "18.1"
    assert xsd.declared_version(data) == "18.1"
    assert xsd.resolve_version("18.1") == "26.2"
    assert _valid(data, "26.2") == []
    assert _valid(data, "18.1") == []


def test_parser_reads_single_quoted_tableau_workbooks_without_losing_content(tmp_path):
    path = tmp_path / "real.twb"
    path.write_text(TABLEAU_STYLE, encoding="utf-8")
    workbook = parse_workbook(path)
    assert workbook.datasource_names() == ["federated.abc"]
    assert workbook.worksheet_names() == ["Sheet 1"]
    assert workbook.worksheets[0].mark_class == "Bar"
    assert [(f.caption, f.datatype, f.role) for f in workbook.datasources[0].fields] == [("category", "string", "dimension"), ("sales", "real", "measure")]
    assert workbook.datasources[0].connection_path == "/data/orders.csv"
    assert "worksheet" in workbook.worksheets_xml["Sheet 1"] and "rows" in workbook.worksheets_xml["Sheet 1"]
    rebuilt = c.compile_workbook(workbook)
    assert _valid(rebuilt) == []
    root = etree.fromstring(rebuilt)
    assert root.find(".//worksheet/table/rows").text == "[federated.abc].[sum:sales:qk]"
    assert root.find(".//datasource/connection/metadata-records") is not None
    assert root.find("thumbnails") is None
    assert root.find("explain-data").get("enabled-for-viewer") == "true"


def test_parser_only_reads_top_level_datasources_and_worksheets(tmp_path):
    path = tmp_path / "real.twb"
    path.write_text(TABLEAU_STYLE, encoding="utf-8")
    workbook = parse_workbook(path)
    assert len(workbook.datasources) == 1


def test_new_worksheets_and_dashboards_get_windows_and_dropped_ones_lose_them(tmp_path, csv_file):
    path = tmp_path / "real.twb"
    path.write_text(TABLEAU_STYLE, encoding="utf-8")
    workbook = parse_workbook(path)
    c.compile_workbook(workbook, worksheets_to_add=(("Second", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    workbook.dashboards.append(Dashboard(name="Dash"))
    workbook.dashboards_xml["Dash"] = c.render_dashboard("Dash", c.default_layout(["Sheet 1", "Second"]))
    data = c.compile_workbook(workbook)
    windows = {(w.get("class"), w.get("name")) for w in etree.fromstring(data).iter("window")}
    assert windows == {("worksheet", "Sheet 1"), ("worksheet", "Second"), ("dashboard", "Dash")}
    assert _valid(data) == []
    workbook.worksheets = [w for w in workbook.worksheets if w.name != "Second"]
    workbook.dashboards = []
    remaining = {w.get("name") for w in etree.fromstring(c.compile_workbook(workbook)).iter("window")}
    assert remaining == {"Sheet 1"}


def test_dashboard_zones_have_unique_ids_and_bounded_percent_coordinates():
    xml = c.render_dashboard("D", [{"worksheet": "A", "x": 0, "y": 0, "w": 60, "h": 100}, {"worksheet": "B", "x": 60, "y": 0, "w": 40, "h": 100}])
    root = etree.fromstring(xml)
    zones = list(root.iter("zone"))
    assert len({z.get("id") for z in zones}) == len(zones)
    inner = [z for z in zones if z.get("name")]
    assert [(z.get("x"), z.get("w")) for z in inner] == [("0", "60000"), ("60000", "40000")]
    with pytest.raises(TableauIntegrationError) as bad:
        c.render_dashboard("D", [{"worksheet": "A", "x": 50, "w": 80}])
    assert bad.value.code == "INVALID_LAYOUT"
    with pytest.raises(TableauIntegrationError):
        c.render_dashboard("D", [{"worksheet": "A", "h": 150}])


def test_story_points_capture_real_sheets_and_are_emitted(csv_file):
    workbook = _workbook(csv_file)
    c.compile_workbook(workbook, worksheets_to_add=(("A", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})), ("B", parse_visualization({"type": "pie", "cols": ["category"], "measure": "sales"}))))
    name = c.add_story(workbook, "Narrative", ["Intro", {"caption": "Deep dive", "sheet": "B"}, "Wrap"])
    data = c.compile_workbook(workbook)
    root = etree.fromstring(data)
    points = [(p.get("caption"), p.get("captured-sheet"), p.get("id")) for p in root.iter("story-point")]
    assert points == [("Intro", "A", "1"), ("Deep dive", "B", "2"), ("Wrap", "A", "3")]
    assert root.find(f".//dashboard[@name='{name}']").get("type") == "storyboard"
    assert _valid(data) == []
    with pytest.raises(TableauIntegrationError):
        c.add_story(workbook, "Bad", [{"caption": "x", "sheet": "Ghost"}])
    with pytest.raises(TableauIntegrationError):
        c.add_story(Workbook(metadata=WorkbookMetadata()), "Empty", ["x"])


def test_story_points_argument_of_compile_workbook_creates_a_story(csv_file):
    workbook = _workbook(csv_file)
    c.compile_workbook(workbook, worksheets_to_add=(("A", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    data = c.compile_workbook(workbook, story_points=("One", "Two"))
    assert [p.get("caption") for p in etree.fromstring(data).iter("story-point")] == ["One", "Two"]


def test_validator_reports_xsd_errors_dangling_refs_and_legacy_versions(tmp_path, csv_file):
    good = tmp_path / "good.twb"
    good.write_bytes(c.compile_workbook(_workbook(csv_file)))
    assert validate_workbook(good).checks["xsd"] is True

    broken = tmp_path / "broken.twb"
    text = good.read_text(encoding="utf-8").replace('type="nominal"', "", 1)
    broken.write_text(text, encoding="utf-8")
    report = validate_workbook(broken)
    assert not report.valid and report.checks["xsd"] is False
    assert any(e.startswith("TWB_XSD_ERROR: Error(") and "'type'" in e for e in report.errors)

    legacy = tmp_path / "legacy.twb"
    legacy.write_text(TABLEAU_STYLE.replace("26.1", "10.5"), encoding="utf-8")
    old = validate_workbook(legacy)
    assert old.checks["xsd"] == "NOT_ASSESSED" and any("TWB_XSD_NOT_ASSESSED" in w for w in old.warnings)

    dangling = tmp_path / "dangling.twb"
    workbook = _workbook(csv_file)
    c.compile_workbook(workbook, worksheets_to_add=(("A", parse_visualization({"type": "bar", "cols": ["category"], "measure": "sales"})),))
    workbook.dashboards.append(Dashboard(name="D"))
    workbook.dashboards_xml["D"] = c.render_dashboard("D", [{"worksheet": "Ghost", "x": 0, "y": 0, "w": 100, "h": 100}])
    dangling.write_bytes(c.compile_workbook(workbook))
    ref = validate_workbook(dangling)
    assert not ref.valid and any("TWB_DANGLING_DASHBOARD_REF" in e for e in ref.errors)


def test_xsd_validate_rejects_malformed_and_unknown_versions():
    assert xsd.validate(b"<workbook", "26.1")[0].startswith("Error(0,0)")
    with pytest.raises(KeyError):
        xsd.validate(b"<workbook/>", "10.5")


def _call(tool, **kwargs):
    return tool.invoke(kwargs)


def test_generate_tool_profiles_types_validates_output_and_builds_dashboard_and_story(workspace, csv_file):
    result = _call(tools.tableau_workbook_generate, csv_paths=[str(csv_file)], name="My Report", visualizations=[
        {"type": "bar", "cols": ["category"], "measure": "sales", "name": "Sales by category"},
        {"type": "line", "cols": ["order_date"], "measure": "sales"},
    ], story_points=["Intro", "Trend"])
    assert result["validation"] == {"valid": True, "xsd": True, "xsd_version": "26.2", "error_count": 0, "errors": [], "warnings": []}
    assert result["worksheets"] == ["Sales by category", "ws_2"]
    assert result["dashboards"] == ["Auto Dashboard", "Story 1"]
    root = etree.fromstring(Path(result["path"]).read_bytes())
    sales = next(col for col in root.find("datasources/datasource").findall("column") if col.get("name") == "[sales]")
    assert (sales.get("role"), sales.get("datatype"), sales.get("type")) == ("measure", "real", "quantitative")


def test_generate_tool_reports_bad_fields_versions_and_missing_csv(workspace, csv_file):
    bad = _call(tools.tableau_workbook_generate, csv_paths=[str(csv_file)], name="Bad", visualizations=[{"type": "bar", "rows": ["nope"], "measure": "sales"}])
    assert bad["error"] == "FIELD_NOT_FOUND" and "nope" in bad["message"]
    assert _call(tools.tableau_workbook_generate, csv_paths=[str(csv_file)], name="V", visualizations=[], tableau_version="18.1")["error"] == "unsupported_version"
    assert _call(tools.tableau_workbook_generate, csv_paths=["/nope.csv"], name="V", visualizations=[])["error"] == "missing_csv"


def test_generate_tool_supports_version_26_2(workspace, csv_file):
    result = _call(tools.tableau_workbook_generate, csv_paths=[str(csv_file)], name="V2", visualizations=[{"type": "bar", "cols": ["category"], "measure": "sales"}], tableau_version="26.2")
    assert result["validation"]["xsd_version"] == "26.2" and result["validation"]["valid"] is True


@pytest.fixture
def generated(workspace, csv_file) -> str:
    result = _call(tools.tableau_workbook_generate, csv_paths=[str(csv_file)], name="Base", visualizations=[
        {"type": "bar", "cols": ["category"], "measure": "sales", "name": "Bars"},
    ])
    return result["path"]


def test_worksheet_create_and_modify_keep_the_workbook_valid(generated):
    created = _call(tools.tableau_worksheet_create, workbook_path=generated, worksheet_name="Pie", visualization={"type": "pie", "cols": ["category"], "measure": "sales"})
    assert created["validation"]["valid"] and "Pie" in created["worksheets"]
    modified = _call(tools.tableau_worksheet_modify, workbook_path=generated, worksheet_name="Pie", visualization={"type": "bar", "cols": ["category"], "measure": "sales", "measure_aggregation": "MAX"})
    assert modified["validation"]["valid"]
    assert "[max:sales:qk]" in Path(generated).read_text(encoding="utf-8")
    assert _call(tools.tableau_worksheet_create, workbook_path=generated, worksheet_name="Pie", visualization={"type": "bar", "cols": ["category"], "measure": "sales"})["error"] == "duplicate_worksheet"
    assert _call(tools.tableau_worksheet_create, workbook_path=generated, worksheet_name="X", visualization={"type": "bar", "cols": ["ghost"]})["error"] == "FIELD_NOT_FOUND"
    assert _call(tools.tableau_worksheet_modify, workbook_path=generated, worksheet_name="Ghost", visualization={"type": "bar"})["error"] == "not_found"


def test_dashboard_create_and_layout_preserve_size_and_reject_bad_layouts(generated):
    created = _call(tools.tableau_dashboard_create, workbook_path=generated, dashboard_name="Exec", worksheets=["Bars"], layout=[{"worksheet": "Bars", "x": 0, "y": 0, "w": 100, "h": 100}])
    assert created["validation"]["valid"] and "Exec" in created["dashboards"]
    assert _call(tools.tableau_dashboard_create, workbook_path=generated, dashboard_name="Exec", worksheets=["Bars"])["error"] == "duplicate_dashboard"
    assert _call(tools.tableau_dashboard_create, workbook_path=generated, dashboard_name="Y", worksheets=["Ghost"])["error"] == "unknown_worksheet"
    assert _call(tools.tableau_dashboard_layout, workbook_path=generated, dashboard_name="Exec", layout=[{"worksheet": "Bars", "x": 20, "w": 90}])["error"] == "INVALID_LAYOUT"
    updated = _call(tools.tableau_dashboard_layout, workbook_path=generated, dashboard_name="Exec", layout=[{"worksheet": "Bars", "x": 0, "y": 0, "w": 50, "h": 50}])
    assert updated["validation"]["valid"]
    dash = etree.fromstring(Path(generated).read_bytes()).find(".//dashboard[@name='Exec']")
    assert dash.find("size").get("maxwidth") == "1200"
    assert dash.find(".//zone[@name='Bars']").get("w") == "50000"
    assert _call(tools.tableau_dashboard_layout, workbook_path=generated, dashboard_name="Ghost", layout=[])["error"] == "not_found"
    assert _call(tools.tableau_dashboard_layout, workbook_path=generated, dashboard_name="Exec", layout=[{"worksheet": "Ghost"}])["error"] == "unknown_worksheet"


def test_story_create_tool_actually_writes_story_points(generated):
    result = _call(tools.tableau_story_create, workbook_path=generated, story_name="Board", points=["One", {"caption": "Two", "sheet": "Bars"}])
    assert result["validation"]["valid"] and result["story"] == "Board" and result["story_points"] == ["One", "Two"]
    points = [(p.get("caption"), p.get("captured-sheet")) for p in etree.fromstring(Path(generated).read_bytes()).iter("story-point")]
    assert points == [("One", "Auto Dashboard"), ("Two", "Bars")]
    assert _call(tools.tableau_story_create, workbook_path=generated, story_name="Bad", points=[{"caption": "x", "sheet": "Ghost"}])["error"] == "INVALID_LAYOUT"


def test_datasource_replace_renames_fields_and_refuses_broken_results(generated, tmp_path):
    other = tmp_path / "other.csv"
    other.write_text("segment,revenue,order_date\nX,1.5,2024-02-01\n", encoding="utf-8")
    refused = _call(tools.tableau_datasource_replace, workbook_path=generated, csv_path=str(other))
    assert refused["error"] == "fields_missing_in_new_datasource" and set(refused["fields"]) == {"[category]", "[sales]"}
    assert "[none:category:nk]" in Path(generated).read_text(encoding="utf-8")
    assert _call(tools.tableau_datasource_replace, workbook_path=generated, csv_path=str(other), field_map={"category": "ghost"})["error"] == "field_map_target_missing"
    done = _call(tools.tableau_datasource_replace, workbook_path=generated, csv_path=str(other), field_map={"category": "segment", "sales": "revenue"})
    assert done["validation"]["valid"] and done["missing_fields"] == []
    text = Path(generated).read_text(encoding="utf-8")
    assert "[none:segment:nk]" in text and "[sum:revenue:qk]" in text and "[sum:sales:qk]" not in text
    revenue = next(col for col in etree.fromstring(text.encode()).find("datasources/datasource").findall("column") if col.get("name") == "[revenue]")
    assert revenue.get("role") == "measure"


def test_datasource_replace_can_be_forced_with_missing_fields(generated, tmp_path):
    other = tmp_path / "other.csv"
    other.write_text("x,y\n1,2\n", encoding="utf-8")
    forced = _call(tools.tableau_datasource_replace, workbook_path=generated, csv_path=str(other), allow_missing_fields=True)
    assert set(forced["missing_fields"]) == {"[category]", "[sales]"}


def test_twb_export_round_trip_stays_valid(generated, tmp_path):
    out = _call(tools.tableau_twb_export, workbook_path=generated, target_path=str(tmp_path / "out" / "exported.twb"))
    assert xsd.validate(Path(out["path"]).read_bytes()) == []


def test_doctype_and_entities_are_rejected_everywhere(tmp_path):
    hostile = b'<?xml version="1.0"?><!DOCTYPE w [<!ENTITY a "AAAA">]><workbook version="26.1" source-build="x" original-version="26.1">&a;</workbook>'
    assert xsd.validate(hostile, "26.1")[0].startswith("Error(0,0): DOCTYPE")
    with pytest.raises(TableauIntegrationError, match="DOCTYPE"):
        parse_workbook_bytes(hostile)
    path = tmp_path / "hostile.twb"
    path.write_bytes(hostile)
    report = validate_workbook(path)
    assert not report.valid and any("DOCTYPE" in e for e in report.errors)
