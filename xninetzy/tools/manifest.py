from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from functools import lru_cache
import json
from pathlib import Path
from typing import Optional

from xninetzy.os.policy.action_policy import RiskClass


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
    policy_known: bool = True
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


@lru_cache(maxsize=1)
def policy_catalog() -> dict[str, str]:
    """Repository-owned execution policy; never inferred from caller text."""
    payload = json.loads(Path(__file__).with_name("execution_policies.json").read_text())
    policies = payload["tools"]
    if payload["version"] != 1 or not isinstance(policies, dict):
        raise ValueError("Invalid execution policy catalog")
    for name, risk in policies.items():
        if not isinstance(name, str) or risk not in {item.value for item in RiskClass}:
            raise ValueError("Invalid execution policy entry")
    return policies


def manifest_for(name: str) -> ToolManifest:
    policies = policy_catalog()
    risk = RiskClass(policies.get(name, "final"))
    return ToolManifest(
        name=name,
        feature_pack=_feature_pack(name),
        risk=risk,
        stability=ToolStability.STABLE,
        version="1.0.0",
        requires_approval=risk is RiskClass.FINAL,
        requires_idempotency=risk in (RiskClass.WRITE, RiskClass.FINAL),
        requires_evidence=_requires_evidence(name),
        policy_known=name in policies,
    )
