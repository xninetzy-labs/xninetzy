from __future__ import annotations

import json

from langchain_core.tools import tool

from xninetzy.os.notes.organization_service import ObsidianOrganizationService


def _service() -> ObsidianOrganizationService:
    return ObsidianOrganizationService()


@tool
def obsidian_vault_init(
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Minta approval owner sebelum membuat folder canonical Xninetzy di vault."""
    from xninetzy.os.hitl.approval_service import request_approval

    if not sender_id:
        return json.dumps({
            "error": "sender_id wajib untuk vault_init (mass-write; butuh approval)",
        }, ensure_ascii=False)
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=sender_id,
        action_type="obsidian_vault_init",
        title="Inisialisasi struktur vault Obsidian",
        summary="Membuat 30+ folder canonical + Home.md di vault.",
        payload={},
    )
    try:
        result = _service().ensure_structure()
    except Exception as exc:
        return f"Gagal menyiapkan struktur vault: {exc}"
    payload = {"approval_id": approval_id, **result}
    return json.dumps(payload, ensure_ascii=False, indent=2)


@tool
def obsidian_folder_status() -> str:
    """Tampilkan status struktur folder canonical dan kesehatan metadata."""
    try:
        return json.dumps(_service().verify(), ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal memeriksa struktur vault: {exc}"


@tool
def obsidian_organize_preview() -> str:
    """Buat preview migrasi folder tanpa mengubah isi vault."""
    try:
        return json.dumps(_service().preview(), ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal membuat preview organisasi vault: {exc}"


@tool
async def obsidian_organize_apply(
    plan: dict,
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Minta approval owner sebelum memindahkan note ke folder canonical."""
    from xninetzy.os.hitl.approval_service import request_approval
    from xninetzy.os.notifications.admin_notifier import notify_admin_approval

    moves = list(plan.get("moves") or [])
    if not moves:
        return "Tidak ada perpindahan note yang perlu diterapkan."
    if not sender_id:
        return "sender_id wajib untuk obsidian_organize_apply (mass-write; butuh approval)."
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=sender_id,
        action_type="obsidian_organize_apply",
        title="Terapkan foldering canonical Obsidian",
        summary=f"Memindahkan {len(moves)} note setelah backup dan validasi hash sumber.",
        payload={"plan": plan},
    )
    delivered = await notify_admin_approval(
        approval_id,
        "obsidian_organize_apply",
        "Terapkan foldering canonical Obsidian",
        f"Memindahkan {len(moves)} note setelah backup dan validasi hash sumber.",
    )
    delivery = "Tombol approval dikirim ke  admin." if delivered else "Approval tersimpan; pengiriman tombol admin gagal."
    return f"Approval foldering #{approval_id} dibuat. {delivery}"


@tool
def obsidian_moc_refresh(
    chat_id: str = "system",
    sender_id: str | None = None,
) -> str:
    """Minta approval owner sebelum refresh MOC navigasi utama (7 Index.md ditimpa)."""
    from xninetzy.os.hitl.approval_service import request_approval

    if not sender_id:
        return json.dumps({
            "error": "sender_id wajib untuk moc_refresh (mass-write; butuh approval)",
        }, ensure_ascii=False)
    approval_id = request_approval(
        chat_id=chat_id,
        sender_id=sender_id,
        action_type="obsidian_moc_refresh",
        title="Refresh Map of Content Obsidian",
        summary="Menimpa 7 Index.md (Learning, Projects, Academic, Research, Life, Knowledge, System).",
        payload={},
    )
    try:
        service = _service()
        structure = service.ensure_structure()
        mocs = service.refresh_mocs()
        return json.dumps({
            "approval_id": approval_id,
            "structure": structure,
            "mocs": mocs,
            "status": service.verify(),
        }, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal memperbarui MOC vault: {exc}"


@tool
def obsidian_verify() -> str:
    """Verifikasi struktur folder dan duplicate note ID."""
    return obsidian_folder_status.invoke({})
