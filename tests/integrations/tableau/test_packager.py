from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.packager import package_twbx


TEMPLATE_PATH = (
    Path(__file__).resolve().parents[3]
    / "xninetzy"
    / "templates"
    / "tableau"
    / "Progres1ya.twb"
)


@pytest.fixture(scope="module")
def template_path() -> Path:
    if not TEMPLATE_PATH.is_file():
        pytest.skip(f"Progres1ya.twb not staged at {TEMPLATE_PATH}")
    return TEMPLATE_PATH


def test_package_twbx_basic(template_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "basic.twbx"
    result = package_twbx(twb_path=template_path, output_path=out)
    assert result.package_path == out
    assert result.workbook_present is True
    with zipfile.ZipFile(out) as zf:
        names = zf.namelist()
        assert template_path.name in names


def test_package_twbx_includes_resources(template_path: Path, tmp_path: Path) -> None:
    extra = tmp_path / "extra.csv"
    extra.write_text("a,b\n1,2\n", encoding="utf-8")
    out = tmp_path / "with_extra.twbx"
    result = package_twbx(
        twb_path=template_path,
        resources=[extra],
        output_path=out,
    )
    assert "extra.csv" in result.entries
    assert "extra.csv" in result.extras_included


def test_package_twbx_missing_source(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError):
        package_twbx(twb_path=tmp_path / "ghost.twb")


def test_package_twbx_missing_resource(template_path: Path, tmp_path: Path) -> None:
    out = tmp_path / "bad.twbx"
    with pytest.raises(TableauIntegrationError):
        package_twbx(
            twb_path=template_path,
            resources=[tmp_path / "no.csv"],
            output_path=out,
        )
