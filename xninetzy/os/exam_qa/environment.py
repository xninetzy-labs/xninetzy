from __future__ import annotations

import os
import platform
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True, slots=True)
class EnvironmentSnapshot:
    captured_at: str
    python_version: str
    platform_name: str
    offline_only: bool
    sandboxed: bool
    notes: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        return {
            "captured_at": self.captured_at,
            "python_version": self.python_version,
            "platform": self.platform_name,
            "offline_only": self.offline_only,
            "sandboxed": self.sandboxed,
            "notes": list(self.notes),
        }


def _detect_offline() -> bool:
    for name in ("XNINETZY_EXAM_OFFLINE", "XNINETZY_OFFLINE_ONLY"):
        value = os.environ.get(name, "").lower()
        if value in {"1", "true", "yes"}:
            return True
    return True


def _detect_sandbox() -> bool:
    for name in ("XNINETZY_EXAM_SANDBOX", "XNINETZY_SANDBOX"):
        value = os.environ.get(name, "").lower()
        if value in {"1", "true", "yes"}:
            return True
    return False


def capture_environment(
    *, now: str | None = None, notes: tuple[str, ...] = ()
) -> EnvironmentSnapshot:
    return EnvironmentSnapshot(
        captured_at=now or datetime.now(timezone.utc).isoformat(),
        python_version=sys.version.split()[0],
        platform_name=platform.platform(),
        offline_only=_detect_offline(),
        sandboxed=_detect_sandbox(),
        notes=notes,
    )