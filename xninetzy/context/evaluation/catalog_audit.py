from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from xninetzy.context.evaluation.skill_eval import (
    SkillAudit,
    evaluate_skill,
)
from xninetzy.context.evaluation.tool_eval import (
    ToolAudit,
    evaluate_tool,
)


@dataclass(frozen=True, slots=True)
class ToolCatalogAudit:
    name: str
    success_count: int
    failure_count: int
    avg_latency_ms: float
    cost_score: float
    security_risk: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "avg_latency_ms": round(self.avg_latency_ms, 4),
            "cost_score": round(self.cost_score, 4),
            "security_risk": round(self.security_risk, 4),
        }


@dataclass(frozen=True, slots=True)
class SkillCatalogAudit:
    name: str
    invocation_count: int
    success_count: int
    reuse_count: int
    complexity_score: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "invocation_count": self.invocation_count,
            "success_count": self.success_count,
            "reuse_count": self.reuse_count,
            "complexity_score": round(self.complexity_score, 4),
        }


@dataclass(frozen=True, slots=True)
class CatalogAuditReport:
    tool_audits: tuple[ToolAudit, ...]
    skill_audits: tuple[SkillAudit, ...]
    promote_tools: tuple[str, ...]
    remove_tools: tuple[str, ...]
    deprecated_skills: tuple[str, ...]
    notes: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_audits": [a.to_dict() for a in self.tool_audits],
            "skill_audits": [a.to_dict() for a in self.skill_audits],
            "promote_tools": list(self.promote_tools),
            "remove_tools": list(self.remove_tools),
            "deprecated_skills": list(self.deprecated_skills),
            "notes": list(self.notes),
        }


def audit_tool_catalog(
    *,
    tool_metrics: dict[str, dict[str, float]],
) -> tuple[ToolAudit, ...]:
    audits: list[ToolAudit] = []
    for name, metrics in tool_metrics.items():
        audits.append(
            evaluate_tool(
                tool_name=name,
                success_count=int(metrics.get("success", 0)),
                failure_count=int(metrics.get("failure", 0)),
                avg_latency_ms=float(metrics.get("avg_latency_ms", 0.0)),
                cost_score=float(metrics.get("cost_score", 0.5)),
                security_risk=float(metrics.get("security_risk", 0.0)),
            )
        )
    return tuple(audits)


def audit_skill_catalog(
    *,
    skill_metrics: dict[str, dict[str, float]],
) -> tuple[SkillAudit, ...]:
    audits: list[SkillAudit] = []
    for name, metrics in skill_metrics.items():
        audits.append(
            evaluate_skill(
                skill_name=name,
                invocation_count=int(metrics.get("invocation_count", 0)),
                success_count=int(metrics.get("success_count", 0)),
                reuse_count=int(metrics.get("reuse_count", 0)),
                complexity_score=float(metrics.get("complexity_score", 0.5)),
            )
        )
    return tuple(audits)


def synthesize_catalog_report(
    *,
    tool_metrics: dict[str, dict[str, float]] | None = None,
    skill_metrics: dict[str, dict[str, float]] | None = None,
) -> CatalogAuditReport:
    tool_audits = audit_tool_catalog(tool_metrics=tool_metrics or {})
    skill_audits = audit_skill_catalog(skill_metrics=skill_metrics or {})
    from xninetzy.context.evaluation.tool_eval import (
        TOOL_PROMOTE,
        TOOL_REMOVE,
    )
    from xninetzy.context.evaluation.skill_eval import SKILL_DEPRECATED
    promote_tools = tuple(a.tool_name for a in tool_audits if a.verdict == TOOL_PROMOTE)
    remove_tools = tuple(a.tool_name for a in tool_audits if a.verdict == TOOL_REMOVE)
    deprecated_skills = tuple(a.skill_name for a in skill_audits if a.verdict == SKILL_DEPRECATED)
    notes: list[str] = []
    if promote_tools:
        notes.append(f"tools to promote: {list(promote_tools)}")
    if remove_tools:
        notes.append(f"tools to remove: {list(remove_tools)}")
    if deprecated_skills:
        notes.append(f"skills deprecated: {list(deprecated_skills)}")
    return CatalogAuditReport(
        tool_audits=tool_audits,
        skill_audits=skill_audits,
        promote_tools=promote_tools,
        remove_tools=remove_tools,
        deprecated_skills=deprecated_skills,
        notes=tuple(notes),
    )
