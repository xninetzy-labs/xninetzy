from __future__ import annotations

from langchain_core.tools import tool

from app.reminders.reminder_service import ReminderService, format_reminder_creation_response


@tool
def reminder_create(chat_id: str, message: str) -> str:
    """Buat reminder baru dari pesan natural language.

    Parser otomatis mengenali waktu dari kalimat seperti:
    "besok jam 8", "2 jam lagi", "nanti jam 14.30", "minggu depan"

    Args:
        chat_id: WhatsApp chat ID untuk mengirim reminder nanti (dari context)
        message: Pesan berisi deskripsi dan waktu reminder
    """
    try:
        svc = ReminderService()
        result = svc.create_from_message(chat_id, None, message)
        return format_reminder_creation_response(result)
    except Exception as e:
        return f"Gagal membuat reminder: {e}"


@tool
def reminder_list(chat_id: str) -> str:
    """Lihat semua reminder pending untuk chat ini.

    Args:
        chat_id: WhatsApp chat ID (dari context)
    """
    svc = ReminderService()
    reminders = svc.list_pending(chat_id)
    if not reminders:
        return "Belum ada reminder pending."
    lines = ["*Reminder pending:*"]
    for r in reminders[:20]:
        lines.append(f"• `{r['id']}` {r['title']} - _{r['remind_at']}_ ({r['status']})")
    return "\n".join(lines)


@tool
def reminder_cancel(reminder_id: int) -> str:
    """Batalkan reminder berdasarkan ID.

    Args:
        reminder_id: ID reminder yang ingin dibatalkan (lihat dari reminder_list)
    """
    try:
        ReminderService().cancel(reminder_id)
        return f"✅ Reminder `{reminder_id}` dibatalkan."
    except Exception as e:
        return f"Gagal membatalkan reminder `{reminder_id}`: {e}"
