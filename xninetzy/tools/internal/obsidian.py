from __future__ import annotations

import json
from datetime import datetime

from langchain_core.tools import tool

from app.xninetzy.os.notes.template_service import TemplateService
from app.xninetzy.os.notes.vault_service import ObsidianVaultService


def _vault() -> ObsidianVaultService:
    return ObsidianVaultService()


@tool
def obsidian_list(folder: str = "", limit: int = 100) -> str:
    """Daftar file markdown/text dalam vault atau folder tertentu."""
    try:
        files = _vault().list_files(folder or None)[: max(1, min(limit, 500))]
        return json.dumps(files, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal menampilkan isi vault: {exc}"


@tool
def obsidian_create_folder(path: str) -> str:
    """Buat folder baru di dalam vault menggunakan path relatif."""
    try:
        result = _vault().create_folder(path)
        return f"✅ Folder siap: `{result['path']}`"
    except Exception as exc:
        return f"Gagal membuat folder: {exc}"


@tool
def obsidian_update_section(path: str, heading: str, content: str) -> str:
    """Ganti isi section berdasarkan heading; buat section jika belum ada."""
    try:
        result = _vault().update_section(path, heading, content)
        return f"✅ Section *{heading}* diperbarui di `{result['path']}`"
    except Exception as exc:
        return f"Gagal memperbarui section: {exc}"


@tool
def obsidian_todos(folder: str = "", limit: int = 100) -> str:
    """Ambil checkbox todo selesai/belum selesai dari seluruh atau sebagian vault."""
    try:
        items = _vault().extract_todos(folder or None)[: max(1, min(limit, 500))]
        return json.dumps(items, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal membaca todo vault: {exc}"


@tool
def obsidian_backlinks(note_path: str, limit: int = 100) -> str:
    """Cari note yang memiliki wikilink menuju note tertentu."""
    try:
        items = _vault().get_backlinks(note_path)[: max(1, min(limit, 500))]
        return json.dumps(items, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal membaca backlinks: {exc}"


@tool
def obsidian_headings(path: str) -> str:
    """Ambil struktur heading beserta level dan nomor baris suatu note."""
    try:
        return json.dumps(_vault().extract_headings(path), ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal membaca heading: {exc}"


@tool
def obsidian_generate_moc(folder: str = "", title: str = "Index") -> str:
    """Buat atau perbarui Map of Content berisi wikilink note dalam folder."""
    try:
        result = _vault().generate_moc(folder or None, title)
        return f"✅ Map of Content dibuat: `{result['path']}`"
    except Exception as exc:
        return f"Gagal membuat Map of Content: {exc}"


@tool
def obsidian_add_tags(path: str, tags: list[str]) -> str:
    """Tambahkan tags ke frontmatter note tanpa menghapus tag lama."""
    try:
        result = _vault().add_tags(path, tags)
        return f"✅ Tags diperbarui di `{result['path']}`"
    except Exception as exc:
        return f"Gagal menambahkan tags: {exc}"


@tool
def obsidian_set_frontmatter(path: str, data: dict) -> str:
    """Tambah atau perbarui field frontmatter note."""
    try:
        result = _vault().add_frontmatter(path, data)
        return f"✅ Frontmatter diperbarui di `{result['path']}`"
    except Exception as exc:
        return f"Gagal memperbarui frontmatter: {exc}"


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
def obsidian_search_health() -> str:
    """Periksa kesehatan indeks pencarian Obsidian berbasis SQLite FTS."""
    try:
        health = _vault().search_index_health().as_dict()
        return json.dumps(health, ensure_ascii=False)
    except Exception as exc:
        return json.dumps({"healthy": False, "error": str(exc)}, ensure_ascii=False)


@tool
def obsidian_read(path: str, offset: int = 0, limit: int = 3000) -> str:
    """Baca isi catatan markdown dari Obsidian vault.

    Args:
        path: Path relatif ke file di vault, contoh: "Daily/2026-06-01.md"
        offset: Karakter awal yang dibaca (default 0)
        limit: Jumlah karakter maksimal yang dibaca (default 3000)
    """
    try:
        content = _vault().read_note(path)
        total = len(content)
        selected = content[offset : offset + limit]
        truncated = offset + len(selected) < total
        note = f"*{path}* (total {total} chars)\n\n{selected}"
        if truncated:
            note += f"\n\n_(dipotong: {offset + len(selected)}/{total} — gunakan offset untuk lanjut)_"
        return note
    except Exception as e:
        return f"Gagal membaca '{path}': {e}"


@tool
def obsidian_create(path: str, content: str, overwrite: bool = False) -> str:
    """Buat catatan baru di Obsidian vault.

    Args:
        path: Path relatif file baru, contoh: "Tasks/2026-06-01-tugas.md"
        content: Konten markdown catatan
        overwrite: Timpa file yang sudah ada (default False)
    """
    try:
        result = _vault().create_note(path, content, overwrite=overwrite)
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
def obsidian_save_note(title: str, content: str, folder: str = "Knowledge/Notes") -> str:
    """Simpan catatan dengan judul tertentu ke folder Obsidian.

    Args:
        title: Judul catatan (dipakai sebagai nama file)
        content: Isi catatan dalam markdown
        folder: Folder tujuan di vault (default: "Knowledge/Notes")
    """
    safe_title = title.replace("/", "-").replace("\\", "-").strip()
    path = f"{folder}/{safe_title}.md"
    try:
        result = _vault().create_note(path, content, overwrite=False)
        return f"✅ Disimpan: `{result['path']}`"
    except Exception:
        today = datetime.now().strftime("%Y-%m-%d-%H%M")
        path = f"{folder}/{safe_title}-{today}.md"
        try:
            result = _vault().create_note(path, content, overwrite=False)
            return f"✅ Disimpan (dengan timestamp): `{result['path']}`"
        except Exception as e2:
            return f"Gagal menyimpan catatan: {e2}"
