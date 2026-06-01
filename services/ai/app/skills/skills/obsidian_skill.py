from __future__ import annotations

from datetime import datetime

from app.obsidian.template_service import TemplateService
from app.obsidian.vault_service import ObsidianVaultService
from app.skills.base import SkillInput, SkillOutput


class ObsidianSkill:
    name = "obsidian"
    description = "Baca, cari, buat, dan append note di Obsidian vault lokal yang sudah dimount aman."
    category = "knowledge_base"
    input_schema = {"message": "string", "metadata": "action/path/content/query"}
    output_schema = {"path": "string", "matches": "array"}
    safety_policy = "Semua path dibatasi ke OBSIDIAN_VAULT_PATH dengan sanitizer, backup, dan log operasi."
    memory_behavior = "Simpan path note yang dibuat/diubah ke memory summary."

    def __init__(self) -> None:
        self.vault = ObsidianVaultService()
        self.templates = TemplateService()

    async def run(self, payload: SkillInput) -> SkillOutput:
        action = str(payload.metadata.get("action") or payload.metadata.get("skill_action") or "").strip()
        message = payload.message

        if action in {"search", "search_or_read"} or any(word in message.casefold() for word in ["cari", "search"]):
            query = str(payload.metadata.get("query") or message.replace("di obsidian", "").replace("cari", "")).strip()
            matches = self.vault.search_notes(query)
            text = self._render_matches(query, matches)
            return SkillOutput(success=True, skill_name=self.name, result={"matches": matches}, user_facing_text=text)

        if action == "read":
            path = str(payload.metadata.get("path"))
            content = self.vault.read_note(path)
            return SkillOutput(success=True, skill_name=self.name, result={"path": path, "content": content}, user_facing_text=f"*{path}*\n\n{content[:3000]}")

        if action == "daily":
            path, content = self.templates.daily_note()
            result = self.vault.create_note(path, content, overwrite=False)
            return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=f"✅ Daily note sudah dibuat:\n\n`{result['path']}`")

        if action == "generate_moc":
            folder = payload.metadata.get("folder")
            title = str(payload.metadata.get("title") or "Index")
            result = self.vault.generate_moc(str(folder) if folder else None, title)
            return SkillOutput(success=True, skill_name=self.name, result=result, user_facing_text=f"✅ MOC dibuat:\n\n`{result['path']}`")

        content = str(payload.metadata.get("content") or self._extract_note_content(message))
        path = str(payload.metadata.get("path") or self._default_daily_path())
        append = bool(payload.metadata.get("append", True))
        result = self.vault.append_note(path, content) if append else self.vault.create_note(path, content, overwrite=False)
        return SkillOutput(
            success=True,
            skill_name=self.name,
            result=result,
            user_facing_text=f"✅ Sudah aku catat ke Obsidian.\n\nFile:\n`{result['path']}`",
            memory_updates=[{"type": "obsidian_note", "path": result["path"]}],
        )

    def _extract_note_content(self, message: str) -> str:
        separators = [":", "："]
        for separator in separators:
            if separator in message:
                return message.split(separator, 1)[1].strip()
        return message.strip()

    def _default_daily_path(self) -> str:
        return f"Daily/{datetime.now().strftime('%Y-%m-%d')}.md"

    def _render_matches(self, query: str, matches: list[dict]) -> str:
        if not matches:
            return f"Belum ketemu catatan tentang *{query}* di Obsidian."
        lines = [f"Ketemu beberapa catatan tentang *{query}*:"]
        for index, item in enumerate(matches[:10], start=1):
            lines.append(f"{index}. `{item['path']}`")
        return "\n".join(lines)
