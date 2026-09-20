from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta, timezone
from threading import Lock
from time import monotonic

from xninetzy.core.config import get_settings


def _now() -> datetime:
    return datetime.now(timezone.utc)


_LOCK = Lock()
_STATE: dict[str, tuple[datetime, int]] = defaultdict(lambda: (datetime.now(timezone.utc), 0))


def _now() -> datetime:
    return datetime.now(timezone.utc)


def check(tool_name: str) -> tuple[bool, int]:
    """Return (allowed, remaining) for the tool's hourly retry budget."""
    settings = get_settings()
    budget = max(0, settings.TOOL_RETRY_BUDGET_PER_HOUR)
    with _LOCK:
        window_start, count = _STATE[tool_name]
        if _now() - window_start > timedelta(hours=1):
            _STATE[tool_name] = (_now(), 0)
            count = 0
        if count >= budget:
            return False, 0
        _STATE[tool_name] = (window_start, count + 1)
        return True, max(0, budget - count - 1)


def reset(tool_name: str | None = None) -> int:
    """Reset budget counter. Returns number of keys cleared."""
    with _LOCK:
        if tool_name is None:
            count = len(_STATE)
            _STATE.clear()
            return count
        existed = tool_name in _STATE
        _STATE.pop(tool_name, None)
        return 1 if existed else 0


def stats() -> dict:
    """Return lightweight snapshot: keys tracked + per-key (count, age_seconds)."""
    now = _now()
    with _LOCK:
        keys = list(_STATE.keys())
        sample = {}
        for key in keys[:5]:
            window_start, count = _STATE[key]
            sample[key] = {
                "count": count,
                "age_seconds": round((now - window_start).total_seconds(), 3),
            }
    return {
        "tracked_keys": len(keys),
        "sample": sample,
    }
