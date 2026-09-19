from __future__ import annotations

from dataclasses import dataclass

from xninetzy.context.process_engineering.model import (
    ProcessModel,
    validate_process_model,
)


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    code: str
    message: str
    location: str | None = None


@dataclass(frozen=True, slots=True)
class ValidationReport:
    artifact_id: str
    issues: tuple[ValidationIssue, ...]
    passed: bool
    checked_at: str

    def by_severity(self) -> dict[str, list[ValidationIssue]]:
        bucket: dict[str, list[ValidationIssue]] = {
            "structural": [],
            "diagram": [],
            "xml": [],
        }
        for issue in self.issues:
            bucket.setdefault(issue.code.split(":", 1)[0], []).append(issue)
        return bucket


def _issue_for(structure_error: str) -> ValidationIssue:
    return ValidationIssue(code="structural", message=structure_error)


def validate_against_diagram(
    model: ProcessModel,
    *,
    artifact_id: str,
    checked_at: str,
) -> ValidationReport:
    errors = validate_process_model(model)
    issues = tuple(_issue_for(msg) for msg in errors)
    return ValidationReport(
        artifact_id=artifact_id,
        issues=issues,
        passed=not issues,
        checked_at=checked_at,
    )


def validate_against_xml(
    xml_text: str,
    *,
    artifact_id: str,
    checked_at: str,
) -> ValidationReport:
    from xninetzy.context.process_engineering.bpmn_io import parse_bpmn_text

    issues: list[ValidationIssue] = []
    try:
        model = parse_bpmn_text(xml_text)
    except ValueError as exc:
        issues.append(ValidationIssue(code="xml", message=str(exc)))
        return ValidationReport(
            artifact_id=artifact_id,
            issues=tuple(issues),
            passed=False,
            checked_at=checked_at,
        )
    structure_errors = validate_process_model(model)
    issues.extend(_issue_for(msg) for msg in structure_errors)
    return ValidationReport(
        artifact_id=artifact_id,
        issues=tuple(issues),
        passed=not issues,
        checked_at=checked_at,
    )