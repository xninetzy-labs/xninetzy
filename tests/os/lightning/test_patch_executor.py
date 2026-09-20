from __future__ import annotations

from pathlib import Path

import pytest

from xninetzy.db.migrations import run_migrations
from xninetzy.os.lightning.patch_executor import (
    execute_patch,
    execute_rollback,
    is_capability_enabled,
    list_disabled_capabilities,
    load_context_config_overrides,
)


@pytest.fixture(autouse=True)
def _isolated_db(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    db_file = tmp_path / "patch.db"
    monkeypatch.setenv("SQLITE_PATH", str(db_file))
    from xninetzy.core import config as cfg
    cfg.get_settings.cache_clear()
    run_migrations()
    yield db_file


def test_execute_patch_capability_toggle_persists():
    result = execute_patch(
        target_area="capability_toggle",
        patch={"capability": "do_thing", "enabled": False},
        owner_scope="local",
    )
    assert result["applied"] is True
    assert is_capability_enabled("do_thing") is False
    assert "do_thing" in list_disabled_capabilities()


def test_execute_rollback_capability_toggle_restores():
    execute_patch(
        target_area="capability_toggle",
        patch={"capability": "do_thing", "enabled": False},
        owner_scope="local",
    )
    result = execute_rollback(
        target_area="capability_toggle",
        rollback={"capability": "do_thing"},
        owner_scope="local",
    )
    assert result["rolled_back"] is True
    assert is_capability_enabled("do_thing") is True


def test_execute_patch_context_config_persists():
    result = execute_patch(
        target_area="context_config",
        patch={"setting": "LIGHTNING_EXPLORATION_RATE", "value": 0.42},
        owner_scope="local",
    )
    assert result["applied"] is True
    overrides = load_context_config_overrides()
    assert overrides.get("LIGHTNING_EXPLORATION_RATE") == 0.42


def test_execute_rollback_context_config_restores_previous():
    execute_patch(
        target_area="context_config",
        patch={"setting": "LIGHTNING_EXPLORATION_RATE", "value": 0.42},
        owner_scope="local",
    )
    result = execute_rollback(
        target_area="context_config",
        rollback={"setting": "LIGHTNING_EXPLORATION_RATE", "previous_value": 0.10},
        owner_scope="local",
    )
    assert result["rolled_back"] is True
    overrides = load_context_config_overrides()
    assert "LIGHTNING_EXPLORATION_RATE" not in overrides


def test_execute_patch_unknown_target_area_rejected():
    result = execute_patch(
        target_area="magic_universe",
        patch={},
        owner_scope="local",
    )
    assert result["applied"] is False
    assert "not in allowlist" in result["reason"]


def test_execute_patch_rule_requires_content():
    result = execute_patch(
        target_area="rule",
        patch={"user_id": "local"},
        owner_scope="local",
    )
    assert result["applied"] is False


def test_execute_patch_rule_with_content_succeeds():
    result = execute_patch(
        target_area="rule",
        patch={"rule_content": "be terse", "user_id": "local"},
        owner_scope="local",
    )
    assert result["applied"] is True
    assert "rule_id" in result


def test_execute_patch_tool_routing_creates_provider():
    result = execute_patch(
        target_area="tool_routing",
        patch={
            "provider_id": "newprov",
            "transport": "stdio",
            "endpoint": "cmd",
            "trust_tier": 1,
            "capabilities": ("do_thing",),
        },
        owner_scope="local",
    )
    assert result["applied"] is True


def test_execute_rollback_tool_routing_removes_provider():
    execute_patch(
        target_area="tool_routing",
        patch={
            "provider_id": "tempprov",
            "transport": "stdio",
            "endpoint": "cmd",
            "trust_tier": 1,
            "capabilities": ("do_thing",),
        },
        owner_scope="local",
    )
    result = execute_rollback(
        target_area="tool_routing",
        rollback={"provider_id": "tempprov"},
        owner_scope="local",
    )
    assert result["rolled_back"] is True


def test_capability_toggle_default_enabled():
    assert is_capability_enabled("never_toggled_capability") is True


def test_execute_patch_memory_tuning_persists():
    result = execute_patch(
        target_area="memory_tuning",
        patch={"threshold": 0.85},
        owner_scope="local",
    )
    assert result["applied"] is True
    assert result["threshold"] == 0.85


def test_execute_rollback_memory_tuning_clears():
    execute_patch(
        target_area="memory_tuning",
        patch={"threshold": 0.85},
        owner_scope="local",
    )
    result = execute_rollback(
        target_area="memory_tuning",
        rollback={},
        owner_scope="local",
    )
    assert result["rolled_back"] is True
