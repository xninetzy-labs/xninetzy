from app.ecosystem.command_router import parse_command


def test_rule_add():
    assert parse_command("/rule add jangan kirim reminder di atas jam 22") == (
        "rule_add", {"content": "jangan kirim reminder di atas jam 22"},
    )


def test_rule_list_variants():
    assert parse_command("/rule list") == ("rule_list", {})
    assert parse_command("/rule") == ("rule_list", {})
    assert parse_command("/rules") == ("rule_list", {})


def test_rule_off_on_delete():
    assert parse_command("/rule off 3") == ("rule_disable", {"rule_id": 3})
    assert parse_command("/rule on 3") == ("rule_enable", {"rule_id": 3})
    assert parse_command("/rule delete 3") == ("rule_delete", {"rule_id": 3})


def test_rule_search():
    assert parse_command("/rule search coding") == ("rule_search", {"query": "coding"})


def test_style_commands():
    assert parse_command("/style set santai dan teknis") == (
        "style_set", {"description": "santai dan teknis"},
    )
    assert parse_command("/style show") == ("style_show", {})
    assert parse_command("/style") == ("style_show", {})
    assert parse_command("/style reset") == ("style_reset", {})


def test_test_rules_command():
    assert parse_command("/test-rules") == ("rules_healthcheck", {})


def test_rules_style_tools_registered():
    from app.tools.registry import get_tool_names

    names = get_tool_names()
    for t in ("rule_add", "rule_list", "rule_disable", "rule_enable", "rule_delete",
              "rule_search", "rules_healthcheck", "style_set", "style_show", "style_reset"):
        assert t in names
