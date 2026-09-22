from __future__ import annotations

import csv
from pathlib import Path

import pytest

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.hyper import (
    extract_csv_to_hyper,
    hyper_available,
    validate_hyper,
)
from xninetzy.integrations.tableau.profiling import profile_csv


def _write_csv(tmp_path: Path, name: str, rows: list[list[str]]) -> Path:
    p = tmp_path / name
    with p.open("w", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(row)
    return p


def test_hyper_unavailable_clean_error(tmp_path: Path) -> None:
    src = _write_csv(tmp_path, "data.csv", [["id", "price"], ["1", "1.5"]])
    dst = tmp_path / "out.hyper"
    if not hyper_available():
        with pytest.raises(TableauIntegrationError) as excinfo:
            extract_csv_to_hyper(src, dst)
        assert excinfo.value.code == "TABLEAU_DEPENDENCY_MISSING"
        assert not dst.exists()


def test_hyper_validate_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError) as excinfo:
        validate_hyper(tmp_path / "absent.hyper")
    assert excinfo.value.code == "ARTIFACT_NOT_FOUND"


def test_hyper_validate_dependency_missing(tmp_path: Path) -> None:
    p = tmp_path / "fake.hyper"
    p.write_bytes(b"\x00\x01\x02")
    if not hyper_available():
        with pytest.raises(TableauIntegrationError) as excinfo:
            validate_hyper(p)
        assert excinfo.value.code == "TABLEAU_DEPENDENCY_MISSING"


def test_hyper_extract_missing_csv(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError) as excinfo:
        extract_csv_to_hyper(tmp_path / "absent.csv", tmp_path / "out.hyper")
    assert excinfo.value.code == "INVALID_DATASET"


def test_hyper_extract_uses_profile(tmp_path: Path) -> None:
    src = _write_csv(
        tmp_path,
        "data.csv",
        [
            ["order_id", "price", "customer_state"],
            ["1", "10.0", "SP"],
            ["2", "20.5", "RJ"],
        ],
    )
    profile = profile_csv(src)
    if not hyper_available():
        with pytest.raises(TableauIntegrationError) as excinfo:
            extract_csv_to_hyper(src, tmp_path / "out.hyper", profile=profile)
        assert excinfo.value.code == "TABLEAU_DEPENDENCY_MISSING"


def test_hyper_extract_with_real_api_if_available(tmp_path: Path) -> None:
    if not hyper_available():
        pytest.skip("tableauhyperapi not installed")
    src = _write_csv(
        tmp_path,
        "data.csv",
        [
            ["id", "price"],
            ["1", "1.5"],
            ["2", "2.5"],
            ["3", "3.5"],
        ],
    )
    dst = tmp_path / "out.hyper"
    record = extract_csv_to_hyper(src, dst)
    assert record.row_count == 3
    assert record.size_bytes > 0
    assert len(record.schema_hash) == 16
    assert dst.exists()
    info = validate_hyper(dst)
    assert info["valid"] is True
    assert info["size_bytes"] > 0
