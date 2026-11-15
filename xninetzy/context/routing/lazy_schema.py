from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from typing import Any

from xninetzy.tools.manifest import manifest_for
from xninetzy.tools.tool_meta import meta_for

MAX_FULL_SCHEMA_BYTES = 16_000
MAX_LIGHT_METADATA_BYTES = 512
MAX_TOTAL_BUDGET_BYTES = 64_000


@dataclass(frozen=True, slots=True)
class LazySchemaBundle:
    primary_tool: str
    primary_schema: dict[str, Any]
    alternates: tuple[dict[str, Any], ...]
    omitted: tuple[str, ...]
    total_bytes: int
    truncation_applied: bool


def _truncate(value: Any, max_bytes: int) -> tuple[Any, bool]:
    raw = json.dumps(value, ensure_ascii=False, default=str).encode("utf-8")
    if len(raw) <= max_bytes:
        return value, False
    encoded = raw.decode("utf-8", errors="replace")[:max_bytes]
    return encoded + f"...[truncated:{max_bytes}]", True


def materialize_schemas(
    chosen_tool: str,
    *,
    alternates: tuple[str, ...] = (),
    primary_schema: dict[str, Any] | None = None,
) -> LazySchemaBundle:
    if primary_schema is None:
        primary_schema = {
            "name": chosen_tool,
            "manifest": asdict(manifest_for(chosen_tool)),
            "metadata": meta_for(chosen_tool),
        }
    primary_value, primary_truncated = _truncate(primary_schema, MAX_FULL_SCHEMA_BYTES)
    alt_materialized: list[dict[str, Any]] = []
    alt_omitted: list[str] = []
    for alt in alternates[:5]:
        light = {
            "name": alt,
            "manifest_summary": {
                "feature_pack": meta_for(alt).get("feature_pack"),
                "risk": meta_for(alt).get("risk"),
                "stability": meta_for(alt).get("stability"),
                "tags": meta_for(alt).get("tags", []),
            },
        }
        v, tr = _truncate(light, MAX_LIGHT_METADATA_BYTES)
        if isinstance(v, dict):
            alt_materialized.append({**v, "_truncated": tr})
        else:
            alt_materialized.append({"name": alt, "_raw": v, "_truncated": tr})
    for alt in alternates[5:]:
        alt_omitted.append(alt)
    bundle_intermediate = {
        "primary_tool": chosen_tool,
        "primary": primary_value,
        "alternates": alt_materialized,
    }
    encoded = json.dumps(bundle_intermediate, ensure_ascii=False, default=str).encode("utf-8")
    if len(encoded) > MAX_TOTAL_BUDGET_BYTES:
        primary_value, primary_truncated = _truncate(primary_schema, 4_000)
        alt_materialized = alt_materialized[:3]
        bundle_intermediate = {
            "primary_tool": chosen_tool,
            "primary": primary_value,
            "alternates": alt_materialized,
        }
        encoded = json.dumps(bundle_intermediate, ensure_ascii=False, default=str).encode("utf-8")
        alt_omitted = list(alternates[3:])
    return LazySchemaBundle(
        primary_tool=chosen_tool,
        primary_schema=bundle_intermediate["primary"],
        alternates=tuple(bundle_intermediate["alternates"]),
        omitted=tuple(alt_omitted),
        total_bytes=len(encoded),
        truncation_applied=primary_truncated or len(alt_omitted) > 0,
    )
