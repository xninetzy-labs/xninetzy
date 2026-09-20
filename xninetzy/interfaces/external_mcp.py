from __future__ import annotations

import asyncio
import io
import json
import os
import re
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from xninetzy.core.config import get_settings
from xninetzy.os.research.permissions import is_owner_admin


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")

RiskLevel = Literal["unreviewed", "low", "medium", "high"]


@dataclass(frozen=True, slots=True)
class ExternalMcpServer:
    name: str
    command: str
    args: list[str]
    env_vars: list[str]
    enabled: bool
    risk_level: RiskLevel = "unreviewed"
    allowed_tools: tuple[str, ...] = ()
    last_reviewed_at: str | None = None


def _registry_path() -> Path:
    return Path(get_settings().EXTERNAL_MCP_REGISTRY_PATH).expanduser()


def _load_servers() -> dict[str, ExternalMcpServer]:
    path = _registry_path()
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    servers: dict[str, ExternalMcpServer] = {}
    for entry in raw.get("servers", []):
        allowed_raw = entry.get("allowed_tools") or []
        allowed = tuple(str(value) for value in allowed_raw)
        risk = str(entry.get("risk_level", "unreviewed"))
        if risk not in {"unreviewed", "low", "medium", "high"}:
            risk = "unreviewed"
        server = ExternalMcpServer(
            name=str(entry["name"]),
            command=str(entry["command"]),
            args=[str(value) for value in entry.get("args", [])],
            env_vars=[str(value) for value in entry.get("env_vars", [])],
            enabled=bool(entry.get("enabled", True)),
            risk_level=risk,
            allowed_tools=allowed,
            last_reviewed_at=(str(entry["last_reviewed_at"]) if entry.get("last_reviewed_at") else None),
        )
        servers[server.name] = server
    return servers


def _save_servers(servers: dict[str, ExternalMcpServer]) -> None:
    path = _registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"servers": [asdict(servers[name]) for name in sorted(servers)]}
    temporary = path.with_suffix(f"{path.suffix}.tmp")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.chmod(0o600)
    temporary.replace(path)


def _owner_allowed(sender_id: str, sender_name: str) -> bool:
    return is_owner_admin(sender_id, sender_name)


def _validate_server(name: str, command: str, args: list[str], env_vars: list[str]) -> str | None:
    if not _NAME_PATTERN.fullmatch(name):
        return "Nama MCP harus huruf kecil, angka, garis bawah, atau strip."
    if not command.strip() or any(character.isspace() for character in command.strip()):
        return "Command MCP harus berupa satu executable tanpa shell."
    if any(not value or "\x00" in value for value in args):
        return "Argumen MCP tidak valid."
    if any(not re.fullmatch(r"[A-Z][A-Z0-9_]*", value) for value in env_vars):
        return "Nama environment MCP tidak valid."
    return None


def _server_payload(server: ExternalMcpServer) -> dict[str, Any]:
    return {
        "name": server.name,
        "command": server.command,
        "args": server.args,
        "env_vars": server.env_vars,
        "enabled": server.enabled,
        "risk_level": server.risk_level,
        "allowed_tools": list(server.allowed_tools),
        "last_reviewed_at": server.last_reviewed_at,
    }


def _normalize_allowed(allowed_json: str) -> tuple[str, ...] | str:
    try:
        parsed = json.loads(allowed_json or "[]")
    except json.JSONDecodeError:
        return "allowed_tools_json harus JSON array."
    if not isinstance(parsed, list):
        return "allowed_tools_json harus JSON array."
    cleaned: list[str] = []
    for value in parsed:
        if not isinstance(value, str) or not value.strip():
            return "allowed_tools berisi nama tool tidak valid."
        cleaned.append(value.strip())
    return tuple(cleaned)


async def _session(server: ExternalMcpServer):
    env = {key: os.environ[key] for key in server.env_vars if key in os.environ}
    parameters = StdioServerParameters(
        command=server.command,
        args=server.args,
        env={**{"PATH": os.environ.get("PATH", "")}, **env},
    )
    return stdio_client(parameters, errlog=io.StringIO())


@tool
def external_mcp_list(sender_id: str = "", sender_name: str = "") -> dict[str, Any]:
    """Daftar server MCP eksternal owner-scoped tanpa membocorkan secret."""
    if not _owner_allowed(sender_id, sender_name):
        return {"success": False, "message": "Hanya owner yang dapat melihat MCP eksternal."}
    return {"success": True, "enabled": get_settings().EXTERNAL_MCP_ENABLED, "servers": [_server_payload(server) for server in _load_servers().values()]}


@tool
def external_mcp_add(
    name: str,
    command: str,
    args_json: str = "[]",
    env_vars_json: str = "[]",
    allowed_tools_json: str = "[]",
    risk_level: str = "unreviewed",
    enabled: bool = True,
    sender_id: str = "",
    sender_name: str = "",
) -> dict[str, Any]:
    """Daftarkan MCP stdio eksternal. Secret tetap dibaca dari environment lokal."""
    if not _owner_allowed(sender_id, sender_name):
        return {"success": False, "message": "Hanya owner yang dapat menambah MCP eksternal."}
    try:
        args = json.loads(args_json)
        env_vars = json.loads(env_vars_json)
    except json.JSONDecodeError:
        return {"success": False, "message": "args_json dan env_vars_json harus JSON array."}
    if not isinstance(args, list) or not isinstance(env_vars, list):
        return {"success": False, "message": "args_json dan env_vars_json harus JSON array."}
    allowed = _normalize_allowed(allowed_tools_json)
    if isinstance(allowed, str):
        return {"success": False, "message": allowed}
    if risk_level not in {"unreviewed", "low", "medium", "high"}:
        return {"success": False, "message": "risk_level tidak valid."}
    normalized_args = [str(value) for value in args]
    normalized_env_vars = [str(value) for value in env_vars]
    error = _validate_server(name, command, normalized_args, normalized_env_vars)
    if error:
        return {"success": False, "message": error}
    servers = _load_servers()
    reviewed_at = datetime.now(timezone.utc).isoformat()
    server = ExternalMcpServer(
        name=name,
        command=command,
        args=normalized_args,
        env_vars=normalized_env_vars,
        enabled=enabled,
        risk_level=risk_level,
        allowed_tools=allowed,
        last_reviewed_at=reviewed_at,
    )
    if name not in servers and len(servers) >= getattr(get_settings(), "EXTERNAL_MCP_MAX_SERVERS", 8):
        return {"success": False, "message": "Batas jumlah MCP eksternal tercapai."}
    servers[name] = server
    _save_servers(servers)
    try:
        from xninetzy.tools.registry import refresh_external_mcp_tools

        refresh_external_mcp_tools()
    except Exception as error:
        try:
            from xninetzy.observability.trace import emit

            emit(
                "external_mcp_refresh_failed",
                name=name,
                error_type=type(error).__name__,
                error=str(error)[:200],
            )
        except Exception:
            pass
    return {"success": True, "server": _server_payload(server)}


@tool
def external_mcp_remove(name: str, sender_id: str = "", sender_name: str = "") -> dict[str, Any]:
    """Hapus konfigurasi MCP eksternal owner-scoped tanpa menyentuh MCP server sumber."""
    if not _owner_allowed(sender_id, sender_name):
        return {"success": False, "message": "Hanya owner yang dapat menghapus MCP eksternal."}
    servers = _load_servers()
    removed = servers.pop(name, None)
    if removed is None:
        return {"success": False, "message": "MCP eksternal tidak ditemukan."}
    _save_servers(servers)
    return {"success": True, "removed": name}


async def _with_session(server: ExternalMcpServer, operation):
    async with await _session(server) as (read_stream, write_stream):
        async with ClientSession(read_stream, write_stream) as session:
            await session.initialize()
            return await operation(session)


@tool
async def external_mcp_tools(
    name: str, sender_id: str = "", sender_name: str = ""
) -> dict[str, Any]:
    """Inspeksi schema tools MCP eksternal terdaftar tanpa memanggil tool-nya."""
    if not _owner_allowed(sender_id, sender_name):
        return {"success": False, "message": "Hanya owner yang dapat memakai MCP eksternal."}
    settings = get_settings()
    if not settings.EXTERNAL_MCP_ENABLED:
        return {"success": False, "message": "Set EXTERNAL_MCP_ENABLED=true untuk mengaktifkan integrasi."}
    server = _load_servers().get(name)
    if server is None or not server.enabled:
        return {"success": False, "message": "MCP eksternal tidak ditemukan atau dinonaktifkan."}
    try:
        result = await asyncio.wait_for(
            _with_session(server, lambda session: session.list_tools()),
            timeout=settings.XNINETZY_MCP_CONNECT_TIMEOUT_SECONDS,
        )
    except Exception as error:
        return {"success": False, "message": f"MCP eksternal tidak tersedia: {type(error).__name__}"}
    return {
        "success": True,
        "server": server.name,
        "tools": [
            {"name": item.name, "description": item.description or "", "input_schema": item.inputSchema}
            for item in result.tools
        ],
    }


@tool
async def external_mcp_call(
    name: str,
    tool_name: str,
    arguments_json: str = "{}",
    sender_id: str = "",
    sender_name: str = "",
) -> dict[str, Any]:
    """Panggil tool MCP eksternal yang sudah didaftarkan dengan input JSON eksplisit."""
    if not _owner_allowed(sender_id, sender_name):
        return {"success": False, "message": "Hanya owner yang dapat memakai MCP eksternal."}
    settings = get_settings()
    if not settings.EXTERNAL_MCP_ENABLED or not settings.EXTERNAL_MCP_ALLOW_CALLS:
        return {"success": False, "message": "Aktifkan EXTERNAL_MCP_ENABLED dan EXTERNAL_MCP_ALLOW_CALLS untuk memanggil tool eksternal."}
    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError:
        return {"success": False, "message": "arguments_json harus JSON object."}
    if not isinstance(arguments, dict):
        return {"success": False, "message": "arguments_json harus JSON object."}
    server = _load_servers().get(name)
    if server is None or not server.enabled:
        return {"success": False, "message": "MCP eksternal tidak ditemukan atau dinonaktifkan."}
    max_age = get_settings().EXTERNAL_MCP_TRUST_MAX_AGE_DAYS
    if max_age > 0:
        if not server.last_reviewed_at:
            return {
                "success": False,
                "message": (
                    f"Server '{server.name}' belum pernah divalidasi (last_reviewed_at kosong)."
                ),
            }
        try:
            reviewed = datetime.fromisoformat(server.last_reviewed_at)
        except ValueError:
            return {
                "success": False,
                "message": f"Server '{server.name}' memiliki last_reviewed_at tidak valid.",
            }
        if reviewed.tzinfo is None:
            reviewed = reviewed.replace(tzinfo=timezone.utc)
        age_days = (datetime.now(timezone.utc) - reviewed).days
        if age_days > max_age:
            return {
                "success": False,
                "message": (
                    f"Server '{server.name}' kadaluarsa: terakhir divalidasi {age_days} hari lalu "
                    f"(batas {max_age})."
                ),
            }
    if server.allowed_tools and tool_name not in server.allowed_tools:
        return {
            "success": False,
            "message": f"Tool '{tool_name}' tidak termasuk allowed_tools untuk MCP '{server.name}'.",
        }
    try:
        result = await asyncio.wait_for(
            _with_session(server, lambda session: session.call_tool(tool_name, arguments)),
            timeout=settings.XNINETZY_MCP_CALL_TIMEOUT_SECONDS,
        )
    except Exception as error:
        return {"success": False, "message": f"MCP eksternal gagal: {type(error).__name__}"}
    content = [getattr(item, "text", str(item)) for item in result.content]
    return {
        "success": not result.isError,
        "server": server.name,
        "tool": tool_name,
        "content": content,
        "untrusted_source": True,
        "risk_level": server.risk_level,
    }


EXTERNAL_MCP_TOOLS = [
    external_mcp_list,
    external_mcp_add,
    external_mcp_remove,
    external_mcp_tools,
    external_mcp_call,
]
