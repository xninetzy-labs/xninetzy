from __future__ import annotations

import asyncio
import os
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.xninetzy.core.config import Settings, get_settings
from app.xninetzy.db.migrations import run_migrations
from app.xninetzy.db.sqlite import connect, init_db


@dataclass(frozen=True)
class CodingAgentInfo:
    name: str
    binary: str
    allowed: bool
    installed: bool
    model: str


@dataclass(frozen=True)
class CodingAgentResult:
    run_id: str
    runtime: str
    status: str
    output: str
    error: str = ""


def _csv(value: str) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(item.strip().lower() for item in value.split(",") if item.strip())
    )


def subprocess_environment(settings: Settings | None = None) -> dict[str, str]:
    """Build a minimal environment so service secrets are not inherited by agents."""
    s = settings or get_settings()
    allowed = {
        name.strip() for name in s.CODING_AGENT_ENV_ALLOWLIST.split(",") if name.strip()
    }
    return {name: value for name, value in os.environ.items() if name in allowed}


def runtime_catalog(settings: Settings | None = None) -> dict[str, CodingAgentInfo]:
    s = settings or get_settings()
    allowed = set(_csv(s.CODING_AGENT_ALLOWED))
    configured = {
        "internal": ("", ""),
        "codex": (s.CODEX_BIN, s.CODEX_MODEL),
        "claude-code": (s.CLAUDE_CODE_BIN, s.CLAUDE_CODE_MODEL),
        "opencode": (s.OPENCODE_BIN, s.OPENCODE_MODEL),
    }
    return {
        name: CodingAgentInfo(
            name=name,
            binary=binary,
            allowed=name in allowed,
            installed=name == "internal" or bool(shutil.which(binary)),
            model=model.strip(),
        )
        for name, (binary, model) in configured.items()
    }


def validate_runtime(name: str, settings: Settings | None = None) -> CodingAgentInfo:
    normalized = name.strip().lower()
    info = runtime_catalog(settings).get(normalized)
    if info is None:
        raise ValueError(f"Coding agent tidak dikenal: {normalized}")
    if not info.allowed:
        raise ValueError(f"Coding agent '{normalized}' tidak diizinkan.")
    if not info.installed:
        raise ValueError(
            f"Binary untuk '{normalized}' tidak ditemukan di PATH service AI."
        )
    return info


def resolve_workspace(
    requested: str | None = None, settings: Settings | None = None
) -> Path:
    s = settings or get_settings()
    root = Path(s.CODING_AGENT_ALLOWED_ROOT).expanduser().resolve()
    candidate = Path(requested or s.CODING_AGENT_WORKSPACE).expanduser()
    if not candidate.is_absolute():
        candidate = root / candidate
    workspace = candidate.resolve()
    if workspace != root and root not in workspace.parents:
        raise ValueError(f"Workspace harus berada di dalam {root}")
    if not workspace.is_dir():
        raise ValueError(f"Workspace tidak ditemukan: {workspace}")
    return workspace


def build_command(
    runtime: str, task: str, workspace: Path, settings: Settings | None = None
) -> list[str]:
    s = settings or get_settings()
    info = validate_runtime(runtime, s)
    if runtime == "codex":
        command = [
            info.binary,
            "exec",
            "--json",
            "--ephemeral",
            "--color",
            "never",
            "-C",
            str(workspace),
            "--sandbox",
            s.CODING_AGENT_SANDBOX,
        ]
        if info.model:
            command.extend(["--model", info.model])
        command.append(task)
        return command
    if runtime == "claude-code":
        command = [
            info.binary,
            "-p",
            "--output-format",
            "json",
            "--no-session-persistence",
            "--permission-mode",
            "acceptEdits",
        ]
        if info.model:
            command.extend(["--model", info.model])
        command.append(task)
        return command
    if runtime == "opencode":
        command = [info.binary, "run", "--format", "json", "--dir", str(workspace)]
        if info.model:
            command.extend(["--model", info.model])
        command.append(task)
        return command
    raise ValueError(
        "Runtime 'internal' memakai agent chat Xninetzy; kirim permintaan tanpa /code."
    )


def _extract_output(runtime: str, stdout: str) -> str:
    if runtime == "claude-code":
        try:
            payload = json.loads(stdout)
            if isinstance(payload, dict) and payload.get("result"):
                return str(payload["result"])
        except json.JSONDecodeError:
            pass

    messages: list[str] = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except json.JSONDecodeError:
            continue
        if runtime == "codex":
            item = event.get("item") if isinstance(event, dict) else None
            if (
                isinstance(item, dict)
                and item.get("type") == "agent_message"
                and item.get("text")
            ):
                messages.append(str(item["text"]))
        elif runtime == "opencode" and isinstance(event, dict):
            part = event.get("part")
            if (
                isinstance(part, dict)
                and part.get("type") == "text"
                and part.get("text")
            ):
                messages.append(str(part["text"]))
    return messages[-1] if messages else stdout.strip()


def _record_start(
    run_id: str, user_id: str, chat_id: str, runtime: str, task: str, workspace: Path
) -> None:
    init_db()
    run_migrations()
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute(
            "INSERT INTO coding_agent_runs "
            "(id, user_id, chat_id, runtime, task, workspace, status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, 'running', ?)",
            (run_id, user_id, chat_id, runtime, task, str(workspace), now),
        )


def _record_finish(run_id: str, status: str, output: str, error: str) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with connect() as conn:
        conn.execute(
            "UPDATE coding_agent_runs SET status = ?, output = ?, error = ?, finished_at = ? WHERE id = ?",
            (status, output, error, now, run_id),
        )


async def run_coding_agent(
    runtime: str,
    task: str,
    *,
    user_id: str,
    chat_id: str,
    workspace: str | None = None,
    settings: Settings | None = None,
) -> CodingAgentResult:
    s = settings or get_settings()
    if not s.CODING_AGENT_ENABLED:
        raise ValueError(
            "Coding-agent runtime belum diaktifkan (CODING_AGENT_ENABLED=false)."
        )
    if not task.strip():
        raise ValueError("Task coding tidak boleh kosong.")

    resolved_workspace = resolve_workspace(workspace, s)
    command = build_command(runtime, task.strip(), resolved_workspace, s)
    run_id = uuid4().hex
    _record_start(run_id, user_id, chat_id, runtime, task.strip(), resolved_workspace)

    process = await asyncio.create_subprocess_exec(
        *command,
        cwd=resolved_workspace,
        stdin=asyncio.subprocess.DEVNULL,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        env=subprocess_environment(s),
    )
    try:
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            process.communicate(), timeout=s.CODING_AGENT_TIMEOUT_SECONDS
        )
    except TimeoutError:
        process.kill()
        await process.communicate()
        error = f"Timeout setelah {s.CODING_AGENT_TIMEOUT_SECONDS:g} detik."
        _record_finish(run_id, "timeout", "", error)
        return CodingAgentResult(run_id, runtime, "timeout", "", error)

    stdout = stdout_bytes.decode("utf-8", errors="replace")
    stderr = stderr_bytes.decode("utf-8", errors="replace")
    output = _extract_output(runtime, stdout)[-s.CODING_AGENT_MAX_OUTPUT_CHARS :]
    error = stderr[-s.CODING_AGENT_MAX_OUTPUT_CHARS :]
    status = "completed" if process.returncode == 0 else "failed"
    _record_finish(run_id, status, output, error)
    return CodingAgentResult(run_id, runtime, status, output, error)
