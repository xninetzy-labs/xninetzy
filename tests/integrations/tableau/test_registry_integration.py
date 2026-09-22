from __future__ import annotations

from xninetzy.tools.manifest import manifest_for, ToolStability
from xninetzy.tools.registry import get_all_tools, get_tool_names


EXPECTED_TABLEAU_TOOLS = {
    "tableau_capabilities",
    "tableau_template_list",
    "tableau_template_inspect",
    "tableau_workbook_inspect",
    "tableau_workbook_validate",
    "tableau_workbook_generate",
    "tableau_datasource_replace",
    "tableau_worksheet_create",
    "tableau_worksheet_modify",
    "tableau_dashboard_create",
    "tableau_dashboard_layout",
    "tableau_story_create",
    "tableau_twb_export",
    "tableau_twbx_package",
    "tableau_hyper_create",
    "tableau_profile_dataset",
    "tableau_validate_hyper",
    "tableau_infer_schema",
    "tableau_publish_workbook",
    "tableau_refresh_workbook",
    "tableau_list_workbooks",
}


def test_tableau_tools_registered() -> None:
    names = set(get_tool_names())
    missing = EXPECTED_TABLEAU_TOOLS - names
    assert not missing, f"Missing tableau tools: {sorted(missing)}"


def test_tableau_tools_present_in_get_all_tools() -> None:
    tool_names = {t.name for t in get_all_tools()}
    assert EXPECTED_TABLEAU_TOOLS.issubset(tool_names)


def test_tableau_read_tools_stable() -> None:
    read_tools = {
        "tableau_capabilities",
        "tableau_template_list",
        "tableau_template_inspect",
        "tableau_workbook_inspect",
        "tableau_workbook_validate",
        "tableau_profile_dataset",
        "tableau_validate_hyper",
        "tableau_infer_schema",
        "tableau_list_workbooks",
    }
    for name in read_tools:
        manifest = manifest_for(name)
        assert manifest.stability == ToolStability.STABLE, name
        assert manifest.requires_approval is False, name


def test_tableau_write_tools_require_idempotency() -> None:
    write_tools = {
        "tableau_workbook_generate",
        "tableau_datasource_replace",
        "tableau_worksheet_create",
        "tableau_worksheet_modify",
        "tableau_dashboard_create",
        "tableau_dashboard_layout",
        "tableau_story_create",
        "tableau_twb_export",
        "tableau_twbx_package",
        "tableau_hyper_create",
        "tableau_refresh_workbook",
    }
    for name in write_tools:
        manifest = manifest_for(name)
        assert manifest.requires_idempotency is True, name


def test_tableau_publish_requires_approval() -> None:
    manifest = manifest_for("tableau_publish_workbook")
    assert manifest.requires_approval is True
