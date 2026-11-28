from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Protocol, Sequence

from xninetzy.core.config import expand_path, get_settings
from xninetzy.integrations.kaggle.workspace import workspace_dir

RUNNER = Path(__file__).resolve().parent / "runner" / "sdk_runner.py"
SDK_PROBE = "import kaggle, kagglesdk"


class KaggleBackendError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def to_dict(self) -> dict[str, Any]:
        return {"error_code": self.code, "message": self.message, "retryable": self.code != "KAGGLE_SDK_MISSING"}


@dataclass(frozen=True, slots=True)
class OpResult:
    ok: bool
    data: dict[str, Any] | None = None
    error_type: str | None = None
    error_message: str | None = None
    status_code: int | None = None

    def error_dict(self) -> dict[str, Any]:
        return {
            "type": self.error_type,
            "message": self.error_message,
            "status_code": self.status_code,
        }


Operation = tuple[str, dict[str, Any]]


class Backend(Protocol):
    def run(
        self,
        operations: Sequence[Operation],
        *,
        bearer_token: str | None = None,
        timeout: int | None = None,
    ) -> list[OpResult]: ...


@lru_cache(maxsize=8)
def _supports_sdk(candidate: str) -> bool:
    try:
        completed = subprocess.run(
            [candidate, "-E", "-c", SDK_PROBE],
            capture_output=True,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return completed.returncode == 0


def resolve_python() -> str:
    configured = get_settings().KAGGLE_PYTHON.strip()
    candidates = [expand_path(configured)] if configured else []
    candidates += [sys.executable, "/usr/bin/python3", shutil.which("python3") or ""]
    seen: set[str] = set()
    for candidate in candidates:
        if not candidate or candidate in seen:
            continue
        seen.add(candidate)
        if _supports_sdk(candidate):
            return candidate
    raise KaggleBackendError(
        "KAGGLE_SDK_MISSING",
        "No Python interpreter with the `kaggle` package was found. Install it with "
        "`python3 -m pip install --user kaggle` or point KAGGLE_PYTHON at an interpreter that has it.",
    )


def _decode(operations: Sequence[Operation], completed: subprocess.CompletedProcess[str]) -> list[OpResult]:
    lines = [line for line in completed.stdout.splitlines() if line.startswith("{")]
    if not lines:
        tail = (completed.stderr or "").strip()[-300:]
        raise KaggleBackendError("KAGGLE_RUNNER_PROTOCOL", "Kaggle runner returned no result. " + tail)
    try:
        payload = json.loads(lines[-1])
        raw = payload["results"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise KaggleBackendError("KAGGLE_RUNNER_PROTOCOL", "Kaggle runner returned malformed output") from None
    if not isinstance(raw, list) or len(raw) != len(operations):
        raise KaggleBackendError("KAGGLE_RUNNER_PROTOCOL", "Kaggle runner result count mismatch")
    results: list[OpResult] = []
    for item in raw:
        if item.get("ok"):
            results.append(OpResult(ok=True, data=item.get("data") or {}))
        else:
            error = item.get("error") or {}
            results.append(
                OpResult(
                    ok=False,
                    error_type=error.get("type"),
                    error_message=error.get("message"),
                    status_code=error.get("status_code"),
                )
            )
    return results


class SubprocessBackend:
    def run(
        self,
        operations: Sequence[Operation],
        *,
        bearer_token: str | None = None,
        timeout: int | None = None,
    ) -> list[OpResult]:
        python = resolve_python()
        limit = timeout or get_settings().KAGGLE_RUNNER_TIMEOUT_SECONDS
        payload = json.dumps({"ops": [{"op": name, "args": args} for name, args in operations]})
        environment = {key: value for key, value in os.environ.items() if not key.startswith("PYTHON")}
        if bearer_token:
            environment["KAGGLE_API_TOKEN"] = bearer_token
        try:
            completed = subprocess.run(
                [python, "-E", "-P", str(RUNNER)],
                input=payload,
                capture_output=True,
                text=True,
                timeout=max(10, int(limit)),
                env=environment,
                cwd=str(workspace_dir()),
                check=False,
            )
        except subprocess.TimeoutExpired:
            raise KaggleBackendError(
                "KAGGLE_RUNNER_TIMEOUT",
                f"Kaggle runner exceeded {limit}s; remote state is unknown, reconcile before retrying",
            ) from None
        except OSError as exc:
            raise KaggleBackendError("KAGGLE_RUNNER_UNAVAILABLE", f"Cannot start Kaggle runner: {type(exc).__name__}") from exc
        return _decode(operations, completed)


_ACTIVE: Backend | None = None


def get_backend() -> Backend:
    global _ACTIVE
    if _ACTIVE is None:
        _ACTIVE = SubprocessBackend()
    return _ACTIVE


def set_backend(backend: Backend | None) -> None:
    global _ACTIVE
    _ACTIVE = backend


__all__ = [
    "Backend",
    "KaggleBackendError",
    "OpResult",
    "Operation",
    "RUNNER",
    "SubprocessBackend",
    "get_backend",
    "resolve_python",
    "set_backend",
]
