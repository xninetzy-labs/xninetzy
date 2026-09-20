from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

EVAL_VERDICT_PASS: str = "pass"
EVAL_VERDICT_WARN: str = "warn"
EVAL_VERDICT_FAIL: str = "fail"
EVAL_VERDICT_CRITICAL: str = "critical"


@dataclass(frozen=True, slots=True)
class AuditFindings:
    passed: tuple[str, ...]
    warnings: tuple[str, ...]
    failed: tuple[str, ...]
    critical: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": list(self.passed),
            "warnings": list(self.warnings),
            "failed": list(self.failed),
            "critical": list(self.critical),
        }


@dataclass(frozen=True, slots=True)
class AuditVerdict:
    label: str
    score: float
    findings: AuditFindings

    @property
    def is_critical(self) -> bool:
        return self.label == EVAL_VERDICT_CRITICAL

    @property
    def is_passing(self) -> bool:
        return self.label == EVAL_VERDICT_PASS

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "score": round(self.score, 4),
            "findings": self.findings.to_dict(),
        }


@dataclass(frozen=True, slots=True)
class AuditReport:
    verdicts: tuple[AuditVerdict, ...]
    overall: AuditVerdict
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdicts": [v.to_dict() for v in self.verdicts],
            "overall": self.overall.to_dict(),
            "notes": list(self.notes),
        }


def evaluate_audit_trail(
    *,
    verdicts: tuple[AuditVerdict, ...],
) -> AuditReport:
    if not verdicts:
        empty = AuditVerdict(
            label=EVAL_VERDICT_WARN,
            score=0.0,
            findings=AuditFindings(passed=(), warnings=(), failed=(), critical=()),
        )
        return AuditReport(
            verdicts=(),
            overall=empty,
            notes=("no verdicts",),
        )
    scores = [v.score for v in verdicts]
    avg = sum(scores) / len(scores)
    critical_count = sum(1 for v in verdicts if v.is_critical)
    fail_count = sum(1 for v in verdicts if v.label == EVAL_VERDICT_FAIL)
    warn_count = sum(1 for v in verdicts if v.label == EVAL_VERDICT_WARN)
    passed_count = sum(1 for v in verdicts if v.label == EVAL_VERDICT_PASS)
    if critical_count:
        label = EVAL_VERDICT_CRITICAL
    elif fail_count:
        label = EVAL_VERDICT_FAIL
    elif warn_count and not passed_count:
        label = EVAL_VERDICT_WARN
    elif warn_count:
        label = EVAL_VERDICT_WARN
    else:
        label = EVAL_VERDICT_PASS
    passed_names = tuple(v.findings.passed[0] if v.findings.passed else v.label for v in verdicts if v.label == EVAL_VERDICT_PASS)
    warning_names = tuple(v.label for v in verdicts if v.label == EVAL_VERDICT_WARN)
    failed_names = tuple(v.label for v in verdicts if v.label == EVAL_VERDICT_FAIL)
    critical_names = tuple(v.label for v in verdicts if v.label == EVAL_VERDICT_CRITICAL)
    overall = AuditVerdict(
        label=label,
        score=avg,
        findings=AuditFindings(
            passed=passed_names,
            warnings=warning_names,
            failed=failed_names,
            critical=critical_names,
        ),
    )
    notes: list[str] = []
    if critical_count:
        notes.append(f"{critical_count} critical verdicts")
    notes.append(
        f"verdicts: pass={passed_count} warn={warn_count} fail={fail_count} critical={critical_count}"
    )
    return AuditReport(
        verdicts=verdicts,
        overall=overall,
        notes=tuple(notes),
    )
