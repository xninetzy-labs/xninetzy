from __future__ import annotations

import asyncio
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Awaitable, Callable
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import Settings, get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.db.sqlite import connect
from app.xninetzy.ecosystem.context_builder import build_personal_context
from app.xninetzy.interfaces.whatsapp.client import call_wa_tool
from app.xninetzy.os.jobs.store import JobStore

logger = logging.getLogger(__name__)

MessageSender = Callable[[str, str], Awaitable[None]]
HebatRunner = Callable[[str], Awaitable[str]]


@dataclass(frozen=True)
class JobSpec:
    key: str
    job_type: str
    scheduled_for: str
    delivery: bool


def owner_notification_jid(settings: Settings | None = None) -> str | None:
    active = settings or get_settings()
    raw = (
        active.OS_NOTIFY_CHAT_ID
        or active.HEBAT_NOTIFY_CHAT_ID
        or active.ADMIN_JID
        or ""
    ).strip()
    if not raw:
        return None
    if "@" not in raw:
        return f"{raw}@s.whatsapp.net"
    return raw


def due_job_specs(now: datetime, settings: Settings | None = None) -> list[JobSpec]:
    active = settings or get_settings()
    local = _local_time(now, active)
    date_key = local.date().isoformat()
    specs: list[JobSpec] = []
    if active.MORNING_BRIEFING_ENABLED and local.hour >= active.MORNING_BRIEFING_HOUR:
        specs.append(
            JobSpec(
                f"morning_briefing:{date_key}",
                "morning_briefing",
                local.replace(
                    hour=active.MORNING_BRIEFING_HOUR, minute=0, second=0, microsecond=0
                ).isoformat(),
                True,
            )
        )
    if active.EVENING_CHECKIN_ENABLED and local.hour >= active.EVENING_CHECKIN_HOUR:
        specs.append(
            JobSpec(
                f"evening_checkin:{date_key}",
                "evening_checkin",
                local.replace(
                    hour=active.EVENING_CHECKIN_HOUR, minute=0, second=0, microsecond=0
                ).isoformat(),
                True,
            )
        )
    if (
        active.WEEKLY_REVIEW_ENABLED
        and local.weekday() == active.WEEKLY_REVIEW_WEEKDAY
        and local.hour >= active.WEEKLY_REVIEW_HOUR
    ):
        year, week, _ = local.isocalendar()
        specs.append(
            JobSpec(
                f"weekly_review:{year}-W{week:02d}",
                "weekly_review",
                local.replace(
                    hour=active.WEEKLY_REVIEW_HOUR, minute=0, second=0, microsecond=0
                ).isoformat(),
                True,
            )
        )
    if active.HEBAT_PERIODIC_SYNC_ENABLED:
        interval = max(1, active.HEBAT_SYNC_INTERVAL_MINUTES)
        bucket = int(local.timestamp()) // (interval * 60)
        specs.append(
            JobSpec(
                f"hebat_sync:{bucket}",
                "hebat_sync",
                datetime.fromtimestamp(
                    bucket * interval * 60, tz=local.tzinfo
                ).isoformat(),
                False,
            )
        )
    return specs


async def run_os_job_tick(
    *,
    now: datetime | None = None,
    store: JobStore | None = None,
    sender: MessageSender | None = None,
    hebat_runner: HebatRunner | None = None,
) -> dict:
    settings = get_settings()
    current = _local_time(now, settings)
    target = owner_notification_jid(settings)
    stats = {
        "claimed": 0,
        "delivered": 0,
        "succeeded": 0,
        "failed": 0,
        "skipped": 0,
        "target_configured": bool(target),
    }
    if not settings.OS_SCHEDULER_ENABLED:
        return stats
    jobs = store or JobStore()
    for spec in due_job_specs(current, settings):
        if not target:
            stats["skipped"] += 1
            continue
        claimed = jobs.claim(
            job_key=spec.key,
            job_type=spec.job_type,
            owner_id=target,
            scheduled_for=spec.scheduled_for,
            now=current,
            lease_seconds=settings.OS_JOB_LEASE_SECONDS,
        )
        if not claimed:
            stats["skipped"] += 1
            continue
        stats["claimed"] += 1
        try:
            if spec.job_type == "hebat_sync":
                result = await (hebat_runner or _run_hebat_sync)(target)
                jobs.mark_succeeded(claimed["id"], result, current)
                stats["succeeded"] += 1
                continue
            message = build_scheduled_message(spec.job_type, target, current)
            if not jobs.start_delivery(claimed["id"], message, current):
                stats["skipped"] += 1
                continue
            try:
                await (sender or _send_message)(target, message)
            except Exception as error:
                jobs.mark_failed(
                    claimed["id"],
                    str(error),
                    current,
                    retryable=False,
                    retry_delay_seconds=settings.OS_JOB_RETRY_DELAY_SECONDS,
                    delivery_uncertain=True,
                )
                stats["failed"] += 1
                continue
            jobs.mark_delivered(claimed["id"], "WhatsApp delivery accepted", current)
            stats["delivered"] += 1
        except Exception as error:
            logger.exception("OS scheduled job failed: %s", spec.key)
            jobs.mark_failed(
                claimed["id"],
                str(error),
                current,
                retryable=not spec.delivery,
                retry_delay_seconds=settings.OS_JOB_RETRY_DELAY_SECONDS,
            )
            stats["failed"] += 1
    return stats


async def os_job_loop() -> None:
    settings = get_settings()
    if not settings.OS_SCHEDULER_ENABLED:
        return
    await asyncio.sleep(max(0, settings.OS_SCHEDULER_STARTUP_DELAY_SECONDS))
    reconciled = JobStore().reconcile_orphaned_deliveries(_local_time(None, settings))
    if reconciled:
        logger.warning(
            "Marked %d interrupted WA deliveries as delivery_uncertain", reconciled
        )
    while True:
        try:
            await run_os_job_tick()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Unexpected OS scheduler tick failure")
        await asyncio.sleep(max(5, settings.OS_SCHEDULER_POLL_SECONDS))


def build_scheduled_message(job_type: str, chat_id: str, now: datetime) -> str:
    if job_type == "morning_briefing":
        return build_morning_briefing(chat_id, now)
    if job_type == "evening_checkin":
        return build_evening_checkin(chat_id, now)
    if job_type == "weekly_review":
        return build_weekly_review(chat_id, now)
    raise ValueError(f"Unknown delivery job type: {job_type}")


def get_data_freshness(now: datetime | None = None) -> dict:
    current = _local_time(now, get_settings())
    with connect() as conn:
        hebat = conn.execute(
            """
            SELECT MAX(value) AS latest FROM (
              SELECT MAX(last_synced_at) AS value FROM hebat_courses
              UNION ALL SELECT MAX(last_synced_at) FROM hebat_activities
              UNION ALL SELECT MAX(last_synced_at) FROM hebat_assignments
            )
            """
        ).fetchone()["latest"]
        knowledge = conn.execute(
            "SELECT MAX(updated_at) AS latest FROM knowledge_sources"
        ).fetchone()["latest"]
    threshold = max(1, get_settings().HEBAT_SYNC_INTERVAL_MINUTES) * 2
    return {
        "hebat": _freshness_item(hebat, current, threshold),
        "knowledge": _freshness_item(knowledge, current, 24 * 60),
    }


def build_morning_briefing(chat_id: str, now: datetime) -> str:
    context = build_personal_context(chat_id, "morning briefing")
    freshness = get_data_freshness(now)
    lines = [f"🌅 *Morning Briefing — {now:%d %B %Y}*"]
    lines += _context_lines(context)
    lines += ["", "*Freshness data:*", _freshness_line("HEBAT", freshness["hebat"])]
    if freshness["hebat"]["stale"]:
        lines.append(
            "⚠️ Deadline mungkin belum terbaru. Jalankan `hebat_sync_assignments`."
        )
    lines += ["", "Fokuskan satu task kecil, selesaikan, lalu catat hasil belajarnya."]
    return "\n".join(lines)


def build_evening_checkin(chat_id: str, now: datetime) -> str:
    context = build_personal_context(chat_id, "evening check-in")
    counts = _event_counts(now.replace(hour=0, minute=0, second=0, microsecond=0))
    completed = counts.get("task_completed", 0)
    lines = [f"🌙 *Evening Check-in — {now:%d %B %Y}*", ""]
    lines.append(f"Task selesai hari ini: *{completed}*")
    if context["habit_status"]:
        lines.append("Habit: " + " | ".join(context["habit_status"][:5]))
    lines += [
        "",
        "Balas dengan mood, energi, fokus, dan satu pelajaran hari ini.",
        "Atau gunakan `/review`.",
    ]
    return "\n".join(lines)


def build_weekly_review(chat_id: str, now: datetime) -> str:
    context = build_personal_context(chat_id, "weekly review")
    counts = _event_counts(now - timedelta(days=7))
    lines = [f"📊 *Weekly Review — {now:%Y}-W{now.isocalendar().week:02d}*", ""]
    lines.append(f"Task selesai: *{counts.get('task_completed', 0)}*")
    lines.append(f"Habit dicatat: *{counts.get('habit_logged', 0)}*")
    lines.append(f"Workout dicatat: *{counts.get('workout_logged', 0)}*")
    if context["active_roadmaps"]:
        lines += ["", "Roadmap: " + " | ".join(context["active_roadmaps"][:3])]
    if context["active_goals"]:
        lines.append("Goal aktif: " + " | ".join(context["active_goals"][:3]))
    lines += [
        "",
        "Pilih: lanjutkan, sederhanakan, atau hentikan komitmen yang tidak lagi relevan.",
    ]
    return "\n".join(lines)


def _context_lines(context: dict) -> list[str]:
    lines: list[str] = []
    if context.get("attention_queue"):
        lines += [
            "",
            "*Attention queue:*",
            *[f"• {item}" for item in context["attention_queue"]],
        ]
    if context.get("os_inbox_count"):
        lines.append(f"📥 {context['os_inbox_count']} capture perlu ditriage.")
    if context["today_tasks"]:
        lines += [
            "",
            "*Task hari ini:*",
            *[f"• {item}" for item in context["today_tasks"]],
        ]
    else:
        lines += ["", "Belum ada task due hari ini."]
    if context["urgent_deadlines"]:
        lines += [
            "",
            "*Deadline HEBAT:*",
            *[f"• {item}" for item in context["urgent_deadlines"]],
        ]
    if context["active_roadmaps"]:
        lines += [
            "",
            "*Roadmap:*",
            *[f"• {item}" for item in context["active_roadmaps"]],
        ]
    return lines


def _event_counts(since: datetime) -> Counter:
    with connect() as conn:
        rows = conn.execute(
            "SELECT event_type, COUNT(*) AS total FROM ecosystem_events WHERE created_at>=? GROUP BY event_type",
            (since.isoformat(),),
        ).fetchall()
    return Counter({row["event_type"]: row["total"] for row in rows})


def _freshness_item(value: str | None, now: datetime, threshold_minutes: int) -> dict:
    if not value:
        return {
            "status": "never_synced",
            "latest": None,
            "age_minutes": None,
            "stale": True,
        }
    try:
        parsed = datetime.fromisoformat(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=now.tzinfo)
        age = max(0, int((now - parsed.astimezone(now.tzinfo)).total_seconds() // 60))
    except (TypeError, ValueError):
        return {
            "status": "invalid",
            "latest": value,
            "age_minutes": None,
            "stale": True,
        }
    stale = age > threshold_minutes
    return {
        "status": "stale" if stale else "fresh",
        "latest": value,
        "age_minutes": age,
        "stale": stale,
    }


def _freshness_line(label: str, item: dict) -> str:
    if item["status"] == "never_synced":
        return f"• {label}: belum pernah sync"
    if item["age_minutes"] is None:
        return f"• {label}: timestamp tidak valid"
    marker = "⚠️" if item["stale"] else "✅"
    return f"• {label}: {marker} {item['age_minutes']} menit lalu"


def _local_time(now: datetime | None, settings: Settings) -> datetime:
    zone = ZoneInfo(settings.APP_TIMEZONE)
    if now is None:
        return datetime.now(zone)
    return now.astimezone(zone) if now.tzinfo else now.replace(tzinfo=zone)


async def _send_message(chat_id: str, message: str) -> None:
    await call_wa_tool("send_text_message", {"jid": chat_id, "text": message})


async def _run_hebat_sync(chat_id: str) -> str:
    from app.xninetzy.os.academic.hebat.tools import hebat_sync_assignments

    result = str(
        await hebat_sync_assignments.ainvoke({"chat_id": chat_id, "course_id": None})
    )
    lowered = result.casefold()
    failure_markers = (
        "belum login",
        "gagal",
        "error",
        "tidak ada assignment ditemukan",
    )
    if any(marker in lowered for marker in failure_markers):
        raise RuntimeError(result)
    return result
