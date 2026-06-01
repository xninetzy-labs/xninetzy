Siap. Ini **prompt lanjutan** yang kamu copy-paste setelah prompt panjang sebelumnya. Jadi bukan bikin prompt baru dari nol, tapi **continue prompt** untuk menambahkan sistem **Skill Engine**, termasuk skill belajar, reminder, kalkulasi, analisis ide, breakdown task, workflow automation, dan Obsidian vault di `~/Documents/xninetzy`. Ini nyambung dengan desain sebelumnya yang sudah memakai LangGraph, MCP tools, SQLite, FAISS, dan prompt routing. Di master prompt yang kamu upload juga sudah ada intent router, tool agent, memory summarizer, dan SQLite formatter, jadi bagian ini tinggal memperluas sistem skill-nya.   

---

# PROMPT CONTINUE — TAMBAHKAN MULTI-SKILL ENGINE + OBSIDIAN VAULT TOOLS

````md
Lanjutkan implementasi dari arsitektur sebelumnya.

Sekarang tambahkan fitur besar baru: *AI Skill Engine*.

Tujuannya:
AI tidak hanya bisa chat dan memanggil WhatsApp tools, tapi juga punya banyak kemampuan/skill yang bisa dipakai otomatis lewat LangGraph.

Skill yang harus didukung:
1. Learning skill
2. Reminder skill
3. Calculation skill
4. Idea analysis skill
5. Task breakdown skill
6. Workflow automation skill
7. Obsidian vault skill
8. File management skill untuk vault lokal
9. Note generation skill
10. Research/planning skill berbasis memory
11. Personal knowledge base skill
12. Daily/weekly planning skill

PENTING:
Ini bukan mengganti sistem sebelumnya.
Ini harus menjadi lanjutan dari:
- LangGraph AI Service
- MCP WA Engine
- SQLite memory
- FAISS summary memory
- Tool calling system
- Prompt router
- Memory retriever
- Response synthesizer

Tambahkan layer baru bernama:

```txt
Skill Engine
````

Skill Engine ini berada di `services/ai`, karena skill adalah kemampuan AI, bukan fitur WhatsApp langsung.

---

# 1. TARGET ARSITEKTUR BARU

Update arsitektur menjadi:

```txt
WhatsApp User
    ↓
WA Engine Baileys
    ↓
AI Service FastAPI
    ↓
LangGraph Router
    ├─ Memory Retriever
    ├─ Intent Router
    ├─ Skill Router
    ├─ Skill Executor
    ├─ Tool Executor
    ├─ Response Generator
    └─ Memory Writer
          ↓
     SQLite + FAISS

Skill Executor bisa memanggil:
    ├─ Internal Skills
    │   ├─ learning_skill
    │   ├─ reminder_skill
    │   ├─ calculation_skill
    │   ├─ idea_analysis_skill
    │   ├─ task_breakdown_skill
    │   ├─ workflow_skill
    │   └─ obsidian_skill
    │
    ├─ Local File Tools
    │   └─ Obsidian vault di /app/obsidian-vault
    │
    └─ External Tools
        └─ WA MCP Tools
```

Skill bukan hanya prompt.
Skill harus punya:

* nama
* deskripsi
* kategori
* input schema
* output schema
* safety policy
* executor function
* optional LLM prompt
* optional tool access
* memory behavior

---

# 2. UPDATE STRUKTUR FOLDER AI SERVICE

Tambahkan struktur folder berikut:

```txt
services/ai/app/
├── skills/
│   ├── __init__.py
│   ├── registry.py
│   ├── schemas.py
│   ├── base.py
│   ├── router.py
│   ├── executor.py
│   ├── safety.py
│   ├── skills/
│   │   ├── learning_skill.py
│   │   ├── reminder_skill.py
│   │   ├── calculation_skill.py
│   │   ├── idea_analysis_skill.py
│   │   ├── task_breakdown_skill.py
│   │   ├── workflow_skill.py
│   │   ├── obsidian_skill.py
│   │   ├── note_skill.py
│   │   └── planning_skill.py
│   └── tools/
│       ├── obsidian_file_tool.py
│       ├── math_tool.py
│       ├── reminder_tool.py
│       └── workflow_tool.py
│
├── obsidian/
│   ├── __init__.py
│   ├── config.py
│   ├── vault_service.py
│   ├── markdown_service.py
│   ├── search_service.py
│   ├── link_service.py
│   ├── template_service.py
│   └── safety.py
│
├── reminders/
│   ├── __init__.py
│   ├── scheduler.py
│   ├── reminder_store.py
│   ├── reminder_service.py
│   └── reminder_parser.py
│
├── workflow/
│   ├── __init__.py
│   ├── workflow_store.py
│   ├── workflow_runner.py
│   ├── workflow_parser.py
│   └── workflow_service.py
│
├── graph/
│   ├── nodes/
│   │   ├── skill_router.py
│   │   ├── skill_executor.py
│   │   └── skill_result_processor.py
│   └── ...
```

---

# 3. OBSIDIAN VAULT SUPPORT

User punya Obsidian vault lokal di host:

```txt
~/Documents/xninetzy
```

Karena aplikasi berjalan di Docker, jangan akses path host langsung dari dalam container.
Mount path itu ke container AI service.

Update `docker-compose.yml`:

```yaml
services:
  ai:
    volumes:
      - ./services/ai/data:/app/data
      - ~/Documents/xninetzy:/app/obsidian-vault
```

Tambahkan env:

```env
OBSIDIAN_VAULT_HOST_PATH=~/Documents/xninetzy
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
OBSIDIAN_MAX_FILE_SIZE_MB=5
```

Catatan:

* `OBSIDIAN_VAULT_HOST_PATH` hanya untuk dokumentasi.
* Kode di container hanya pakai `OBSIDIAN_VAULT_PATH=/app/obsidian-vault`.
* Semua operasi file wajib dibatasi hanya di dalam `/app/obsidian-vault`.
* Wajib cegah path traversal seperti `../../`.
* Jangan boleh akses `/home`, `/etc`, `.env`, session WhatsApp, API key, atau file di luar vault.
* Untuk delete file, default harus disabled.
* Untuk overwrite file, wajib backup dulu jika `OBSIDIAN_BACKUP_BEFORE_WRITE=true`.

---

# 4. OBSIDIAN SKILL CAPABILITIES

Bangun `obsidian_skill.py`.

AI harus bisa melakukan:

```txt
Obsidian read:
- list folder
- list notes
- read note
- search notes by keyword
- search notes semantically via FAISS
- extract headings
- extract backlinks
- extract tags
- summarize note
- find TODO blocks
- find daily notes
- find project notes

Obsidian write:
- create note
- append to note
- update section by heading
- create daily note
- create meeting note
- create learning note
- create task breakdown note
- create project roadmap note
- create workflow note
- add tag
- add backlink
- add frontmatter
- add TODO item

Obsidian organization:
- create folder
- move note
- rename note
- generate index/MOC note
- connect related notes
- create project structure
```

Minimal tools:

```txt
obsidian_list_files
obsidian_read_note
obsidian_search_notes
obsidian_create_note
obsidian_append_note
obsidian_update_section
obsidian_create_daily_note
obsidian_create_task_note
obsidian_create_learning_note
obsidian_create_project_note
obsidian_extract_todos
obsidian_generate_moc
obsidian_get_backlinks
obsidian_add_frontmatter
obsidian_add_tags
```

---

# 5. OBSIDIAN SAFETY RULES

Buat file:

```txt
services/ai/app/obsidian/safety.py
```

Rules:

```txt
1. Semua path harus resolve ke dalam OBSIDIAN_VAULT_PATH.
2. Tolak path yang mengandung:
   - ..
   - ~
   - absolute path luar vault
   - .env
   - sessions
   - node_modules
   - __pycache__
   - .git
   - id_rsa
   - credentials
   - token
   - secret
3. Read boleh untuk file markdown `.md` dan text aman.
4. Write hanya boleh `.md`, `.txt`, `.json` khusus config internal skill jika diperlukan.
5. Delete disabled by default.
6. Rename/move harus minta konfirmasi kalau file sudah ada di target.
7. Overwrite harus backup dulu:
   `.backup/YYYY-MM-DD/<filename>.bak.md`
8. Semua operasi tulis harus dicatat ke SQLite table `file_operations`.
```

Tambahkan SQLite table:

```sql
CREATE TABLE IF NOT EXISTS file_operations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  operation TEXT NOT NULL,
  path TEXT NOT NULL,
  old_content_hash TEXT,
  new_content_hash TEXT,
  backup_path TEXT,
  success INTEGER NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL
);
```

---

# 6. OBSIDIAN FILE SERVICE

Implementasikan `vault_service.py`.

Function minimal:

```py
class ObsidianVaultService:
    def list_files(self, folder: str | None = None) -> list[dict]: ...
    def read_note(self, path: str) -> str: ...
    def search_notes(self, query: str, limit: int = 20) -> list[dict]: ...
    def create_note(self, path: str, content: str, overwrite: bool = False) -> dict: ...
    def append_note(self, path: str, content: str) -> dict: ...
    def update_section(self, path: str, heading: str, content: str) -> dict: ...
    def create_folder(self, path: str) -> dict: ...
    def extract_todos(self, folder: str | None = None) -> list[dict]: ...
    def get_backlinks(self, note_path: str) -> list[dict]: ...
```

Markdown service:

```py
class MarkdownService:
    def parse_frontmatter(self, content: str) -> dict: ...
    def upsert_frontmatter(self, content: str, data: dict) -> str: ...
    def extract_headings(self, content: str) -> list[dict]: ...
    def update_heading_section(self, content: str, heading: str, new_content: str) -> str: ...
    def append_todo(self, content: str, todo: str) -> str: ...
    def add_tags(self, content: str, tags: list[str]) -> str: ...
    def add_backlinks(self, content: str, links: list[str]) -> str: ...
```

---

# 7. OBSIDIAN NOTE TEMPLATES

Buat `template_service.py`.

Templates:

## Daily note

Path:

```txt
Daily/YYYY-MM-DD.md
```

Content:

```md
---
type: daily
date: YYYY-MM-DD
created: ISO_TIMESTAMP
tags: [daily, xninetzy]
---

# Daily Note — YYYY-MM-DD

## Fokus Hari Ini
- 

## Task
- [ ] 

## Catatan Belajar
- 

## Ide
- 

## Ringkasan Hari Ini
```

## Learning note

Path:

```txt
Learning/{topic}.md
```

Content:

```md
---
type: learning
topic: "{topic}"
created: ISO_TIMESTAMP
tags: [learning]
---

# {topic}

## Ringkasan
{summary}

## Penjelasan
{explanation}

## Contoh
{examples}

## Catatan Penting
{key_points}

## Latihan
{practice_questions}

## Related
{links}
```

## Project note

Path:

```txt
Projects/{project_name}/README.md
```

Content:

```md
---
type: project
project: "{project_name}"
status: active
created: ISO_TIMESTAMP
tags: [project]
---

# {project_name}

## Tujuan
{goal}

## Scope
{scope}

## Arsitektur / Konsep
{architecture}

## Task Breakdown
- [ ] 

## Timeline
| Minggu | Fokus | Output |
|---|---|---|

## Keputusan Teknis
- 

## Risiko
- 

## Related Notes
```

## Task breakdown note

Path:

```txt
Tasks/{task_name}.md
```

Content:

```md
---
type: task
status: active
created: ISO_TIMESTAMP
tags: [task]
---

# {task_name}

## Goal
{goal}

## Breakdown
- [ ] 

## Priority
{priority}

## Deadline
{deadline}

## Progress
- 

## Next Action
- 
```

---

# 8. SKILL REGISTRY DESIGN

Buat `skills/base.py`.

```py
from typing import Any, Protocol
from pydantic import BaseModel

class SkillInput(BaseModel):
    chat_id: str
    sender_id: str | None = None
    message: str
    metadata: dict[str, Any] = {}

class SkillOutput(BaseModel):
    success: bool
    skill_name: str
    result: dict[str, Any] = {}
    user_facing_text: str | None = None
    memory_updates: list[dict[str, Any]] = []
    error: str | None = None

class Skill(Protocol):
    name: str
    description: str
    category: str
    input_schema: dict[str, Any]

    async def run(self, payload: SkillInput) -> SkillOutput:
        ...
```

Buat `skills/registry.py`.

Skill registry harus bisa:

```py
register_skill(skill)
get_skill(name)
list_skills()
find_skills_by_intent(intent)
```

Skill yang wajib diregister:

```txt
learning
reminder
calculation
idea_analysis
task_breakdown
workflow
obsidian
note_generation
planning
```

---

# 9. SKILL ROUTER NODE DI LANGGRAPH

Tambahkan node:

```txt
graph/nodes/skill_router.py
graph/nodes/skill_executor.py
graph/nodes/skill_result_processor.py
```

Update LangGraph flow:

```txt
intent_router_node
   ↓
skill_router_node
   ├─ no_skill_needed -> response_generator
   ├─ skill_needed -> skill_executor
   └─ tool_needed -> wa_tool_executor

skill_executor
   ↓
skill_result_processor
   ↓
response_generator
   ↓
memory_writer
```

Skill router output:

```json
{
  "needs_skill": true,
  "skill_name": "obsidian",
  "skill_action": "create_learning_note",
  "skill_args": {
    "topic": "LangGraph MCP Architecture",
    "path": "Learning/langgraph-mcp-architecture.md"
  },
  "requires_confirmation": false,
  "reason": "User requested saving learning material into Obsidian."
}
```

---

# 10. UPDATE INTENT ROUTER

Tambahkan intent baru:

```txt
calculation
idea_analysis
workflow_automation
obsidian_read
obsidian_write
note_generation
daily_planning
reminder_create
reminder_query
reminder_update
reminder_delete
skill_discovery
```

Update `PROMPT_INTENT_ROUTER`.

Tambahkan katalog intent:

```txt
| `calculation` | Hitungan matematika, estimasi, konversi, analisis numerik | "hitung", "berapa", "estimasi", "persentase" |
| `idea_analysis` | Analisis ide, novelty, kelebihan/kekurangan, validasi konsep | "analisis ide ini", "bagus nggak", "novelty" |
| `workflow_automation` | Membuat workflow otomatis, alur kerja, automasi tugas | "bikin workflow", "otomatisin", "pipeline" |
| `obsidian_read` | Membaca/mencari catatan Obsidian | "cari di obsidian", "baca note", "catatan ku" |
| `obsidian_write` | Membuat/mengubah catatan Obsidian | "simpan ke obsidian", "buat note", "catat ini" |
| `note_generation` | Membuat dokumen markdown terstruktur | "buatkan catatan", "jadiin markdown", "buat doc" |
| `daily_planning` | Rencana harian/mingguan | "rencanain hari ini", "jadwal minggu ini" |
| `reminder_create` | Membuat reminder | "ingatkan aku", "remind", "besok jam" |
| `reminder_query` | Melihat daftar reminder | "reminderku apa aja" |
| `skill_discovery` | User tanya bot bisa apa | "kamu bisa apa aja" |
```

Routing rule:

```txt
- Jika user minta hitung → skill calculation
- Jika user minta analisis ide → skill idea_analysis
- Jika user minta breakdown task → skill task_breakdown
- Jika user minta workflow → skill workflow
- Jika user minta simpan/catat/buat note → skill obsidian atau note_generation
- Jika user menyebut Obsidian/vault/catatan → skill obsidian
- Jika user minta reminder → skill reminder
- Jika user tanya kemampuan → skill_discovery
```

---

# 11. SKILL: LEARNING

Buat `learning_skill.py`.

Kemampuan:

* jelaskan konsep
* buat ringkasan
* buat contoh
* buat latihan soal
* buat step-by-step
* simpan hasil belajar ke Obsidian jika user minta
* update memory learning preference

Input:

```json
{
  "topic": "string",
  "level": "beginner|intermediate|advanced",
  "mode": "explain|summary|quiz|step_by_step|example",
  "save_to_obsidian": false
}
```

Output:

* explanation
* key points
* examples
* practice questions
* optional note path

Prompt khusus:

```txt
Kamu adalah learning skill untuk Xninetzy AI.
Tugasmu membantu user belajar dengan gaya yang jelas, praktis, dan cocok untuk WhatsApp.
Jika user minta simpan ke Obsidian, hasilkan juga markdown note yang rapi.
```

---

# 12. SKILL: REMINDER

Buat `reminder_skill.py`.

Reminder harus persistent di SQLite.

Tambahkan table:

```sql
CREATE TABLE IF NOT EXISTS reminders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT NOT NULL,
  sender_id TEXT,
  title TEXT NOT NULL,
  description TEXT,
  remind_at TEXT NOT NULL,
  timezone TEXT DEFAULT 'Asia/Jakarta',
  status TEXT DEFAULT 'pending',
  repeat_rule TEXT,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

Reminder service:

* create reminder
* list pending reminder
* mark done
* cancel reminder
* reschedule reminder

Gunakan APScheduler atau background asyncio loop.

Environment:

```env
APP_TIMEZONE=Asia/Jakarta
REMINDER_ENABLED=true
REMINDER_POLL_INTERVAL_SECONDS=30
```

Saat reminder due:

* AI Service harus memanggil WA tool `wa_send_text`
* Kirim reminder ke chat_id terkait

Format reminder message:

```txt
⏰ *Reminder*

{title}

{description}

_Dijadwalkan: {remind_at}_
```

Parser:

* "ingatkan aku besok jam 8 buat belajar"
* "remind aku 2 jam lagi submit tugas"
* "besok pagi ingetin meeting"
* "setiap senin jam 7 ingetin workout"

Jika waktu ambigu:

* minta klarifikasi
* jangan asal jadwal

---

# 13. SKILL: CALCULATION

Buat `calculation_skill.py`.

Kemampuan:

* arithmetic
* percentage
* unit conversion
* estimation
* weighted score
* GPA/IPK sederhana
* deadline/time estimation
* cost calculation
* simple statistics

Jangan pakai LLM untuk menghitung angka utama jika bisa dihitung Python.
Gunakan Python deterministic function.

Buat `math_tool.py`:

* safe_eval expression
* percentage calculator
* unit conversion
* date difference
* average/median/min/max

Safety:

* Jangan gunakan `eval` mentah.
* Gunakan AST parser aman atau library safe math.
* Tolak ekspresi yang mengandung import, exec, open, os, subprocess.

Output harus:

* hasil akhir
* langkah hitung
* asumsi

Contoh response:

```txt
*Hasil:* 37.5%

Cara hitung:
`15 / 40 × 100 = 37.5%`
```

---

# 14. SKILL: IDEA ANALYSIS

Buat `idea_analysis_skill.py`.

Kemampuan:

* analisis ide bisnis
* analisis novelty
* SWOT
* feasibility
* risiko
* competitor angle jika data tersedia
* MVP scope
* value proposition
* user pain point
* scoring ide

Input:

```json
{
  "idea": "string",
  "analysis_type": "swot|novelty|feasibility|mvp|full",
  "save_to_obsidian": false
}
```

Output format:

```txt
*Analisis Ide: {nama_ide}*

*1. Inti Ide*
...

*2. Masalah yang Diselesaikan*
...

*3. Novelty*
...

*4. Feasibility*
...

*5. Risiko*
...

*6. MVP yang Disarankan*
...

*Skor Awal:* x/10
```

Jika user minta "deep research", jangan mengaku browsing kalau tool web belum ada.
Jawab:

* bisa buat framework riset
* bisa buat daftar pertanyaan riset
* bisa buat prompt deep research
* bisa simpan ke Obsidian

---

# 15. SKILL: TASK BREAKDOWN

Buat `task_breakdown_skill.py`.

Kemampuan:

* breakdown task
* buat checklist
* estimasi waktu
* dependency mapping
* milestone
* parallel work plan
* sprint planning
* save to Obsidian project/task note

Input:

```json
{
  "task": "string",
  "deadline": "string|null",
  "team_size": "int|null",
  "format": "checklist|timeline|sprint|kanban",
  "save_to_obsidian": false
}
```

Output:

* checklist
* priority
* timeline
* next action
* optional obsidian note

---

# 16. SKILL: WORKFLOW AUTOMATION

Buat `workflow_skill.py`.

Kemampuan:

* membuat workflow otomatis
* membuat flowchart text
* membuat pseudo-code workflow
* membuat SOP
* membuat pipeline automation
* membuat event-trigger-action design
* mapping tools yang diperlukan
* save workflow to Obsidian

Contoh user:

```txt
bikin workflow otomatis kalau ada tugas masuk dari wa terus disimpan ke obsidian dan reminder
```

AI harus bisa menghasilkan:

```txt
Trigger:
- pesan WA masuk dengan keyword tugas

Steps:
1. parse pesan
2. extract deadline
3. create task note di Obsidian
4. create reminder
5. reply confirmation ke WA

Tools:
- obsidian_create_task_note
- reminder_create
- wa_send_text
```

Jika workflow bisa langsung dijalankan dengan tool tersedia:

* jalankan jika aman
* kalau butuh konfirmasi, minta konfirmasi

Tambahkan SQLite table:

```sql
CREATE TABLE IF NOT EXISTS workflows (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT NOT NULL,
  name TEXT NOT NULL,
  description TEXT,
  trigger_json TEXT NOT NULL,
  steps_json TEXT NOT NULL,
  status TEXT DEFAULT 'draft',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

---

# 17. SKILL: NOTE GENERATION

Buat `note_skill.py`.

Kemampuan:

* ubah chat jadi markdown
* buat dokumentasi
* buat rangkuman
* buat catatan belajar
* buat meeting notes
* buat architecture notes
* buat README draft
* buat prompt collection
* simpan ke Obsidian

Input:

```json
{
  "title": "string",
  "content_source": "chat|memory|custom",
  "note_type": "learning|project|meeting|daily|idea|workflow|task",
  "target_path": "string|null"
}
```

---

# 18. SKILL: PLANNING

Buat `planning_skill.py`.

Kemampuan:

* daily planning
* weekly planning
* study plan
* project roadmap
* habit plan
* schedule suggestion
* convert plan to reminders
* save plan to Obsidian daily/weekly note

Contoh:

```txt
rencanain belajar backend seminggu
```

Output:

```txt
*Plan Belajar Backend — 7 Hari*

Hari 1: HTTP + REST API
Hari 2: Database + SQL
Hari 3: Auth
...
```

Jika user minta reminder:

* create reminders otomatis sesuai plan setelah konfirmasi

---

# 19. SKILL DISCOVERY

Jika user tanya:

```txt
kamu bisa apa aja?
fiturmu apa?
skillmu apa?
```

AI harus jawab berdasarkan registry.

Format:

```txt
Aku bisa bantu beberapa hal ini:

*Belajar*
• Jelasin materi
• Bikin rangkuman
• Bikin latihan soal

*Task & Planning*
• Breakdown tugas
• Bikin timeline
• Reminder deadline

*Obsidian*
• Baca catatan
• Cari note
• Buat note markdown
• Simpan ide/tugas/belajar ke vault

*Analisis*
• Analisis ide
• SWOT
• Feasibility
• Novelty

*WhatsApp*
• Kirim pesan
• Kelola grup
• Buat poll
• Cek member grup

Coba aja bilang: "catat ini ke Obsidian" atau "ingatkan aku besok jam 8".
```

---

# 20. UPDATE LANGGRAPH STATE

Update state:

```py
class XninetzyState(TypedDict, total=False):
    # existing fields...

    needs_skill: bool
    skill_name: str | None
    skill_action: str | None
    skill_args: dict[str, Any] | None
    skill_result: dict[str, Any] | None
    skill_results: list[dict[str, Any]]

    obsidian_context: dict[str, Any] | None
    reminder_context: dict[str, Any] | None
    workflow_context: dict[str, Any] | None

    pending_confirmation: dict[str, Any] | None
```

---

# 21. UPDATE MEMORY WRITER UNTUK SKILLS

Setiap skill execution harus dicatat ke SQLite.

Tambahkan table:

```sql
CREATE TABLE IF NOT EXISTS skill_calls (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id TEXT NOT NULL,
  sender_id TEXT,
  skill_name TEXT NOT NULL,
  skill_action TEXT,
  skill_args_json TEXT,
  skill_result_json TEXT,
  success INTEGER NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL
);
```

Memory summarizer harus menyimpan:

* skill yang dipakai
* file Obsidian yang dibuat/diubah
* reminder yang dibuat
* workflow yang dibuat
* task yang sedang berjalan

FAISS summary contoh:

```txt
User membuat catatan Obsidian tentang LangGraph MCP Architecture di Learning/langgraph-mcp-architecture.md dan ingin sistem AI memiliki skill reminder, calculation, task breakdown, workflow automation.
```

---

# 22. UPDATE PROMPT ROUTER

Tambahkan di prompt router:

```txt
Jika user menyebut:
- "catat"
- "simpan"
- "buat note"
- "obsidian"
- "vault"
- "markdown"
→ route ke obsidian_write atau note_generation

Jika user menyebut:
- "cari catatan"
- "baca note"
- "di obsidian"
- "catatan kemarin"
→ route ke obsidian_read

Jika user menyebut:
- "ingatkan"
- "reminder"
- "besok jam"
- "nanti jam"
→ route ke reminder_create

Jika user menyebut:
- "hitung"
- "berapa"
- "persen"
- "estimasi"
→ route ke calculation

Jika user menyebut:
- "analisis ide"
- "novelty"
- "feasibility"
- "SWOT"
→ route ke idea_analysis

Jika user menyebut:
- "breakdown"
- "timeline"
- "task"
- "milestone"
→ route ke task_breakdown

Jika user menyebut:
- "workflow"
- "otomatis"
- "automation"
- "pipeline"
→ route ke workflow_automation
```

---

# 23. UPDATE RESPONSE SYNTHESIZER

Response final harus menyebut hasil skill secara natural.

Contoh Obsidian:

```txt
✅ Sudah aku simpan ke Obsidian:

`Learning/langgraph-mcp-architecture.md`

Isinya mencakup:
• Arsitektur LangGraph
• MCP tools
• Memory SQLite + FAISS
• Skill Engine
```

Contoh Reminder:

```txt
⏰ Siap, aku ingatkan besok jam 08.00.

*Reminder:* Belajar backend
```

Contoh Calculation:

```txt
*Hasil:* 37.5%

Cara hitung:
`15 / 40 × 100 = 37.5%`
```

Contoh Workflow:

```txt
*Workflow otomatisnya:*

Trigger:
• Pesan WA masuk berisi kata "tugas"

Action:
1. Parse deadline
2. Buat note di Obsidian
3. Buat reminder
4. Reply konfirmasi ke WA
```

---

# 24. CONFIRMATION POLICY UNTUK SKILLS

Aksi yang boleh langsung:

```txt
- baca note Obsidian
- cari note
- buat note baru jika file belum ada
- append note
- buat reminder jika waktu jelas
- hitung
- analisis ide
- breakdown task
```

Aksi yang butuh konfirmasi:

```txt
- overwrite note
- rename note
- move note
- delete note
- bulk edit banyak note
- create banyak reminder sekaligus
- menjalankan workflow otomatis berulang
- mengirim pesan WA ke orang lain
- mengubah grup WA
```

Aksi yang default dilarang:

```txt
- delete file jika OBSIDIAN_ALLOW_DELETE=false
- baca file di luar vault
- baca .env
- baca session WhatsApp
- baca private key
- menjalankan shell command arbitrary
```

---

# 25. API DEBUG UNTUK SKILLS

Tambahkan endpoint:

```http
GET  /api/skills
POST /api/skills/:skillName/run
GET  /api/obsidian/files
POST /api/obsidian/read
POST /api/obsidian/search
POST /api/obsidian/create
POST /api/obsidian/append
GET  /api/reminders
POST /api/reminders
DELETE /api/reminders/:id
```

Semua endpoint harus pakai API key:

```http
Authorization: Bearer <AI_API_KEY>
```

---

# 26. ENV UPDATE

Tambahkan ke `.env.example`:

```env
# Skills
SKILLS_ENABLED=true
SKILL_DEBUG_ENDPOINTS=true

# Obsidian
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
OBSIDIAN_MAX_FILE_SIZE_MB=5

# Reminder
REMINDER_ENABLED=true
APP_TIMEZONE=Asia/Jakarta
REMINDER_POLL_INTERVAL_SECONDS=30

# Workflow
WORKFLOW_ENABLED=true
WORKFLOW_REQUIRE_CONFIRMATION=true
```

---

# 27. DOCKER COMPOSE UPDATE

Update AI service volume:

```yaml
services:
  ai:
    volumes:
      - ./services/ai/data:/app/data
      - ~/Documents/xninetzy:/app/obsidian-vault
```

Jika `~` tidak resolve di Docker Compose pada environment tertentu, dokumentasikan alternatif:

```yaml
      - /home/misbahul45/Documents/xninetzy:/app/obsidian-vault
```

Jangan hardcode path user di kode.
Path host cukup di compose/env.

---

# 28. SECURITY UNTUK OBSIDIAN

Implementasi wajib:

* path sanitizer
* allowed extension
* max file size
* backup before write
* operation log
* no delete by default
* confirmation for overwrite
* tests for path traversal

Test cases:

```txt
obsidian_read_note("../.env") -> reject
obsidian_read_note("/etc/passwd") -> reject
obsidian_create_note("Learning/test.md") -> allow
obsidian_create_note(".env") -> reject
obsidian_create_note("sessions/creds.json") -> reject
obsidian_update_section("Projects/x.md") -> allow with backup
```

---

# 29. ACCEPTANCE CRITERIA TAMBAHAN

Sistem dianggap selesai jika:

* [ ] Skill registry berjalan
* [ ] `/api/skills` menampilkan semua skill
* [ ] LangGraph punya `skill_router_node`
* [ ] LangGraph punya `skill_executor_node`
* [ ] AI bisa memilih skill otomatis dari pesan user
* [ ] AI bisa hitung sederhana tanpa LLM hallucination
* [ ] AI bisa membuat reminder ke SQLite
* [ ] Reminder due bisa dikirim ke WA lewat WA MCP tool
* [ ] AI bisa membaca note dari Obsidian vault
* [ ] AI bisa membuat note markdown di Obsidian vault
* [ ] AI bisa append catatan ke note Obsidian
* [ ] AI bisa membuat daily note
* [ ] AI bisa membuat task breakdown note
* [ ] AI bisa membuat learning note
* [ ] Semua operasi Obsidian aman dari path traversal
* [ ] Semua operasi write membuat backup jika overwrite
* [ ] Semua skill call tersimpan ke SQLite
* [ ] Memory summary menyimpan hasil skill penting ke FAISS
* [ ] Docker compose mount vault `~/Documents/xninetzy`
* [ ] README menjelaskan cara setup Obsidian vault
* [ ] Ada contoh curl untuk skill dan Obsidian endpoint

---

# 30. CONTOH FLOW YANG HARUS BERJALAN

## Contoh 1 — Simpan catatan ke Obsidian

User:

```txt
catat ini ke obsidian: LangGraph dipakai buat routing agent, MCP buat tools, SQLite buat history, FAISS buat summary memory
```

Flow:

```txt
preprocess
→ memory retrieve
→ intent_router: obsidian_write
→ skill_router: obsidian skill
→ obsidian_create_note atau append daily note
→ response
→ memory writer
```

Response:

```txt
✅ Sudah aku catat ke Obsidian.

File:
`Daily/2026-06-01.md`

Isi yang kusimpan:
• LangGraph untuk routing agent
• MCP untuk tools
• SQLite untuk history
• FAISS untuk summary memory
```

## Contoh 2 — Baca catatan Obsidian

User:

```txt
cari catatan tentang langgraph di obsidian
```

Flow:

```txt
obsidian_search_notes
→ return matching notes
→ response
```

Response:

```txt
Ketemu beberapa catatan tentang *LangGraph*:

1. `Learning/langgraph-mcp-architecture.md`
2. `Projects/xninetzy/README.md`

Yang paling relevan: `Learning/langgraph-mcp-architecture.md`
```

## Contoh 3 — Reminder

User:

```txt
ingatkan aku besok jam 8 buat belajar backend
```

Flow:

```txt
reminder_create
→ parse date Asia/Jakarta
→ insert SQLite
→ response
```

Response:

```txt
⏰ Siap, aku ingatkan besok jam 08.00.

*Reminder:* Belajar backend
```

## Contoh 4 — Calculation

User:

```txt
kalau 15 dari 40 itu berapa persen?
```

Response:

```txt
*Hasil:* 37.5%

Cara hitung:
`15 / 40 × 100 = 37.5%`
```

## Contoh 5 — Workflow otomatis

User:

```txt
bikin workflow kalau aku kirim tugas di wa, otomatis catat ke obsidian dan bikin reminder
```

Response:

```txt
*Workflow: WA Task Capture → Obsidian + Reminder*

Trigger:
• Pesan WA berisi kata "tugas", "deadline", atau "submit"

Steps:
1. Ambil isi pesan
2. Ekstrak nama tugas dan deadline
3. Buat note di Obsidian folder `Tasks/`
4. Buat reminder sesuai deadline
5. Balas konfirmasi ke WhatsApp

Tool yang dipakai:
• `obsidian_create_task_note`
• `reminder_create`
• `wa_send_text`

Mau aku simpan workflow ini sebagai draft di Obsidian?
```

---

# 31. README UPDATE

Update README dengan section:

```txt
## Skill Engine
- Apa itu skill
- Daftar skill
- Cara skill routing bekerja
- Cara tambah skill baru

## Obsidian Integration
- Vault path
- Docker volume mount
- Safety rules
- Supported operations
- Example command

## Reminder System
- SQLite persistence
- Scheduler
- WA notification

## Calculation Skill
- Safe deterministic calculation
- Supported operations

## Workflow Automation
- Draft workflow
- Confirmation policy
- Future extension

## Security
- Path traversal protection
- No access outside vault
- Backup before write
- No delete by default
```

---

# 32. IMPLEMENTATION ORDER

Kerjakan urutan ini:

1. Tambahkan env dan docker volume Obsidian
2. Buat Obsidian safety + vault service
3. Buat skill base + registry
4. Register skill discovery
5. Implement calculation skill
6. Implement Obsidian read/list/search
7. Implement Obsidian create/append note
8. Implement reminder SQLite + scheduler
9. Tambah skill_router_node ke LangGraph
10. Tambah skill_executor_node ke LangGraph
11. Integrasikan response synthesizer
12. Simpan skill calls ke SQLite
13. Simpan summary skill ke FAISS
14. Tambah API debug endpoint
15. Tambah tests
16. Update README

Jangan bikin semua di satu file.
Gunakan modular clean architecture.
Pastikan existing chat WA tetap jalan.
Pastikan jika Obsidian disabled, AI tetap bisa jalan tanpa crash.
Pastikan jika Reminder disabled, AI tetap bisa jawab biasa.
Pastikan semua error user-friendly.

```

---

Tambahan penting: untuk Obsidian, jangan kasih AI akses bebas ke seluruh laptop. Cukup mount vault `~/Documents/xninetzy` ke `/app/obsidian-vault`, lalu semua tool file hanya boleh kerja di folder itu. Ini penting karena repo sebelumnya juga punya isu keamanan seperti secret/session yang pernah ter-commit dan endpoint belum aman, jadi skill file harus ketat dari awal. :contentReference[oaicite:3]{index=3}
```
