from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from xninetzy.context.gateway.trust import (
    HEALTH_UNKNOWN,
    TRANSPORT_STDIO,
    trust_for_risk,
)
from xninetzy.core.config import get_settings
from xninetzy.db.sqlite import connect


@dataclass(frozen=True, slots=True)
class ProviderRecord:
    provider_id: str
    transport: str
    endpoint: str | None
    trust_tier: int
    risk_class: str
    capabilities: tuple[str, ...]
    health_state: str
    last_seen_at: str | None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class SeedProviderResult:
    upserted: tuple[str, ...]
    skipped: tuple[str, ...]
    total_rows: int


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _registry_path() -> Path:
    return Path(get_settings().EXTERNAL_MCP_REGISTRY_PATH).expanduser()


def _load_external_entries() -> list[dict[str, Any]]:
    path = _registry_path()
    if not path.is_file():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    servers = payload.get("servers", [])
    return [entry for entry in servers if isinstance(entry, dict)]


def _row_to_record(row) -> ProviderRecord:
    raw_caps = row["capabilities_json"]
    try:
        parsed = json.loads(raw_caps) if raw_caps else []
    except json.JSONDecodeError:
        parsed = []
    capabilities = tuple(str(item) for item in parsed) if isinstance(parsed, list) else ()
    raw_meta = row["metadata_json"]
    try:
        parsed_meta = json.loads(raw_meta) if raw_meta else {}
    except json.JSONDecodeError:
        parsed_meta = {}
    metadata = parsed_meta if isinstance(parsed_meta, dict) else {}
    return ProviderRecord(
        provider_id=str(row["provider_id"]),
        transport=str(row["transport"]),
        endpoint=row["endpoint"],
        trust_tier=int(row["trust_tier"]),
        risk_class=str(row["risk_class"]),
        capabilities=capabilities,
        health_state=str(row["health_state"]),
        last_seen_at=row["last_seen_at"],
        metadata=metadata,
    )


def list_providers() -> list[ProviderRecord]:
    with connect() as conn:
        rows = conn.execute(
            "SELECT provider_id, transport, endpoint, trust_tier, risk_class, "
            "capabilities_json, health_state, last_seen_at, metadata_json "
            "FROM mcp_providers ORDER BY trust_tier, provider_id"
        ).fetchall()
    return [_row_to_record(row) for row in rows]


def upsert_provider(
    provider_id: str,
    *,
    transport: str = TRANSPORT_STDIO,
    endpoint: str | None = None,
    trust_tier: int,
    risk_class: str,
    capabilities: tuple[str, ...] = (),
    health_state: str = HEALTH_UNKNOWN,
    metadata: dict[str, Any] | None = None,
    now: str | None = None,
) -> ProviderRecord:
    stamp = now or _utcnow()
    payload_meta = json.dumps(metadata or {}, ensure_ascii=False, sort_keys=True)
    payload_caps = json.dumps(list(capabilities), ensure_ascii=False)
    try:
        from xninetzy.context.gateway.provider_cache import invalidate_cache
        invalidate_cache()
    except ImportError:
        pass
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO mcp_providers
                (provider_id, transport, endpoint, trust_tier, risk_class,
                 capabilities_json, health_state, last_seen_at,
                 metadata_json, created_at, updated_at)
            VALUES (:provider_id, :transport, :endpoint, :trust_tier, :risk_class,
                    :capabilities_json, :health_state, :last_seen_at,
                    :metadata_json, :created_at, :updated_at)
            ON CONFLICT(provider_id) DO UPDATE SET
                transport = excluded.transport,
                endpoint = excluded.endpoint,
                trust_tier = excluded.trust_tier,
                risk_class = excluded.risk_class,
                capabilities_json = excluded.capabilities_json,
                health_state = excluded.health_state,
                last_seen_at = excluded.last_seen_at,
                metadata_json = excluded.metadata_json,
                updated_at = excluded.updated_at
            """,
            {
                "provider_id": provider_id,
                "transport": transport,
                "endpoint": endpoint,
                "trust_tier": int(trust_tier),
                "risk_class": risk_class,
                "capabilities_json": payload_caps,
                "health_state": health_state,
                "last_seen_at": stamp,
                "metadata_json": payload_meta,
                "created_at": stamp,
                "updated_at": stamp,
            },
        )
        row = conn.execute(
            "SELECT provider_id, transport, endpoint, trust_tier, risk_class, "
            "capabilities_json, health_state, last_seen_at, metadata_json "
            "FROM mcp_providers WHERE provider_id = ?",
            (provider_id,),
        ).fetchone()
    assert row is not None
    return _row_to_record(row)


def seed_providers_from_external(*, now: str | None = None) -> SeedProviderResult:
    entries = _load_external_entries()
    upserted: list[str] = []
    skipped: list[str] = []
    for entry in entries:
        provider_id = str(entry.get("name", "")).strip()
        if not provider_id:
            skipped.append("")
            continue
        risk_class = str(entry.get("risk_level", "unreviewed"))
        trust_tier = trust_for_risk(risk_class)
        command = str(entry.get("command", ""))
        endpoint = command or None
        allowed = entry.get("allowed_tools") or []
        capabilities = tuple(str(item) for item in allowed if isinstance(item, str))
        metadata = {
            "args": list(entry.get("args") or []),
            "env_vars": list(entry.get("env_vars") or []),
            "enabled": bool(entry.get("enabled", True)),
            "last_reviewed_at": entry.get("last_reviewed_at"),
        }
        existing_rows = []
        with connect() as conn:
            existing_rows = conn.execute(
                "SELECT 1 FROM mcp_providers WHERE provider_id = ?",
                (provider_id,),
            ).fetchall()
        if existing_rows:
            skipped.append(provider_id)
            continue
        upsert_provider(
            provider_id=provider_id,
            transport=TRANSPORT_STDIO,
            endpoint=endpoint,
            trust_tier=trust_tier,
            risk_class=risk_class,
            capabilities=capabilities,
            metadata=metadata,
            now=now,
        )
        upserted.append(provider_id)
    total = 0
    with connect() as conn:
        total = conn.execute("SELECT COUNT(*) AS n FROM mcp_providers").fetchone()["n"]
    return SeedProviderResult(
        upserted=tuple(sorted(upserted)),
        skipped=tuple(sorted(skipped)),
        total_rows=int(total),
    )


def record_lifecycle_event(
    *,
    capability: str,
    provider_id: str,
    stage: str,
    notes: str | None = None,
    actor: str | None = None,
    now: str | None = None,
) -> int:
    stamp = now or _utcnow()
    with connect() as conn:
        cursor = conn.execute(
            """
            INSERT INTO capability_lifecycle
                (capability, provider_id, stage, notes, actor, created_at)
            VALUES (:capability, :provider_id, :stage, :notes, :actor, :created_at)
            """,
            {
                "capability": capability,
                "provider_id": provider_id,
                "stage": stage,
                "notes": notes,
                "actor": actor,
                "created_at": stamp,
            },
        )
        return int(cursor.lastrowid or 0)


def list_lifecycle(capability: str | None = None) -> list[dict[str, Any]]:
    with connect() as conn:
        if capability is None:
            rows = conn.execute(
                "SELECT capability, provider_id, stage, notes, actor, created_at "
                "FROM capability_lifecycle ORDER BY created_at DESC, id DESC"
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT capability, provider_id, stage, notes, actor, created_at "
                "FROM capability_lifecycle WHERE capability = ? "
                "ORDER BY created_at DESC, id DESC",
                (capability,),
            ).fetchall()
    return [dict(row) for row in rows]
