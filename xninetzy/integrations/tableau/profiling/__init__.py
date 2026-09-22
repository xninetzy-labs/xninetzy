from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any

from xninetzy.integrations.tableau.errors import TableauIntegrationError
from xninetzy.integrations.tableau.ir import (
    DatasetProfile,
    SchemaColumn,
    _stable_hash,
)


_SAMPLE_ROWS = 200
_BOOL_TRUE = frozenset({"true", "false", "t", "f", "yes", "no", "0", "1"})

_DATE_HINTS = re.compile(r"(\bdate\b|\bday\b|\bmonth\b|year|created|updated|deleted|purchase|delivery)", re.IGNORECASE)
_GEO_HINTS = re.compile(r"(state|city|country|region|province|zip|postal|latitude|longitude|geo|coord)", re.IGNORECASE)


def _looks_like_int(values: list[str]) -> bool:
    for v in values:
        if not v:
            continue
        try:
            int(v)
        except ValueError:
            return False
    return True


def _looks_like_float(values: list[str]) -> bool:
    for v in values:
        if not v:
            continue
        try:
            float(v)
        except ValueError:
            return False
    return True


def _looks_like_bool(values: list[str]) -> bool:
    lowered = {v.strip().lower() for v in values if v}
    return bool(lowered) and lowered.issubset(_BOOL_TRUE)


def _looks_like_date(values: list[str]) -> bool:
    for v in values:
        if not v:
            continue
        if "-" in v or "/" in v:
            parts = re.split(r"[-/]", v)
            if len(parts) >= 2 and all(p.isdigit() for p in parts):
                return True
        if v.isdigit() and 8 <= len(v) <= 14:
            return True
    return False


def _classify_column(samples: list[str], caption: str = "") -> tuple[str, str, str | None]:
    joined = " ".join(samples)
    if _looks_like_bool(samples):
        return ("boolean", "dimension", None)
    if _looks_like_int(samples):
        return ("integer", "measure", None)
    if _looks_like_float(samples):
        return ("real", "measure", None)
    if _looks_like_date(samples):
        return ("datetime", "dimension", None)
    if _GEO_HINTS.search(caption) or _GEO_HINTS.search(joined):
        return ("string", "dimension", "geo")
    if _DATE_HINTS.search(caption) or _DATE_HINTS.search(joined):
        return ("datetime", "dimension", None)
    return ("string", "dimension", None)


def profile_csv(csv_path: str | Path) -> DatasetProfile:
    p = Path(csv_path)
    if not p.is_file():
        raise TableauIntegrationError(
            f"INVALID_DATASET: CSV not found at {p}",
            code="INVALID_DATASET",
        )
    with p.open("r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration as exc:
            raise TableauIntegrationError(
                f"INVALID_DATASET: empty CSV at {p}",
                code="INVALID_DATASET",
            ) from exc
        if not header or all(not c for c in header):
            raise TableauIntegrationError(
                f"INVALID_DATASET: CSV at {p} has empty header",
                code="INVALID_DATASET",
            )
        samples_per_col: list[list[str]] = [[] for _ in header]
        nulls_per_col: list[int] = [0 for _ in header]
        uniques_per_col: list[set[str]] = [set() for _ in header]
        row_count = 0
        for row in reader:
            row_count += 1
            for idx, value in enumerate(row):
                if idx >= len(samples_per_col):
                    continue
                if value == "" or value is None:
                    nulls_per_col[idx] += 1
                    continue
                if len(samples_per_col[idx]) < _SAMPLE_ROWS:
                    samples_per_col[idx].append(value)
                uniques_per_col[idx].add(value)
            if row_count >= _SAMPLE_ROWS * 4:
                break

    columns: list[SchemaColumn] = []
    duplicates: list[str] = []
    seen_tokens: set[str] = set()
    for raw, samples, nulls, uniques in zip(header, samples_per_col, nulls_per_col, uniques_per_col):
        from xninetzy.integrations.tableau.compiler import safe_field_token
        token = safe_field_token(raw)
        if not token:
            continue
        if token in seen_tokens:
            duplicates.append(token)
            continue
        seen_tokens.add(token)
        datatype, role, semantic_role = _classify_column(samples, raw)
        columns.append(
            SchemaColumn(
                name=token,
                caption=raw,
                datatype=datatype,
                role=role,
                semantic_role=semantic_role,
                null_count=nulls,
                unique_count=len(uniques),
                sample=samples[:5],
            )
        )

    profile = DatasetProfile(
        source_path=str(p),
        row_count=row_count,
        column_count=len(columns),
        columns=columns,
        duplicate_columns=duplicates,
    )
    return profile


def profile_schema_hash(profile: DatasetProfile) -> str:
    parts = tuple((c.name, c.datatype, c.role, c.semantic_role or "") for c in profile.columns)
    return _stable_hash(("csv", profile.source_path, parts))


def profile_to_dict(profile: DatasetProfile) -> dict[str, Any]:
    return profile.to_dict()


__all__ = ["profile_csv", "profile_schema_hash", "profile_to_dict"]
