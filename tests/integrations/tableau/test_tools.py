from __future__ import annotations

import csv
from pathlib import Path

import pytest

from xninetzy.integrations.tableau.server import tsc_available
from xninetzy.tools.ecosystem.tableau_tools import (
    tableau_infer_schema,
    tableau_list_workbooks,
    tableau_profile_dataset,
    tableau_publish_workbook,
    tableau_refresh_workbook,
    tableau_validate_hyper,
)


_SECRET = "SECRET_TOKEN_FOR_TEST_ABC123XYZ_DO_NOT_USE"


def _write_csv(tmp_path: Path, name: str, rows: list[list[str]]) -> Path:
    p = tmp_path / name
    with p.open("w", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(row)
    return p


def _target() -> dict[str, str]:
    return {
        "server_url": "https://tableau.example.com",
        "site_id": "mysite",
        "project": "default",
        "token_name": "alice",
        "token_secret": _SECRET,
    }


def _invoke(tool_obj, **kwargs):
    try:
        return tool_obj.invoke(kwargs)
    except Exception as exc:
        return {"error": getattr(exc, "code", "PROVIDER_ERROR"), "message": str(exc)}


def test_infer_schema_returns_typed_fields(tmp_path: Path) -> None:
    src = _write_csv(
        tmp_path,
        "data.csv",
        [
            ["order_id", "price", "state"],
            ["1", "10.5", "SP"],
            ["2", "20.0", "RJ"],
        ],
    )
    out = _invoke(tableau_infer_schema, csv_path=str(src))
    assert out["row_count"] == 2
    assert out["column_count"] == 3
    fields = {f["name"]: f for f in out["fields"]}
    assert fields["order_id"]["datatype"] == "integer"
    assert fields["price"]["datatype"] == "real"
    assert fields["state"]["datatype"] == "string"
    assert "price" in out["measures"]
    assert "state" in out["dimensions"]


def test_infer_schema_missing_csv(tmp_path: Path) -> None:
    out = _invoke(tableau_infer_schema, csv_path=str(tmp_path / "absent.csv"))
    assert "error" in out


def test_profile_dataset_returns_schema_hash(tmp_path: Path) -> None:
    src = _write_csv(
        tmp_path,
        "data.csv",
        [
            ["id", "amount"],
            ["1", "1.5"],
            ["2", "2.5"],
        ],
    )
    out = _invoke(tableau_profile_dataset, csv_path=str(src))
    assert out["row_count"] == 2
    assert "schema_hash" in out
    assert len(out["schema_hash"]) == 16


def test_profile_dataset_missing_csv(tmp_path: Path) -> None:
    out = _invoke(tableau_profile_dataset, csv_path=str(tmp_path / "absent.csv"))
    assert "error" in out


def test_validate_hyper_missing_path(tmp_path: Path) -> None:
    out = _invoke(tableau_validate_hyper, extract_path=str(tmp_path / "absent.hyper"))
    assert out["error"] == "ARTIFACT_NOT_FOUND"


def test_validate_hyper_dependency_missing(tmp_path: Path) -> None:
    p = tmp_path / "fake.hyper"
    p.write_bytes(b"\x00\x01\x02")
    out = _invoke(tableau_validate_hyper, extract_path=str(p))
    if "error" not in out:
        pytest.skip("hyper available")
    assert out["error"] == "TABLEAU_DEPENDENCY_MISSING"


def test_publish_workbook_missing_dependency(tmp_path: Path) -> None:
    twb = tmp_path / "fake.twb"
    twb.write_text("<workbook/>", encoding="utf-8")
    out = _invoke(tableau_publish_workbook, workbook_path=str(twb), target=_target())
    if "error" not in out:
        pytest.skip("TSC available")
    assert out["error"] in {"TABLEAU_DEPENDENCY_MISSING", "PUBLISH_AUTH_REQUIRED"}


def test_publish_workbook_missing_token_secret(tmp_path: Path) -> None:
    twb = tmp_path / "fake.twb"
    twb.write_text("<workbook/>", encoding="utf-8")
    target = _target()
    target["token_secret"] = ""
    out = _invoke(tableau_publish_workbook, workbook_path=str(twb), target=target)
    assert out["error"] == "PUBLISH_AUTH_REQUIRED"
    assert _SECRET not in str(out)


def test_publish_workbook_missing_file(tmp_path: Path) -> None:
    out = _invoke(
        tableau_publish_workbook,
        workbook_path=str(tmp_path / "absent.twb"),
        target=_target(),
    )
    assert out["error"] == "ARTIFACT_NOT_FOUND"


def test_refresh_workbook_missing_dependency() -> None:
    out = _invoke(tableau_refresh_workbook, workbook_id="wb-1", target=_target())
    if "error" not in out:
        pytest.skip("TSC available")
    assert out["error"] == "TABLEAU_DEPENDENCY_MISSING"


def test_refresh_workbook_missing_id() -> None:
    out = _invoke(tableau_refresh_workbook, workbook_id="", target=_target())
    assert out["error"] == "PROVIDER_ERROR"


def test_refresh_workbook_missing_creds() -> None:
    target = _target()
    target["token_secret"] = ""
    out = _invoke(tableau_refresh_workbook, workbook_id="wb-1", target=target)
    assert out["error"] == "PUBLISH_AUTH_REQUIRED"


def test_list_workbooks_missing_dependency() -> None:
    out = _invoke(tableau_list_workbooks, target=_target())
    if "error" not in out:
        pytest.skip("TSC available")
    assert out["error"] == "TABLEAU_DEPENDENCY_MISSING"


def test_list_workbooks_missing_creds() -> None:
    target = _target()
    target["token_secret"] = ""
    out = _invoke(tableau_list_workbooks, target=target)
    assert out["error"] == "PUBLISH_AUTH_REQUIRED"
