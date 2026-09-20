from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

OUTCOME_AUDIT_PASS: str = "pass"
OUTCOME_AUDIT_PARTIAL: str = "partial"
OUTCOME_AUDIT_INCOMPLETE: str = "incomplete"
OUTCOME_AUDIT_MISLEADING: str = "misleading"

VALID_OUTCOME_AUDITS: frozenset[str] = frozenset(
    {
        OUTCOME_AUDIT_PASS,
        OUTCOME_AUDIT_PARTIAL,
        OUTCOME_AUDIT_INCOMPLETE,
        OUTCOME_AUDIT_MISLEADING,
    }
)


@dataclass(frozen=True, slots=True)
class OutcomeAudit:
    objective: str
    expected: str
    observed: str
    verdict: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "objective": self.objective,
            "expected": self.expected,
            "observed": self.observed,
            "verdict": self.verdict,
            "evidence_refs": list(self.evidence_refs),
            "notes": list(self.notes),
        }


def evaluate_outcome(
    *,
    objective: str,
    expected: str,
    observed: str,
    evidence_refs: tuple[str, ...] = (),
    success_criteria: tuple[str, ...] = (),
    observed_criteria_hits: tuple[str, ...] = (),
) -> OutcomeAudit:
    if success_criteria:
        hit_set = set(observed_criteria_hits)
        missed = [c for c in success_criteria if c not in hit_set]
        if not missed:
            return OutcomeAudit(
                objective=objective,
                expected=expected,
                observed=observed,
                verdict=OUTCOME_AUDIT_PASS,
                evidence_refs=evidence_refs,
                notes=("criteria satisfied",),
            )
        if len(missed) == len(success_criteria):
            return OutcomeAudit(
                objective=objective,
                expected=expected,
                observed=observed,
                verdict=OUTCOME_AUDIT_INCOMPLETE,
                evidence_refs=evidence_refs,
                notes=(f"missed criteria: {missed}",),
            )
        return OutcomeAudit(
            objective=objective,
            expected=expected,
            observed=observed,
            verdict=OUTCOME_AUDIT_PARTIAL,
            evidence_refs=evidence_refs,
            notes=(f"missed criteria: {missed}",),
        )
    if expected == observed:
        return OutcomeAudit(
            objective=objective,
            expected=expected,
            observed=observed,
            verdict=OUTCOME_AUDIT_PASS,
            evidence_refs=evidence_refs,
            notes=("expected == observed",),
        )
    return OutcomeAudit(
        objective=objective,
        expected=expected,
        observed=observed,
        verdict=OUTCOME_AUDIT_PARTIAL,
        evidence_refs=evidence_refs,
        notes=("expected != observed",),
    )
