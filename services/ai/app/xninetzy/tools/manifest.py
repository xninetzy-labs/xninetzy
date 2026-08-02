from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum

from app.xninetzy.os.policy.action_policy import RiskClass, classify_risk


class ToolStability(StrEnum):
    STABLE = "stable"
    EXPERIMENTAL = "experimental"


class FeaturePack(StrEnum):
    CORE = "core"
    ACADEMIC_UNAIR = "academic-unair"
    RESEARCH = "research"
    CODING = "coding"


_POLICY_ACTIONS = {
    "hebat_upload_submission": "hebat_submit_submission",
    "qa_fill_kuesioner": "qa_submit_kuesioner",
}

@dataclass(frozen=True, slots=True)
class ToolManifest:
    name: str
    feature_pack: FeaturePack
    risk: RiskClass
    stability: ToolStability
    requires_approval: bool
    requires_idempotency: bool
    requires_evidence: bool

    def as_dict(self) -> dict[str, str | bool]:
        return asdict(self)


def _feature_pack(name: str) -> FeaturePack:
    if name.startswith(("hebat_", "portal_", "qa_")):
        return FeaturePack.ACADEMIC_UNAIR
    if name.startswith(("web_", "youtube_", "research_", "deep_research", "pixelrag_")):
        return FeaturePack.RESEARCH
    if name.startswith(("coding_", "ai_provider_")):
        return FeaturePack.CODING
    return FeaturePack.CORE


def _requires_evidence(name: str) -> bool:
    return name.startswith(("knowledge_answer", "deep_research", "research_"))


def manifest_for(name: str) -> ToolManifest:
    risk = classify_risk(_POLICY_ACTIONS.get(name, name))
    return ToolManifest(
        name=name,
        feature_pack=_feature_pack(name),
        risk=risk,
        stability=ToolStability.STABLE,
        requires_approval=risk is RiskClass.FINAL,
        requires_idempotency=risk in (RiskClass.WRITE, RiskClass.FINAL),
        requires_evidence=_requires_evidence(name),
    )
