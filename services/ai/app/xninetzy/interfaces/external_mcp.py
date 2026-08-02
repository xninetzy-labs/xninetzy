from __future__ import annotations

import asyncio
import io
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from langchain_core.tools import tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from app.xninetzy.core.config import get_settings
from app.xninetzy.os.research.permissions import is_owner_admin


_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_-]{1,63}$")


@dataclass(frozen=True, slots=True)
class ExternalMcpServer:
    name: str
    command: str
    args: list[str]
    env_vars: list[str]
    enabled: bool


def _registry_path() -> Path:
    return Path(get_settings().EXTERNAL_MCP_REGISTRY_PATH).expanduser()


def _load_servers() -> dict[str, ExternalMcpServer]:
    path = _registry_path()
    if not path.is_file():
        return {}
    raw = json.loads(path.read_text(encoding="utf-8"))
    servers: dict[str, ExternalMcpServer] = {}
    for entry in raw.get("servers", []):
        server = ExternalMcpServer(
            name=str(entry["name"]),
            command=str(entry["command"]),
            args=[str(value) for value in entry.get("args", [])],
            env_vars=[str(value) for value in entry.get("env_vars", [])],
            enabled=bool(entry.get("enabled", True)),
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
    }


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
    normalized_args = [str(value) for value in args]
    normalized_env_vars = [str(value) for value in env_vars]
    error = _validate_server(name, command, normalized_args, normalized_env_vars)
    if error:
        return {"success": False, "message": error}
    servers = _load_servers()
    server = ExternalMcpServer(name, command, normalized_args, normalized_env_vars, enabled)
    if name not in servers and len(servers) >= getattr(get_settings(), "EXTERNAL_MCP_MAX_SERVERS", 8):
        return {"success": False, "message": "Batas jumlah MCP eksternal tercapai."}
    servers[name] = server
    _save_servers(servers)
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
            timeout=settings.EXTERNAL_MCP_TIMEOUT_SECONDS,
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
    try:
        result = await asyncio.wait_for(
            _with_session(server, lambda session: session.call_tool(tool_name, arguments)),
            timeout=settings.EXTERNAL_MCP_TIMEOUT_SECONDS,
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
    }


EXTERNAL_MCP_TOOLS = [
    external_mcp_list,
    external_mcp_add,
    external_mcp_remove,
    external_mcp_tools,
    external_mcp_call,
]
