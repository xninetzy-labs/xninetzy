from __future__ import annotations

import json
from pathlib import Path

import pytest

from xninetzy.integrations.tableau.parser import WORKBOOK_NS, parse_workbook
from xninetzy.integrations.tableau.validator import (
    ValidationReport,
    validate_workbook,
)


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "xninetzy"
    / "templates"
    / "tableau"
    / "Progres1ya.twb"
)


@pytest.fixture(scope="module")
def parsed_template() -> object:
    if not TEMPLATE_PATH.is_file():
        pytest.skip(f"Progres1ya.twb not staged at {TEMPLATE_PATH}")
    return parse_workbook(TEMPLATE_PATH)


def _write_minimal_twb(path: Path) -> None:
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<workbook xmlns:user="{WORKBOOK_NS}" version="18.1" '
        'source-build="2024.1" source-platform="linux" original-version="18.1">\n'
        "  <datasources>\n"
        '    <datasource name="ds1" caption="ds1" version="18.1">\n'
        '      <connection class="textscan" filename="/tmp/missing.csv"/>\n'
        '      <column name="[cat]" datatype="string" role="dimension"/>\n'
        '      <column name="[val]" datatype="real" role="measure"/>\n'
        "    </datasource>\n"
        "  </datasources>\n"
        "  <worksheets>\n"
        '    <worksheet name="ws1">\n'
        '      <datasource-dependencies datasource="ds1"/>\n'
        "      <table>\n"
        "        <view>\n"
        '          <datasource-dependencies datasource="ds1"/>\n'
        "          <rows/>\n"
        "          <cols/>\n"
        "        </view>\n"
        "        <panes><pane><view/><mark class='Bar'/></pane></panes>\n"
        "      </table>\n"
        "    </worksheet>\n"
        "  </worksheets>\n"
        "  <dashboards>\n"
        '    <dashboard name="dash1">\n'
        '      <zones><zone name="ws1" x="0" y="0" w="100" h="100"/></zones>\n'
        "    </dashboard>\n"
        "  </dashboards>\n"
        "</workbook>\n"
    )
    path.write_text(xml, encoding="utf-8")


def test_validate_minimal_workbook(tmp_path: Path) -> None:
    twb = tmp_path / "mini.twb"
    _write_minimal_twb(twb)
    report = validate_workbook(twb)
    assert isinstance(report, ValidationReport)
    assert report.xml_root_present is True
    assert report.checks["xml"] is True
    assert report.checks["datasources"] is True
    assert report.checks["worksheets"] is True


def test_validate_template_passes(parsed_template: object) -> None:
    report = validate_workbook(TEMPLATE_PATH)
    assert report.checks["serialization_roundtrip"] is True
    assert isinstance(report.to_dict(), dict)
    json.dumps(report.to_dict())


def test_validate_flags_unknown_dashboard_reference(tmp_path: Path) -> None:
    twb = tmp_path / "bad_ref.twb"
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<workbook xmlns:user="{WORKBOOK_NS}" version="18.1" '
        'source-platform="linux">\n'
        "  <datasources>\n"
        '    <datasource name="ds1" caption="ds1" version="18.1">\n'
        '      <column name="[a]" datatype="string" role="dimension"/>\n'
        "    </datasource>\n"
        "  </datasources>\n"
        "  <worksheets>\n"
        '    <worksheet name="ws1">\n'
        '      <datasource-dependencies datasource="ds1"/>\n'
        "    </worksheet>\n"
        "  </worksheets>\n"
        "  <dashboards>\n"
        '    <dashboard name="dash1">\n'
        '      <zones><zone name="ghost_ws" x="0" y="0" w="100" h="100"/></zones>\n'
        "    </dashboard>\n"
        "  </dashboards>\n"
        "</workbook>\n"
    )
    twb.write_text(xml, encoding="utf-8")
    report = validate_workbook(twb)
    assert not report.valid
    assert any("ghost_ws" in err for err in report.errors)


def test_validate_flags_windows_path(tmp_path: Path) -> None:
    twb = tmp_path / "win.twb"
    xml = (
        '<?xml version="1.0" encoding="utf-8"?>\n'
        f'<workbook xmlns:user="{WORKBOOK_NS}" version="18.1" '
        'source-platform="linux">\n'
        "  <datasources>\n"
        '    <datasource name="ds1" caption="ds1" version="18.1">\n'
        '      <connection class="textscan" filename="C:\\\\data\\\\file.csv"/>\n'
        '      <column name="[a]" datatype="string" role="dimension"/>\n'
        "    </datasource>\n"
        "  </datasources>\n"
        "  <worksheets>\n"
        '    <worksheet name="ws1">\n'
        '      <datasource-dependencies datasource="ds1"/>\n'
        "    </worksheet>\n"
        "  </worksheets>\n"
        "  <dashboards/>\n"
        "</workbook>\n"
    )
    twb.write_text(xml, encoding="utf-8")
    report = validate_workbook(twb)
    assert any("stale Windows" in w for w in report.warnings)


def test_validate_handles_parse_error(tmp_path: Path) -> None:
    twb = tmp_path / "broken.twb"
    twb.write_text("not xml", encoding="utf-8")
    report = validate_workbook(twb)
    assert report.valid is False
    assert any("TWB_PARSE_ERROR" in err for err in report.errors)
