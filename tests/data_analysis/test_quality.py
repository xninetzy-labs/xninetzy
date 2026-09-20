from __future__ import annotations

import csv
from pathlib import Path

from xninetzy.context.data_analysis import audit_quality
from xninetzy.context.data_analysis.profiling import profile_csv


def _write_csv(path: Path, rows: list[list]) -> None:
    with open(path, "w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def test_quality_empty_dataset(tmp_path: Path) -> None:
    p = tmp_path / "empty.csv"
    p.write_text("")
    s = profile_csv(p)
    report = audit_quality(s)
    assert report.passed is True
    assert report.scores["completeness"] == 1.0


def test_quality_identifier_duplicates_high_severity(tmp_path: Path) -> None:
    p = tmp_path / "dupes.csv"
    _write_csv(p, [
        ["customer_id", "amount"],
        ["1", "100"],
        ["1", "200"],
        ["2", "50"],
    ])
    s = profile_csv(p)
    types = {c.name: c.semantic_type for c in s.columns}
    assert types["customer_id"] == "identifier"
    report = audit_quality(s)
    issues = [i for i in report.issues if i.dimension.value == "uniqueness"]
    assert any(i.severity == "high" for i in issues)
    assert report.passed is False


def test_quality_scores_dimensions_present(tmp_path: Path) -> None:
    p = tmp_path / "good.csv"
    _write_csv(p, [
        ["id", "value"],
        [1, "a"],
        [2, "b"],
        [3, "c"],
    ])
    s = profile_csv(p)
    report = audit_quality(s)
    assert set(report.scores) == {
        "completeness",
        "validity",
        "uniqueness",
        "consistency",
    }
