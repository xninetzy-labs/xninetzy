from __future__ import annotations

import re

from app.skills.schemas import SkillRoute


def route_skill(message: str) -> SkillRoute:
    text = message.casefold()

    if _has_any(text, ["kamu bisa apa", "fiturmu", "skillmu", "bisa apa aja"]):
        return SkillRoute(needs_skill=True, skill_name="skill_discovery", skill_action="list", reason="User asked skill discovery")
    if _has_any(text, ["tanggal berapa", "hari ini", "sekarang tanggal", "jam berapa", "hari apa", "tanggal sekarang"]):
        return SkillRoute(needs_skill=True, skill_name="date_time", skill_action="now", reason="User asked current date/time")
    if _has_any(text, ["pin", "announce", "announcement", "annonce", "tutup grup", "buka grup", "hanya admin", "admin only"]):
        return SkillRoute(needs_skill=True, skill_name="group_action", skill_action="execute", reason="User requested WhatsApp group action")
    if _has_any(text, ["obsidian", "vault", "catatan"]) and _has_any(text, ["cari", "baca", "lihat", "search"]):
        return SkillRoute(needs_skill=True, skill_name="obsidian", skill_action="search_or_read", reason="User requested Obsidian read")
    if _has_any(text, ["catat", "simpan", "buat note", "markdown", "obsidian", "vault"]):
        return SkillRoute(needs_skill=True, skill_name="obsidian", skill_action="write", reason="User requested note write")
    if _has_any(text, ["ingatkan", "reminder", "remind", "ingetin"]):
        return SkillRoute(needs_skill=True, skill_name="reminder", skill_action="create", reason="User requested reminder")
    if _has_any(text, ["hitung", "berapa", "persen", "persentase", "estimasi"]) and re.search(r"\d", text):
        return SkillRoute(needs_skill=True, skill_name="calculation", skill_action="calculate", reason="User requested calculation")
    if _has_any(text, ["analisis ide", "novelty", "feasibility", "swot", "bagus nggak"]):
        return SkillRoute(needs_skill=True, skill_name="idea_analysis", skill_action="analyze", reason="User requested idea analysis")
    if _has_any(text, ["breakdown", "timeline", "milestone", "sprint", "kanban"]):
        return SkillRoute(needs_skill=True, skill_name="task_breakdown", skill_action="breakdown", reason="User requested task breakdown")
    if _has_any(text, ["workflow", "otomatis", "automation", "pipeline", "otomatisin"]):
        return SkillRoute(needs_skill=True, skill_name="workflow", skill_action="draft", reason="User requested workflow automation")
    if _has_any(text, ["rencanain", "planning", "jadwal minggu", "jadwal hari", "plan belajar"]):
        return SkillRoute(needs_skill=True, skill_name="planning", skill_action="plan", reason="User requested planning")

    return SkillRoute(needs_skill=False, reason="No skill needed")


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword in text for keyword in keywords)
