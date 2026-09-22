from __future__ import annotations

import csv
from pathlib import Path

import pytest

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.profiling import profile_csv, profile_schema_hash


def _write_csv(tmp_path: Path, rows: list[list[str]]) -> Path:
    p = tmp_path / "fixture.csv"
    with p.open("w", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        for row in rows:
            writer.writerow(row)
    return p


def test_profile_csv_integer_and_float_detection(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        [
            ["id", "price", "category"],
            ["1", "10.50", "a"],
            ["2", "20.00", "b"],
            ["3", "30.25", "a"],
            ["4", "40.10", "c"],
        ],
    )
    profile = profile_csv(p)
    by_name = {c.name: c for c in profile.columns}
    assert by_name["id"].datatype == "integer"
    assert by_name["price"].datatype == "real"
    assert by_name["category"].datatype == "string"
    assert by_name["id"].role == "measure"
    assert by_name["price"].role == "measure"
    assert by_name["category"].role == "dimension"


def test_profile_csv_date_detection(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        [
            ["order_date", "customer_state"],
            ["2024-01-01", "SP"],
            ["2024-01-02", "RJ"],
            ["2024-01-03", "MG"],
        ],
    )
    profile = profile_csv(p)
    by_name = {c.name: c for c in profile.columns}
    assert by_name["order_date"].datatype == "datetime"
    assert by_name["customer_state"].semantic_role == "geo"


def test_profile_csv_duplicate_detection(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        [
            ["category", "category"],
            ["a", "x"],
            ["b", "y"],
        ],
    )
    profile = profile_csv(p)
    assert "category" in profile.duplicate_columns
    by_name = {c.name: c for c in profile.columns}
    assert "category" in by_name


def test_profile_csv_missing_file(tmp_path: Path) -> None:
    with pytest.raises(TableauIntegrationError):
        profile_csv(tmp_path / "absent.csv")


def test_profile_csv_empty(tmp_path: Path) -> None:
    p = _write_csv(tmp_path, [[]])
    with pytest.raises(TableauIntegrationError):
        profile_csv(p)


def test_profile_schema_hash_stable(tmp_path: Path) -> None:
    p = _write_csv(
        tmp_path,
        [
            ["a", "b"],
            ["1", "x"],
            ["2", "y"],
        ],
    )
    profile = profile_csv(p)
    h1 = profile_schema_hash(profile)
    h2 = profile_schema_hash(profile)
    assert h1 == h2
    assert len(h1) == 16
