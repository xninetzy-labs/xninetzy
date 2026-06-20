from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.helper.command_docs import get_help


@tool
def helper_get(topic: str | None = None) -> str:
    """Tampilkan panduan command dan capability Xninetzy AI.

    Args:
        topic: Kategori (learning/hebat/life/task/money/workout/knowledge/obsidian/research/help)
               Kosongkan untuk overview semua kategori.
    """
    return get_help(topic)


@tool
def helper_generate_obsidian_docs() -> str:
    """Buat file dokumentasi lengkap di Obsidian vault /Helper/.

    Membuat:
    - Helper/README.md — overview capability
    - Helper/Commands.md — semua slash commands
    - Helper/Examples.md — contoh percakapan
    """
    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService
        from app.xninetzy.helper.command_docs import FULL_OVERVIEW, CATEGORIES
        vault = ObsidianVaultService()

        readme = (
            "---\ntype: helper\ntags: [helper, xninetzy]\n---\n\n"
            + FULL_OVERVIEW.replace("*", "**").replace("_", "")
        )
        vault.create_note("Helper/README.md", readme, overwrite=True)

        commands_lines = ["# Xninetzy Commands\n"]
        for key, cat in CATEGORIES.items():
            commands_lines.append(f"## {cat['title']}\n")
            for ex in cat["examples"]:
                commands_lines.append(f"- `{ex}`")
            commands_lines.append("")
        vault.create_note("Helper/Commands.md", "\n".join(commands_lines), overwrite=True)

        return "✅ Dokumentasi dibuat:\n- `Helper/README.md`\n- `Helper/Commands.md`"
    except Exception as e:
        return f"Gagal membuat dokumentasi Obsidian: {e}"
