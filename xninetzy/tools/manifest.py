from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from typing import Optional

from xninetzy.os.policy.action_policy import RiskClass, classify_risk


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
    "tableau_publish_workbook": "tableau_publish_workbook",
}

@dataclass(frozen=True, slots=True)
class ToolManifest:
    name: str
    feature_pack: FeaturePack
    risk: RiskClass
    stability: ToolStability
    version: str
    requires_approval: bool
    requires_idempotency: bool
    requires_evidence: bool
    deprecated: bool = False
    replacement: Optional[str] = None
    max_output_bytes: int = 32_768

    def as_dict(self) -> dict[str, object]:
        payload = asdict(self)
        if not self.deprecated:
            payload.pop("deprecated", None)
            payload.pop("replacement", None)
        return payload


def _feature_pack(name: str) -> FeaturePack:
    if name.startswith(("hebat_", "portal_", "qa_", "uacc_")):
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
        version="1.0.0",
        requires_approval=risk is RiskClass.FINAL,
        requires_idempotency=risk in (RiskClass.WRITE, RiskClass.FINAL),
        requires_evidence=_requires_evidence(name),
    )
