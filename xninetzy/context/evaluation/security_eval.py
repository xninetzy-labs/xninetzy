from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SECURITY_RISK_LOW: str = "low"
SECURITY_RISK_MEDIUM: str = "medium"
SECURITY_RISK_HIGH: str = "high"

VALID_SECURITY_RISKS: frozenset[str] = frozenset(
    {SECURITY_RISK_LOW, SECURITY_RISK_MEDIUM, SECURITY_RISK_HIGH}
)


SECURITY_RISK_INDICATORS: dict[str, float] = {
    "prompt_injection": 0.7,
    "memory_poisoning": 0.8,
    "context_poisoning": 0.6,
    "tool_abuse": 0.7,
    "mcp_poisoning": 0.8,
    "supply_chain": 0.5,
    "credential_leakage": 0.9,
    "unsafe_execution": 0.8,
    "routing_attack": 0.5,
}


@dataclass(frozen=True, slots=True)
class SecurityAudit:
    risk_level: str
    indicators: dict[str, float]
    overall_score: float
    mitigations: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_level": self.risk_level,
            "indicators": {k: round(v, 4) for k, v in self.indicators.items()},
            "overall_score": round(self.overall_score, 4),
            "mitigations": list(self.mitigations),
        }


def evaluate_security(
    *,
    triggered: tuple[str, ...] = (),
    additional_risk: float = 0.0,
) -> SecurityAudit:
    indicators: dict[str, float] = {
        name: SECURITY_RISK_INDICATORS[name]
        for name in triggered
        if name in SECURITY_RISK_INDICATORS
    }
    overall = (sum(indicators.values()) / len(indicators)) if indicators else 0.0
    overall = min(1.0, overall + additional_risk)
    if overall >= 0.7:
        risk_level = SECURITY_RISK_HIGH
    elif overall >= 0.4:
        risk_level = SECURITY_RISK_MEDIUM
    else:
        risk_level = SECURITY_RISK_LOW
    mitigations: list[str] = []
    for indicator in indicators:
        if indicator == "prompt_injection":
            mitigations.append("sanitize untrusted context before model input")
        elif indicator == "memory_poisoning":
            mitigations.append("verify memory provenance before reuse")
        elif indicator == "context_poisoning":
            mitigations.append("validate retrieved context against trusted sources")
        elif indicator == "tool_abuse":
            mitigations.append("enforce side-effect policy gate")
        elif indicator == "mcp_poisoning":
            mitigations.append("sandbox external MCP servers")
        elif indicator == "supply_chain":
            mitigations.append("pin dependency versions and verify hashes")
        elif indicator == "credential_leakage":
            mitigations.append("redact secrets in logs and audit entries")
        elif indicator == "unsafe_execution":
            mitigations.append("require HITL approval for irreversible actions")
        elif indicator == "routing_attack":
            mitigations.append("verify provider trust tiers before routing")
    return SecurityAudit(
        risk_level=risk_level,
        indicators=indicators,
        overall_score=overall,
        mitigations=tuple(mitigations),
    )
