from xninetzy.os.policy.action_policy import RiskClass
from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.registry import get_tool_names


def test_unknown_tool_has_no_execution_permission():
    assert manifest_for("future_unreviewed_read_tool").risk is RiskClass.FINAL
    assert not manifest_for("future_unreviewed_read_tool").policy_known


def test_explicit_policies_cover_complete_registry():
    from xninetzy.tools.manifest import policy_catalog

    assert set(policy_catalog()) == set(get_tool_names())
    assert all(manifest_for(name).policy_known for name in get_tool_names())


def test_state_change_cannot_be_misclassified_by_status_suffix():
    assert manifest_for("personal_project_status").risk is RiskClass.WRITE
    assert manifest_for("datetime_now").risk is RiskClass.READ


def test_destructive_and_external_dispatch_require_approval():
    for name in ("hebat_remove_submission", "external_mcp_call", "graph_v3_rebuild", "admin_notify_progress"):
        assert manifest_for(name).requires_approval, name


def test_unknown_action_names_cannot_claim_read_or_draft_permissions():
    from xninetzy.os.policy.action_policy import classify_risk

    for name in ("get_unreviewed_credentials", "draft_external_submit", "read_unknown_action"):
        assert classify_risk(name) is RiskClass.FINAL
