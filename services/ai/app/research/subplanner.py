from __future__ import annotations

import re

from pydantic import BaseModel


class ResearchSubPlan(BaseModel):
    id: str
    title: str
    question: str
    search_queries: list[str]
    source_types: list[str]
    expected_output: str
    priority: int


def _mode_limit(mode: str) -> int:
    return {"speed": 3, "balanced": 5, "quality": 8}.get(mode, 5)


async def generate_research_subplans(
    topic: str,
    scope: str | None = None,
    mode: str = "balanced",
) -> list[ResearchSubPlan]:
    clean = re.sub(r"\s+", " ", topic).strip()
    templates = [
        ("Konsep dasar", f"Apa definisi, tujuan, dan istilah penting dari {clean}?"),
        ("Arsitektur dan workflow", f"Bagaimana arsitektur dan alur kerja {clean}?"),
        ("Perbandingan pendekatan", f"Apa alternatif dan tradeoff utama untuk {clean}?"),
        ("Tools dan sumber belajar", f"Tools, library, dokumentasi, dan video apa yang relevan untuk {clean}?"),
        ("Implementasi MVP", f"Bagaimana menerapkan {clean} sebagai MVP yang realistis?"),
        ("Risiko dan batasan", f"Apa risiko, batasan, dan kesalahan umum dalam {clean}?"),
        ("Roadmap Xninetzy", f"Bagaimana {clean} diterapkan ke Personal Learning OS Xninetzy?"),
        ("Evaluasi hasil", f"Bagaimana mengukur keberhasilan implementasi {clean}?"),
    ]
    source_types = ["web", "docs", "youtube"]
    if mode == "quality":
        source_types.append("academic")

    plans: list[ResearchSubPlan] = []
    for idx, (title, question) in enumerate(templates[: _mode_limit(mode)], 1):
        base = f"{clean} {title}".strip()
        plans.append(
            ResearchSubPlan(
                id=f"sp-{idx}",
                title=title,
                question=question,
                search_queries=[
                    base,
                    f"{clean} explained",
                    f"{clean} implementation guide",
                ][: 2 if mode == "speed" else 3],
                source_types=source_types,
                expected_output=f"Ringkasan fokus {title.lower()} untuk {clean}",
                priority=idx,
            )
        )
    return plans


def format_subplans_for_whatsapp(topic: str, subplans: list[ResearchSubPlan]) -> str:
    lines = [f"*Research Sub-Plan*\nTopik: {topic}\n"]
    for i, subplan in enumerate(subplans, 1):
        lines.append(f"{i}. {subplan.title}")
        lines.append("   Query:")
        for query in subplan.search_queries:
            lines.append(f"   • {query}")
        lines.append("")
    return "\n".join(lines).strip()
