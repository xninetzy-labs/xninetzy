"""Maps each WorkflowActionType to a concrete, best-effort handler.

Handlers wire into the existing subsystems (hebat tools, deep research, learning,
planning, knowledge, obsidian). Every handler is defensive: it returns a
:class:`WorkflowActionResult` and never raises, so one failing step can't crash
the whole workflow. The executor decides whether a failure is fatal.
"""

from __future__ import annotations

import re
from typing import Awaitable, Callable

from app.xninetzy.core.logging import logging
from app.xninetzy.workflow.models import (
    WorkflowAction,
    WorkflowActionResult,
    WorkflowActionStatus,
    WorkflowActionType,
    WorkflowState,
)

logger = logging.getLogger(__name__)

Handler = Callable[[WorkflowAction, WorkflowState], Awaitable[WorkflowActionResult]]

_STOPWORDS = {
    "carikan", "cari", "materi", "lengkap", "lalu", "kemudian", "buat", "bikin",
    "roadmap", "belajar", "planning", "rencana", "pengerjaan", "tugas", "dari",
    "tentang", "deep", "research", "riset", "simpan", "ke", "obsidian", "dan",
    "hebat", "course", "file", "download", "yang", "untuk", "saya", "tolong",
}


def _topic_from(message: str) -> str:
    words = [w for w in re.findall(r"[A-Za-z0-9\-]+", message) if w.lower() not in _STOPWORDS]
    topic = " ".join(words).strip()
    return topic or message.strip()[:80]


def _ok(action: WorkflowAction, summary: str, **data) -> WorkflowActionResult:
    return WorkflowActionResult(
        action_id=action.id, status=WorkflowActionStatus.SUCCESS, summary=summary, data=data
    )


def _fail(action: WorkflowAction, error: str) -> WorkflowActionResult:
    return WorkflowActionResult(action_id=action.id, status=WorkflowActionStatus.FAILED, error=error)


def _skip(action: WorkflowAction, reason: str) -> WorkflowActionResult:
    return WorkflowActionResult(
        action_id=action.id, status=WorkflowActionStatus.SKIPPED, summary=reason
    )


def _first_lines(text: str, n: int = 2, limit: int = 220) -> str:
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    return " ".join(lines[:n])[:limit] or (text or "")[:limit]


# ─── HEBAT ───────────────────────────────────────────────────────────────────

async def _h_sync(action, state):
    try:
        from app.xninetzy.os.academic.hebat.tools import hebat_sync_courses
        res = await hebat_sync_courses.ainvoke({"chat_id": state.chat_id})
        state.course_context = {"sync": _first_lines(res)}
        return _ok(action, _first_lines(res))
    except Exception as exc:
        return _fail(action, f"sync course HEBAT gagal: {exc}")


async def _h_course_detail(action, state):
    course_id = action.input.get("course_id") or (state.course_context or {}).get("course_id")
    if not course_id:
        return _skip(action, "Course belum dipilih — butuh course_id untuk detail.")
    try:
        from app.xninetzy.os.academic.hebat.tools import hebat_sync_course_activities
        res = await hebat_sync_course_activities.ainvoke(
            {"chat_id": state.chat_id, "course_id": str(course_id)}
        )
        state.course_context = {**(state.course_context or {}), "detail": _first_lines(res)}
        return _ok(action, _first_lines(res))
    except Exception as exc:
        return _fail(action, f"detail course gagal: {exc}")


async def _h_assignment_detail(action, state):
    assign = action.input.get("assignment_id") or action.input.get("activity_url")
    if not assign:
        return _skip(action, "Belum ada id/URL tugas spesifik untuk diambil detailnya.")
    try:
        from app.xninetzy.os.academic.hebat.tools import hebat_get_assignment_detail
        res = await hebat_get_assignment_detail.ainvoke(
            {"chat_id": state.chat_id, "assignment_id_or_url": str(assign)}
        )
        state.assignment_context = {"detail": _first_lines(res, 4)}
        return _ok(action, _first_lines(res))
    except Exception as exc:
        return _fail(action, f"detail tugas gagal: {exc}")


async def _h_download(action, state):
    target = action.input.get("activity_url") or action.input.get("cmid")
    if not target:
        return _skip(action, "Belum ada activity/file spesifik untuk diunduh.")
    try:
        from app.xninetzy.os.academic.hebat.tools import hebat_download_material
        res = await hebat_download_material.ainvoke(
            {"chat_id": state.chat_id, "activity_id_or_url": str(target)}
        )
        state.downloaded_files.append(str(target))
        return _ok(action, _first_lines(res))
    except Exception as exc:
        return _fail(action, f"download materi gagal: {exc}")


# ─── research / search ───────────────────────────────────────────────────────

async def _h_deep_research(action, state):
    topic = action.input.get("topic") or _topic_from(state.original_user_message)
    try:
        from app.xninetzy.os.research.deep_research import run_deep_research
        res = await run_deep_research(
            topic=topic, chat_id=state.chat_id, sender_id=None, sender_name=None,
            chat_type="private", metadata={}, mode="balanced",
        )
        state.research_context = {"topic": topic, "brief": res}
        return _ok(action, f"Riset '{topic}' selesai.", topic=topic)
    except Exception as exc:
        return _fail(action, f"deep research gagal: {exc}")


def _make_search_handler(kind: str) -> Handler:
    async def handler(action: WorkflowAction, state: WorkflowState) -> WorkflowActionResult:
        topic = action.input.get("topic") or _topic_from(state.original_user_message)
        try:
            items: list = []
            if kind == "youtube":
                from app.xninetzy.os.research.youtube_search import search_youtube as fn  # type: ignore
                items = await fn(topic)  # type: ignore
            elif kind == "web":
                from app.xninetzy.os.research.web_search import search_web as fn  # type: ignore
                items = await fn(topic)  # type: ignore
            count = len(items) if isinstance(items, list) else 0
            if isinstance(items, list):
                state.sources.extend(items)
            return _ok(action, f"Ditemukan {count} sumber {kind} untuk '{topic}'.", count=count)
        except Exception as exc:
            return _fail(action, f"pencarian {kind} gagal: {exc}")

    return handler


# ─── knowledge / deliverables ────────────────────────────────────────────────

async def _h_knowledge(action, state):
    text = ""
    if state.research_context:
        text = state.research_context.get("brief", "")
    title = f"Workflow: {_topic_from(state.original_user_message)}"
    if not text.strip():
        return _skip(action, "Belum ada teks untuk di-ingest ke knowledge.")
    try:
        from app.xninetzy.os.knowledge.ingestion import ingest_text
        res = ingest_text(title, text, source_type="workflow")
        chunks = res.get("chunks", 0)
        return _ok(action, f"{chunks} chunk disimpan ke knowledge base.", chunks=chunks)
    except Exception as exc:
        return _fail(action, f"knowledge ingest gagal: {exc}")


async def _h_roadmap(action, state):
    topic = _topic_from(state.original_user_message)
    try:
        from app.xninetzy.domains.it_learning.roadmap_planner import create_roadmap_draft
        draft = create_roadmap_draft(topic)
        state.roadmap_context = {"topic": topic, "milestones": list(draft.milestones)}
        n = len(draft.milestones)
        return _ok(action, f"Roadmap '{topic}' dibuat: {n} milestone.", milestones=n)
    except Exception as exc:
        return _fail(action, f"buat roadmap gagal: {exc}")


async def _h_planning(action, state):
    topic = _topic_from(state.original_user_message)
    milestones = (state.roadmap_context or {}).get("milestones") or [
        "Pahami instruksi & kumpulkan bahan",
        "Susun kerangka",
        "Kerjakan bagian inti",
        "Review & finalisasi",
    ]
    try:
        from app.xninetzy.os.life.task_manager import create_task
        created = 0
        for m in milestones[:8]:
            try:
                create_task(title=f"[{topic}] {m}", description="Auto dari workflow")
                created += 1
            except Exception:
                continue
        state.planning_context = {"topic": topic, "milestones": milestones, "created": created}
        return _ok(action, f"Planning dibuat: {created} milestone/task.", milestones=created)
    except Exception as exc:
        return _fail(action, f"buat planning gagal: {exc}")


async def _h_reminder_create(action, state):
    try:
        from app.xninetzy.os.reminders.reminder_service import ReminderService, format_reminder_creation_response

        svc = ReminderService()
        if action.input.get("remind_at"):
            parsed = {
                "title": action.input.get("title") or _topic_from(state.original_user_message),
                "description": action.input.get("description"),
                "deadline_at": action.input.get("deadline_at"),
                "remind_at": action.input["remind_at"],
                "timezone": action.input.get("timezone") or "Asia/Jakarta",
                "priority": action.input.get("priority") or "normal",
                "reminder_type": action.input.get("reminder_type") or "explicit",
                "offset_value": action.input.get("offset_value"),
                "offset_unit": action.input.get("offset_unit"),
                "metadata": action.input.get("metadata") or {},
            }
            res = svc.create_from_parsed(chat_id=state.chat_id, user_id=None, parsed=parsed)
        else:
            res = svc.create_from_message(
                state.chat_id,
                None,
                action.input.get("message") or state.original_user_message,
                source="workflow",
                source_ref_id=state.plan_id,
            )
        state.reminder_context = {"created": [res]}
        if not res.get("created") and res.get("duplicate"):
            return _ok(action, f"Reminder sudah ada: {res.get('title')}", reminder=res)
        if not res.get("created"):
            return _skip(action, f"Reminder tidak dibuat: {res.get('reason', 'waktu tidak valid')}")
        return _ok(action, format_reminder_creation_response(res), reminder=res)
    except Exception as exc:
        return _fail(action, f"buat reminder gagal: {exc}")


async def _h_reminder_infer(action, state):
    try:
        from app.xninetzy.os.reminders.reminder_service import ReminderService, format_auto_reminder_summary

        svc = ReminderService()
        topic = (state.planning_context or {}).get("topic") or _topic_from(state.original_user_message)
        description = None
        if state.planning_context:
            milestones = state.planning_context.get("milestones") or []
            description = "; ".join(str(m) for m in milestones[:4]) or None
        created = svc.create_auto_from_context(
            chat_id=state.chat_id,
            user_id=None,
            text=state.original_user_message,
            title=topic,
            description=description,
            source="planning" if state.planning_context else "workflow",
            source_ref_id=state.plan_id,
        )
        state.reminder_context = {"created": created}
        made = [r for r in created if r.get("created")]
        duplicates = [r for r in created if r.get("duplicate")]
        if made:
            return _ok(action, format_auto_reminder_summary(made), reminders=made)
        if duplicates:
            return _ok(action, f"Reminder otomatis sudah ada ({len(duplicates)}).", reminders=duplicates)
        return _skip(action, "Reminder otomatis tidak dibuat karena belum ada waktu/deadline yang jelas.")
    except Exception as exc:
        return _fail(action, f"infer reminder gagal: {exc}")


async def _h_reminder_list(action, state):
    try:
        from app.xninetzy.os.reminders.reminder_service import ReminderService
        reminders = ReminderService().list_pending(state.chat_id)
        return _ok(action, f"{len(reminders)} reminder pending.", reminders=reminders)
    except Exception as exc:
        return _fail(action, f"list reminder gagal: {exc}")


async def _h_reminder_cancel(action, state):
    reminder_id = action.input.get("reminder_id") or action.input.get("id")
    if not reminder_id:
        return _skip(action, "Butuh reminder_id untuk cancel.")
    try:
        from app.xninetzy.os.reminders.reminder_service import ReminderService
        ReminderService().cancel(reminder_id)
        return _ok(action, f"Reminder `{reminder_id}` dibatalkan.")
    except Exception as exc:
        return _fail(action, f"cancel reminder gagal: {exc}")


async def _h_obsidian(action, state):
    topic = _topic_from(state.original_user_message)
    body_parts = [f"# {topic} — Workflow Output", ""]
    if state.research_context:
        body_parts += ["## Ringkasan Riset", state.research_context.get("brief", "")[:4000], ""]
    if state.roadmap_context:
        body_parts += ["## Roadmap"] + [f"- {m}" for m in state.roadmap_context.get("milestones", [])] + [""]
    if state.planning_context:
        body_parts += ["## Planning"] + [f"- {m}" for m in state.planning_context.get("milestones", [])] + [""]
    if state.reminder_context:
        reminders = state.reminder_context.get("created", [])
        if reminders:
            body_parts += ["## Reminder"] + [
                f"- {r.get('title')} @ {r.get('display_time_label') or r.get('remind_at')} ({r.get('offset_label') or r.get('status')})"
                for r in reminders
            ] + [""]
    content = "\n".join(body_parts).strip() or f"# {topic}"
    path = f"Workflow/{_safe(topic)}.md"
    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService
        ObsidianVaultService().create_note(path, content, overwrite=True)
        state.obsidian_paths.append(path)
        return _ok(action, f"Disimpan ke Obsidian: `{path}`", path=path)
    except Exception as exc:
        return _fail(action, f"simpan Obsidian gagal: {exc}")


async def _h_memory(action, state):
    return _skip(action, "Memory save belum diaktifkan untuk workflow.")


async def _h_final(action, state):
    # Deterministic synthesis from accumulated summaries (no LLM needed).
    lines = ["✅ *Workflow selesai*", ""]
    if state.summaries:
        lines.append("*Yang berhasil:*")
        lines += [f"{i+1}. {s}" for i, s in enumerate(state.summaries)]
    if state.obsidian_paths:
        lines += ["", "*Catatan tersimpan:*"] + [f"- `{p}`" for p in state.obsidian_paths]
    if state.reminder_context and state.reminder_context.get("created"):
        lines += ["", "*Reminder:*"]
        for r in state.reminder_context["created"]:
            if r.get("created") or r.get("duplicate"):
                label = r.get("offset_label") or "Reminder"
                when = r.get("display_time_label") or r.get("remind_at")
                lines.append(f"- {r.get('title')} — {label}: {when}")
    summary = "\n".join(lines).strip()
    return _ok(action, summary)


def _safe(name: str) -> str:
    return re.sub(r"[^\w\s-]", "", name).strip().replace(" ", "_")[:60] or "untitled"


DEFAULT_HANDLERS: dict[WorkflowActionType, Handler] = {
    WorkflowActionType.HEBAT_SYNC: _h_sync,
    WorkflowActionType.HEBAT_COURSE_DETAIL: _h_course_detail,
    WorkflowActionType.HEBAT_ASSIGNMENT_DETAIL: _h_assignment_detail,
    WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS: _h_download,
    WorkflowActionType.DEEP_RESEARCH: _h_deep_research,
    WorkflowActionType.KNOWLEDGE_INGEST: _h_knowledge,
    WorkflowActionType.ROADMAP_CREATE: _h_roadmap,
    WorkflowActionType.TASK_PLANNING: _h_planning,
    WorkflowActionType.REMINDER_CREATE: _h_reminder_create,
    WorkflowActionType.REMINDER_INFER: _h_reminder_infer,
    WorkflowActionType.REMINDER_LIST: _h_reminder_list,
    WorkflowActionType.REMINDER_CANCEL: _h_reminder_cancel,
    WorkflowActionType.OBSIDIAN_SAVE: _h_obsidian,
    WorkflowActionType.MEMORY_SAVE: _h_memory,
    WorkflowActionType.FINAL_SYNTHESIS: _h_final,
}


DEFAULT_HANDLERS[WorkflowActionType.WEB_SEARCH] = _make_search_handler("web")
DEFAULT_HANDLERS[WorkflowActionType.YOUTUBE_SEARCH] = _make_search_handler("youtube")
DEFAULT_HANDLERS[WorkflowActionType.PAPER_SEARCH] = _make_search_handler("paper")


async def execute_action(
    action: WorkflowAction,
    state: WorkflowState,
    handlers: dict[WorkflowActionType, Handler] | None = None,
) -> WorkflowActionResult:
    """Dispatch one action to its handler. Always returns a result."""
    registry = handlers or DEFAULT_HANDLERS
    handler = registry.get(action.type)
    if handler is None:
        return _skip(action, f"Tidak ada handler untuk {action.type.value}.")
    try:
        return await handler(action, state)
    except Exception as exc:  # pragma: no cover - handlers already guard
        logger.warning("workflow handler crashed type=%s err=%s", action.type, exc)
        return _fail(action, str(exc))
