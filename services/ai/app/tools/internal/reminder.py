from __future__ import annotations

from langchain_core.tools import tool

from app.reminders.reminder_service import ReminderService


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
        return (
            f"⏰ Reminder dibuat!\n\n"
            f"*Judul:* {result['title']}\n"
            f"_Jadwal: {result['remind_at']}_"
        )
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
        lines.append(f"• `{r['id']}` {r['title']} - _{r['remind_at']}_")
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
