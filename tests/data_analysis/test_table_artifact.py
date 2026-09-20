from __future__ import annotations

from pathlib import Path

from xninetzy.context.data_analysis import (
    generate_xlsx_artifact,
    validate_xlsx_artifact,
)


def test_xlsx_round_trip_valid(tmp_path: Path) -> None:
    p = tmp_path / "out.xlsx"
    art = generate_xlsx_artifact(
        path=p,
        name="data",
        rows=[{"a": 1, "b": "x"}, {"a": 2, "b": "y"}],
        source="memory",
        transformation="identity",
    )
    assert art.row_count == 2
    assert art.schema == ("a", "b")
    validated = validate_xlsx_artifact(art)
    assert validated.validation_status == "valid"


def test_xlsx_schema_mismatch_detected(tmp_path: Path) -> None:
    p = tmp_path / "m.xlsx"
    art = generate_xlsx_artifact(path=p, name="x", rows=[{"a": 1}], source="", transformation="")
    with open(p, "wb") as handle:
        from openpyxl import Workbook
        wb = Workbook()
        try:
            ws = wb.active
            ws.append(["different", "columns"])
            ws.append([1, 2])
            wb.save(handle)
        finally:
            wb.close()
    validated = validate_xlsx_artifact(art)
    assert validated.validation_status in {"schema_mismatch", "row_count_mismatch"}


def test_xlsx_missing_file(tmp_path: Path) -> None:
    p = tmp_path / "nope.xlsx"
    art = generate_xlsx_artifact(path=p, name="x", rows=[{"a": 1}], source="", transformation="")
    p.unlink()
    validated = validate_xlsx_artifact(art)
    assert validated.validation_status == "missing"


def test_xlsx_corrupt_file(tmp_path: Path) -> None:
    p = tmp_path / "bad.xlsx"
    art = generate_xlsx_artifact(path=p, name="x", rows=[{"a": 1}], source="", transformation="")
    p.write_text("not a real xlsx")
    validated = validate_xlsx_artifact(art)
    assert validated.validation_status == "corrupt"
