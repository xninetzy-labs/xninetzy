from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any

from xninetzy.db.sqlite import connect


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def execute_patch(
    *,
    target_area: str,
    patch: dict[str, Any],
    rollback: dict[str, Any] | None = None,
    owner_scope: str = "system",
) -> dict[str, Any]:
    """Execute an approved proposal's patch, restricted to a small allowlist."""
    allowed = {"rule", "tool_routing", "context_config", "memory_tuning", "capability_toggle"}
    if target_area not in allowed:
        return {
            "applied": False,
            "reason": f"target_area {target_area!r} not in allowlist {sorted(allowed)}",
        }
    if target_area == "rule":
        from xninetzy.os.rules.store import add_rule

        rule_user = str(patch.get("user_id") or owner_scope or "default")
        rule_content = str(patch.get("rule_content") or "")
        if not rule_content:
            return {"applied": False, "reason": "rule_content missing"}
        rule = add_rule(rule_user, rule_content, priority=int(patch.get("priority", 60)))
        return {"applied": True, "kind": "rule", "rule_id": int(rule["id"])}
    if target_area == "context_config":
        setting_key = str(patch.get("setting") or "")
        setting_value = patch.get("value")
        if not setting_key:
            return {"applied": False, "reason": "setting missing"}
        from xninetzy.core.config import get_settings

        settings = get_settings()
        if not hasattr(settings, setting_key):
            return {
                "applied": False,
                "reason": f"setting {setting_key!r} not in Settings",
            }
        previous_value = getattr(settings, setting_key)
        try:
            setattr(settings, setting_key, setting_value)
        except Exception as exc:
            return {"applied": False, "reason": f"cannot set: {exc}"}
        with connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO context_config_overrides
                  (name, value_json, updated_at, updated_by)
                VALUES (?, ?, ?, ?)
                """,
                (
                    setting_key,
                    json.dumps(setting_value, ensure_ascii=False),
                    _utcnow(),
                    owner_scope or "system",
                ),
            )
        return {
            "applied": True,
            "kind": "context_config",
            "setting": setting_key,
            "value": setting_value,
            "previous_value": previous_value,
        }
    if target_area == "tool_routing":
        from xninetzy.context.gateway.registry import upsert_provider

        provider_id = str(patch.get("provider_id") or "")
        if not provider_id:
            return {"applied": False, "reason": "provider_id missing"}
        try:
            upsert_provider(
                provider_id=provider_id,
                transport=str(patch.get("transport", "stdio")),
                endpoint=str(patch.get("endpoint", "")),
                trust_tier=int(patch.get("trust_tier", 1)),
                risk_class=str(patch.get("risk_class", "low")),
                capabilities=tuple(patch.get("capabilities", ())),
                health_state=str(patch.get("health_state", "ok")),
            )
        except Exception as exc:
            return {"applied": False, "reason": f"upsert failed: {exc}"}
        return {
            "applied": True,
            "kind": "tool_routing",
            "provider_id": provider_id,
        }
    if target_area == "memory_tuning":
        threshold = float(patch.get("threshold", 0.7) or 0.7)
        with connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS memory_tuning_overrides (
                    name TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """,
            )
            conn.execute(
                "INSERT OR REPLACE INTO memory_tuning_overrides (name, value, updated_at) VALUES (?, ?, ?)",
                ("learning_threshold", str(threshold), _utcnow()),
            )
        return {
            "applied": True,
            "kind": "memory_tuning",
            "threshold": threshold,
        }
    if target_area == "capability_toggle":
        capability = str(patch.get("capability") or "")
        enabled = bool(patch.get("enabled", True))
        if not capability:
            return {"applied": False, "reason": "capability missing"}
        from xninetzy.os.lightning.capability_cache import write_capability_toggle
        write_capability_toggle(capability, enabled)
        return {
            "applied": True,
            "kind": "capability_toggle",
            "capability": capability,
            "enabled": enabled,
        }
    return {"applied": False, "reason": "no executor"}


def execute_rollback(
    *,
    target_area: str,
    rollback: dict[str, Any] | None = None,
    owner_scope: str = "system",
) -> dict[str, Any]:
    if rollback is None:
        rollback = {}
    if target_area == "rule":
        from xninetzy.os.rules.store import list_rules

        rules = list_rules(str(rollback.get("user_id") or owner_scope), active_only=True)
        return {
            "rolled_back": True,
            "kind": "rule",
            "active_rules_count": len(rules),
            "note": "manual rule deletion required",
        }
    if target_area == "tool_routing":
        provider_id = str(rollback.get("provider_id") or "")
        if not provider_id:
            return {"rolled_back": False, "reason": "provider_id missing"}
        with connect() as conn:
            conn.execute("DELETE FROM mcp_providers WHERE provider_id=?", (provider_id,))
        return {"rolled_back": True, "kind": "tool_routing", "provider_id": provider_id}
    if target_area == "context_config":
        setting_key = str(rollback.get("setting") or "")
        previous_value = rollback.get("previous_value")
        if not setting_key:
            return {"rolled_back": False, "reason": "setting missing"}
        from xninetzy.core.config import get_settings

        settings = get_settings()
        if hasattr(settings, setting_key):
            try:
                setattr(settings, setting_key, previous_value)
            except Exception:
                pass
        with connect() as conn:
            conn.execute(
                "DELETE FROM context_config_overrides WHERE name=?",
                (setting_key,),
            )
        return {
            "rolled_back": True,
            "kind": "context_config",
            "setting": setting_key,
            "previous_value": previous_value,
        }
    if target_area == "capability_toggle":
        capability = str(rollback.get("capability") or "")
        if not capability:
            return {"rolled_back": False, "reason": "capability missing"}
        from xninetzy.os.lightning.capability_cache import clear_capability_toggle
        clear_capability_toggle(capability)
        return {
            "rolled_back": True,
            "kind": "capability_toggle",
            "capability": capability,
        }
    if target_area == "memory_tuning":
        with connect() as conn:
            conn.execute(
                "DELETE FROM memory_tuning_overrides WHERE name=?",
                ("learning_threshold",),
            )
        return {"rolled_back": True, "kind": "memory_tuning"}
    return {
        "rolled_back": False,
        "reason": f"no rollback executor for {target_area}",
    }


def is_capability_enabled(capability: str) -> bool:
    """Read capability toggle state. Disabled overrides default (enabled)."""
    try:
        with connect() as conn:
            row = conn.execute(
                "SELECT enabled FROM capability_toggles WHERE capability=?",
                (capability,),
            ).fetchone()
        if row is None:
            return True
        return bool(row["enabled"])
    except Exception:
        return True


def list_disabled_capabilities() -> tuple[str, ...]:
    try:
        with connect() as conn:
            rows = conn.execute(
                "SELECT capability FROM capability_toggles WHERE enabled=0"
            ).fetchall()
        return tuple(str(r["capability"]) for r in rows)
    except Exception:
        return ()


def load_context_config_overrides() -> dict[str, Any]:
    """Read all persisted context_config overrides as {name: value}."""
    try:
        with connect() as conn:
            rows = conn.execute(
                "SELECT name, value_json FROM context_config_overrides"
            ).fetchall()
        return {str(r["name"]): json.loads(str(r["value_json"])) for r in rows}
    except Exception:
        return {}

