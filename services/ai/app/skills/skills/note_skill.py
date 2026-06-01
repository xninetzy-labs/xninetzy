from __future__ import annotations

from app.obsidian.vault_service import ObsidianVaultService
from app.skills.base import SkillInput, SkillOutput


class NoteGenerationSkill:
    name = "note_generation"
    description = "Membuat markdown note terstruktur dari chat, memory, atau konten custom."
    category = "knowledge_base"
    input_schema = {"title": "string", "content_source": "chat|memory|custom", "note_type": "learning|project|meeting|daily|idea|workflow|task"}
    output_schema = {"markdown": "string", "path": "string|null"}
    safety_policy = "Write ke vault mengikuti Obsidian safety service."
    memory_behavior = "Simpan note path jika file dibuat."

    async def run(self, payload: SkillInput) -> SkillOutput:
        title = str(payload.metadata.get("title") or "Catatan")
        body = str(payload.metadata.get("content") or payload.message)
        markdown = f"# {title}\n\n{body.strip()}\n"
        result = {"markdown": markdown}
        text = markdown
        if payload.metadata.get("target_path"):
            saved = ObsidianVaultService().create_note(str(payload.metadata["target_path"]), markdown, overwrite=False)
            result["path"] = saved["path"]
            text = f"✅ Note markdown dibuat:\n\n`{saved['path']}`"
        return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=text)
