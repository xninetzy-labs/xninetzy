from __future__ import annotations

import json

from langchain_core.tools import tool

from app.xninetzy.os.notes.organization_service import ObsidianOrganizationService


def _service() -> ObsidianOrganizationService:
    return ObsidianOrganizationService()


@tool
def obsidian_vault_init() -> str:
    """Siapkan struktur folder canonical Xninetzy di vault."""
    try:
        return json.dumps(_service().ensure_structure(), ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal menyiapkan struktur vault: {exc}"


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
    from app.xninetzy.os.hitl.approval_service import request_approval
    from app.xninetzy.os.notifications.admin_notifier import notify_admin_approval

    moves = list(plan.get("moves") or [])
    if not moves:
        return "Tidak ada perpindahan note yang perlu diterapkan."
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
    delivery = "Tombol approval dikirim ke WhatsApp admin." if delivered else "Approval tersimpan; pengiriman tombol admin gagal."
    return f"Approval foldering #{approval_id} dibuat. {delivery}"


@tool
def obsidian_moc_refresh() -> str:
    """Siapkan folder canonical dan refresh MOC navigasi utama."""
    try:
        service = _service()
        structure = service.ensure_structure()
        mocs = service.refresh_mocs()
        return json.dumps({"structure": structure, "mocs": mocs, "status": service.verify()}, ensure_ascii=False, indent=2)
    except Exception as exc:
        return f"Gagal memperbarui MOC vault: {exc}"


@tool
def obsidian_verify() -> str:
    """Verifikasi struktur folder dan duplicate note ID."""
    return obsidian_folder_status.invoke({})
