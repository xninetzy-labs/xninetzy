from __future__ import annotations

from app.reminders.reminder_service import ReminderService
from app.skills.base import SkillInput, SkillOutput


class ReminderSkill:
    name = "reminder"
    description = "Membuat, melihat, membatalkan, dan menjadwalkan reminder persistent di SQLite."
    category = "productivity"
    input_schema = {"message": "string", "chat_id": "string"}
    output_schema = {"id": "integer", "remind_at": "datetime", "status": "string"}
    safety_policy = "Jika waktu ambigu, minta klarifikasi. Reminder due dikirim lewat WA MCP."
    memory_behavior = "Simpan reminder penting dan deadline ke memory."

    def __init__(self) -> None:
        self.service = ReminderService()

    async def run(self, payload: SkillInput) -> SkillOutput:
        action = str(payload.metadata.get("action") or payload.metadata.get("skill_action") or "create")
        if action == "list":
            reminders = self.service.list_pending(payload.chat_id)
            return SkillOutput(success=True, skill_name=self.name, result={"reminders": reminders}, user_facing_text=self._render_list(reminders))

        reminder = self.service.create_from_message(payload.chat_id, payload.sender_id, payload.message)
        return SkillOutput(
            success=True,
            skill_name=self.name,
            result=reminder,
            user_facing_text=f"⏰ Siap, aku ingatkan di waktu ini:\n\n*Reminder:* {reminder['title']}\n_Dijadwalkan: {reminder['remind_at']}_",
            memory_updates=[{"type": "reminder", **reminder}],
        )

    def _render_list(self, reminders: list[dict]) -> str:
        if not reminders:
            return "Belum ada reminder pending."
        lines = ["*Reminder pending:*"]
        for reminder in reminders[:20]:
            lines.append(f"• `{reminder['id']}` {reminder['title']} - {reminder['remind_at']}")
        return "\n".join(lines)
