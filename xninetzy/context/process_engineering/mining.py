from __future__ import annotations

import csv
import io
import os
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

MINING_PROVIDER_NAME: str = "native_event_log_miner"
MINING_OPT_IN_ENV: str = "XNINETZY_ENABLE_NATIVE_MINING"


@dataclass(frozen=True, slots=True)
class EventLogRow:
    case_id: str
    activity: str
    timestamp: str
    resource: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "activity": self.activity,
            "timestamp": self.timestamp,
            "resource": self.resource,
        }


@dataclass(frozen=True, slots=True)
class DiscoveryReport:
    case_count: int
    activity_count: int
    activity_frequency: dict[str, int]
    variants: tuple[tuple[str, ...], ...]
    variant_counts: dict[str, int]
    avg_events_per_case: float
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "case_count": self.case_count,
            "activity_count": self.activity_count,
            "activity_frequency": dict(self.activity_frequency),
            "variants": [list(v) for v in self.variants],
            "variant_counts": dict(self.variant_counts),
            "avg_events_per_case": round(self.avg_events_per_case, 4),
            "notes": list(self.notes),
        }


def is_native_mining_enabled() -> bool:
    value = os.environ.get(MINING_OPT_IN_ENV, "").strip().lower()
    return value in ("1", "true", "yes", "on")


def parse_event_log_csv(text: str) -> tuple[EventLogRow, ...]:
    rows: list[EventLogRow] = []
    reader = csv.DictReader(io.StringIO(text))
    required = {"case_id", "activity", "timestamp"}
    if reader.fieldnames is None or not required.issubset(set(reader.fieldnames)):
        missing = required - set(reader.fieldnames or ())
        raise ValueError(f"event log CSV missing required columns: {sorted(missing)}")
    for row in reader:
        rows.append(
            EventLogRow(
                case_id=str(row["case_id"]).strip(),
                activity=str(row["activity"]).strip(),
                timestamp=str(row["timestamp"]).strip(),
                resource=str(row.get("resource", "")).strip() or None,
            )
        )
    return tuple(rows)


def discover_process(rows: tuple[EventLogRow, ...]) -> DiscoveryReport:
    if not rows:
        return DiscoveryReport(
            case_count=0,
            activity_count=0,
            activity_frequency={},
            variants=(),
            variant_counts={},
            avg_events_per_case=0.0,
            notes=("empty event log",),
        )
    cases: dict[str, list[str]] = {}
    activity_freq: Counter[str] = Counter()
    for row in rows:
        cases.setdefault(row.case_id, []).append(row.activity)
        activity_freq[row.activity] += 1
    variants: dict[tuple[str, ...], int] = Counter()
    for sequence in cases.values():
        variants[tuple(sequence)] += 1
    total_events = sum(activity_freq.values())
    avg = total_events / max(len(cases), 1)
    notes: list[str] = []
    if not is_native_mining_enabled():
        notes.append(
            "native mining is opt-in; set XNINETZY_ENABLE_NATIVE_MINING=1 to enable"
        )
    notes.append(
        "PM4Py (AGPL-3.0) is a separate opt-in provider; not bundled"
    )
    return DiscoveryReport(
        case_count=len(cases),
        activity_count=len(activity_freq),
        activity_frequency=dict(activity_freq),
        variants=tuple(variants.keys()),
        variant_counts={",".join(v): c for v, c in variants.items()},
        avg_events_per_case=avg,
        notes=tuple(notes),
    )
