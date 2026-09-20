from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class DataFormat(str, Enum):
    CSV = "csv"
    TSV = "tsv"
    XLSX = "xlsx"
    XLS = "xls"
    JSON = "json"
    JSONL = "jsonl"
    PARQUET = "parquet"
    SQLITE = "sqlite"
    UNKNOWN = "unknown"


_XLSX_SIG = b"PK\x03\x04"
_XLS_SIG = b"\xd0\xcf\x11\xe0"
_PARQUET_SIG = b"PAR1"
_SQLITE_SIG = b"SQLite format 3"


def detect_format(path: str | Path) -> DataFormat:
    p = Path(path)
    if not p.exists():
        return DataFormat.UNKNOWN
    suffix = p.suffix.lower().lstrip(".")
    if suffix in {"xlsx"}:
        return DataFormat.XLSX
    if suffix in {"xls"}:
        return DataFormat.XLS
    if suffix == "csv":
        return DataFormat.CSV
    if suffix == "tsv":
        return DataFormat.TSV
    if suffix == "json":
        return DataFormat.JSON
    if suffix == "jsonl":
        return DataFormat.JSONL
    if suffix == "parquet":
        return DataFormat.PARQUET
    if suffix in {"sqlite", "db"}:
        return DataFormat.SQLITE
    try:
        with open(p, "rb") as handle:
            head = handle.read(8)
    except OSError:
        return DataFormat.UNKNOWN
    if head.startswith(_XLSX_SIG):
        return DataFormat.XLSX
    if head.startswith(_XLS_SIG):
        return DataFormat.XLS
    if head.startswith(_PARQUET_SIG):
        return DataFormat.PARQUET
    if head.startswith(_SQLITE_SIG):
        return DataFormat.SQLITE
    return DataFormat.UNKNOWN


def checksum_file(path: str | Path, algorithm: str = "sha256") -> str:
    h = hashlib.new(algorithm)
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


@dataclass(frozen=True, slots=True)
class ColumnProfile:
    name: str
    physical_type: str
    semantic_type: str
    nullable: bool
    unique_count: int
    null_count: int
    example_values: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "physical_type": self.physical_type,
            "semantic_type": self.semantic_type,
            "nullable": self.nullable,
            "unique_count": self.unique_count,
            "null_count": self.null_count,
            "example_values": list(self.example_values),
        }


@dataclass(frozen=True, slots=True)
class DatasetSummary:
    dataset_id: str
    source_uri: str
    format: DataFormat
    row_count: int
    column_count: int
    checksum: str
    columns: tuple[ColumnProfile, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "source_uri": self.source_uri,
            "format": self.format.value,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "checksum": self.checksum,
            "columns": [c.to_dict() for c in self.columns],
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, ensure_ascii=False)


@dataclass(frozen=True, slots=True)
class Dataset:
    dataset_id: str
    source_uri: str
    format: DataFormat
    summary: DatasetSummary
    line_count: int = 0

    @property
    def row_count(self) -> int:
        return self.summary.row_count

    @property
    def column_count(self) -> int:
        return self.summary.column_count

    @property
    def checksum(self) -> str:
        return self.summary.checksum
