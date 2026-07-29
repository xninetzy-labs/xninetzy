from __future__ import annotations

import re
from collections.abc import Iterable

from app.xninetzy.domains.it_learning.roadmap_models import (
    RoadmapDraft,
    RoadmapPhase,
    RoadmapSource,
)

PHASE_LIBRARY = (
    (
        "Orientasi dan prerequisite",
        "Peta konsep serta gap prerequisite teridentifikasi",
    ),
    ("Fondasi konseptual", "Istilah inti dapat dijelaskan dengan contoh sendiri"),
    ("Latihan terarah", "Konsep diterapkan pada latihan kecil yang dapat diperiksa"),
    ("Integrasi", "Beberapa konsep terhubung dalam satu alur kerja"),
    ("Mini project", "Artefak yang berjalan dan bukti hasil tersedia"),
    ("Evaluasi dan adaptasi", "Gap mastery, dokumentasi, dan next step tercatat"),
)


def create_roadmap_draft(
    topic: str,
    duration_days: int = 14,
    level: str = "beginner",
    sources: Iterable[dict | RoadmapSource] | None = None,
) -> RoadmapDraft:
    clean = re.sub(r"\s+", " ", topic).strip()
    duration = max(1, min(int(duration_days), 180))
    normalized_level = _normalize_level(level)
    source_refs = _normalize_sources(sources)
    phases = _build_phases(duration, normalized_level)
    source_note = (
        f" dengan referensi {len(source_refs)} sumber internal"
        if source_refs
        else " dengan sumber yang perlu divalidasi selama belajar"
    )
    milestones = [
        f"Hari {_day_range(phase)}: {phase.focus} — {phase.outcome}" for phase in phases
    ]
    first_tasks = _first_day_tasks(clean, normalized_level, source_refs)
    strategy = _strategy(duration, normalized_level, bool(source_refs))
    return RoadmapDraft(
        topic=clean,
        duration_days=duration,
        level=normalized_level,
        target=f"Menerapkan {clean} dalam artefak relevan untuk Learning OS{source_note}.",
        milestones=milestones,
        first_day_tasks=first_tasks,
        strategy=strategy,
        phases=phases,
        source_refs=source_refs,
    )


def format_roadmap_draft(draft: RoadmapDraft) -> str:
    lines = [f"*Draft Roadmap Belajar: {draft.topic} {draft.duration_days} Hari*\n"]
    lines.append(f"Level: {draft.level} | Strategy: {draft.strategy}")
    lines.append("\n*Target Akhir*")
    lines.append(f"{draft.target}\n")
    lines.append("*Milestone*")
    for milestone in draft.milestones:
        lines.append(f"• {milestone}")
    if draft.source_refs:
        lines.append("\n*Sumber internal yang dipakai*")
        for source in draft.source_refs:
            lines.append(f"• #{source.source_id} {source.title} ({source.source_type})")
    else:
        lines.append(
            "\n⚠️ Belum ada sumber internal relevan; validasi sumber sebelum membuat klaim."
        )
    lines.append("\n*Task Hari Pertama*")
    for task in draft.first_day_tasks:
        lines.append(f"• {task}")
    lines.append("\nButuh approval untuk mengaktifkan roadmap dan membuat task.")
    lines.append("Balas:\n`/approve <id>`\natau\n`/reject <id>`")
    return "\n".join(lines)


def _build_phases(duration: int, level: str) -> list[RoadmapPhase]:
    phase_count = 4 if duration <= 7 else 5 if duration <= 14 else 6
    phase_count = min(phase_count, duration)
    base, remainder = divmod(duration, phase_count)
    phases: list[RoadmapPhase] = []
    day = 1
    for index in range(phase_count):
        span = base + (1 if index < remainder else 0)
        start, end = day, day + span - 1
        focus, outcome = PHASE_LIBRARY[index]
        if level == "advanced" and index < 2:
            focus = focus.replace("Fondasi", "Audit fondasi").replace(
                "Orientasi", "Audit prerequisite"
            )
        phases.append(
            RoadmapPhase(start_day=start, end_day=end, focus=focus, outcome=outcome)
        )
        day = end + 1
    return phases


def _first_day_tasks(topic: str, level: str, sources: list[RoadmapSource]) -> list[str]:
    tasks = [f"Tulis baseline kemampuan dan target terukur untuk {topic}"]
    if sources:
        titles = ", ".join(source.title for source in sources[:3])
        tasks.append(f"Petakan konsep dan prerequisite dari sumber internal: {titles}")
    else:
        tasks.append("Cari dan validasi minimal dua sumber primer atau materi resmi")
    tasks.append(
        "Buat diagnostic exercise untuk menemukan gap"
        if level != "beginner"
        else "Buat eksperimen paling kecil yang dapat dijalankan"
    )
    return tasks


def _normalize_sources(
    sources: Iterable[dict | RoadmapSource] | None,
) -> list[RoadmapSource]:
    normalized: list[RoadmapSource] = []
    seen: set[int] = set()
    for source in sources or []:
        item = (
            source
            if isinstance(source, RoadmapSource)
            else RoadmapSource.model_validate(source)
        )
        if item.source_id in seen:
            continue
        seen.add(item.source_id)
        normalized.append(item)
        if len(normalized) == 5:
            break
    return normalized


def _normalize_level(level: str) -> str:
    value = (level or "beginner").strip().casefold()
    return value if value in {"beginner", "intermediate", "advanced"} else "beginner"


def _strategy(duration: int, level: str, grounded: bool) -> str:
    pace = (
        "sprint" if duration <= 7 else "balanced" if duration <= 14 else "deep-practice"
    )
    evidence = "source-grounded" if grounded else "source-discovery"
    return f"{pace}/{level}/{evidence}"


def _day_range(phase: RoadmapPhase) -> str:
    return (
        str(phase.start_day)
        if phase.start_day == phase.end_day
        else f"{phase.start_day}-{phase.end_day}"
    )
