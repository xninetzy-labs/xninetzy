from __future__ import annotations

import asyncio
import json
import urllib.request
from typing import Any

from app.xninetzy.core.config import get_settings


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


def _is_cache_miss(message: str) -> bool:
    lowered = message.lower()
    return "not found in cache" in lowered or "expired" in lowered


async def download_media_message(
    chat_jid: str, message_id: str, participant_jid: str | None = None
) -> dict[str, Any]:
    """Download a WhatsApp media message via the wa-enggine MCP tool.

    Returns ``{"ok": True, local_path, filename, mime_type, size_bytes, sha256}``
    on success, or ``{"ok": False, "error": <friendly msg>}`` — never raises, so
    media ingestion can degrade gracefully on a cache miss.
    """
    input_data: dict[str, Any] = {"chat_id": chat_jid, "message_id": message_id}
    if participant_jid:
        input_data["participant_jid"] = participant_jid
    try:
        data = await call_wa_tool("download_media_message", input_data)
    except WaToolError as error:
        msg = str(error)
        friendly = (
            "Media message tidak ditemukan di cache. Coba kirim ulang file."
            if _is_cache_miss(msg)
            else f"Gagal download media WhatsApp: {msg}"
        )
        return {"ok": False, "error": friendly}
    return {"ok": True, **(data.get("result") or {})}


async def get_message_metadata(chat_jid: str, message_id: str) -> dict[str, Any]:
    """Check whether a message carries media without downloading it."""
    try:
        data = await call_wa_tool(
            "get_message_metadata", {"chat_id": chat_jid, "message_id": message_id}
        )
    except WaToolError as error:
        return {"ok": False, "error": str(error)}
    return {"ok": True, **(data.get("result") or {})}
