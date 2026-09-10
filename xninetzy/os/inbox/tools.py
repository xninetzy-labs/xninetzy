from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.inbox.service import (
    build_attention_queue,
    capture_item,
    capture_summary,
    list_captures,
    triage_capture,
)


@tool
def os_capture(
    content: str,
    kind: str = "auto",
    idempotency_key: str | None = None,
    chat_id: str = "system",
) -> str:
    """Capture cepat ke OS Inbox untuk input yang belum jelas menjadi task/note/ide."""
    try:
        item, created = capture_item(
            content,
            kind=kind,
            chat_id=chat_id,
            idempotency_key=idempotency_key,
        )
    except ValueError as error:
        return f"⚠️ Capture ditolak: {error}"
    state = "ditangkap" if created else "sudah pernah ditangkap"
    return (
        f"📥 *OS Inbox #{item['id']}* {state}.\n"
        f"Jenis: {item['inferred_kind']}\n"
        f"{item['title']}\n\n"
        f"Triage: `/triage {item['id']} task` atau `/triage {item['id']} archive`"
    )


@tool
def os_inbox(status: str = "inbox", limit: int = 10) -> str:
    """Lihat capture yang belum diproses di OS Inbox lintas WhatsApp dan MCP."""
    try:
        items = list_captures(status=status, limit=limit)
    except ValueError as error:
        return f"⚠️ {error}"
    summary = capture_summary()
    lines = [
        f"📥 *OS Inbox* — {summary['inbox']} belum diproses",
        f"Processed: {summary['processed']} | Archived: {summary['archived']}",
    ]
    if not items:
        lines.append("\nInbox kosong. Semua capture sudah diproses.")
        return "\n".join(lines)
    lines.append("")
    for item in items:
        lines.append(
            f"`{item['id']}` [{item['inferred_kind']}] {item['title']}"
        )
    lines.append("\nGunakan `/triage <id> task|archive`.")
    return "\n".join(lines)


@tool
def os_triage(
    capture_id: int,
    target: str = "task",
    priority: str = "medium",
    due_at: str | None = None,
    chat_id: str = "system",
) -> str:
    """Proses satu OS capture menjadi task atau archive secara idempotent."""
    try:
        result = triage_capture(
            capture_id,
            target=target,
            priority=priority,
            due_at=due_at,
            chat_id=chat_id,
        )
    except ValueError as error:
        return f"⚠️ Triage ditolak: {error}"
    if result["replayed"]:
        return (
            f"Capture #{capture_id} sudah diproses sebagai "
            f"{result.get('target_type') or result['status']}"
            + (f" #{result['target_id']}" if result.get("target_id") else ".")
        )
    if result["target_type"] == "archive":
        return f"🗄️ Capture #{capture_id} diarsipkan."
    return (
        f"✅ Capture #{capture_id} menjadi task #{result['target_id']}.\n"
        f"{result['title']}"
    )


@tool
def os_today(limit: int = 5) -> str:
    """Tampilkan attention queue lintas task, learning state, dan OS Inbox."""
    queue = build_attention_queue(limit=limit)
    summary = capture_summary()
    lines = ["🧭 *Xninetzy OS — Attention Queue*"]
    if not queue:
        lines += ["", "Tidak ada komitmen aktif.", "Capture sesuatu dengan `/capture <isi>`."]
        return "\n".join(lines).rstrip()
    top = queue[0]
    lines += [
        "",
        "*Fokus utama:*",
        f"{top['title']}",
        f"Alasan: {top['reason']}",
        f"Next action: {top['action']}",
        "",
        "*Queue:*",
    ]
    for position, item in enumerate(queue, start=1):
        lines.append(
            f"{position}. [{item['kind']}] {item['title']} — {item['reason']}"
        )
    if summary["inbox"]:
        lines += ["", f"📥 {summary['inbox']} capture masih perlu ditriage."]
    return "\n".join(lines)


OS_INBOX_TOOLS = [os_capture, os_inbox, os_triage, os_today]
