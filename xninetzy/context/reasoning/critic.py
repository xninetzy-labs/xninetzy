from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


CRITIC_VERDICT_PASS: str = "pass"
CRITIC_VERDICT_WARN: str = "warn"
CRITIC_VERDICT_FAIL: str = "fail"

CRITIC_SEVERITY_INFO: str = "info"
CRITIC_SEVERITY_WARNING: str = "warning"
CRITIC_SEVERITY_BLOCKER: str = "blocker"


@dataclass(frozen=True, slots=True)
class CriticDefect:
    code: str
    severity: str
    message: str
    evidence_refs: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "severity": self.severity,
            "message": self.message,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True, slots=True)
class CriticVerdict:
    verdict: str
    defects: tuple[CriticDefect, ...]
    checked_claims: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    @property
    def has_blocker(self) -> bool:
        return any(d.severity == CRITIC_SEVERITY_BLOCKER for d in self.defects)

    @property
    def is_passing(self) -> bool:
        return self.verdict == CRITIC_VERDICT_PASS and not self.has_blocker

    def to_dict(self) -> dict[str, Any]:
        return {
            "verdict": self.verdict,
            "defects": [d.to_dict() for d in self.defects],
            "checked_claims": list(self.checked_claims),
            "notes": list(self.notes),
        }


def _looks_unsupported(claim: str) -> bool:
    lowered = claim.lower()
    markers = ("probably", "maybe", "i think", "might be", "should be", "i believe")
    return any(marker in lowered for marker in markers)


def critique_outcome(
    *,
    expected: str | None,
    actual: str | None,
    claims: tuple[str, ...] = (),
    evidence_ids: tuple[str, ...] = (),
    missing_evidence_codes: tuple[str, ...] = (),
    contradictions: tuple[str, ...] = (),
    notes: tuple[str, ...] = (),
) -> CriticVerdict:
    defects: list[CriticDefect] = []
    if expected is not None and actual is not None and expected != actual:
        defects.append(
            CriticDefect(
                code="EXPECTATION_MISMATCH",
                severity=CRITIC_SEVERITY_BLOCKER,
                message=f"expected={expected!r} actual={actual!r}",
                evidence_refs=evidence_ids,
            )
        )
    for index, claim in enumerate(claims):
        if not claim or not claim.strip():
            defects.append(
                CriticDefect(
                    code=f"EMPTY_CLAIM_{index}",
                    severity=CRITIC_SEVERITY_WARNING,
                    message="empty claim recorded",
                )
            )
            continue
        if _looks_unsupported(claim):
            defects.append(
                CriticDefect(
                    code=f"UNSUPPORTED_CLAIM_{index}",
                    severity=CRITIC_SEVERITY_WARNING,
                    message=f"claim reads as unsupported: {claim!r}",
                )
            )
    for code in missing_evidence_codes:
        defects.append(
            CriticDefect(
                code=f"MISSING_EVIDENCE_{code}",
                severity=CRITIC_SEVERITY_BLOCKER,
                message=f"required evidence missing: {code}",
                evidence_refs=evidence_ids,
            )
        )
    for contradiction in contradictions:
        defects.append(
            CriticDefect(
                code="CONTRADICTION",
                severity=CRITIC_SEVERITY_BLOCKER,
                message=contradiction,
            )
        )
    if any(d.severity == CRITIC_SEVERITY_BLOCKER for d in defects):
        verdict = CRITIC_VERDICT_FAIL
    elif defects:
        verdict = CRITIC_VERDICT_WARN
    else:
        verdict = CRITIC_VERDICT_PASS
    return CriticVerdict(
        verdict=verdict,
        defects=tuple(defects),
        checked_claims=tuple(claims),
        notes=tuple(notes),
    )
