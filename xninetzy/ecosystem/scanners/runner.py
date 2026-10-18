from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from xninetzy.os.security.guards import redact_secrets

STATUS_OK = "OK"
STATUS_MISSING = "TOOL_MISSING"
STATUS_BLOCKED = "TOOL_BLOCKED"
STATUS_TIMEOUT = "TIMEOUT"
STATUS_FAILED = "FAILED"
OUTPUT_LIMIT = 4000
_FORBIDDEN_MOUNT_MARKERS = ("docker.sock",)

Executor = Callable[..., subprocess.CompletedProcess]


@dataclass(slots=True)
class RunSpec:
    tool: str
    image: str
    args: list[str]
    source: Path | None = None
    out_mount: str = "/out"
    network: str = "none"
    memory: str = "1g"
    pids_limit: int = 256
    cpus: str = "1.0"
    timeout: int = 600
    ok_codes: frozenset[int] = frozenset({0})
    capture_stdout_to: str = ""
    env: dict[str, str] = field(default_factory=dict)
    tmpfs: list[str] = field(default_factory=list)
    cache_dir: Path | None = None
    extra_mounts: list[tuple[str, str, str]] = field(default_factory=list)
    read_only_rootfs: bool = True
    entrypoint: str = ""
    name: str = ""


@dataclass(slots=True)
class RunResult:
    status: str
    returncode: int = 0
    stdout: str = ""
    stderr: str = ""
    output_path: Path | None = None
    detail: str = ""
    command: list[str] = field(default_factory=list)


def docker_binary() -> str | None:
    return shutil.which("docker")


def image_reference(image: str, digest: str) -> str:
    if digest and "@" not in image:
        head, sep, tail = image.rpartition("/")
        return f"{head}{sep}{tail.split(':', 1)[0]}@{digest}"
    return image


def build_command(spec: RunSpec, session_dir: Path, *, uid: int | None = None, gid: int | None = None) -> list[str]:
    for host, _container, _mode in _all_mounts(spec, session_dir):
        if any(marker in host for marker in _FORBIDDEN_MOUNT_MARKERS):
            raise ValueError(f"mount ditolak: {host}")
    user = f"{os.getuid() if uid is None else uid}:{os.getgid() if gid is None else gid}"
    command = [
        "docker", "run", "--rm",
        "--cap-drop=ALL",
        "--security-opt=no-new-privileges",
        "--memory", spec.memory,
        "--memory-swap", spec.memory,
        "--pids-limit", str(spec.pids_limit),
        "--cpus", spec.cpus,
        "--network", spec.network,
        "--user", user,
        "--tmpfs", "/tmp:rw,size=256m",
        "-e", "HOME=/tmp",
    ]
    if spec.read_only_rootfs:
        command.append("--read-only")
    for entry in spec.tmpfs:
        command.extend(["--tmpfs", entry])
    for key, value in sorted(spec.env.items()):
        command.extend(["-e", f"{key}={value}"])
    for host, container, mode in _all_mounts(spec, session_dir):
        command.extend(["-v", f"{host}:{container}:{mode}"])
    if spec.entrypoint:
        command.extend(["--entrypoint", spec.entrypoint])
    if spec.name:
        command.extend(["--name", spec.name])
    command.append(spec.image)
    command.extend(spec.args)
    return command


def _all_mounts(spec: RunSpec, session_dir: Path) -> list[tuple[str, str, str]]:
    mounts: list[tuple[str, str, str]] = []
    if spec.source is not None:
        mounts.append((str(spec.source), "/src", "ro"))
    mounts.append((str(session_dir), spec.out_mount, "rw"))
    if spec.cache_dir is not None:
        mounts.append((str(spec.cache_dir), "/cache", "rw"))
    mounts.extend(spec.extra_mounts)
    return mounts


def image_present(image: str, executor: Executor = subprocess.run) -> tuple[bool, str]:
    binary = docker_binary()
    if binary is None:
        return False, "docker tidak ditemukan"
    try:
        proc = executor(
            [binary, "image", "inspect", "--format", "{{json .RepoDigests}}", image],
            capture_output=True, text=True, timeout=30, check=False,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        return False, f"docker tidak dapat dijalankan: {type(exc).__name__}"
    if proc.returncode != 0:
        return False, (proc.stderr or "image tidak ditemukan").strip()[:200]
    return True, (proc.stdout or "").strip()


def run(
    spec: RunSpec,
    session_dir: Path,
    *,
    executor: Executor = subprocess.run,
    uid: int | None = None,
    gid: int | None = None,
) -> RunResult:
    if docker_binary() is None:
        return RunResult(STATUS_MISSING, detail="docker tidak ditemukan")
    present, info = image_present(spec.image, executor)
    if not present:
        return RunResult(STATUS_MISSING, detail=f"image {spec.image} tidak tersedia lokal; jalankan: docker pull {spec.image}")
    session_dir.mkdir(parents=True, exist_ok=True)
    if spec.cache_dir is not None:
        spec.cache_dir.mkdir(parents=True, exist_ok=True)
    try:
        command = build_command(spec, session_dir, uid=uid, gid=gid)
    except ValueError as exc:
        return RunResult(STATUS_BLOCKED, detail=str(exc))
    try:
        proc = executor(command, capture_output=True, text=True, timeout=spec.timeout, check=False)
    except subprocess.TimeoutExpired:
        return RunResult(STATUS_TIMEOUT, detail=f"melebihi {spec.timeout}s", command=command)
    except (OSError, subprocess.SubprocessError) as exc:
        return RunResult(STATUS_FAILED, detail=type(exc).__name__, command=command)
    stdout = proc.stdout or ""
    output_path: Path | None = None
    if spec.capture_stdout_to:
        output_path = session_dir / spec.capture_stdout_to
        output_path.write_text(stdout, encoding="utf-8")
    status = STATUS_OK if proc.returncode in spec.ok_codes else STATUS_FAILED
    return RunResult(
        status=status,
        returncode=proc.returncode,
        stdout=redact_secrets(stdout)[:OUTPUT_LIMIT] if not spec.capture_stdout_to else "",
        stderr=redact_secrets(proc.stderr or "")[:OUTPUT_LIMIT],
        output_path=output_path,
        detail="" if status == STATUS_OK else f"exit {proc.returncode}",
        command=command,
    )
