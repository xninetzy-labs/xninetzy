from __future__ import annotations

import asyncio
import json
import urllib.request
from typing import Any

from app.core.config import get_settings


class WaToolError(RuntimeError):
    pass


async def call_wa_tool(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    return await asyncio.to_thread(_call_wa_tool_sync, tool, input_data)


def _call_wa_tool_sync(tool: str, input_data: dict[str, Any]) -> dict[str, Any]:
    settings = get_settings()
    payload = {"tool": tool, "input": input_data}
    headers = {"Content-Type": "application/json"}
    if settings.WA_MCP_API_KEY:
        headers["Authorization"] = f"Bearer {settings.WA_MCP_API_KEY}"

    request = urllib.request.Request(
        f"{settings.WA_MCP_BASE_URL.rstrip('/')}/mcp/call",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception as error:
        raise WaToolError(f"WA MCP tidak bisa dihubungi: {error}") from error

    if not data.get("success"):
        message = data.get("error", {}).get("message") or "Tool WhatsApp gagal"
        raise WaToolError(message)

    return data
