from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace

from langchain_core.tools import tool

from scripts import mcp_audit
from xninetzy.tools.manifest import manifest_for


def _snapshot(finals):
    return {
        "bad_risk": [],
        "missing_idempotency": [],
        "missing_approval": [],
        "duplicate_names": [],
        "final_tools": finals,
    }


def test_strict_accepts_additional_final_tools():
    finals = [
        "hebat_upload_submission", "portal_krs_war_arm", "qa_fill_kuesioner",
        "tableau_publish_workbook", "future_external_publish",
    ]
    assert mcp_audit._verify(_snapshot(finals), strict=True) == []


def test_strict_rejects_missing_or_downgraded_required_final_tool():
    finals = ["hebat_upload_submission", "portal_krs_war_arm", "qa_fill_kuesioner"]
    failures = mcp_audit._verify(_snapshot(finals), strict=True)
    assert any("tableau_publish_workbook" in item for item in failures)


def test_snapshot_detects_missing_final_approval_metadata(monkeypatch):
    manifest = replace(manifest_for("tableau_publish_workbook"), requires_approval=False)
    monkeypatch.setattr(mcp_audit, "get_all_tools", lambda: [
        SimpleNamespace(name="tableau_publish_workbook"),
    ])
    monkeypatch.setattr(mcp_audit, "manifest_for", lambda _: manifest)
    snapshot = mcp_audit._tool_snapshot()
    assert snapshot["missing_approval"] == ["tableau_publish_workbook"]
    assert mcp_audit._verify(snapshot, strict=False)


def test_snapshot_detects_duplicate_names(monkeypatch):
    monkeypatch.setattr(mcp_audit, "get_all_tools", lambda: [
        SimpleNamespace(name="task_list"), SimpleNamespace(name="task_list"),
    ])
    snapshot = mcp_audit._tool_snapshot()
    assert snapshot["duplicate_names"] == ["task_list"]
    assert mcp_audit._verify(snapshot, strict=False)


def test_inventory_inspects_schemas_without_executing_tool(monkeypatch):
    @tool
    def example_query(query: str, limit: int = 5) -> str:
        """Inspect a bounded query."""
        raise AssertionError("inventory must not invoke tools")

    monkeypatch.setattr(mcp_audit, "get_all_tools", lambda: [example_query])
    monkeypatch.setattr(mcp_audit, "get_tool_groups", lambda: {"example": ["example_query"]})
    rows = mcp_audit._tool_inventory()
    assert len(rows) == 1
    row = rows[0]
    assert row["name"] == "example_query"
    assert row["groups"] == ["example"]
    assert row["input_schema"]["properties"]["limit"]["default"] == 5
    assert isinstance(row["output_schema"], dict)
    assert row["output_schema_source"] == "langchain declared/inferred; MCP validates before returning"
    assert row["runtime_execution"] == "UNKNOWN"
    assert "gateway-v1 scoped reservation" in row["idempotency_enforcement"]
    assert "denies FINAL" in row["approval_enforcement"]


def test_inventory_cli_emits_json_without_changing_default_output(monkeypatch, capsys):
    monkeypatch.setattr(mcp_audit, "_tool_snapshot", lambda: _snapshot([]))
    monkeypatch.setattr(mcp_audit, "_transport_snapshot", lambda: {})
    monkeypatch.setattr(mcp_audit, "_tool_inventory", lambda: [{"name": "sample"}])
    monkeypatch.setattr("sys.argv", ["mcp_audit.py", "--inventory"])
    assert mcp_audit.main() == 0
    import json

    assert json.loads(capsys.readouterr().out)["inventory"] == [{"name": "sample"}]
