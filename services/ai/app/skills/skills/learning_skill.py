from __future__ import annotations

from app.obsidian.template_service import TemplateService
from app.obsidian.vault_service import ObsidianVaultService
from app.skills.base import SkillInput, SkillOutput


class LearningSkill:
    name = "learning"
    description = "Menjelaskan konsep, ringkasan, contoh, latihan soal, dan catatan belajar."
    category = "education"
    input_schema = {"topic": "string", "level": "beginner|intermediate|advanced", "mode": "explain|summary|quiz|step_by_step|example"}
    output_schema = {"explanation": "string", "key_points": "array", "examples": "array"}
    safety_policy = "Bantu proses belajar, jangan sekadar memberi jawaban final untuk tugas akademik."
    memory_behavior = "Simpan preferensi belajar dan topik ongoing."

    async def run(self, payload: SkillInput) -> SkillOutput:
        topic = str(payload.metadata.get("topic") or payload.message).strip()
        text = f"""*{topic}*

Ringkasnya: ini topik yang bisa dipahami dengan memecahnya jadi konsep inti, contoh, lalu latihan.

*Langkah Belajar:*
1. Pahami definisi dan tujuan topiknya
2. Lihat contoh konkret
3. Coba latihan kecil
4. Review bagian yang masih kabur

*Latihan:*
• Jelaskan ulang topik ini dengan bahasamu sendiri
• Buat satu contoh kasus nyata"""
        result = {"topic": topic, "explanation": text}
        if payload.metadata.get("save_to_obsidian"):
            path, content = TemplateService().learning_note(topic, summary=text)
            result["obsidian"] = ObsidianVaultService().create_note(path, content, overwrite=False)
            text += f"\n\n✅ Catatan belajar disimpan: `{result['obsidian']['path']}`"
        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=text)
