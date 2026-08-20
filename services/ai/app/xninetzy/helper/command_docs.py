from __future__ import annotations

CATEGORIES = {
    "os": {
        "title": "Xninetzy OS Kernel",
        "examples": [
            "/capture ide atau informasi yang belum jelas",
            "/inbox — lihat capture yang belum diproses",
            "/triage 12 task — promosikan capture menjadi task",
            "/triage 12 archive — arsipkan capture",
            "/today — attention queue lintas task, learning, dan inbox",
        ],
    },
    "learning": {
        "title": "Learning OS",
        "examples": [
            "belajarin aku DFD dari materi HEBAT",
            "buat roadmap belajar blockchain 30 hari",
            "cari video terbaik untuk sequence diagram",
            "simpan materi ini ke knowledge",
            "tanya knowledge: apa bedanya DFD dan UML?",
            "buat workspace APSI dari semua materi",
            "deep research tentang AI agent security",
            "/concepts 12 — concept graph, prerequisite, evidence, dan mastery",
            "/recall — pertanyaan active recall yang jatuh tempo",
        ],
    },
    "hebat": {
        "title": "HEBAT / E-Learning UNAIR",
        "examples": [
            "login hebat",
            "sync course hebat",
            "cek tugas hebat",
            "deadline terdekat apa",
            "ambil materi APSI week 12",
            "ringkas PDF tugas besar",
            "kumpulkan file ini ke Tugas Besar APSI Progress 1",
        ],
    },
    "life": {
        "title": "Life OS",
        "examples": [
            "buat goal: paham React dalam 2 minggu",
            "progress goal React: hari ini belajar hooks",
            "review goal React",
            "/today",
            "/review",
            "/goals",
        ],
    },
    "task": {
        "title": "Task Management",
        "examples": [
            "catat task: kerjakan bab 1 APSI deadline kamis",
            "task hari ini apa",
            "tandai task 3 selesai",
            "/tasks",
        ],
    },
    "money": {
        "title": "Money OS",
        "examples": [
            "catat pengeluaran 25000 makan siang",
            "catat pemasukan 500000 freelance",
            "ringkas uang bulan ini",
            "kategori boros bulan ini apa",
            "/money",
        ],
    },
    "workout": {
        "title": "Workout OS",
        "examples": [
            "catat workout push up 3x15, squat 3x20 durasi 30 menit",
            "ringkas workout minggu ini",
            "buat plan workout pemula 3 hari",
            "/workout",
        ],
    },
    "knowledge": {
        "title": "Knowledge OS",
        "examples": [
            "cari di knowledge: apa itu event driven architecture",
            "ingest materi ini ke knowledge",
            "rebuild knowledge index",
        ],
    },
    "obsidian": {
        "title": "Obsidian Vault",
        "examples": [
            "buat daily note",
            "catat di obsidian: LangGraph pakai state machine",
            "cari catatan tentang langchain",
            "baca catatan HEBAT/APSI/materi1",
        ],
    },
    "ai-runtime": {
        "title": "Provider LLM & Coding Agent",
        "examples": [
            "/llm — provider/model chat aktif",
            "/llm list — provider yang disiapkan operator",
            "/llm use flaz deepseek-v4-pro",
            "/agent list — runtime coding lokal",
            "/agent use codex",
            "/code <task> — jalankan task coding (admin)",
        ],
    },
    "research": {
        "title": "Research Tools",
        "examples": [
            "deep research tentang zero knowledge proof",
            "cari sumber belajar smart contract auditing",
            "cari video sequence diagram",
            "buat research brief AI security",
        ],
    },
    "help": {
        "title": "Slash Commands",
        "examples": [
            "/helper           — tampilkan semua kategori",
            "/helper learning  — panduan belajar",
            "/helper hebat     — panduan HEBAT",
            "/helper life      — panduan life OS",
            "/helper money     — panduan uang",
            "/helper workout   — panduan workout",
            "/today            — rencana hari ini",
            "/review           — review harian",
            "/goals            — list goals aktif",
            "/tasks            — task hari ini",
            "/money            — ringkasan keuangan",
            "/workout          — ringkasan workout",
            "/hebat            — digest HEBAT",
            "/hebat-login      — login HEBAT dengan kredensial server",
            "/jadwal           — snapshot jadwal lokal",
            "/nilai            — minta token untuk membaca KHS",
            "/nilai changes    — perubahan dua snapshot nilai terakhir",
            "/cyber-profile    — profil akademik minimal",
            "/status-akademik  — riwayat status semester",
            "/krs status       — mata kuliah dan total SKS aktif",
            "/portalinfo       — status portal lokal",
            "/web-analysis     — status structural cache",
            "/knowledge        — cari di knowledge",
        ],
    },
}

FULL_OVERVIEW = """🤖 *Xninetzy AI — Capability Map*

*1. Xninetzy OS Kernel*
Universal capture, inbox, triage, dan attention queue lintas interface

*2. Learning OS*
Roadmap belajar, materi HEBAT, PDF, video YouTube, workspace Q&A

*3. HEBAT / E-Learning UNAIR*
Login, sync course, cek tugas, download PDF, upload dengan konfirmasi

*4. Life OS*
Goal tracking, daily review, roadmap pribadi

*5. Task Management*
Catat task, lihat task hari ini, centang selesai

*6. Money OS*
Catat pengeluaran/pemasukan, ringkasan bulanan

*7. Workout OS*
Log sesi olahraga, ringkasan, plan latihan

*8. Knowledge OS*
Simpan & cari knowledge dari PDF/note/web secara semantik

*9. Research*
Web search, YouTube search, deep research brief

*10. Obsidian Vault*
Daily note, learning note, project note, append, search

*11. AI Runtime*
Pilih provider/model chat dan jalankan Codex, Claude Code, OpenCode, Gemini, Qwen, atau Kilo di host (admin)

*12. Slash Commands*
/capture, /inbox, /triage, /today, /review, /goals, /tasks, /hebat-login, /llm, /agent, /code

Ketik: */helper <kategori>* untuk detail
Contoh: /helper learning"""


def get_help(topic: str | None = None) -> str:
    if not topic or topic == "help":
        return FULL_OVERVIEW

    cat = CATEGORIES.get(topic.lower())
    if not cat:
        available = ", ".join(CATEGORIES.keys())
        return f"Kategori tidak dikenal: '{topic}'\nYang tersedia: {available}"

    title = cat["title"]
    examples = cat["examples"]
    lines = [f"📌 *{title}*\n"]
    lines.extend(f"• {ex}" for ex in examples)
    return "\n".join(lines)
