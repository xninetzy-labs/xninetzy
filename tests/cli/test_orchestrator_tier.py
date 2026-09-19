from __future__ import annotations

from xninetzy.cli.orchestrator import _effective_tier
from xninetzy.os.policy.action_policy import RiskClass


def test_effective_tier_uses_manifest_for_write_tool() -> None:
    assert _effective_tier("obsidian_create", 0) >= 1


def test_effective_tier_uses_manifest_for_read_tool() -> None:
    from xninetzy.tools.manifest import manifest_for
    from xninetzy.cli.orchestrator import _RISK_TO_TIER
    m = manifest_for("list_notes")
    expected = _RISK_TO_TIER[m.risk]
    assert _effective_tier("list_notes", 0) == expected


def test_effective_tier_takes_max_of_declared_and_manifest() -> None:
    assert _effective_tier("list_notes", 3) == 3


def test_effective_tier_unknown_tool_falls_back_to_declared() -> None:
    assert _effective_tier("definitely_not_a_real_tool_xyz", 1) == 1


def test_effective_tier_blocks_owner_downgrade_of_final_tool() -> None:
    from xninetzy.tools.manifest import manifest_for
    final_tools = [
        name for name in ("portal_krs_final_submit", "hebat_submit_submission", "qa_submit_kuesioner")
    ]
    for tool_name in final_tools:
        m = manifest_for(tool_name)
        if m.risk == RiskClass.FINAL:
            assert _effective_tier(tool_name, 0) == 3


def test_risk_to_tier_mapping_complete() -> None:
    from xninetzy.cli.orchestrator import _RISK_TO_TIER
    assert set(_RISK_TO_TIER.keys()) == set(RiskClass)
    assert _RISK_TO_TIER[RiskClass.READ] == 0
    assert _RISK_TO_TIER[RiskClass.DRAFT] == 1
    assert _RISK_TO_TIER[RiskClass.WRITE] == 1
    assert _RISK_TO_TIER[RiskClass.FINAL] == 3
