from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.academic.qa_portal.automation import (
    QaPortalError,
    fill_all_questionnaires,
    list_questionnaires,
)

from app.xninetzy.os.hitl.approval_service import request_approval, validate_approval
from app.xninetzy.os.notifications.admin_notifier import notify_admin_approval
from app.xninetzy.os.policy.action_policy import evaluate_action
from app.xninetzy.os.research.permissions import is_owner_admin


@tool
async def qa_list_kuesioner() -> str:
    """Daftar kuesioner QA (qa.unair.ac.id) untuk owner beserta kode dan link isinya."""
    try:
        entries = await list_questionnaires()
    except QaPortalError as exc:
        return f"Gagal mengambil daftar kuesioner QA: {exc}"
    if not entries:
        return "Tidak ada kuesioner QA yang tersedia."
    return "\n".join(f"{e['code']} — {e['title']}" for e in entries)


@tool
async def qa_fill_kuesioner(
    score: int = 10,
    chat_id: str = "system",
    sender_id: str | None = None,
    approval_id: int | None = None,
) -> str:
    """Isi semua kuesioner QA (qa.unair.ac.id) dengan skor yang diminta (default 10)."""
    if not 1 <= score <= 10:
        return "Skor harus antara 1 sampai 10."
    if not is_owner_admin(sender_id or chat_id, None):
        return "Pengisian kuesioner QA hanya dapat dilakukan oleh admin."
    try:
        entries = await list_questionnaires()
    except QaPortalError as exc:
        return f"Gagal memuat kuesioner QA sebelum approval: {exc}"
    payload = {
        "score": score,
        "questionnaire_codes": sorted(entry["code"] for entry in entries),
    }
    policy = evaluate_action("qa_submit_kuesioner", payload)
    if not policy.allowed:
        return f"Pengisian QA ditahan policy: {policy.reason}"
    if policy.requires_approval:
        if approval_id is None:
            requested_id = request_approval(
                chat_id,
                sender_id,
                "qa_submit_kuesioner",
                "Isi kuesioner QA",
                f"{len(entries)} kuesioner dengan skor {score}.",
                payload,
            )
            delivered = await notify_admin_approval(
                requested_id,
                "qa_submit_kuesioner",
                "Isi kuesioner QA",
                f"{len(entries)} kuesioner dengan skor {score}.",
            )
            delivery = "Tombol approval dikirim ke WhatsApp admin." if delivered else "Tombol approval gagal dikirim."
            return f"Pengisian QA membutuhkan approval #{requested_id}. {delivery}"
        try:
            validate_approval(approval_id, "qa_submit_kuesioner", policy.action_hash)
        except ValueError as exc:
            return f"Pengisian QA ditahan approval: {exc}"
    try:
        result = await fill_all_questionnaires(score=score)
    except QaPortalError as exc:
        return f"Gagal mengisi kuesioner QA: {exc}"
    lines = [f"Skor: {result['score']}"]
    for item in result["results"]:
        if "error" in item:
            lines.append(f"{item['code']} — ERROR: {item['error']}")
        else:
            sections = ", ".join(f"{s['name']}={s['filled']}" for s in item["sections"])
            lines.append(
                f"{item['code']} — {item['title']} — total {item['total_filled']} jawaban ({sections})"
            )
    return "\n".join(lines)
