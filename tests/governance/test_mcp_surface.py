from __future__ import annotations


def test_mcp_server_advertises_resources_and_prompts() -> None:
    """XNINETZY MCP must expose at least one resource and one prompt.

    MCP 2025-06-18 spec supports tools, resources, prompts, sampling,
    elicitation, roots. This test asserts the minimum: tools + resources
    + prompts. Sampling/elicitation/roots are deferred.
    """
    from xninetzy.interfaces.mcp_server import mcp

    tool_count = len(mcp._tool_manager._tools)
    resource_count = len(mcp._resource_manager._resources)
    prompt_count = len(mcp._prompt_manager._prompts)

    assert tool_count > 0, "MCP server exposes no tools"
    assert resource_count > 0, "MCP server exposes no resources"
    assert prompt_count > 0, "MCP server exposes no prompts"


def test_tool_manifests_have_no_idempotency_gaps() -> None:
    """Every WRITE/FINAL tool must declare requires_idempotency=True."""
    from xninetzy.tools.manifest import manifest_for
    from xninetzy.tools.registry import get_tool_names

    gaps: list[str] = []
    for name in get_tool_names():
        try:
            m = manifest_for(name)
        except Exception:
            continue
        if m.risk.value in {"write", "final"} and not m.requires_idempotency:
            gaps.append(name)
    assert not gaps, f"idempotency gap on: {gaps}"


def test_final_tools_are_exactly_three_named() -> None:
    """FINAL risk class is reserved for: hebat_upload_submission,
    portal_krs_war_arm, qa_fill_kuesioner. Any drift must be intentional."""
    from xninetzy.tools.manifest import manifest_for
    from xninetzy.tools.registry import get_tool_names

    expected = {"hebat_upload_submission", "portal_krs_war_arm", "qa_fill_kuesioner"}
    finals: set[str] = set()
    for name in get_tool_names():
        try:
            m = manifest_for(name)
            if m.risk.value == "final":
                finals.add(name)
        except Exception:
            continue
    assert finals == expected, f"FINAL drift: got {finals - expected} new, {expected - finals} missing"
