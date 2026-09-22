from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.parser import (
    WORKBOOK_NS,
    parse_workbook,
    serialize_workbook,
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


def test_parse_template_root_is_workbook(parsed_template: object) -> None:
    assert parsed_template.metadata is not None
    assert parsed_template.metadata.source_platform in {"win", "mac", "linux"}


def test_parse_template_datasources(parsed_template: object) -> None:
    names = parsed_template.datasource_names()
    assert names, "expected at least one datasource in Progres1ya.twb"
    unique = {n for n in names}
    assert len(unique) >= 2


def test_parse_template_worksheets(parsed_template: object) -> None:
    ws_names = parsed_template.worksheet_names()
    assert len(ws_names) >= 5


def test_parse_template_dashboards_include_storyboard(parsed_template: object) -> None:
    db_names = parsed_template.dashboard_names()
    assert len(db_names) >= 2
    assert any(db.is_storyboard for db in parsed_template.dashboards)


def test_parse_template_preserves_xml_fragments(parsed_template: object) -> None:
    for ws in parsed_template.worksheets:
        assert ws.name in parsed_template.worksheets_xml
    for db in parsed_template.dashboards:
        assert db.name in parsed_template.dashboards_xml
    for ds in parsed_template.datasources:
        assert ds.name in parsed_template.datasource_xml


def test_serialize_workbook_roundtrip(parsed_template: object) -> None:
    body = serialize_workbook(parsed_template)
    assert body.startswith(b"<?xml")
    assert WORKBOOK_NS.encode() in body


def test_parse_invalid_root_raises(tmp_path: Path) -> None:
    bad = tmp_path / "bad.twb"
    bad.write_text(
        '<?xml version="1.0" encoding="utf-8"?>'
        "<notworkbook xmlns:user='http://x'/>",
        encoding="utf-8",
    )
    with pytest.raises(TableauIntegrationError):
        parse_workbook(bad)


def test_parse_missing_file_raises(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError):
        parse_workbook(tmp_path / "nope.twb")
