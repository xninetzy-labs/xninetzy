from __future__ import annotations

from app.workflow.workflow_service import WorkflowService
from app.skills.base import SkillInput, SkillOutput


class WorkflowSkill:
    name = "workflow"
    description = "Membuat draft workflow automation, SOP, pipeline, trigger, steps, dan tools."
    category = "automation"
    input_schema = {"workflow_request": "string"}
    output_schema = {"trigger": "array", "steps": "array", "tools": "array"}
    safety_policy = "Workflow berulang dan aksi eksternal butuh konfirmasi."
    memory_behavior = "Simpan workflow draft ke SQLite jika diminta."

    async def run(self, payload: SkillInput) -> SkillOutput:
        steps = [
            "Ambil isi pesan WA",
            "Ekstrak nama tugas dan deadline",
            "Buat note di Obsidian folder `Tasks/`",
            "Buat reminder sesuai deadline",
            "Balas konfirmasi ke WhatsApp",
        ]
        result = {
            "name": "WA Task Capture -> Obsidian + Reminder",
            "trigger": ["Pesan WA berisi kata tugas, deadline, atau submit"],
            "steps": steps,
            "tools": ["obsidian_create_task_note", "reminder_create", "wa_send_text"],
        }
        if payload.metadata.get("save"):
            result["stored"] = WorkflowService().create_draft(payload.chat_id, result)
        text = "*Workflow: WA Task Capture → Obsidian + Reminder*\n\nTrigger:\n• Pesan WA berisi kata \"tugas\", \"deadline\", atau \"submit\"\n\nSteps:\n"
        text += "\n".join(f"{i}. {step}" for i, step in enumerate(steps, 1))
        text += "\n\nTool yang dipakai:\n• `obsidian_create_task_note`\n• `reminder_create`\n• `wa_send_text`\n\nMau aku simpan workflow ini sebagai draft di Obsidian?"
        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=text)
