from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.integrations.tableau.compiler import (
    compile_datasource_from_csv,
    compile_workbook,
    safe_field_token,
)
from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.parser import parse_workbook
from xninetzy.integrations.tableau.visualizations import (
    SUPPORTED_VISUALIZATIONS,
    compile_visualization,
    parse_visualization,
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


@pytest.mark.parametrize(
    "viz_type",
    sorted(SUPPORTED_VISUALIZATIONS),
)
def test_compile_visualization_supported(viz_type: str) -> None:
    spec = parse_visualization(
        {"type": viz_type, "rows": ["category"], "measure": "value"}
    )
    compiled = compile_visualization(spec)
    assert compiled.mark_class


def test_compile_visualization_unsupported_type() -> None:
    with pytest.raises(TableauIntegrationError):
        parse_visualization({"type": "radial"})


def test_safe_field_token_strips_invalid() -> None:
    assert safe_field_token("My Field!") == "My_Field"
    assert safe_field_token("###") == "field"


def test_compile_workbook_preserves_source(parsed_template: object) -> None:
    body = compile_workbook(parsed_template)
    assert body.startswith(b"<?xml")
    assert b"<datasources>" in body


def test_compile_workbook_appends_worksheet(parsed_template: object) -> None:
    spec = parse_visualization(
        {"type": "bar", "rows": ["federated.col1"], "measure": "value"}
    )
    body = compile_workbook(
        parsed_template,
        worksheets_to_add=(("new_ws", spec),),
    )
    assert b'new_ws' in body
    assert b"<datasources>" in body


def test_compile_workbook_duplicate_worksheet_rejected(parsed_template: object) -> None:
    existing = parsed_template.worksheets[0].name
    spec = parse_visualization({"type": "bar", "measure": "value"})
    with pytest.raises(TableauIntegrationError):
        compile_workbook(
            parsed_template,
            worksheets_to_add=((existing, spec),),
        )


def test_compile_datasource_from_csv(tmp_path: Path) -> None:
    csv = tmp_path / "data.csv"
    csv.write_text("alpha,beta\n1,2\n3,4\n", encoding="utf-8")
    ds = compile_datasource_from_csv(csv_path=str(csv), name="federated.demo")
    assert ds.connection_class == "textscan"
    assert ds.connection_path == str(csv)
    captions = [f.caption for f in ds.fields]
    assert "alpha" in captions
    assert "beta" in captions


def test_compile_workbook_with_story_points(parsed_template: object) -> None:
    body = compile_workbook(
        parsed_template,
        story_points=("intro", "analysis"),
    )
    assert body.startswith(b"<?xml")
