from __future__ import annotations

from xninetzy.interfaces.mcp_tool_adapter import _DOMAIN_NODE_TYPE, _semantic_node_type


def test_semantic_lookup_known_prefixes():
    assert _semantic_node_type("career_apply") == "job_application"
    assert _semantic_node_type("research_search_papers") == "research_paper"
    assert _semantic_node_type("hebat_upload_submission") == "course"
    assert _semantic_node_type("learning_get_roadmap") == "learning_concept"
    assert _semantic_node_type("obsidian_create") == "obsidian_note"
    assert _semantic_node_type("security_sast") == "security_finding"
    assert _semantic_node_type("image_ocr") == "image"
    assert _semantic_node_type("memory_add") == "memory_note"


def test_semantic_lookup_unknown_returns_none():
    assert _semantic_node_type("foo_bar") is None
    assert _semantic_node_type("unknown_tool") is None


def test_prefix_table_covers_all_domains():
    expected_prefixes = {
        "career", "research", "web", "hebat", "portal", "learning",
        "obsidian", "repo", "security", "image", "memory",
    }
    mapped = set(_DOMAIN_NODE_TYPE.keys())
    missing = expected_prefixes - mapped
    assert not missing, f"missing prefixes: {missing}"
