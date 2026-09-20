from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TOOL_PROMOTE: str = "promote"
TOOL_MONITOR: str = "monitor"
TOOL_DEMOTE: str = "demote"
TOOL_REMOVE: str = "remove"

VALID_TOOL_VERDICTS: frozenset[str] = frozenset(
    {TOOL_PROMOTE, TOOL_MONITOR, TOOL_DEMOTE, TOOL_REMOVE}
)


@dataclass(frozen=True, slots=True)
class ToolAudit:
    tool_name: str
    success_rate: float
    latency_ms: float
    cost_score: float
    security_risk: float
    value_score: float
    verdict: str
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_name": self.tool_name,
            "success_rate": round(self.success_rate, 4),
            "latency_ms": round(self.latency_ms, 4),
            "cost_score": round(self.cost_score, 4),
            "security_risk": round(self.security_risk, 4),
            "value_score": round(self.value_score, 4),
            "verdict": self.verdict,
            "notes": list(self.notes),
        }


def evaluate_tool(
    *,
    tool_name: str,
    success_count: int,
    failure_count: int,
    avg_latency_ms: float,
    cost_score: float = 0.5,
    security_risk: float = 0.0,
) -> ToolAudit:
    total = success_count + failure_count
    success_rate = (success_count / total) if total else 0.0
    value_score = success_rate - 0.3 * cost_score - security_risk - min(avg_latency_ms / 10000.0, 0.5)
    notes: list[str] = []
    if success_rate < 0.5 and total >= 5:
        verdict = TOOL_REMOVE
        notes.append("low success rate")
    elif value_score < 0.2 and total >= 3:
        verdict = TOOL_DEMOTE
        notes.append("low value score")
    elif value_score >= 0.6:
        verdict = TOOL_PROMOTE
    else:
        verdict = TOOL_MONITOR
    if security_risk > 0.6:
        notes.append("high security risk — restrict or sandbox")
    if avg_latency_ms > 5000:
        notes.append("high latency")
    return ToolAudit(
        tool_name=tool_name,
        success_rate=success_rate,
        latency_ms=avg_latency_ms,
        cost_score=cost_score,
        security_risk=security_risk,
        value_score=value_score,
        verdict=verdict,
        notes=tuple(notes),
    )
