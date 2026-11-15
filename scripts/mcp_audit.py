"""MCP system audit.

Emits a machine-readable snapshot of the live tool registry and runtime
configuration so docs and operators can verify the canonical truth
(`docs/superpowers/specs/mcp-system-audit.md`). Exit non-zero if any
expected invariant fails.

    uv run --no-project python scripts/mcp_audit.py
    uv run --no-project python scripts/mcp_audit.py --json
    uv run --no-project python scripts/mcp_audit.py --strict
    uv run --no-project python scripts/mcp_audit.py --inventory
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from xninetzy.core.config import get_settings  # noqa: E402
from xninetzy.tools.manifest import manifest_for  # noqa: E402
from xninetzy.tools.registry import get_all_tools, get_tool_groups  # noqa: E402


_REQUIRED_FINAL = frozenset({
    "hebat_upload_submission",
    "portal_krs_war_arm",
    "qa_fill_kuesioner",
    "tableau_publish_workbook",
})


def _tool_snapshot() -> dict[str, object]:
    tools = get_all_tools()
    risks: Counter[str] = Counter()
    packs: Counter[str] = Counter()
    stabilities: Counter[str] = Counter()
    finals: list[str] = []
    bad_risk: list[str] = []
    missing_idem: list[str] = []
    missing_approval: list[str] = []
    names: Counter[str] = Counter()
    for tool in tools:
        name = getattr(tool, "name", None) or getattr(tool, "__name__", None) or str(tool)
        manifest = manifest_for(name)
        names[name] += 1
        risks[manifest.risk.value] += 1
        packs[manifest.feature_pack.value] += 1
        stabilities[manifest.stability.value] += 1
        if manifest.risk.value == "final":
            finals.append(name)
            if not manifest.requires_approval:
                missing_approval.append(name)
        if not manifest.policy_known or manifest.risk.value not in {"read", "draft", "write", "final"}:
            bad_risk.append(name)
        if manifest.risk.value in {"write", "final"} and not manifest.requires_idempotency:
            missing_idem.append(name)
    return {
        "total": len(tools),
        "risk": dict(risks),
        "feature_pack": dict(packs),
        "stability": dict(stabilities),
        "final_tools": sorted(finals),
        "bad_risk": sorted(bad_risk),
        "missing_idempotency": sorted(missing_idem),
        "missing_approval": sorted(missing_approval),
        "duplicate_names": sorted(name for name, count in names.items() if count > 1),
    }


def _tool_inventory() -> list[dict[str, object]]:
    """Inspect registry declarations without invoking tools or testing providers.

    LangChain generates schemas from annotations. Their presence is not proof
    of output validation, approval enforcement, or live provider availability.
    """
    groups = get_tool_groups()
    rows: list[dict[str, object]] = []
    for tool in sorted(get_all_tools(), key=lambda item: item.name):
        manifest = manifest_for(tool.name)
        function = getattr(tool, "func", None) or getattr(tool, "coroutine", None)
        try:
            output_schema = tool.get_output_schema().model_json_schema()
        except (AttributeError, TypeError, ValueError):
            output_schema = "UNKNOWN"
        rows.append({
            "name": tool.name,
            "aliases": "UNKNOWN",
            "groups": sorted(group for group, names in groups.items() if tool.name in names),
            "module": getattr(function, "__module__", "UNKNOWN"),
            "description": tool.description,
            "input_schema": tool.args_schema.model_json_schema(),
            "input_schema_source": "domain registry; MCP hides identity and adds idempotency_key for mutations where absent",
            "output_schema": output_schema,
            "output_schema_source": "langchain declared/inferred; MCP validates before returning",
            "manifest": manifest_for(tool.name).as_dict(),
            "policy_source": "tools/execution_policies.json; canonical MCP gateway enforcement",
            "side_effect_class": {"read": "read_only", "draft": "read_only", "write": "local_mutation", "final": "approval_required"}[manifest.risk.value],
            "data_sensitivity": "UNKNOWN",
            "dependencies": "UNKNOWN",
            "runtime_availability": "registered",
            "runtime_execution": "UNKNOWN",
            "average_execution_cost": "UNKNOWN",
            "test_coverage": "UNKNOWN",
            "consumer_workflows": "UNKNOWN",
            "owner": "UNKNOWN",
            "idempotency_enforcement": "MCP gateway-v1 scoped reservation for WRITE/FINAL; domain paths audited separately",
            "approval_enforcement": "MCP denies FINAL until independent owner authorization is integrated",
        })
    return rows


def _transport_snapshot() -> dict[str, object]:
    settings = get_settings()
    return {
        "transport": (settings.XNINETZY_MCP_TRANSPORT or "stdio").strip().lower(),
        "host": settings.XNINETZY_MCP_HTTP_HOST,
        "port": int(settings.XNINETZY_MCP_HTTP_PORT),
        "path": settings.XNINETZY_MCP_HTTP_PATH,
    }


def _verify(snapshot: dict[str, object], strict: bool) -> list[str]:
    failures: list[str] = []
    if snapshot["bad_risk"]:
        failures.append(f"bad_risk: {snapshot['bad_risk']}")
    if snapshot["missing_idempotency"]:
        failures.append(f"missing_idempotency: {snapshot['missing_idempotency']}")
    if snapshot.get("missing_approval"):
        failures.append(f"missing_approval: {snapshot['missing_approval']}")
    if snapshot.get("duplicate_names"):
        failures.append(f"duplicate_names: {snapshot['duplicate_names']}")
    if strict:
        missing = sorted(_REQUIRED_FINAL - set(snapshot["final_tools"]))
        if missing:
            failures.append(f"required_final_tools missing or downgraded: {missing}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP system audit")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--strict", action="store_true", help="require known consequential tools to remain FINAL")
    parser.add_argument("--inventory", action="store_true", help="emit JSON with full declared tool schemas; never invokes tools")
    args = parser.parse_args()

    snapshot = {
        "tools": _tool_snapshot(),
        "transport": _transport_snapshot(),
    }
    failures = _verify(snapshot["tools"], args.strict)
    snapshot["ok"] = not failures
    snapshot["failures"] = failures
    if args.inventory:
        snapshot["inventory"] = _tool_inventory()

    if args.json or args.inventory:
        print(json.dumps(snapshot, indent=2, ensure_ascii=False, default=str))
    else:
        tools = snapshot["tools"]
        transport = snapshot["transport"]
        print(f"total tools       : {tools['total']}")
        print(f"risk distribution : {tools['risk']}")
        print(f"feature pack      : {tools['feature_pack']}")
        print(f"final tools       : {tools['final_tools']}")
        print(f"transport         : {transport['transport']} host={transport['host']} port={transport['port']} path={transport['path']}")
        print(f"idempotency gaps  : {len(tools['missing_idempotency'])}")
        if failures:
            print()
            print("FAIL:")
            for f in failures:
                print(f"  - {f}")
        else:
            print()
            print("overall: PASS")
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
