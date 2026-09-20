from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Iterable


class QualityDimension(str, Enum):
    COMPLETENESS = "completeness"
    VALIDITY = "validity"
    UNIQUENESS = "uniqueness"
    CONSISTENCY = "consistency"


@dataclass(frozen=True, slots=True)
class QualityIssue:
    dimension: QualityDimension
    column: str
    severity: str
    description: str
    affected_rows: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "dimension": self.dimension.value,
            "column": self.column,
            "severity": self.severity,
            "description": self.description,
            "affected_rows": self.affected_rows,
        }


@dataclass(frozen=True, slots=True)
class QualityReport:
    dataset_id: str
    row_count: int
    column_count: int
    issues: tuple[QualityIssue, ...]
    scores: dict[str, float]

    @property
    def passed(self) -> bool:
        return all(issue.severity != "high" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "dataset_id": self.dataset_id,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "issues": [i.to_dict() for i in self.issues],
            "scores": dict(self.scores),
            "passed": self.passed,
        }


def _completeness_score(null_counts: Iterable[int], total_rows: int) -> float:
    if total_rows <= 0:
        return 1.0
    total_nulls = sum(null_counts)
    return max(0.0, 1.0 - total_nulls / (total_rows * max(1, len(list(null_counts)))))


def _uniqueness_score(profiles: Iterable[Any]) -> float:
    score = 0.0
    count = 0
    for col in profiles:
        if col.null_count + col.unique_count == 0:
            continue
        unique_ratio = col.unique_count / max(1, col.null_count + col.unique_count)
        if col.semantic_type == "identifier":
            score += min(1.0, unique_ratio)
        else:
            score += min(1.0, unique_ratio)
        count += 1
    return score / max(1, count)


def audit_quality(summary: Any) -> QualityReport:
    issues: list[QualityIssue] = []
    if not summary.columns:
        return QualityReport(
            dataset_id=summary.dataset_id,
            row_count=summary.row_count,
            column_count=summary.column_count,
            issues=(),
            scores={
                QualityDimension.COMPLETENESS.value: 1.0,
                QualityDimension.VALIDITY.value: 1.0,
                QualityDimension.UNIQUENESS.value: 1.0,
                QualityDimension.CONSISTENCY.value: 1.0,
            },
        )
    null_counts = [c.null_count for c in summary.columns]
    completeness = _completeness_score(null_counts, summary.row_count)
    uniqueness = _uniqueness_score(summary.columns)
    validity = 1.0
    consistency = 1.0
    for col in summary.columns:
        if col.null_count == summary.row_count and col.nullable is False:
            issues.append(
                QualityIssue(
                    dimension=QualityDimension.VALIDITY,
                    column=col.name,
                    severity="high",
                    description="non-nullable column is fully null",
                    affected_rows=col.null_count,
                )
            )
            validity -= 0.5
        if col.semantic_type == "identifier":
            total_in_column = col.null_count + col.unique_count + max(
                0, summary.row_count - col.null_count - col.unique_count
            )
            non_null_rows = summary.row_count - col.null_count
            dup_rows = non_null_rows - col.unique_count
            if dup_rows > 0 and total_in_column > 0:
                issues.append(
                    QualityIssue(
                        dimension=QualityDimension.UNIQUENESS,
                        column=col.name,
                        severity="high",
                        description="identifier column has duplicate values",
                        affected_rows=dup_rows,
                    )
                )
                uniqueness -= 0.25
    scores = {
        QualityDimension.COMPLETENESS.value: max(0.0, completeness),
        QualityDimension.VALIDITY.value: max(0.0, validity),
        QualityDimension.UNIQUENESS.value: max(0.0, uniqueness),
        QualityDimension.CONSISTENCY.value: max(0.0, consistency),
    }
    return QualityReport(
        dataset_id=summary.dataset_id,
        row_count=summary.row_count,
        column_count=summary.column_count,
        issues=tuple(issues),
        scores=scores,
    )


def new_dataset_id() -> str:
    return f"ds-{uuid.uuid4().hex[:12]}"
