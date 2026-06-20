"""Detect and decompose multi-action requests into a :class:`WorkflowPlan`.

Deterministic (no LLM) so it is fast, predictable and unit-testable. Detection
is keyword/connector based per the spec; decomposition assembles actions in a
canonical order with linear dependencies (each step waits on the previous one).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from app.xninetzy.core.config import get_settings
from app.xninetzy.core.logging import logging
from app.xninetzy.workflow.models import (
    WorkflowAction,
    WorkflowActionType,
    WorkflowPlan,
)

logger = logging.getLogger(__name__)

# Connectors that chain actions ("do X then Y").
_CONNECTORS = (
    "lalu", "kemudian", "setelah itu", "sekalian", "dan buat", "dan bikin",
    "terus", "habis itu", "then", "dan simpan", "lalu buat", "abis itu",
)

# Per-domain keyword buckets (spec section F).
_DOMAIN_KEYWORDS: dict[str, tuple[str, ...]] = {
    "hebat": ("hebat", "course", "kursus", "mata kuliah", "matkul", "tugas",
              "assignment", "deadline", "e-learning", "elearning"),
    "research": ("deep research", "riset", "research", "cari sumber",
                 "carikan materi", "materi lengkap", "cari referensi", "referensi"),
    "search": ("youtube", "video", "paper", "jurnal", "journal", "artikel",
               "web", "browsing", "ilmiah", "academic"),
    "roadmap": ("roadmap", "belajar", "learning path", "kurikulum"),
    "planning": ("planning", "rencana", "milestone", "pengerjaan", "jadwal kerja",
                 "plan pengerjaan", "rencana pengerjaan"),
    "reminder": ("ingatkan", "ingetin", "remind", "reminder", "deadline",
                 "dikumpulkan", "tenggat", "h-", "sebelum deadline", "jam ",
                 "nanti malam", "besok"),
    "obsidian": ("obsidian", "catatan", "vault", "note"),
    "knowledge": ("knowledge", "second brain", "ingest", "jadikan knowledge"),
}


def _has(text: str, words: tuple[str, ...]) -> bool:
    return any(w in text for w in words)


def detected_domains(text: str) -> set[str]:
    lowered = text.lower()
    return {name for name, words in _DOMAIN_KEYWORDS.items() if _has(lowered, words)}


def has_connector(text: str) -> bool:
    lowered = text.lower()
    return any(c in lowered for c in _CONNECTORS)


def is_multi_action_request(text: str) -> bool:
    """True for compound requests worth running as a staged workflow.

    Requires ≥2 action domains AND (an explicit connector OR ≥3 domains), so a
    single-domain message ("ringkas dokumen ini") stays on the normal flow.
    """
    if not text or not text.strip():
        return False
    lowered = text.lower()
    if _is_explicit_reminder(lowered):
        return True
    domains = detected_domains(text)
    if "planning" in domains and _has_time_or_deadline(lowered):
        return True
    if len(domains) < 2:
        return False
    return has_connector(text) or len(domains) >= 3


async def build_workflow_plan(
    chat_id: str, user_message: str, context: dict | None = None
) -> WorkflowPlan:
    """Decompose ``user_message`` into an ordered list of workflow actions."""
    lowered = user_message.lower()
    domains = detected_domains(user_message)

    course_id = (context or {}).get("course_id") if context else None
    types: list[tuple[WorkflowActionType, str, str, bool]] = []  # (type, title, goal, critical)

    if _is_explicit_reminder(lowered) and "planning" not in domains and "roadmap" not in domains:
        types.append((WorkflowActionType.REMINDER_CREATE, "Buat reminder",
                      "Buat reminder eksplisit dari pesan user", False))
        types.append((WorkflowActionType.FINAL_SYNTHESIS, "Ringkasan akhir",
                      "Gabungkan semua hasil jadi jawaban final", False))
        return _materialize_plan(chat_id, user_message, types, course_id)

    # ── HEBAT block ──────────────────────────────────────────────────────────
    wants_course = _has(lowered, ("course", "kursus", "mata kuliah", "matkul"))
    wants_assignment = _has(lowered, ("tugas", "assignment", "deadline"))
    wants_download = _has(lowered, ("download", "unduh", "file", "lampiran", "materi")) or wants_assignment
    hebat = "hebat" in domains

    if hebat:
        if wants_course:
            types.append((WorkflowActionType.HEBAT_SYNC, "Sinkronisasi course HEBAT",
                          "Refresh daftar course dari HEBAT", False))
            types.append((WorkflowActionType.HEBAT_COURSE_DETAIL, "Detail course HEBAT",
                          "Ambil struktur section & aktivitas course", False))
        if wants_assignment:
            types.append((WorkflowActionType.HEBAT_ASSIGNMENT_DETAIL, "Detail tugas HEBAT",
                          "Ambil instruksi, deadline & lampiran tugas", False))
        if wants_download:
            types.append((WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS, "Download materi HEBAT",
                          "Unduh & parse file materi/lampiran", False))

    # ── research / search ────────────────────────────────────────────────────
    research = "research" in domains
    search = "search" in domains
    research_added = False
    if research:
        types.append((WorkflowActionType.DEEP_RESEARCH, "Deep research materi",
                      "Riset materi dari web, paper & video", False))
        research_added = True
    elif search:
        if _has(lowered, ("youtube", "video")):
            types.append((WorkflowActionType.YOUTUBE_SEARCH, "Cari video YouTube",
                          "Kumpulkan video relevan", False))
            research_added = True
        if _has(lowered, ("paper", "jurnal", "journal", "ilmiah", "academic")):
            types.append((WorkflowActionType.PAPER_SEARCH, "Cari paper akademik",
                          "Kumpulkan paper/jurnal relevan", False))
            research_added = True
        if _has(lowered, ("web", "artikel", "browsing")) or not research_added:
            types.append((WorkflowActionType.WEB_SEARCH, "Cari artikel web",
                          "Kumpulkan artikel web relevan", False))
            research_added = True

    has_research_domain = research or search
    wants_knowledge = "knowledge" in domains or has_research_domain
    wants_download_action = any(t[0] == WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS for t in types)

    # Knowledge ingest: after HEBAT download (ingest the file) if present,
    # otherwise after research (ingest the findings). Only when a research/
    # knowledge intent exists — plain HEBAT→planning needs no ingest step.
    knowledge_action = (
        WorkflowActionType.KNOWLEDGE_INGEST, "Simpan ke knowledge base",
        "Chunk & index materi ke knowledge/RAG", False,
    )
    if wants_knowledge and wants_download_action:
        # Insert right after the download action.
        idx = next(i for i, t in enumerate(types)
                   if t[0] == WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS) + 1
        types.insert(idx, knowledge_action)
    elif wants_knowledge and research_added:
        types.append(knowledge_action)

    # ── deliverables ───────────────────────────────────────────────────────────
    if "roadmap" in domains:
        types.append((WorkflowActionType.ROADMAP_CREATE, "Buat roadmap belajar",
                      "Susun roadmap belajar bertahap", False))
        if "planning" not in domains and _has(lowered, ("minggu", "hari", "bulan")):
            types.append((WorkflowActionType.TASK_PLANNING, "Buat planning pengerjaan",
                          "Pecah roadmap menjadi milestone kerja", False))
    if "planning" in domains:
        types.append((WorkflowActionType.TASK_PLANNING, "Buat planning pengerjaan",
                      "Pecah tugas menjadi milestone", False))

    if _should_infer_reminder(lowered, domains, types):
        types.append((WorkflowActionType.REMINDER_INFER, "Infer reminder otomatis",
                      "Buat reminder jika ada deadline/waktu jelas", False))

    wants_save = (
        "obsidian" in domains
        or any(t[0] in (WorkflowActionType.ROADMAP_CREATE, WorkflowActionType.TASK_PLANNING)
               for t in types)
    )
    if wants_save:
        types.append((WorkflowActionType.OBSIDIAN_SAVE, "Simpan ke Obsidian",
                      "Tulis hasil ke vault Obsidian", False))

    # Final synthesis always closes the workflow.
    types.append((WorkflowActionType.FINAL_SYNTHESIS, "Ringkasan akhir",
                  "Gabungkan semua hasil jadi jawaban final", False))

    return _materialize_plan(chat_id, user_message, types, course_id)


def _materialize_plan(
    chat_id: str,
    user_message: str,
    types: list[tuple[WorkflowActionType, str, str, bool]],
    course_id: str | None = None,
) -> WorkflowPlan:
    domains = detected_domains(user_message)
    # ── materialise actions with linear dependencies ──────────────────────────
    actions: list[WorkflowAction] = []
    prev_id: str | None = None
    for i, (atype, title, goal, critical) in enumerate(types):
        aid = f"a{i + 1}"
        action_input: dict = {}
        if course_id and atype in (
            WorkflowActionType.HEBAT_COURSE_DETAIL,
            WorkflowActionType.HEBAT_DOWNLOAD_MATERIALS,
        ):
            action_input["course_id"] = course_id
        actions.append(WorkflowAction(
            id=aid, type=atype, title=title, goal=goal,
            input=action_input,
            depends_on=[prev_id] if prev_id else [],
            critical=critical,
        ))
        prev_id = aid

    plan = WorkflowPlan(
        id=uuid.uuid4().hex,
        chat_id=chat_id,
        original_user_message=user_message,
        title=_plan_title(user_message),
        actions=actions,
        final_goal=user_message.strip(),
        created_at=_now_iso(),
    )
    logger.info(
        "workflow_plan_created workflow_id=%s chat_id=%s actions=%d domains=%s",
        plan.id, chat_id, len(actions), sorted(domains),
    )
    return plan


def _is_explicit_reminder(lowered: str) -> bool:
    return _has(lowered, ("ingatkan", "ingetin", "remind", "reminder"))


def _has_time_or_deadline(lowered: str) -> bool:
    return _has(lowered, ("deadline", "dikumpulkan", "tenggat", "besok", "hari ini", "nanti malam", "jam ", "tanggal", "h-"))


def _should_infer_reminder(
    lowered: str,
    domains: set[str],
    types: list[tuple[WorkflowActionType, str, str, bool]],
) -> bool:
    has_deliverable = any(t[0] in (WorkflowActionType.TASK_PLANNING, WorkflowActionType.ROADMAP_CREATE) for t in types)
    if not has_deliverable:
        return False
    if "reminder" in domains or _has_time_or_deadline(lowered):
        return True
    return "roadmap" in domains and _has(lowered, ("minggu", "hari", "bulan"))


def _plan_title(message: str) -> str:
    flat = " ".join(message.split())
    return flat[:60] + ("…" if len(flat) > 60 else "")


def _now_iso() -> str:
    try:
        tz = ZoneInfo(get_settings().APP_TIMEZONE)
    except Exception:
        tz = ZoneInfo("UTC")
    return datetime.now(tz).isoformat()
