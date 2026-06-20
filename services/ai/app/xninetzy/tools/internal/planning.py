from __future__ import annotations

from langchain_core.tools import tool


@tool
def skill_discovery() -> str:
    """Tampilkan daftar kemampuan dan fitur yang tersedia di bot ini.

    Gunakan saat user bertanya "kamu bisa apa", "fitur apa", atau sejenisnya.
    """
    return """🤖 *Xninetzy AI — Personal Learning & Life OS*

Ketik */helper* untuk detail command.

*1. Learning OS*
• Roadmap belajar otomatis
• Materi HEBAT → ringkas → simpan ke knowledge
• Tanya jawab dari knowledge base (RAG)
• Cari video YouTube & artikel web

*2. HEBAT / E-Learning UNAIR*
• Login, sync course, cek tugas & deadline
• Download & ringkas PDF materi
• Upload tugas (perlu konfirmasi token)

*3. Knowledge OS*
• Simpan teks/PDF ke vector store
• Cari secara semantik
• Deep research → Obsidian + knowledge

*4. Life OS*
• Goal: buat, track progress, review
• /today — rencana & task hari ini
• /review — review harian otomatis

*5. Task Management*
• Catat task, lihat yang due, centang selesai

*6. Money OS*
• Catat pengeluaran/pemasukan
• Ringkasan & breakdown kategori

*7. Workout & Habit OS*
• Log olahraga, habit harian

*8. Obsidian Vault*
• Daily note, learning note, project note

*9. Research*
• web_search, youtube_search, deep_research

*Slash commands:*
/helper /today /goals /tasks /money /workout /hebat /review

Coba: "buat goal belajar React 2 minggu", "cek tugas hebat", "/today" """


@tool
def task_breakdown(task: str, deadline: str | None = None) -> str:
    """Pecah tugas atau proyek menjadi checklist langkah-langkah konkret.

    Args:
        task: Deskripsi tugas atau proyek yang ingin di-breakdown
        deadline: Deadline opsional (contoh: "2 minggu", "30 Juni")
    """
    deadline_info = f"\n\n*Deadline:* {deadline}" if deadline else ""
    return f"""*Task Breakdown: {task}*{deadline_info}

*Langkah-langkah:*
1. Definisikan hasil akhir yang diinginkan secara spesifik
2. Kumpulkan requirement dan batasan yang ada
3. Identifikasi dependencies dan risiko utama
4. Pecah jadi subtask yang bisa dikerjakan dalam 1-2 jam
5. Prioritaskan berdasarkan impact dan urgency (matrix Eisenhower)
6. Kerjakan yang paling blocking terlebih dahulu
7. Review progress dan sesuaikan plan setiap hari

*Next Action:*
Mulai dari langkah 1 — tulis definisi hasil akhir dalam 1-2 kalimat.

_Mau aku simpan breakdown ini ke Obsidian?_"""


@tool
def idea_analysis(idea: str) -> str:
    """Analisis ide secara mendalam: novelty, feasibility, risiko, dan MVP.

    Args:
        idea: Deskripsi ide yang ingin dianalisis
    """
    return f"""*Analisis Ide*

*Ide:* {idea}

*1. Masalah yang Diselesaikan*
Perjelas pain point utama, siapa targetnya, dan seberapa sering masalah itu muncul.

*2. Novelty*
Nilai novelty tergantung pada pembeda: workflow, data, distribusi, atau eksekusi yang lebih sederhana dari solusi yang ada.

*3. Feasibility*
Layak dibuat sebagai MVP jika scope awal dipersempit ke satu use case paling jelas. Estimasi waktu MVP: 1-4 minggu tergantung kompleksitas teknis.

*4. Risiko Utama*
• Scope creep — fitur melebar sebelum validasi
• User belum tervalidasi — asumsi problem belum diconfirm
• Technical uncertainty — stack/infrastruktur belum jelas

*5. MVP yang Disarankan*
Buat versi paling sederhana yang menyelesaikan satu masalah utama, lalu uji ke 3-5 user nyata.

*Skor Awal:* 7/10

_Mau aku bantu breakdown langkah membangun MVP-nya?_"""


@tool
def generate_plan(goal: str, duration: str = "7 hari") -> str:
    """Buat rencana belajar atau kerja terstruktur untuk mencapai goal tertentu.

    Args:
        goal: Goal yang ingin dicapai (contoh: "belajar FastAPI", "selesaikan proyek X")
        duration: Durasi plan (contoh: "7 hari", "2 minggu", "1 bulan")
    """
    return f"""*Plan {duration}: {goal}*

*Fase 1 — Fondasi (25% waktu)*
- Pahami konsep dasar dan setup environment
- Kumpulkan resource dan referensi terbaik
- Definisikan success metric yang jelas

*Fase 2 — Praktik (50% waktu)*
- Bangun sesuatu yang kecil tapi fungsional
- Iterasi cepat: buat → test → perbaiki
- Dokumentasikan temuan dan error yang muncul

*Fase 3 — Konsolidasi (25% waktu)*
- Review semua yang sudah dipelajari/dikerjakan
- Identifikasi gap dan area yang perlu diperkuat
- Rapikan dokumentasi dan catatan
- Rencanakan next step

*Tips:*
- Utamakan progress daripada perfectionism
- Cek progress setiap akhir hari (5 menit)
- Sesuaikan plan jika ada hambatan nyata

_Mau aku buat reminder harian untuk plan ini?_"""


@tool
def draft_workflow(workflow_request: str) -> str:
    """Buat draft workflow automation berdasarkan kebutuhan yang dijelaskan.

    Args:
        workflow_request: Deskripsi workflow yang ingin diautomasi
    """
    return f"""*Draft Workflow: {workflow_request}*

*Trigger:*
• Kondisi yang memulai workflow (pesan masuk, jadwal, event tertentu)

*Steps:*
1. Terima dan parse input
2. Validasi data/kondisi
3. Jalankan aksi utama
4. Handle error jika ada
5. Kirim notifikasi/konfirmasi hasil

*Tools yang Mungkin Dibutuhkan:*
• `reminder_create` — penjadwalan
• `obsidian_create` — penyimpanan catatan
• `wa_send_text` — notifikasi WhatsApp

*Catatan:*
Workflow ini masih draft — perlu disesuaikan dengan sistem dan tools yang tersedia.

_Mau aku simpan draft ini ke Obsidian untuk referensi?_"""
