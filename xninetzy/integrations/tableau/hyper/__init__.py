from __future__ import annotations

import csv
import os
from pathlib import Path
from typing import Any

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    DatasetProfile,
    HyperExtractRecord,
    SchemaColumn,
    _stable_hash,
)


_DATATYPE_MAP = {
    "integer": "BIG_INT",
    "real": "DOUBLE",
    "string": "VARCHAR",
    "boolean": "BOOLEAN",
    "date": "DATE",
    "datetime": "TIMESTAMP",
}


def _import_hyper() -> tuple[Any, Any, Any]:
    try:
        from tableauhyperapi import HyperProcess, TableName, Telemetry  # type: ignore[import-not-found]
    except ImportError as exc:
        raise TableauIntegrationError(
            "TABLEAU_DEPENDENCY_MISSING: tableauhyperapi not installed",
            code="TABLEAU_DEPENDENCY_MISSING",
        ) from exc
    return HyperProcess, TableName, Telemetry


def hyper_available() -> bool:
    try:
        import tableauhyperapi  # type: ignore[import-not-found]  # noqa: F401
        return True
    except ImportError:
        return False


def _hyper_unavailable() -> TableauIntegrationError:
    return TableauIntegrationError(
        "TABLEAU_DEPENDENCY_MISSING: tableauhyperapi not installed",
        code="TABLEAU_DEPENDENCY_MISSING",
    )


def extract_csv_to_hyper(
    csv_path: str | Path,
    extract_path: str | Path,
    *,
    table_name: str = "Extract",
    schema_name: str = "Extract",
    profile: DatasetProfile | None = None,
    row_limit: int | None = None,
) -> HyperExtractRecord:
    src = Path(csv_path)
    dst = Path(extract_path)
    if not src.is_file():
        raise TableauIntegrationError(
            f"INVALID_DATASET: CSV not found at {src}",
            code="INVALID_DATASET",
        )
    if dst.exists() and not os.access(dst, os.W_OK):
        raise TableauIntegrationError(
            f"ARTIFACT_PATH_DENIED: cannot write to {dst}",
            code="ARTIFACT_PATH_DENIED",
        )

    if profile is None:
        from xninetzy.integrations.tableau.profiling import profile_csv
        profile = profile_csv(src)

    columns = profile.columns

    try:
        HyperProcess, TableName = _import_hyper()
    except TableauIntegrationError:
        if dst.exists():
            dst.unlink()
        record = HyperExtractRecord(
            extract_path=str(dst),
            schema_hash="",
            row_count=0,
            columns=columns,
            size_bytes=0,
        )
        record.to_dict()
        raise _hyper_unavailable()

    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        dst.unlink()

    rows_written = 0
    try:
        with HyperProcess(Telemetry.DisableTelemetry) as hyper:
            with hyper.connection() as connection:
                connection.execute_command(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                create_sql = _build_create_sql(table_name, schema_name, columns)
                connection.execute_command(create_sql)
                table_def = TableName(schema_name, table_name)
                rows_to_insert = _read_rows(src, columns, row_limit)
                with connection.execute_insertion(table_def) as insert:
                    for row in rows_to_insert:
                        insert.execute_list([_row_to_hyper_values(row, columns)])
                row_count_result = connection.execute_list_query(
                    f'SELECT COUNT(*) FROM "{schema_name}"."{table_name}"'
                )
                rows_written = int(row_count_result[0][0]) if row_count_result else 0

        size_bytes = dst.stat().st_size if dst.exists() else 0
    except Exception as exc:
        if dst.exists():
            dst.unlink()
        raise TableauIntegrationError(
            f"HYPER_CREATION_FAILED: {exc}",
            code="HYPER_CREATION_FAILED",
        ) from exc

    schema_hash = _stable_hash(
        ("hyper", str(src), tuple((c.name, c.datatype) for c in columns))
    )
    return HyperExtractRecord(
        extract_path=str(dst),
        schema_hash=schema_hash,
        row_count=rows_written,
        columns=columns,
        size_bytes=size_bytes,
    )


def _build_create_sql(table: str, schema: str, columns: list[SchemaColumn]) -> str:
    col_defs = []
    for c in columns:
        h_type = _DATATYPE_MAP.get(c.datatype, "VARCHAR")
        col_defs.append(f'"{c.name}" {h_type}')
    cols_sql = ", ".join(col_defs)
    return f'CREATE TABLE "{schema}"."{table}" ({cols_sql})'


def _row_to_hyper_values(row: list[str], columns: list[SchemaColumn]) -> list[Any]:
    out: list[Any] = []
    for idx, col in enumerate(columns):
        raw = row[idx] if idx < len(row) else ""
        if col.datatype == "integer":
            try:
                out.append(int(raw)) if raw else out.append(None)
            except ValueError:
                out.append(None)
        elif col.datatype == "real":
            try:
                out.append(float(raw)) if raw else out.append(None)
            except ValueError:
                out.append(None)
        elif col.datatype == "boolean":
            v = raw.strip().lower() if raw else ""
            out.append(v in {"true", "t", "yes", "1"})
        else:
            out.append(raw if raw else None)
    return out


def _read_rows(src: Path, columns: list[SchemaColumn], row_limit: int | None) -> list[list[str]]:
    rows: list[list[str]] = []
    with src.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            next(reader)
        except StopIteration:
            return rows
        for idx, row in enumerate(reader):
            if row_limit is not None and idx >= row_limit:
                break
            rows.append(row)
    return rows


def validate_hyper(extract_path: str | Path) -> dict[str, Any]:
    p = Path(extract_path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"ARTIFACT_NOT_FOUND: {p}",
            code="ARTIFACT_NOT_FOUND",
        )
    if not hyper_available():
        raise _hyper_unavailable()

    HyperProcess, _, Telemetry = _import_hyper()

    info: dict[str, Any] = {
        "extract_path": str(p),
        "size_bytes": p.stat().st_size,
        "valid": False,
        "tables": [],
    }
    try:
        with HyperProcess(Telemetry.DisableTelemetry) as hyper:
            with hyper.connection() as connection:
                rows = connection.execute_list_query(
                    "SELECT table_schema, table_name FROM information_schema.tables "
                    "WHERE table_schema NOT IN ('pg_catalog', 'information_schema')"
                )
                for schema_name, table_name in rows:
                    info["tables"].append({"schema": schema_name, "table": table_name})
        info["valid"] = True
    except Exception as exc:
        raise TableauIntegrationError(
            f"HYPER_VALIDATION_FAILED: {exc}",
            code="HYPER_VALIDATION_FAILED",
        ) from exc
    return info


__all__ = [
    "extract_csv_to_hyper",
    "validate_hyper",
    "hyper_available",
]
