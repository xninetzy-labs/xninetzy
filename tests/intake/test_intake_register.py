from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.context.gateway.registry import list_lifecycle, list_providers
from xninetzy.context.gateway.trust import (
    TRUST_TIER_BLOCKED,
    TRUST_TIER_KNOWN_EXTERNAL,
    TRUST_TIER_THIRD_PARTY,
    TRUST_TIER_UNVERIFIED,
    trust_for_risk,
)
from xninetzy.context.intake.classify import (
    REPO_KIND_MCP_SERVER,
    classify_layout,
)
from xninetzy.context.intake.layout import collect_layout
from xninetzy.context.intake.register import (
    INTAKE_DEFAULT_TIER,
    PROMOTION_MAX_TIER,
    STAGE_CLASSIFIED,
    STAGE_DISCOVERED,
    STAGE_PROMOTED,
    STAGE_REGISTERED,
    STAGE_REJECTED,
    intake_constants,
    promote_provider_tier,
    register_from_classification,
    reject_provider,
)
from xninetzy.context.intake.urls import parse_github_url
from xninetzy.db.migrations import run_migrations
from xninetzy.db.sqlite import connect


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "intake.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as config_module
    config_module.get_settings.cache_clear()
    run_migrations()
    yield db_file


def _seed_mcp_repo(tmp_path: Path):
    (tmp_path / "README.md").write_text("Built on fastmcp and modelcontextprotocol", encoding="utf-8")
    (tmp_path / "mcp_capabilities.json").write_text('{"tools": ["do_thing", "fetch_x"]}', encoding="utf-8")
    (tmp_path / "server.py").write_text("print('hello')", encoding="utf-8")
    return collect_layout(tmp_path)


def test_intake_constants_match_trust_table():
    constants = intake_constants()
    assert constants["INTAKE_DEFAULT_TIER"] == INTAKE_DEFAULT_TIER
    assert constants["PROMOTION_MAX_TIER"] == PROMOTION_MAX_TIER
    assert STAGE_PROMOTED in constants["STAGES"]
    assert STAGE_REJECTED in constants["STAGES"]


def test_register_from_classification_defaults_to_unverified(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    assert classification.kind == REPO_KIND_MCP_SERVER
    source = parse_github_url("https://github.com/anthropics/anthropic-sdk-python")
    result = register_from_classification(
        source=source,
        classification=classification,
        actor="tester",
    )
    assert result.trust_tier == TRUST_TIER_UNVERIFIED
    assert result.risk_class == "unreviewed"
    assert not result.reused
    assert "do_thing" in result.capabilities
    assert STAGE_DISCOVERED in result.stage_sequence
    assert STAGE_REGISTERED in result.stage_sequence


def test_register_from_classification_persists_provider_row(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    rows = [row for row in list_providers() if row.provider_id == result.provider_id]
    assert rows
    record = rows[0]
    assert record.trust_tier == TRUST_TIER_UNVERIFIED
    assert "do_thing" in record.capabilities
    assert record.metadata.get("canonical_url") == "https://github.com/foo/bar"


def test_register_from_classification_records_lifecycle(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    lifecycle = [row for row in list_lifecycle() if row["provider_id"] == result.provider_id]
    stages = {row["stage"] for row in lifecycle}
    assert {STAGE_DISCOVERED, STAGE_CLASSIFIED, STAGE_REGISTERED}.issubset(stages)


def test_register_is_idempotent_via_provider_id(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    first = register_from_classification(source=source, classification=classification)
    second = register_from_classification(source=source, classification=classification)
    assert first.provider_id == second.provider_id
    rows = [row for row in list_providers() if row.provider_id == first.provider_id]
    assert len(rows) == 1


def test_idempotency_key_is_url_plus_kind(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    expected_prefix = result.idempotency_key[:16]
    assert result.idempotency_key == result.idempotency_key
    assert expected_prefix.isalnum()


def test_promote_provider_tier_moves_to_known_external(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    new_tier = promote_provider_tier(
        provider_id=result.provider_id,
        new_tier=TRUST_TIER_KNOWN_EXTERNAL,
        actor="admin",
        rationale="reviewed manifest",
    )
    assert new_tier == TRUST_TIER_KNOWN_EXTERNAL
    record = next(r for r in list_providers() if r.provider_id == result.provider_id)
    assert record.trust_tier == TRUST_TIER_KNOWN_EXTERNAL


def test_promote_provider_tier_records_lifecycle_event(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    promote_provider_tier(
        provider_id=result.provider_id,
        new_tier=TRUST_TIER_KNOWN_EXTERNAL,
        actor="admin",
        rationale="signed-off",
    )
    lifecycle = [row for row in list_lifecycle() if row["provider_id"] == result.provider_id]
    stages = [row["stage"] for row in lifecycle]
    assert STAGE_PROMOTED in stages


def test_promote_provider_tier_requires_actor_and_rationale(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    with pytest.raises(ValueError):
        promote_provider_tier(
            provider_id=result.provider_id,
            new_tier=TRUST_TIER_KNOWN_EXTERNAL,
            actor="",
            rationale="",
        )


def test_promote_provider_tier_rejects_blocked_target(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    with pytest.raises(ValueError):
        promote_provider_tier(
            provider_id=result.provider_id,
            new_tier=TRUST_TIER_BLOCKED,
            actor="admin",
            rationale="trying to block via promote",
        )


def test_reject_provider_blocks_provider(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(source=source, classification=classification)
    new_tier = reject_provider(
        provider_id=result.provider_id,
        actor="admin",
        rationale="malicious",
    )
    assert new_tier == TRUST_TIER_BLOCKED
    record = next(r for r in list_providers() if r.provider_id == result.provider_id)
    assert record.trust_tier == TRUST_TIER_BLOCKED
    lifecycle = [row for row in list_lifecycle() if row["provider_id"] == result.provider_id]
    assert any(row["stage"] == STAGE_REJECTED for row in lifecycle)


def test_register_writes_capability_aliases(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    register_from_classification(source=source, classification=classification)
    with connect() as conn:
        rows = conn.execute(
            "SELECT capability, surface FROM capability_aliases WHERE capability IN ('do_thing', 'fetch_x')"
        ).fetchall()
    surfaces = {row["surface"] for row in rows}
    assert "tool:do_thing" in surfaces
    assert "tool:fetch_x" in surfaces


def test_register_override_tier_can_bootstrap_higher(_isolated_db, tmp_path):
    layout = _seed_mcp_repo(tmp_path)
    classification = classify_layout(layout)
    source = parse_github_url("https://github.com/foo/bar")
    result = register_from_classification(
        source=source,
        classification=classification,
        override_tier=TRUST_TIER_THIRD_PARTY,
        risk_class="high",
    )
    assert result.trust_tier == TRUST_TIER_THIRD_PARTY
    assert result.risk_class == "high"
    assert trust_for_risk("high") == TRUST_TIER_THIRD_PARTY
