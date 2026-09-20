from __future__ import annotations

import time

from xninetzy.db.sqlite import connect


_CAP_CACHE: dict[str, tuple[bool, float]] = {}
_DISABLED_CACHE: tuple[str, ...] | None = None
_DISABLED_TS: float = 0.0

DEFAULT_TTL_SECONDS: float = 30.0


def _now() -> float:
    return time.monotonic()


def _is_enabled_fresh(capability: str) -> bool | None:
    cached = _CAP_CACHE.get(capability)
    if cached is None:
        return None
    enabled, ts = cached
    if _now() - ts > DEFAULT_TTL_SECONDS:
        return None
    return enabled


def _set_cap(capability: str, enabled: bool) -> None:
    _CAP_CACHE[capability] = (enabled, _now())


def _set_disabled(disabled: tuple[str, ...]) -> None:
    global _DISABLED_CACHE, _DISABLED_TS
    _DISABLED_CACHE = disabled
    _DISABLED_TS = _now()


def invalidate_capability_cache() -> None:
    _CAP_CACHE.clear()
    global _DISABLED_CACHE, _DISABLED_TS
    _DISABLED_CACHE = None
    _DISABLED_TS = 0.0


def capability_toggle_lookup(capability: str) -> bool:
    """Read capability toggle, with TTL cache. Default enabled."""
    cached = _is_enabled_fresh(capability)
    if cached is not None:
        return cached
    try:
        with connect() as conn:
            row = conn.execute(
                "SELECT enabled FROM capability_toggles WHERE capability=?",
                (capability,),
            ).fetchone()
    except Exception:
        return True
    enabled = bool(int(row["enabled"])) if row else True
    _set_cap(capability, enabled)
    return enabled


def disabled_capabilities() -> tuple[str, ...]:
    """Bulk read disabled capabilities with TTL."""
    global _DISABLED_CACHE, _DISABLED_TS
    if _DISABLED_CACHE is not None and _now() - _DISABLED_TS <= DEFAULT_TTL_SECONDS:
        return _DISABLED_CACHE
    try:
        with connect() as conn:
            rows = conn.execute(
                "SELECT capability FROM capability_toggles WHERE enabled=0"
            ).fetchall()
    except Exception:
        return ()
    disabled = tuple(str(r["capability"]) for r in rows)
    _set_disabled(disabled)
    return disabled


def write_capability_toggle(
    capability: str,
    enabled: bool,
) -> None:
    """Write + invalidate caches atomically."""
    from datetime import datetime, timezone

    from xninetzy.db.migrations import run_migrations

    run_migrations()
    with connect() as conn:
        conn.execute(
            """
            INSERT OR REPLACE INTO capability_toggles
              (capability, enabled, updated_at, updated_by)
            VALUES (?, ?, ?, ?)
            """,
            (
                capability,
                1 if enabled else 0,
                datetime.now(timezone.utc).isoformat(),
                "system",
            ),
        )
    _set_cap(capability, enabled)


def clear_capability_toggle(capability: str) -> None:

    from xninetzy.db.migrations import run_migrations

    run_migrations()
    with connect() as conn:
        conn.execute(
            "DELETE FROM capability_toggles WHERE capability=?",
            (capability,),
        )
    _CAP_CACHE.pop(capability, None)
