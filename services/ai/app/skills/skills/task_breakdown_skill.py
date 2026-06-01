from __future__ import annotations

from app.obsidian.template_service import TemplateService
from app.obsidian.vault_service import ObsidianVaultService
from app.skills.base import SkillInput, SkillOutput


class TaskBreakdownSkill:
    name = "task_breakdown"
    description = "Breakdown tugas/proyek menjadi checklist, prioritas, timeline, dan next action."
    category = "productivity"
    input_schema = {"task": "string", "deadline": "string|null", "format": "checklist|timeline|sprint|kanban"}
    output_schema = {"checklist": "array", "timeline": "string", "next_action": "string"}
    safety_policy = "Tidak menjalankan aksi eksternal tanpa konfirmasi."
    memory_behavior = "Simpan task/proyek yang ongoing ke memory."

    async def run(self, payload: SkillInput) -> SkillOutput:
        task = payload.metadata.get("task") or payload.message
        checklist = [
            "Definisikan hasil akhir yang diinginkan",
            "Kumpulkan requirement dan batasan",
            "Pecah pekerjaan menjadi subtask kecil",
            "Kerjakan bagian paling blocking dulu",
            "Review hasil dan rapikan dokumentasi",
        ]
        text = "*Task Breakdown*\n\n" + "\n".join(f"{i}. {item}" for i, item in enumerate(checklist, 1))
        text += "\n\n*Next Action:*\nMulai dari definisi hasil akhir dan deadline."

        result = {"task": str(task), "checklist": checklist, "next_action": "Definisikan hasil akhir dan deadline"}
        if payload.metadata.get("save_to_obsidian"):
            path, content = TemplateService().task_note(str(task), goal=str(task))
            saved = ObsidianVaultService().create_note(path, content, overwrite=False)
            result["obsidian"] = saved
            text += f"\n\n✅ Disimpan ke Obsidian: `{saved['path']}`"

        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=text, memory_updates=[{"type": "task", **result}])
