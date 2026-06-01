from __future__ import annotations

from app.skills.base import SkillInput, SkillOutput
from app.wa_tools import WaToolError, call_wa_tool


class GroupActionSkill:
    name = "group_action"
    description = "Eksekusi aksi WhatsApp ringan lewat WA MCP: pin pesan dan mode announcement."
    category = "whatsapp"
    input_schema = {"message": "string", "chat_id": "group jid", "metadata": "quotedMessageId"}
    output_schema = {"tool": "string", "result": "object"}
    safety_policy = "Beberapa aksi (seperti announce) hanya untuk grup dan membutuhkan akses admin."
    memory_behavior = "Tidak perlu disimpan kecuali aksi penting."

    async def run(self, payload: SkillInput) -> SkillOutput:
        text = payload.message.casefold()

        try:
            if "pin" in text:
                return await self._pin_message(payload)
                
            if not payload.chat_id.endswith("@g.us"):
                return SkillOutput(success=False, skill_name=self.name, error="Aksi ini (selain pin) hanya bisa dipakai di grup")

            if _is_announce_on(text):
                return await self._set_announce(payload, True)
            if _is_announce_off(text):
                return await self._set_announce(payload, False)
        except WaToolError as error:
            return SkillOutput(success=False, skill_name=self.name, error=str(error), user_facing_text=_friendly_tool_error(str(error)))

        return SkillOutput(success=False, skill_name=self.name, error="Aksi WhatsApp tidak dikenali")

    async def _pin_message(self, payload: SkillInput) -> SkillOutput:
        message_id = payload.metadata.get("quotedMessageId") or payload.metadata.get("messageId")
        if not message_id:
            return SkillOutput(
                success=False,
                skill_name=self.name,
                error="missing_quoted_message",
                user_facing_text="Untuk pin pesan, reply dulu pesan yang mau dipin lalu ketik *pin*.",
            )

        from_me = bool(payload.metadata.get("isReplyToBot", False))
        participant = payload.metadata.get("quotedParticipantJid") or payload.metadata.get("participantJid")

        result = await call_wa_tool(
            "pin_message",
            {
                "jid": payload.chat_id,
                "message_id": str(message_id),
                "duration": 604800,
                "from_me": from_me,
                "participant": str(participant) if participant else None,
            },
        )
        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text="✅ Pesan sudah aku pin.")

    async def _set_announce(self, payload: SkillInput, announce: bool) -> SkillOutput:
        result = await call_wa_tool("set_group_announce", {"group_jid": payload.chat_id, "announce": announce})
        text = "✅ Grup sekarang mode announcement — hanya admin yang bisa kirim pesan." if announce else "✅ Mode announcement dimatikan — member bisa chat lagi."
        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=text)


def _is_announce_on(text: str) -> bool:
    return any(keyword in text for keyword in ["announce", "announcement", "annonce", "tutup grup", "hanya admin", "admin only"])


def _is_announce_off(text: str) -> bool:
    return any(keyword in text for keyword in ["buka grup", "matikan announce", "off announce", "member bisa chat"])


def _friendly_tool_error(message: str) -> str:
    lowered = message.casefold()
    if "forbidden" in lowered or "admin" in lowered or "not-authorized" in lowered:
        return "⚠️ Gagal menjalankan aksi. Pastikan bot memiliki izin/sudah jadi admin grup."
    return f"⚠️ Gagal menjalankan aksi WhatsApp: {message}"
