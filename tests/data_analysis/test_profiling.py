from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

from openpyxl import Workbook

from xninetzy.context.data_analysis import detect_format, profile_dataset
from xninetzy.context.data_analysis.profiling import profile_csv, profile_xlsx


def _write_csv(path: Path) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["customer_id", "name", "amount", "created_at"])
        writer.writerow([1, "Alice", 100, "2024-01-01"])
        writer.writerow([2, "Bob", 50, "2024-01-02"])
        writer.writerow([3, "Alice", 100, "2024-01-03"])


def _write_xlsx(path: Path) -> None:
    wb = Workbook()
    try:
        ws = wb.active
        ws.title = "orders"
        ws.append(["sku", "qty", "revenue"])
        ws.append(["A", 10, 100])
        ws.append(["B", 5, 75])
        wb.save(path)
    finally:
        wb.close()


def test_detect_format_by_signature(tmp_path: Path) -> None:
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    assert detect_format(csv_path).value == "csv"
    xlsx_path = tmp_path / "data.xlsx"
    _write_xlsx(xlsx_path)
    assert detect_format(xlsx_path).value == "xlsx"


def test_profile_csv_infers_semantic_types(tmp_path: Path) -> None:
    csv_path = tmp_path / "orders.csv"
    _write_csv(csv_path)
    summary = profile_csv(csv_path)
    assert summary.row_count == 3
    assert summary.column_count == 4
    types = {c.name: c.semantic_type for c in summary.columns}
    assert types["customer_id"] == "identifier"
    types_physical = {c.name: c.physical_type for c in summary.columns}
    assert types_physical["amount"] == "numeric"
    assert types["created_at"] == "temporal"


def test_profile_xlsx(tmp_path: Path) -> None:
    xlsx_path = tmp_path / "orders.xlsx"
    _write_xlsx(xlsx_path)
    summary = profile_xlsx(xlsx_path)
    assert summary.row_count == 2
    assert summary.column_count == 3
    qty = next(c for c in summary.columns if c.name == "qty")
    assert qty.semantic_type == "measure"


def test_profile_dataset_dispatch(tmp_path: Path) -> None:
    csv_path = tmp_path / "x.csv"
    _write_csv(csv_path)
    s = profile_dataset(csv_path)
    assert s.row_count == 3


def test_checksum_changes_on_mutation(tmp_path: Path) -> None:
    p = tmp_path / "d.csv"
    _write_csv(p)
    s1 = profile_csv(p)
    with open(p, "a") as f:
        f.write("4,Carol,75,2024-01-04\n")
    s2 = profile_csv(p)
    assert s1.checksum != s2.checksum
    assert s2.row_count == 4
