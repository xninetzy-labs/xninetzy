from app.xninetzy.tools.registry import get_all_tools, get_tool_groups


def test_get_all_tools_not_empty():
    tools = get_all_tools()
    assert isinstance(tools, list)
    assert len(tools) > 0


def test_tool_groups_has_it_learning():
    groups = get_tool_groups()
    assert "it_learning" in groups
    assert "academic" in groups


def test_tool_group_names_exist_in_registry():
    all_names = {t.name for t in get_all_tools()}
    for group, names in get_tool_groups().items():
        for name in names:
            assert name in all_names, f"{name} (group {group}) missing from registry"
