from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Generic structured result for MCP tools that want to expose a Pydantic output schema.

    Backed by a stable JSON shape so clients can render without parsing prose.
    """

    ok: bool = True
    summary: str = ""
    items: list[dict[str, Any]] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


def to_tool_result(summary: str, items: list[dict[str, Any]] | None = None, **meta: Any) -> dict[str, Any]:
    """Serialize a ToolResult into a JSON payload for str-returning tools."""

    payload = {
        "ok": True,
        "summary": summary,
        "items": list(items or []),
        "meta": dict(meta),
    }
    import json

    return json.dumps(payload, ensure_ascii=False, default=str)
