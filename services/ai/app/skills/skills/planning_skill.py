from __future__ import annotations

from app.skills.base import SkillInput, SkillOutput


class PlanningSkill:
    name = "planning"
    description = "Daily/weekly planning, study plan, project roadmap, habit plan."
    category = "productivity"
    input_schema = {"goal": "string", "period": "daily|weekly|custom"}
    output_schema = {"plan": "array", "reminder_suggestions": "array"}
    safety_policy = "Create banyak reminder butuh konfirmasi."
    memory_behavior = "Simpan plan aktif jika user ingin follow-up."

    async def run(self, payload: SkillInput) -> SkillOutput:
        goal = payload.metadata.get("goal") or payload.message
        days = [
            "Hari 1: Konsep dasar + setup",
            "Hari 2: Praktik kecil dan catatan",
            "Hari 3: Bangun mini project",
            "Hari 4: Review error dan gap",
            "Hari 5: Tambah fitur penting",
            "Hari 6: Rapikan dokumentasi",
            "Hari 7: Evaluasi dan next plan",
        ]
        text = f"*Plan 7 Hari — {goal}*\n\n" + "\n".join(days)
        return SkillOutput(success=True, skill_name=self.name, result={"goal": str(goal), "plan": days}, user_facing_text=text)
