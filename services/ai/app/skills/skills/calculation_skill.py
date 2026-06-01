from __future__ import annotations

import re

from app.skills.base import SkillInput, SkillOutput
from app.skills.tools.math_tool import MathTool


class CalculationSkill:
    name = "calculation"
    description = "Hitungan deterministik: arithmetic, persentase, statistik sederhana, estimasi numerik."
    category = "utility"
    input_schema = {"message": "string"}
    output_schema = {"result": "number|string", "steps": "string"}
    safety_policy = "Gunakan AST safe math, tidak memakai eval mentah."
    memory_behavior = "Simpan hanya jika perhitungan terkait task/proyek penting."

    def __init__(self) -> None:
        self.tool = MathTool()

    async def run(self, payload: SkillInput) -> SkillOutput:
        text = payload.message
        percent = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:dari|/)\s*(\d+(?:[.,]\d+)?)", text.casefold())
        if percent and ("persen" in text.casefold() or "berapa" in text.casefold()):
            part = float(percent.group(1).replace(",", "."))
            whole = float(percent.group(2).replace(",", "."))
            result = self.tool.percentage(part, whole)
            value = result["result"]
            return SkillOutput(
                success=True,
                skill_name=self.name,
                result=result,
                user_facing_text=f"*Hasil:* {value:g}%\n\nCara hitung:\n`{result['steps']}`",
            )

        expression = self._extract_expression(text)
        value = self.tool.safe_eval(expression)
        return SkillOutput(
            success=True,
            skill_name=self.name,
            result={"result": value, "expression": expression},
            user_facing_text=f"*Hasil:* {value:g}\n\nCara hitung:\n`{expression} = {value:g}`",
        )

    def _extract_expression(self, text: str) -> str:
        allowed = re.findall(r"[0-9+\-*/().%\s]+", text)
        expression = " ".join(part.strip() for part in allowed if part.strip()).replace("%", "/100")
        if not expression:
            raise ValueError("Aku belum nemu ekspresi angka yang bisa dihitung")
        return expression
