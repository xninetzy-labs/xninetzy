from __future__ import annotations

from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.registry import get_tool_names
from xninetzy.tools.release_check import (
    _CANONICAL_FINAL_TOOLS,
    check_canonical_final_tools,
    run_release_checks,
)


def test_canonical_final_set_matches_live_registry():
    live_final = sorted(
        name for name in get_tool_names()
        if manifest_for(name).risk.value == "final"
    )
    assert tuple(live_final) == tuple(sorted(_CANONICAL_FINAL_TOOLS))


def test_check_canonical_final_tools_passes():
    result = check_canonical_final_tools()
    assert result.status == "PASS"
    assert result.evidence


def test_run_release_checks_includes_canonical_final():
    run_results = run_release_checks()
    assert any(r.name == "canonical_final_tools" for r in run_results)
    assert all(r.status != "BLOCKED" for r in run_results if r.name == "canonical_final_tools")
