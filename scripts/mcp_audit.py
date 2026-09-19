"""MCP system audit.

Emits a machine-readable snapshot of the live tool registry and runtime
configuration so docs and operators can verify the canonical truth
(`docs/superpowers/specs/mcp-system-audit.md`). Exit non-zero if any
expected invariant fails.

    uv run --no-project python scripts/mcp_audit.py
    uv run --no-project python scripts/mcp_audit.py --json
    uv run --no-project python scripts/mcp_audit.py --strict
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
from xninetzy.tools.registry import get_all_tools  # noqa: E402


_EXPECTED_FINAL = (
    "hebat_upload_submission",
    "portal_krs_war_arm",
    "qa_fill_kuesioner",
)


def _tool_snapshot() -> dict[str, object]:
    tools = get_all_tools()
    risks: Counter[str] = Counter()
    packs: Counter[str] = Counter()
    stabilities: Counter[str] = Counter()
    finals: list[str] = []
    bad_risk: list[str] = []
    missing_idem: list[str] = []
    for tool in tools:
        manifest = manifest_for(tool.name)
        risks[manifest.risk.value] += 1
        packs[manifest.feature_pack.value] += 1
        stabilities[manifest.stability.value] += 1
        if manifest.risk.value == "final":
            finals.append(tool.name)
        if manifest.risk.value not in {"read", "draft", "write", "final"}:
            bad_risk.append(tool.name)
        if manifest.risk.value in {"write", "final"} and not manifest.requires_idempotency:
            missing_idem.append(tool.name)
    return {
        "total": len(tools),
        "risk": dict(risks),
        "feature_pack": dict(packs),
        "stability": dict(stabilities),
        "final_tools": sorted(finals),
        "bad_risk": sorted(bad_risk),
        "missing_idempotency": sorted(missing_idem),
    }


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
    if strict:
        finals = tuple(snapshot["final_tools"])
        if finals != _EXPECTED_FINAL:
            failures.append(f"final_tools drift: got {finals}, want {_EXPECTED_FINAL}")
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="MCP system audit")
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    parser.add_argument("--strict", action="store_true", help="fail on FINAL-tool count drift")
    args = parser.parse_args()

    snapshot = {
        "tools": _tool_snapshot(),
        "transport": _transport_snapshot(),
    }
    failures = _verify(snapshot["tools"], args.strict)
    snapshot["ok"] = not failures
    snapshot["failures"] = failures

    if args.json:
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
