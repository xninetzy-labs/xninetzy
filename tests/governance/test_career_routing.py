from __future__ import annotations

from pathlib import Path

CANONICAL = Path(__file__).resolve().parents[2] / "docs/prompt-injection-core"


def routing_rules():
    lines = (CANONICAL / "CORE_PROMPT.md").read_text(encoding="utf-8").splitlines()
    start = lines.index("## Routing (hybrid)")
    rules = {}
    for line in lines[start + 1:]:
        if line.startswith("## "):
            break
        number, _, body = line.partition(". ")
        if number.isdigit():
            rules[int(number)] = body
    return rules


def test_career_work_is_routed_to_xn_bridge():
    rule = routing_rules()[3]
    for required in ("Career work", "XN-Bridge", "AGENTS.md", "xn-career", "xn-bridge", "awaiting input"):
        assert required in rule


def test_career_rule_forbids_the_generic_discovery_start():
    rule = routing_rules()[3]
    assert "never start with `skill_suggest_for_request`" in rule
    assert "do not substitute generic tools" in rule


def test_xninetzy_domain_rule_no_longer_claims_career():
    rule = routing_rules()[5]
    assert "skill_suggest_for_request" in rule
    assert "career" not in rule.lower()


def test_social_rule_routes_to_xn_interact_with_owner_approval():
    rule = routing_rules()[4]
    for required in ("Social media work", "XN-Interact", "xn-social", "route_intent", "approve", "awaiting input"):
        assert required in rule


def test_security_rule_keeps_career_and_social_routing_unchanged():
    rule = routing_rules()[6]
    assert "security" in rule.lower()
    assert "rules 3 and 4" in rule


def test_native_skill_rule_stays_ahead_of_career_rule():
    rules = routing_rules()
    assert "native skill list" in rules[2]
    assert sorted(rules) == [1, 2, 3, 4, 5, 6]


def test_claude_adapter_carries_exactly_one_trigger_block():
    body = (CANONICAL / "cli-overrides/claude-CLAUDE.md").read_text(encoding="utf-8")
    assert body.count("xn-bridge-trigger:begin") == 1
    assert body.count("xn-bridge-trigger:end") == 1
    assert body.index("xn-bridge-trigger:begin") < body.index("xn-bridge-trigger:end")
    assert "routing rule 3" in body
