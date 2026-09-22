from __future__ import annotations

import csv
import math
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any


_NUMERIC_TYPES = {"numeric", "int", "float", "decimal"}


def _load_numeric_column(path: str, column: str) -> list[float]:
    p = Path(path)
    values: list[float] = []
    if p.suffix.lower() == ".csv":
        with open(p, "r", encoding="utf-8", errors="replace", newline="") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                raw = row.get(column)
                if raw is None or raw == "":
                    continue
                try:
                    values.append(float(raw))
                except ValueError:
                    continue
    return values


@dataclass(frozen=True, slots=True)
class ColumnStatistics:
    column: str
    count: int
    mean: float | None
    median: float | None
    stdev: float | None
    min: float | None
    max: float | None
    p25: float | None
    p75: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "column": self.column,
            "count": self.count,
            "mean": self.mean,
            "median": self.median,
            "stdev": self.stdev,
            "min": self.min,
            "max": self.max,
            "p25": self.p25,
            "p75": self.p75,
        }


def compute_column_stats(values: Sequence[float]) -> ColumnStatistics:
    n = len(values)
    if n == 0:
        return ColumnStatistics(
            column="",
            count=0,
            mean=None,
            median=None,
            stdev=None,
            min=None,
            max=None,
            p25=None,
            p75=None,
        )
    return ColumnStatistics(
        column="",
        count=n,
        mean=statistics.fmean(values),
        median=statistics.median(values),
        stdev=statistics.stdev(values) if n > 1 else 0.0,
        min=min(values),
        max=max(values),
        p25=_percentile(values, 25),
        p75=_percentile(values, 75),
    )


def _percentile(values: Sequence[float], pct: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    rank = (pct / 100.0) * (len(ordered) - 1)
    low = math.floor(rank)
    high = math.ceil(rank)
    if low == high:
        return ordered[int(rank)]
    fraction = rank - low
    return ordered[low] + (ordered[high] - ordered[low]) * fraction


def statistics_for_file(path: str, columns: Iterable[str] | None = None) -> list[dict[str, Any]]:
    """Compute descriptive statistics for numeric columns of a CSV file.

    If ``columns`` is None, all columns are scanned and only numeric-looking
    columns (containing at least one parseable float) are returned.
    """
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(path)
    if p.suffix.lower() != ".csv":
        raise ValueError(f"statistics_for_file currently supports CSV only: {path}")
    columns = list(columns) if columns is not None else None
    if columns is None:
        columns = _csv_header(path)
    out: list[dict[str, Any]] = []
    for column in columns:
        values = _load_numeric_column(path, column)
        if not values:
            continue
        stats = compute_column_stats(values)
        out.append(ColumnStatistics(column=column, **stats.to_dict()).to_dict())
    return out


def _csv_header(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration:
            return []


def correlation_matrix(path: str, columns: Iterable[str] | None = None) -> dict[str, Any]:
    """Compute Pearson correlation between every pair of numeric columns."""
    p = Path(path)
    if p.suffix.lower() != ".csv":
        raise ValueError(f"correlation_matrix currently supports CSV only: {path}")
    chosen = list(columns) if columns is not None else _csv_header(path)
    column_values: dict[str, list[float]] = {}
    for col in chosen:
        column_values[col] = _load_numeric_column(path, col)
    populated = [c for c in chosen if column_values[c]]
    matrix: list[list[float | None]] = []
    for a in populated:
        row: list[float | None] = []
        for b in populated:
            row.append(_pearson(column_values[a], column_values[b]))
        matrix.append(row)
    return {"columns": populated, "matrix": matrix, "count": len(populated)}


def _pearson(xs: Sequence[float], ys: Sequence[float]) -> float | None:
    pairs = [(x, y) for x, y in zip(xs, ys, strict=False) if x is not None and y is not None]
    n = len(pairs)
    if n < 2:
        return None
    sx = sum(p[0] for p in pairs)
    sy = sum(p[1] for p in pairs)
    sxx = sum(p[0] * p[0] for p in pairs)
    syy = sum(p[1] * p[1] for p in pairs)
    sxy = sum(p[0] * p[1] for p in pairs)
    denom = math.sqrt((n * sxx - sx * sx) * (n * syy - sy * sy))
    if denom == 0:
        return None
    return (n * sxy - sx * sy) / denom


__all__ = [
    "ColumnStatistics",
    "compute_column_stats",
    "correlation_matrix",
    "statistics_for_file",
]
