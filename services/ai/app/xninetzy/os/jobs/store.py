from __future__ import annotations

from datetime import datetime, timedelta

from app.xninetzy.db.sqlite import connect, init_db

TERMINAL_STATUSES = {"delivered", "succeeded", "delivery_uncertain"}


class JobStore:
    def claim(
        self,
        *,
        job_key: str,
        job_type: str,
        owner_id: str,
        scheduled_for: str,
        now: datetime,
        lease_seconds: int,
    ) -> dict | None:
        init_db()
        now_iso = now.isoformat()
        lease_until = (now + timedelta(seconds=max(1, lease_seconds))).isoformat()
        with connect() as conn:
            conn.execute("BEGIN IMMEDIATE")
            row = conn.execute(
                "SELECT * FROM os_job_runs WHERE job_key=?", (job_key,)
            ).fetchone()
            if row is None:
                cursor = conn.execute(
                    """
                    INSERT INTO os_job_runs
                      (job_key, job_type, owner_id, scheduled_for, status, attempts,
                       lease_until, retryable, created_at, updated_at)
                    VALUES (?,?,?,?, 'running', 1, ?, 0, ?, ?)
                    """,
                    (
                        job_key,
                        job_type,
                        owner_id,
                        scheduled_for,
                        lease_until,
                        now_iso,
                        now_iso,
                    ),
                )
                claimed = conn.execute(
                    "SELECT * FROM os_job_runs WHERE id=?", (cursor.lastrowid,)
                ).fetchone()
                return dict(claimed) if claimed else None

            data = dict(row)
            if (
                data["status"] in TERMINAL_STATUSES
                or data["status"] == "delivery_started"
            ):
                return None
            reclaim_running = data["status"] == "running" and (
                not data["lease_until"] or data["lease_until"] <= now_iso
            )
            retry_failed = (
                data["status"] == "failed"
                and bool(data["retryable"])
                and (not data["next_retry_at"] or data["next_retry_at"] <= now_iso)
            )
            if not reclaim_running and not retry_failed:
                return None
            conn.execute(
                """
                UPDATE os_job_runs SET status='running', attempts=attempts+1,
                  lease_until=?, retryable=0, next_retry_at=NULL, last_error=NULL,
                  updated_at=? WHERE id=?
                """,
                (lease_until, now_iso, data["id"]),
            )
            claimed = conn.execute(
                "SELECT * FROM os_job_runs WHERE id=?", (data["id"],)
            ).fetchone()
        return dict(claimed) if claimed else None

    def start_delivery(self, job_id: int, output: str, now: datetime) -> bool:
        with connect() as conn:
            result = conn.execute(
                """
                UPDATE os_job_runs SET status='delivery_started', prepared_output=?,
                  lease_until=NULL, updated_at=? WHERE id=? AND status='running'
                """,
                (output, now.isoformat(), job_id),
            )
        return result.rowcount > 0

    def mark_delivered(self, job_id: int, result: str, now: datetime) -> None:
        self._finish(job_id, "delivered", result, now)

    def mark_succeeded(self, job_id: int, result: str, now: datetime) -> None:
        self._finish(job_id, "succeeded", result, now)

    def mark_failed(
        self,
        job_id: int,
        error: str,
        now: datetime,
        *,
        retryable: bool,
        retry_delay_seconds: int,
        delivery_uncertain: bool = False,
    ) -> None:
        status = "delivery_uncertain" if delivery_uncertain else "failed"
        next_retry = (
            (now + timedelta(seconds=max(1, retry_delay_seconds))).isoformat()
            if retryable
            else None
        )
        with connect() as conn:
            conn.execute(
                """
                UPDATE os_job_runs SET status=?, last_error=?, retryable=?,
                  next_retry_at=?, lease_until=NULL, updated_at=?,
                  completed_at=CASE WHEN ? THEN ? ELSE completed_at END
                WHERE id=?
                """,
                (
                    status,
                    error[:2000],
                    int(retryable),
                    next_retry,
                    now.isoformat(),
                    int(not retryable),
                    now.isoformat(),
                    job_id,
                ),
            )

    def get(self, job_key: str) -> dict | None:
        with connect() as conn:
            row = conn.execute(
                "SELECT * FROM os_job_runs WHERE job_key=?", (job_key,)
            ).fetchone()
        return dict(row) if row else None

    def list_recent(self, limit: int = 20) -> list[dict]:
        with connect() as conn:
            rows = conn.execute(
                "SELECT * FROM os_job_runs ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [dict(row) for row in rows]

    def reconcile_orphaned_deliveries(self, now: datetime) -> int:
        """Fail closed after restart when a prior WA send outcome is unknowable."""
        with connect() as conn:
            result = conn.execute(
                """
                UPDATE os_job_runs
                SET status='delivery_uncertain',
                    last_error=COALESCE(last_error, 'Process restarted during delivery'),
                    retryable=0, lease_until=NULL, updated_at=?, completed_at=?
                WHERE status='delivery_started'
                """,
                (now.isoformat(), now.isoformat()),
            )
        return result.rowcount

    def _finish(self, job_id: int, status: str, result: str, now: datetime) -> None:
        with connect() as conn:
            conn.execute(
                """
                UPDATE os_job_runs SET status=?, result_output=?, retryable=0,
                  lease_until=NULL, updated_at=?, completed_at=? WHERE id=?
                """,
                (status, result[:12000], now.isoformat(), now.isoformat(), job_id),
            )
