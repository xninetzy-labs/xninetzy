from __future__ import annotations

from app.xninetzy.os.policy.action_policy import RiskClass
from app.xninetzy.tools.ecosystem.tool_catalog_tools import tool_catalog
from app.xninetzy.tools.manifest import FeaturePack, manifest_for
from app.xninetzy.tools.registry import get_tool_names


def test_manifest_marks_final_academic_actions_as_approval_bound():
    manifest = manifest_for("portal_krs_war_arm")

    assert manifest.feature_pack is FeaturePack.ACADEMIC_UNAIR
    assert manifest.risk is RiskClass.FINAL
    assert manifest.requires_approval is True
    assert manifest.requires_idempotency is True


def test_tool_catalog_is_registered_and_filters_shared_metadata():
    rows = tool_catalog.invoke({"feature_pack": "academic-unair", "risk": "final"})
    names = {row["name"] for row in rows}

    assert "tool_catalog" in get_tool_names()
    assert {"portal_krs_war_arm", "qa_fill_kuesioner", "hebat_upload_submission"} <= names
    assert all(row["requires_approval"] for row in rows)
