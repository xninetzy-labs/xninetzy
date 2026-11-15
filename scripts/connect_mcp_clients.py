"""Plan or apply entry-scoped MCP connection repairs without changing permissions.

Default is a redacted plan. Applying requires an explicit existing SQLite path.
JSONC files containing comments are refused rather than silently rewritten.
"""
from __future__ import annotations

import argparse
import asyncio
import copy
import hashlib
import json
import os
import re
import stat
import tempfile
import time
import tomllib
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCATIONS = {
    "codex": ".codex/config.toml",
    "claude": ".claude.json",
    "opencode": ".config/opencode/opencode.json",
    "opencode-jsonc": ".config/opencode/opencode.jsonc",
    "gemini": ".gemini/settings.json",
    "qwen": ".qwen/settings.json",
    "kilo": ".config/kilo/kilo.jsonc",
    "cursor": ".cursor/mcp.json",
    "vscode": ".config/Code/User/mcp.json",
}


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("Duplicate JSON keys require manual review")
        result[key] = value
    return result


def _key(client: str) -> str:
    if client == "codex":
        return "mcp_servers"
    if client in {"opencode", "opencode-jsonc", "kilo"}:
        return "mcp"
    return "servers" if client == "vscode" else "mcpServers"


def _server_group(obj: dict, client: str) -> dict:
    group = obj.setdefault(_key(client), {})
    if not isinstance(group, dict):
        raise ValueError("MCP server group must be an object")
    if client in {"opencode", "opencode-jsonc"}:
        # Verified OpenCode 2.x schema. Kilo retains its separate flat map.
        servers = group.setdefault("servers", {})
        if not isinstance(servers, dict):
            raise ValueError("OpenCode MCP servers must be an object")
        if "xninetzy" in group:
            legacy = group["xninetzy"]
            if "xninetzy" in servers and servers["xninetzy"] != legacy:
                raise ValueError("Conflicting legacy/current Xninetzy entries require review")
            servers.setdefault("xninetzy", legacy)
            del group["xninetzy"]
        return servers
    return group


def _toml_table(path: tuple[str, ...], data: dict) -> str:
    lines = ["[" + ".".join(json.dumps(key) for key in path) + "]"]
    nested = []
    for key, value in data.items():
        if isinstance(value, dict):
            nested.append((key, value))
        elif isinstance(value, (str, int, float, bool, list)):
            lines.append(f"{json.dumps(key)} = {json.dumps(value)}")
        else:
            raise ValueError("Unsupported TOML value; original configuration was not changed")
    for key, value in nested:
        lines.extend(["", _toml_table((*path, key), value)])
    return "\n".join(lines) + "\n"


def candidate(path: Path, client: str, repo: Path, store: Path, *, source_text: str | None = None) -> str:
    if path.is_symlink():
        raise ValueError("Refusing symlink configuration")
    text = path.read_text(encoding="utf-8") if source_text is None else source_text
    obj = tomllib.loads(text) if client == "codex" else json.loads(text, object_pairs_hook=_unique_object)
    if not isinstance(obj, dict):
        raise ValueError("Configuration must be an object")
    updated = copy.deepcopy(obj)
    group = _server_group(updated, client)
    entry = group.setdefault("xninetzy", {})
    if not isinstance(entry, dict):
        raise ValueError("Xninetzy entry must be an object")
    modern_opencode = client in {"opencode", "opencode-jsonc"}
    if modern_opencode and "enabled" in entry:
        enabled = entry.pop("enabled")
        if not isinstance(enabled, bool):
            raise ValueError("OpenCode enabled flag must be a boolean")
        if "disabled" in entry and entry["disabled"] != (not enabled):
            raise ValueError("Conflicting OpenCode enable flags require review")
        entry["disabled"] = not enabled
    if entry.get("url"):
        raise ValueError("Remote MCP entries require manual transport review")
    python = str(repo / ".venv/bin/python")
    if "cwd" in entry:
        entry["cwd"] = str(repo)
    local = client in {"opencode", "opencode-jsonc", "kilo"}
    entry["command"] = [python, "-m", "xninetzy.interfaces.mcp_server"] if local else python
    if local:
        entry.pop("args", None)
        entry["type"] = "local"
        entry.setdefault("disabled" if modern_opencode else "enabled", False if modern_opencode else True)
    else:
        entry["args"] = ["-m", "xninetzy.interfaces.mcp_server"]
        if client != "codex":
            entry["type"] = "stdio"
    env = entry.setdefault("environment" if local else "env", {})
    if not isinstance(env, dict):
        raise ValueError("MCP environment must be an object")
    env.update({"PYTHONPATH": str(repo), "MCP_RUNTIME_MODE": "host",
                "MCP_HOST_DATA_DIR": str(store.parent), "MCP_HOST_SQLITE_PATH": str(store),
                "SQLITE_PATH": str(store), "XNINETZY_MCP_TRANSPORT": "stdio"})
    if client == "codex":
        entry.setdefault("startup_timeout_sec", 60)
        entry.setdefault("tool_timeout_sec", 180)
        headers = list(re.finditer(r"(?m)^\[([^\n]+)\][ \t]*$", text))
        spans = []
        for index, header in enumerate(headers):
            # TOML quoted keys are equivalent to bare keys. In particular, the
            # renderer emits quoted headers that must be recognized on replan.
            table = tomllib.loads(f"[{header.group(1)}]\n").get("mcp_servers", {})
            if isinstance(table, dict) and "xninetzy" in table:
                end = headers[index + 1].start() if index + 1 < len(headers) else len(text)
                spans.append((header.start(), end))
        rendered = _toml_table(("mcp_servers", "xninetzy"), entry)
        if not spans:
            if "xninetzy" in obj.get("mcp_servers", {}):
                raise ValueError("Unsupported inline TOML layout; review manually")
            result = text.rstrip() + "\n\n" + rendered
        else:
            result = text
            for index, (start, end) in reversed(list(enumerate(spans))):
                result = result[:start] + (rendered + "\n" if index == 0 else "") + result[end:]
        if tomllib.loads(result) != updated:
            raise ValueError("TOML roundtrip changed unrelated configuration")
        return result
    return json.dumps(updated, indent=2, ensure_ascii=False) + "\n"


def plan(path: Path, client: str, repo: Path, store: Path) -> tuple[dict, str]:
    before = path.read_bytes()
    result = candidate(path, client, repo, store, source_text=before.decode("utf-8"))
    return {"client": client, "path": str(path),
            "before_sha256": hashlib.sha256(before).hexdigest(),
            "after_sha256": hashlib.sha256(result.encode()).hexdigest(),
            "changed": before != result.encode(), "command": str(repo / ".venv/bin/python"),
            "module": "xninetzy.interfaces.mcp_server", "store": str(store),
            "permissions": "preserved", "other_settings": "preserved"}, result


def install(path: Path, before_sha256: str, text: str) -> Path:
    if path.is_symlink():
        raise ValueError("Refusing symlink configuration")
    before = path.read_bytes()
    if hashlib.sha256(before).hexdigest() != before_sha256:
        raise ValueError("Configuration changed after planning")
    suffix = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    backup = path.with_name(path.name + ".xninetzy-backup-" + suffix)
    fd = os.open(backup, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(before)
        stream.flush()
        os.fsync(stream.fileno())
    fd, temporary = tempfile.mkstemp(prefix=".xn-mcp-", dir=path.parent)
    try:
        os.fchmod(fd, stat.S_IMODE(path.stat().st_mode))
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        if hashlib.sha256(path.read_bytes()).hexdigest() != before_sha256:
            raise ValueError("Configuration changed during installation")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return backup


async def smoke(home: Path, repo: Path) -> dict:
    """Probe candidate commands with isolated state, never owner databases."""
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    results = []
    with tempfile.TemporaryDirectory(prefix="xn-client-smoke-") as temporary:
        base = Path(temporary)
        for client, rel in LOCATIONS.items():
            path = home / rel
            if not path.is_file():
                continue
            directory = base / client
            directory.mkdir()
            store = directory / "smoke.sqlite3"
            store.touch()
            text = candidate(path, client, repo, store)
            obj = tomllib.loads(text) if client == "codex" else json.loads(text)
            entry = _server_group(obj, client)["xninetzy"]
            if entry.get("enabled") is False or entry.get("disabled") is True:
                results.append({"client": client, "status": "disabled_by_owner"})
                continue
            local = isinstance(entry["command"], list)
            command = entry["command"][0] if local else entry["command"]
            arguments = entry["command"][1:] if local else entry["args"]
            env = dict(os.environ)
            env.update(entry.get("environment" if local else "env", {}))
            for flag in ("AUTO_MEMORY_ENABLED", "AUTO_GRAPH_ENABLED", "AUTO_IMPROVE_ENABLED",
                         "NEO4J_ENABLED", "NEO4J_AUTOSTART_ENABLED", "LIGHTNING_ENABLED",
                         "EXTERNAL_MCP_ENABLED", "OS_SCHEDULER_ENABLED"):
                env[flag] = "false"
            for name in ("DATA_DIR", "BACKUP_DIR", "OUTPUT_DIR", "GENERATED_DOCUMENTS_DIR",
                         "RESEARCH_OUTPUT_DIR", "UNTRACKED_OUTPUT_DIR", "HEBAT_DATA_DIR",
                         "HEBAT_DOWNLOAD_DIR", "OBSIDIAN_VAULT_HOST_PATH", "OBSIDIAN_VAULT_PATH",
                         "WEB_ANALYSIS_DATA_DIR", "VECTOR_DATA_DIR", "GRAPH_VECTOR_DATA_DIR",
                         "VIDEO_OUTPUT_DIR", "XNINETZY_SKILLS_DIR"):
                env[name] = str(directory / name.lower())
            started = time.perf_counter()
            try:
                with (directory / "server.stderr").open("w") as log:
                    parameters = StdioServerParameters(command=command, args=arguments,
                                                       env=env, cwd=str(repo))
                    async with asyncio.timeout(60):
                        async with stdio_client(parameters, errlog=log) as streams:
                            async with ClientSession(*streams) as session:
                                initialized = await session.initialize()
                                if initialized.serverInfo.name != "xninetzy":
                                    raise RuntimeError("unexpected MCP server identity")
                                tools = await session.list_tools()
                                output = await session.call_tool("datetime_now", {})
                                if output.isError or "ISO:" not in str(output):
                                    raise RuntimeError("safe read did not verify")
                    results.append({"client": client, "status": "passed", "tools": len(tools.tools),
                                    "protocol": initialized.protocolVersion,
                                    "seconds": round(time.perf_counter() - started, 3)})
            except Exception as exc:
                results.append({"client": client, "status": "failed", "error": type(exc).__name__})
    return {"candidate_transport_probes": results, "host_configs_modified": False,
            "owner_data_opened": False, "native_client_sessions": "NOT_VERIFIED"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument("--store", type=Path, help="explicit owner-selected existing SQLite file")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--smoke", action="store_true", help="probe candidate commands with temporary state")
    args = parser.parse_args()
    repo = args.repo.resolve()
    if args.smoke:
        if args.apply or args.store:
            parser.error("--smoke cannot modify host configuration or use an owner store")
        report = asyncio.run(smoke(args.home, repo))
        print(json.dumps(report, indent=2))
        probes = report["candidate_transport_probes"]
        return int(not probes or any(row["status"] != "passed" for row in probes))
    if args.store is None:
        parser.error("select --smoke or an explicit --store")
    store = args.store.expanduser()
    if not store.is_absolute() or not store.is_file():
        parser.error("--store must explicitly select an existing absolute database path")
    if not (repo / ".venv/bin/python").is_file():
        parser.error("repository .venv Python is unavailable")
    prepared = []
    for client, rel in LOCATIONS.items():
        path = args.home / rel
        if path.is_file():
            prepared.append((path, *plan(path, client, repo, store)))
    reports = []
    for path, report, text in prepared:
        if args.apply and report["changed"]:
            report["backup"] = str(install(path, report["before_sha256"], text))
        report["applied"] = bool(args.apply and report["changed"])
        reports.append(report)
    print(json.dumps({"clients": reports, "host_prompts_modified": False}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
