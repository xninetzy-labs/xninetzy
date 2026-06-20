from __future__ import annotations

import json

from langchain_core.tools import tool

from app.xninetzy.ecosystem.event_bus import record_event


# ─── Tasks ────────────────────────────────────────────────────────────────────

@tool
def task_capture(title: str, description: str = "", priority: str = "medium",
                 due_at: str | None = None, goal_id: int | None = None,
                 chat_id: str = "system") -> str:
    """Catat task baru.

    Args:
        title: Judul task
        description: Detail (opsional)
        priority: low|medium|high|critical
        due_at: Deadline ISO string atau tanggal (opsional)
        goal_id: ID goal terkait (opsional)
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.task_manager import create_task
    t = create_task(title, description, priority, due_at, goal_id)
    record_event(chat_id, "task_created", "whatsapp", "task", str(t["id"]), {"title": title})
    due = f"\nDeadline: {due_at}" if due_at else ""
    return f"✅ Task dicatat!\n*{title}*\nPriority: {priority} | ID: `{t['id']}`{due}"


@tool
def task_list(status: str | None = None) -> str:
    """Tampilkan daftar task (default: yang belum selesai).

    Args:
        status: inbox|next|done|all (opsional, default: semua yang aktif)
    """
    from app.xninetzy.os.life.task_manager import list_tasks
    tasks = list_tasks(status=status)
    if not tasks:
        return "Tidak ada task." + (" Coba `/tasks` atau tambah task baru." if not status else "")

    lines = [f"📝 *Tasks ({len(tasks)}):*\n"]
    for t in tasks[:20]:
        due = f" — {t.get('due_at', '')[:10]}" if t.get("due_at") else ""
        lines.append(f"`{t['id']}` [{t.get('priority','?')}] {t['title']}{due}")
    return "\n".join(lines)


@tool
def task_today() -> str:
    """Tampilkan task yang harus dikerjakan hari ini (due today atau overdue)."""
    from app.xninetzy.os.life.task_manager import list_tasks_today, list_tasks
    tasks = list_tasks_today()
    all_active = list_tasks()
    inbox = [t for t in all_active if t.get("status") == "inbox"][:3]

    lines = ["📅 *Hari ini:*\n"]
    if tasks:
        lines.append("*Due/Overdue:*")
        for t in tasks[:10]:
            due = t.get("due_at", "")[:10] if t.get("due_at") else ""
            lines.append(f"`{t['id']}` [{t.get('priority','?')}] {t['title']} {due}")
    else:
        lines.append("Tidak ada task due hari ini.")

    if inbox:
        lines.append("\n*Inbox (belum dijadwal):*")
        for t in inbox:
            lines.append(f"`{t['id']}` {t['title']}")

    return "\n".join(lines)


@tool
def task_complete(task_id: int, chat_id: str = "system") -> str:
    """Tandai task sebagai selesai.

    Args:
        task_id: ID task
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.task_manager import complete_task, get_task
    t = get_task(task_id)
    if not t:
        return f"Task ID `{task_id}` tidak ditemukan."
    complete_task(task_id)
    record_event(chat_id, "task_completed", "whatsapp", "task", str(task_id), {"title": t["title"]})
    return f"✅ Task *{t['title']}* selesai!"


# ─── Money ────────────────────────────────────────────────────────────────────

@tool
def money_add_transaction(amount: float, tx_type: str, category: str = "lain-lain",
                          description: str = "", chat_id: str = "system") -> str:
    """Catat transaksi keuangan.

    Args:
        amount: Jumlah (positif)
        tx_type: income|expense
        category: Kategori (makan/transport/belanja/kesehatan/pendidikan/pulsa/kos/hiburan/investasi/lain-lain)
        description: Deskripsi singkat
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.money_manager import add_transaction
    result = add_transaction(amount, tx_type, category, description)
    record_event(chat_id, "money_transaction_logged", "whatsapp", "transaction",
                 str(result["id"]), {"amount": amount, "type": tx_type, "category": category})
    sign = "+" if tx_type == "income" else "-"
    return f"💰 Dicatat: {sign}Rp {amount:,.0f} ({category})\n_{description}_"


@tool
def money_summary(period: str = "month") -> str:
    """Ringkasan keuangan dalam periode tertentu.

    Args:
        period: day|week|month|year (default: month)
    """
    from app.xninetzy.os.life.money_manager import get_summary, category_breakdown, get_account_balances
    s = get_summary(period)
    cats = category_breakdown(period)[:5]
    accounts = get_account_balances()

    cat_lines = "\n".join(f"  • {c['category']}: Rp {c['total']:,.0f}" for c in cats) or "  (belum ada)"
    acc_lines = "\n".join(f"  • {a['name']}: Rp {a['balance']:,.0f}" for a in accounts) or "  (belum ada)"

    net_sign = "+" if s["net"] >= 0 else ""
    return (
        f"💰 *Ringkasan {period}* (sejak {s['since']})\n\n"
        f"Pemasukan: Rp {s['income']:,.0f}\n"
        f"Pengeluaran: Rp {s['expense']:,.0f}\n"
        f"Net: {net_sign}Rp {s['net']:,.0f}\n\n"
        f"*Top kategori pengeluaran:*\n{cat_lines}\n\n"
        f"*Saldo:*\n{acc_lines}"
    )


# ─── Workout ──────────────────────────────────────────────────────────────────

@tool
def workout_log(workout_type: str, exercises: str = "", duration: int | None = None,
                intensity: str = "medium", notes: str = "",
                chat_id: str = "system") -> str:
    """Catat sesi workout.

    Args:
        workout_type: gym|cardio|calisthenics|sport|mobility|other
        exercises: Deskripsi latihan, contoh: "push up 3x15, squat 3x20"
        duration: Durasi dalam menit
        intensity: low|medium|high
        notes: Catatan tambahan
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.workout_manager import log_workout
    exercises_data = [{"exercise": exercises}] if exercises else []
    result = log_workout(workout_type, exercises_data, duration, intensity, notes)
    record_event(chat_id, "workout_logged", "whatsapp", "workout",
                 str(result["id"]), {"type": workout_type, "duration": duration})

    dur_str = f" | {duration} menit" if duration else ""
    return f"💪 Workout dicatat!\nTipe: {workout_type}{dur_str}\n_{exercises}_"


@tool
def workout_summary(period: str = "week") -> str:
    """Ringkasan workout dalam periode tertentu.

    Args:
        period: week|month (default: week)
    """
    from app.xninetzy.os.life.workout_manager import get_workout_summary
    s = get_workout_summary(period)
    sessions = s["sessions"]

    if not sessions:
        return f"Belum ada workout tercatat untuk periode '{period}'."

    lines = [f"💪 *Workout {period}*\n",
             f"Sesi: {s['session_count']} | Total: {s['total_minutes']} menit\n",
             "*Sesi terakhir:*"]
    for sess in sessions[:5]:
        dur = f" ({sess.get('duration_minutes', '?')} min)" if sess.get("duration_minutes") else ""
        lines.append(f"• {sess['workout_date']} — {sess['type']}{dur}")
    return "\n".join(lines)


# ─── Habit ────────────────────────────────────────────────────────────────────

@tool
def habit_log(name: str, value: int = 1, notes: str = "",
              chat_id: str = "system") -> str:
    """Catat habit hari ini.

    Args:
        name: Nama habit (akan dibuat otomatis jika belum ada)
        value: Jumlah (default: 1)
        notes: Catatan (opsional)
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.habit_manager import log_habit
    result = log_habit(name, value, notes)
    record_event(chat_id, "habit_logged", "whatsapp", "habit", name, {"value": value})
    return f"✅ Habit *{name}* dicatat (×{value})"


@tool
def habit_today() -> str:
    """Tampilkan status semua habit hari ini."""
    from app.xninetzy.os.life.habit_manager import get_habit_today
    habits = get_habit_today()
    if not habits:
        return "Belum ada habit. Catat habit pertama: 'habit belajar' atau 'habit olahraga'"

    lines = ["🔄 *Habit hari ini:*\n"]
    for h in habits:
        done = "✅" if h["completed"] else "⬜"
        lines.append(f"{done} {h['name']} ({h['done_today']}/{h['target_count']})")
    return "\n".join(lines)


# ─── Daily ────────────────────────────────────────────────────────────────────

@tool
def daily_checkin(mood: int, energy: int, focus: int, summary: str,
                  chat_id: str = "system") -> str:
    """Catat check-in harian (mood, energi, fokus, ringkasan hari).

    Args:
        mood: Skor mood 1-5
        energy: Skor energi 1-5
        focus: Skor fokus 1-5
        summary: Ringkasan hari ini dalam 1-2 kalimat
        chat_id: WhatsApp chat ID (dari context)
    """
    from app.xninetzy.os.life.journal_manager import checkin
    result = checkin(mood, energy, focus, summary)
    record_event(chat_id, "daily_checkin", "whatsapp", "review", str(result["id"]),
                 {"mood": mood, "energy": energy})

    # Auto-append ke daily note
    try:
        from app.xninetzy.os.notes.vault_service import ObsidianVaultService
        ObsidianVaultService().append_note(
            f"Daily/{result['date']}.md",
            f"**Check-in** Mood:{mood}/5 Energi:{energy}/5 Fokus:{focus}/5\n{summary}",
        )
    except Exception:
        pass

    return f"✅ Check-in {result['date']} disimpan.\nMood: {mood}/5 | Energi: {energy}/5 | Fokus: {focus}/5"


@tool
def daily_review_generate(chat_id: str = "system") -> str:
    """Generate review harian: lihat task selesai, goal progress, dan beri saran."""
    from app.xninetzy.os.life.journal_manager import get_review, save_review
    from app.xninetzy.os.life.task_manager import list_tasks
    from app.xninetzy.os.life.goal_manager import list_goals
    from app.xninetzy.tools.internal.datetime_info import get_now_info

    now = get_now_info()
    today = now["date"]
    review = get_review(today)

    # Completed tasks today
    done_tasks = list_tasks(status="done")
    today_done = [t for t in done_tasks if t.get("updated_at", "")[:10] == today]

    # Active goals
    goals = list_goals(status="active", limit=5)

    summary_parts = []
    if today_done:
        summary_parts.append(f"{len(today_done)} task selesai hari ini")
    if review:
        summary_parts.append(f"Mood {review.get('mood', '?')}/5, Fokus {review.get('focus', '?')}/5")

    wins = "\n".join(f"• {t['title']}" for t in today_done[:5]) or "Belum ada task selesai dicatat."
    goal_status = "\n".join(
        f"• {g['title']} ({g.get('status', '?')})" for g in goals[:3]
    ) or "Belum ada goal aktif."

    output = (
        f"📔 *Review {today}*\n\n"
        f"*Task selesai hari ini:*\n{wins}\n\n"
        f"*Goal aktif:*\n{goal_status}\n\n"
        f"*Saran besok:*\nLihat goal dan task yang belum progress."
    )

    if review:
        save_review(today, wins, "", "", "Auto-generated review")

    record_event(chat_id, "daily_review_created", "system", "review", today, {})
    return output


@tool
def life_dashboard(chat_id: str = "system") -> str:
    """Tampilkan dashboard lengkap hari ini: goals, tasks, habits, dan deadlines."""
    from app.xninetzy.os.life.task_manager import list_tasks_today
    from app.xninetzy.os.life.goal_manager import list_goals
    from app.xninetzy.os.life.habit_manager import get_habit_today
    from app.xninetzy.os.academic.hebat.storage import list_assignments
    from app.xninetzy.tools.internal.datetime_info import get_now_info

    now = get_now_info()
    lines = [f"🌅 *Dashboard {now['human_date']}*\n"]

    # Goals
    goals = list_goals(limit=3)
    if goals:
        lines.append("*🎯 Goals aktif:*")
        for g in goals:
            lines.append(f"  • {g['title']}")

    # Tasks today
    tasks = list_tasks_today()[:5]
    if tasks:
        lines.append("\n*📝 Task hari ini:*")
        for t in tasks:
            lines.append(f"  [{t.get('priority','?')}] {t['title']}")
    else:
        lines.append("\n*📝 Tasks:* tidak ada yang due hari ini")

    # Habits
    habits = get_habit_today()[:4]
    if habits:
        lines.append("\n*🔄 Habits:*")
        for h in habits:
            done = "✅" if h["completed"] else "⬜"
            lines.append(f"  {done} {h['name']}")

    # HEBAT deadlines
    try:
        assigns = [
            a for a in list_assignments()
            if a.get("due_at") and a.get("submission_status", "").lower() not in ("submitted for grading",)
        ][:3]
        if assigns:
            lines.append("\n*📚 HEBAT deadlines:*")
            for a in assigns:
                lines.append(f"  ⏰ {a['title']} — {a.get('due_at', '?')[:16]}")
    except Exception:
        pass

    return "\n".join(lines)
