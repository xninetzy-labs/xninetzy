from __future__ import annotations

from pydantic import BaseModel

from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.registry import get_all_tools, get_tool_names


def _iter_tools():
    for tool in get_all_tools():
        yield tool


def test_every_tool_has_non_empty_name_and_description():
    for tool in _iter_tools():
        assert tool.name, f"tool missing name: {tool!r}"
        assert isinstance(tool.name, str)
        assert tool.description and tool.description.strip(), f"{tool.name} missing description"


def test_every_tool_has_args_schema_subclass_of_basemodel():
    schema = getattr(_iter_tools().__class__, "__name__", "")
    assert schema
    for tool in get_all_tools():
        schema_cls = tool.args_schema
        assert schema_cls is not None, f"{tool.name} missing args_schema"
        assert isinstance(schema_cls, type), f"{tool.name} args_schema is not a class"
        assert issubclass(schema_cls, BaseModel), (
            f"{tool.name} args_schema is not a pydantic BaseModel"
        )


def test_every_tool_has_manifest_entry():
    for tool in get_all_tools():
        manifest = manifest_for(tool.name)
        assert manifest.name == tool.name
        assert manifest.feature_pack is not None
        assert manifest.risk is not None


def test_tool_names_match_registry():
    by_all = {t.name for t in get_all_tools()}
    by_names = set(get_tool_names())
    assert by_all == by_names


def test_no_duplicate_tool_names():
    names = get_tool_names()
    assert len(names) == len(set(names)), f"duplicate names: {[n for n in names if names.count(n) > 1]}"


def test_new_tools_present():
    names = set(get_tool_names())
    assert "lightning_episode_get" in names
    assert "repo_file_outline" in names


def test_all_tools_exposed_to_mcp(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "registry.db"))
    from xninetzy.db.sqlite import init_db
    from xninetzy.db.migrations import run_migrations

    init_db()
    run_migrations()
    from xninetzy.interfaces.mcp_server import mcp
    from xninetzy.tools.registry import get_all_tools

    mcp_names = {tool.name for tool in mcp._tool_manager.list_tools()}
    registry_names = {tool.name for tool in get_all_tools()}
    missing_in_mcp = registry_names - mcp_names
    assert not missing_in_mcp, f"tools not exposed to MCP: {sorted(missing_in_mcp)[:10]}"


def test_manifest_feature_pack_coverage():
    from collections import Counter

    from xninetzy.tools.manifest import FeaturePack, manifest_for

    packs = Counter(manifest_for(name).feature_pack for name in get_tool_names())
    assert packs, "no feature_pack assignments"
    for pack in FeaturePack:
        assert packs[pack] >= 0
    assert packs[FeaturePack.CORE] >= 50, f"CORE pack underweight: {packs}"


def test_manifest_risk_class_coverage():
    from collections import Counter

    from xninetzy.os.policy.action_policy import RiskClass
    from xninetzy.tools.manifest import manifest_for

    risks = Counter(manifest_for(name).risk for name in get_tool_names())
    assert risks, "no risk_class assignments"
    assert risks[RiskClass.READ] > 0, "no READ tools"
    assert risks[RiskClass.WRITE] > 0, "no WRITE tools"


def test_manifest_feature_pack_consistent_with_name_prefix():
    from xninetzy.tools.manifest import FeaturePack, manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        if name.startswith(("hebat_", "portal_", "qa_", "uacc_")):
            assert manifest.feature_pack == FeaturePack.ACADEMIC_UNAIR, (
                f"{name} should be ACADEMIC_UNAIR, got {manifest.feature_pack}"
            )
        elif name.startswith(("web_", "youtube_", "research_", "deep_research", "pixelrag_")):
            assert manifest.feature_pack == FeaturePack.RESEARCH, (
                f"{name} should be RESEARCH, got {manifest.feature_pack}"
            )
        elif name.startswith(("coding_", "ai_provider_")):
            assert manifest.feature_pack == FeaturePack.CODING, (
                f"{name} should be CODING, got {manifest.feature_pack}"
            )
        else:
            assert manifest.feature_pack == FeaturePack.CORE, (
                f"{name} should be CORE, got {manifest.feature_pack}"
            )


def test_manifest_final_tools_require_approval():
    from xninetzy.os.policy.action_policy import RiskClass
    from xninetzy.tools.manifest import manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        if manifest.risk == RiskClass.FINAL:
            assert manifest.requires_approval is True, (
                f"{name} is FINAL but requires_approval={manifest.requires_approval}"
            )


def test_manifest_write_or_final_tools_require_idempotency():
    from xninetzy.os.policy.action_policy import RiskClass
    from xninetzy.tools.manifest import manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        if manifest.risk in (RiskClass.WRITE, RiskClass.FINAL):
            assert manifest.requires_idempotency is True, (
                f"{name} is {manifest.risk.value} but requires_idempotency=False"
            )


def test_no_orphan_tools_without_feature_pack():
    from xninetzy.tools.manifest import manifest_for

    unclassified: list[str] = []
    for name in get_tool_names():
        manifest = manifest_for(name)
        if manifest.feature_pack is None:
            unclassified.append(name)
    assert not unclassified, f"tools without feature_pack: {unclassified[:10]}"


def test_manifest_heuristics_cover_known_prefixes():
    from xninetzy.tools.manifest import FeaturePack, manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        if name.startswith("deep_research"):
            assert manifest.feature_pack == FeaturePack.RESEARCH, (
                f"{name} should be RESEARCH (deep_research prefix)"
            )
        if name.startswith("pixelrag"):
            assert manifest.feature_pack == FeaturePack.RESEARCH, (
                f"{name} should be RESEARCH (pixelrag prefix)"
            )
        if name.startswith("coding_"):
            assert manifest.feature_pack == FeaturePack.CODING, (
                f"{name} should be CODING (coding_ prefix)"
            )


def test_manifest_version_always_set():
    from xninetzy.tools.manifest import manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        assert manifest.version, f"{name} missing version"
        assert "." in manifest.version, f"{name} version not semver: {manifest.version}"


def test_manifest_knowledge_tools_require_evidence():
    from xninetzy.tools.manifest import manifest_for

    knowledge_tools = [
        name for name in get_tool_names()
        if name.startswith(("knowledge_answer", "deep_research", "research_"))
    ]
    assert knowledge_tools, "no knowledge/research tools found"
    for name in knowledge_tools:
        manifest = manifest_for(name)
        assert manifest.requires_evidence is True, (
            f"{name} should require evidence"
        )


def test_manifest_read_tools_dont_require_idempotency():
    from xninetzy.os.policy.action_policy import RiskClass
    from xninetzy.tools.manifest import manifest_for

    for name in get_tool_names():
        manifest = manifest_for(name)
        if manifest.risk == RiskClass.READ:
            assert manifest.requires_idempotency is False, (
                f"READ tool {name} should not require idempotency"
            )
