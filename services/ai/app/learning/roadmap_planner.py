from __future__ import annotations

import re

from app.learning.roadmap_models import RoadmapDraft


def create_roadmap_draft(topic: str, duration_days: int = 14, level: str = "beginner") -> RoadmapDraft:
    clean = re.sub(r"\s+", " ", topic).strip()
    return RoadmapDraft(
        topic=clean,
        duration_days=duration_days,
        target=f"Bisa menerapkan {clean} dalam mini project yang relevan untuk Learning OS.",
        milestones=[
            "Hari 1-3: konsep dasar dan istilah penting",
            "Hari 4-6: arsitektur dan komponen utama",
            "Hari 7-9: praktik dengan contoh kecil",
            "Hari 10-12: integrasi ke mini project",
            "Hari 13-14: review, dokumentasi, dan rencana lanjut",
        ],
        first_day_tasks=[
            f"Baca konsep dasar {clean}",
            "Catat istilah penting ke Obsidian",
            "Buat eksperimen paling kecil yang bisa berjalan",
        ],
    )


def format_roadmap_draft(draft: RoadmapDraft) -> str:
    lines = [f"*Draft Roadmap Belajar: {draft.topic} {draft.duration_days} Hari*\n"]
    lines.append("*Target Akhir*")
    lines.append(f"{draft.target}\n")
    lines.append("*Milestone*")
    for milestone in draft.milestones:
        lines.append(f"• {milestone}")
    lines.append("\n*Task Hari Pertama*")
    for task in draft.first_day_tasks:
        lines.append(f"• {task}")
    lines.append("\nButuh approval untuk mengaktifkan roadmap dan membuat task.")
    lines.append("Balas:\n`/approve <id>`\natau\n`/reject <id>`")
    return "\n".join(lines)
