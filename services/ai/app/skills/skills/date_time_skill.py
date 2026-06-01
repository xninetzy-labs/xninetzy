from __future__ import annotations

from app.skills.base import SkillInput, SkillOutput
from app.skills.tools.date_tool import DateTool


class DateTimeSkill:
    name = "date_time"
    description = "Memberi tanggal, hari, jam, dan timestamp saat ini berdasarkan timezone aplikasi."
    category = "utility"
    input_schema = {"message": "string", "timezone": "string|null"}
    output_schema = {"iso": "string", "date": "string", "time": "string", "human_datetime": "string"}
    safety_policy = "Gunakan waktu sistem server dengan timezone eksplisit, jangan menebak tanggal."
    memory_behavior = "Tidak perlu disimpan kecuali terkait reminder/planning."

    def __init__(self) -> None:
        self.tool = DateTool()

    async def run(self, payload: SkillInput) -> SkillOutput:
        timezone = payload.metadata.get("timezone")
        data = self.tool.now(str(timezone) if timezone else None)
        return SkillOutput(
            success=True,
            skill_name=self.name,
            result=data,
            user_facing_text=f"Sekarang: *{data['human_datetime']}*",
        )
