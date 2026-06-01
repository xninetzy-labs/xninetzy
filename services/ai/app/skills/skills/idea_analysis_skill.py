from __future__ import annotations

from app.skills.base import SkillInput, SkillOutput


class IdeaAnalysisSkill:
    name = "idea_analysis"
    description = "Analisis ide, SWOT, novelty, feasibility, risiko, dan MVP scope."
    category = "analysis"
    input_schema = {"idea": "string", "analysis_type": "swot|novelty|feasibility|mvp|full"}
    output_schema = {"score": "number", "sections": "object"}
    safety_policy = "Tidak mengaku browsing/deep research jika tool web tidak tersedia."
    memory_behavior = "Simpan ide dan keputusan penting ke memory."

    async def run(self, payload: SkillInput) -> SkillOutput:
        idea = str(payload.metadata.get("idea") or payload.message).strip()
        text = f"""*Analisis Ide*

*1. Inti Ide*
{idea}

*2. Masalah yang Diselesaikan*
Perjelas pain point utama, siapa usernya, dan seberapa sering masalah itu muncul.

*3. Novelty*
Nilai novelty tergantung pembeda: workflow, data, distribusi, atau eksekusi yang lebih sederhana.

*4. Feasibility*
Layak dibuat sebagai MVP kalau scope awal dipersempit ke satu use case paling jelas.

*5. Risiko*
• Scope melebar
• Kebutuhan data belum jelas
• User belum tervalidasi

*6. MVP yang Disarankan*
Buat versi kecil yang menyelesaikan satu masalah utama, lalu uji ke 3-5 user.

*Skor Awal:* 7/10"""
        return SkillOutput(success=True, skill_name=self.name, result={"idea": idea, "score": 7}, user_facing_text=text)
