from __future__ import annotations

from datetime import datetime

from langchain_core.tools import tool

from app.xninetzy.os.notes.template_service import TemplateService
from app.xninetzy.os.notes.vault_service import ObsidianVaultService


def _vault() -> ObsidianVaultService:
    return ObsidianVaultService()


@tool
def obsidian_search(query: str, limit: int = 10) -> str:
    """Cari catatan di Obsidian vault berdasarkan keyword.

    Args:
        query: Kata kunci pencarian
        limit: Jumlah maksimal hasil (default 10)
    """
    matches = _vault().search_notes(query, limit)
    if not matches:
        return f"Tidak ada catatan tentang '{query}' di vault."
    lines = [f"Ditemukan {len(matches)} catatan tentang *{query}*:"]
    for i, m in enumerate(matches[:limit], 1):
        lines.append(f"{i}. `{m['path']}`")
    return "\n".join(lines)


@tool
def obsidian_read(path: str) -> str:
    """Baca isi catatan markdown dari Obsidian vault.

    Args:
        path: Path relatif ke file di vault, contoh: "Daily/2026-06-01.md"
    """
    try:
        content = _vault().read_note(path)
        return f"*{path}*\n\n{content[:3000]}"
    except Exception as e:
        return f"Gagal membaca '{path}': {e}"


@tool
def obsidian_create(path: str, content: str) -> str:
    """Buat catatan baru di Obsidian vault (gagal jika sudah ada).

    Args:
        path: Path relatif file baru, contoh: "Tasks/2026-06-01-tugas.md"
        content: Konten markdown catatan
    """
    try:
        result = _vault().create_note(path, content, overwrite=False)
        return f"✅ Catatan dibuat: `{result['path']}`"
    except Exception as e:
        return f"Gagal membuat catatan: {e}"


@tool
def obsidian_append(path: str, content: str) -> str:
    """Tambahkan konten ke catatan yang sudah ada (atau buat baru jika belum ada).

    Args:
        path: Path relatif file, contoh: "Daily/2026-06-01.md"
        content: Konten yang akan ditambahkan
    """
    try:
        result = _vault().append_note(path, content)
        return f"✅ Sudah ditambahkan ke: `{result['path']}`"
    except Exception as e:
        return f"Gagal append ke catatan: {e}"


@tool
def obsidian_daily() -> str:
    """Buat atau ambil daily note untuk hari ini."""
    try:
        path, content = TemplateService().daily_note()
        result = _vault().create_note(path, content, overwrite=False)
        return f"✅ Daily note siap: `{result['path']}`"
    except Exception as e:
        return f"Gagal membuat daily note: {e}"


@tool
def obsidian_save_note(title: str, content: str, folder: str = "Notes") -> str:
    """Simpan catatan dengan judul tertentu ke folder Obsidian.

    Args:
        title: Judul catatan (dipakai sebagai nama file)
        content: Isi catatan dalam markdown
        folder: Folder tujuan di vault (default: "Notes")
    """
    safe_title = title.replace("/", "-").replace("\\", "-").strip()
    path = f"{folder}/{safe_title}.md"
    try:
        result = _vault().create_note(path, content, overwrite=False)
        return f"✅ Disimpan: `{result['path']}`"
    except Exception as e:
        today = datetime.now().strftime("%Y-%m-%d-%H%M")
        path = f"{folder}/{safe_title}-{today}.md"
        try:
            result = _vault().create_note(path, content, overwrite=False)
            return f"✅ Disimpan (dengan timestamp): `{result['path']}`"
        except Exception as e2:
            return f"Gagal menyimpan catatan: {e2}"
