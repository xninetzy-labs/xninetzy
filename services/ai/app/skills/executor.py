from __future__ import annotations

import json
from datetime import datetime
from zoneinfo import ZoneInfo

from app.core.config import get_settings
from app.db.sqlite import connect, init_db
from app.skills.base import SkillInput, SkillOutput
from app.skills.registry import get_skill, list_skills


async def execute_skill(skill_name: str, payload: SkillInput, action: str | None = None) -> SkillOutput:
    if skill_name == "skill_discovery":
        text = _skill_discovery_text()
        return SkillOutput(success=True, skill_name=skill_name, result={"skills": list_skills()}, user_facing_text=text)

    skill = get_skill(skill_name)
    if not skill:
        return SkillOutput(success=False, skill_name=skill_name, error="Skill tidak ditemukan")

    if action:
        payload.metadata["skill_action"] = action

    try:
        output = await skill.run(payload)
    except Exception as error:
        output = SkillOutput(success=False, skill_name=skill_name, error=str(error), user_facing_text=f"Skill {skill_name} gagal dijalankan: {error}")

    log_skill_call(payload, output, action)
    return output


def log_skill_call(payload: SkillInput, output: SkillOutput, action: str | None = None) -> None:
    init_db()
    now = datetime.now(ZoneInfo(get_settings().APP_TIMEZONE)).isoformat()
    with connect() as conn:
        conn.execute(
            """
            INSERT INTO skill_calls
            (chat_id, sender_id, skill_name, skill_action, skill_args_json, skill_result_json, success, error, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.chat_id,
                payload.sender_id,
                output.skill_name,
                action or payload.metadata.get("skill_action"),
                json.dumps(payload.metadata, ensure_ascii=False),
                json.dumps(output.result, ensure_ascii=False),
                1 if output.success else 0,
                output.error,
                now,
            ),
        )


def _skill_discovery_text() -> str:
    return """Aku bisa bantu beberapa hal ini:

*Belajar*
• Jelasin materi
• Bikin rangkuman
• Bikin latihan soal

*Task & Planning*
• Breakdown tugas
• Bikin timeline
• Reminder deadline

*Obsidian*
• Baca catatan
• Cari note
• Buat note markdown
• Simpan ide/tugas/belajar ke vault

*Analisis*
• Analisis ide
• SWOT
• Feasibility
• Novelty

*WhatsApp*
• Kirim pesan
• Kelola grup
• Buat poll
• Cek member grup

Coba bilang: "catat ini ke Obsidian" atau "ingatkan aku besok jam 8"."""
