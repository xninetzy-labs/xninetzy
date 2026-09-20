from __future__ import annotations

from datetime import datetime, timedelta, timezone

from xninetzy.core.config import get_settings
from xninetzy.db.sqlite import connect


def _now() -> datetime:
    return datetime.now(timezone.utc)


def prune_memories(retention_days: int | None = None, per_user_cap: int | None = None) -> dict:
    """Mark inactive old memories. Bounded by retention_days + per_user_cap."""
    settings = get_settings()
    days = retention_days if retention_days is not None else settings.MEMORY_RETENTION_DAYS
    cap = per_user_cap if per_user_cap is not None else settings.MEMORY_PER_USER_CAP
    cutoff = (_now() - timedelta(days=days)).isoformat()
    summary = {"deactivated_old": 0, "capped": 0}
    with connect() as conn:
        cur = conn.execute(
            """
            UPDATE memories
            SET is_active = 0, updated_at = ?
            WHERE is_active = 1
              AND COALESCE(created_at, updated_at, '') < ?
              AND importance < ?
            """,
            (_now().isoformat(), cutoff, settings.MEMORY_RETENTION_IMPORTANCE_FLOOR),
        )
        summary["deactivated_old"] = int(cur.rowcount or 0)
        if cap and cap > 0:
            rows = conn.execute(
                """
                SELECT id FROM memories
                WHERE user_id IN (SELECT DISTINCT user_id FROM memories WHERE is_active = 1)
                  AND is_active = 1
                ORDER BY user_id, importance ASC, id ASC
                """
            ).fetchall()
            by_user: dict[str, list[int]] = {}
            for row in rows:
                by_user.setdefault(row["id"] if False else None, []).append(row["id"])
            user_total = conn.execute(
                "SELECT user_id, COUNT(*) c FROM memories WHERE is_active=1 GROUP BY user_id"
            ).fetchall()
            for row in user_total:
                if row["c"] <= cap:
                    continue
                to_kill = conn.execute(
                    """
                    SELECT id FROM memories
                    WHERE user_id=? AND is_active=1
                    ORDER BY importance ASC, id ASC
                    LIMIT ?
                    """,
                    (row["user_id"], row["c"] - cap),
                ).fetchall()
                ids = [r["id"] for r in to_kill]
                if not ids:
                    continue
                placeholders = ",".join("?" for _ in ids)
                cur = conn.execute(
                    f"UPDATE memories SET is_active=0, updated_at=? WHERE id IN ({placeholders})",
                    [_now().isoformat(), *ids],
                )
                summary["capped"] += int(cur.rowcount or 0)
    return summary


def prune_improvement_signals(retention_days: int | None = None) -> dict:
    """Soft-delete resolved improvement proposals older than retention window."""
    settings = get_settings()
    days = (
        retention_days
        if retention_days is not None
        else getattr(settings, "IMPROVEMENT_RETENTION_DAYS", 90)
    )
    cutoff = (_now() - timedelta(days=days)).isoformat()
    with connect() as conn:
        cur = conn.execute(
            """
            UPDATE improvement_proposals
            SET status = 'retired'
            WHERE status IN ('approved', 'rejected', 'superseded')
              AND COALESCE(updated_at, created_at, '') < ?
            """,
            (cutoff,),
        )
    return {"retired": int(cur.rowcount or 0)}
