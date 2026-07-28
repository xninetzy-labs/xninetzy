# Xninetzy AI

**WhatsApp-first Personal Learning OS + Life OS Assistant.**

Xninetzy AI adalah asisten WhatsApp berbasis AI untuk membantu belajar, riset, pengelolaan tugas kuliah HEBAT/Moodle UNAIR, catatan Obsidian, knowledge base, goal, task, reminder, keuangan, workout, habit, dan review harian.

Bot menerima pesan WhatsApp, menentukan apakah pesan cukup dijawab langsung atau perlu memakai tool, mengeksekusi aksi yang relevan, lalu membalas dalam format WhatsApp.

---

## Arsitektur

Repo ini adalah monorepo dengan dua service utama dan satu terminal client:

```txt
services/
├── ai/          FastAPI + LangGraph + LangChain multi-provider
└── wa-enggine/  Node.js + TypeScript + Baileys
apps/
└── cli/         Ink + React terminal chat client
```

Alur pesan:

```txt
User WhatsApp
   │
   ▼
wa-enggine (Baileys socket)
   │
   │  private: diproses langsung
   │  group: diproses jika mention / prefix / reply ke bot
   ▼
POST /api/chat
   │
   ▼
services/ai
   │
   ├─ slash command → command_router → tool langsung
   └─ pesan biasa   → LangGraph → orchestrator → agent/direct/clarify → format
        │
        └─ jika perlu aksi WhatsApp → POST /mcp/call ke wa-enggine
```

`services/ai` adalah otak agent, prompt, routing, tool registry, database, memory, research, Obsidian, HEBAT, media, dan HITL approval.

`services/wa-enggine` adalah koneksi WhatsApp. Service ini memegang socket Baileys, menerima pesan, mengirim reply, dan menyediakan MCP-style HTTP tool server agar AI bisa menjalankan aksi WhatsApp.

`apps/cli` adalah client terminal alternatif yang memanggil endpoint `/api/chat`
yang sama dengan WhatsApp, sehingga provider, memory, routing, dan tools tetap satu sumber.

---

## Komponen Utama

### AI Service

Lokasi: `services/ai`

- Entry point FastAPI: `app/main.py`
- Chat API: `app/api/routes/chat.py`
- LangGraph flow: `app/agent/graph.py`
- Prompt utama: `app/agent/prompts.py`
- Slash command router: `app/ecosystem/command_router.py`
- Tool registry: `app/tools/registry.py`
- SQLite setup: `app/db/sqlite.py`
- Migrasi tambahan: `app/db/migrations.py`
- Config env: `app/core/config.py`

### WhatsApp Engine

Lokasi: `services/wa-enggine`

- Entry point: `src/app.ts`
- Listener pesan: `src/whatsapp/message-listener.ts`
- Trigger group/private: `src/whatsapp/trigger.ts`
- Payload ke AI: `src/ai/ai-payload.ts`
- Client AI: `src/ai/ai-client.ts`
- MCP server: `src/mcp/server.ts`
- MCP tool registry: `src/mcp/tool-registry.ts`

---

## Fitur

| Area | Fitur |
|---|---|
| Learning OS | Roadmap belajar, rencana belajar harian, review mingguan, resource attachment |
| Research | Search ringan, deep research admin-only, sub-planning, research brief, YouTube learning path |
| HEBAT / Moodle | Login, sync course, sync tugas, digest deadline, download materi PDF, upload tugas dengan konfirmasi |
| Knowledge / RAG | Ingest teks/file, pencarian semantik FAISS, jawab dari knowledge base |
| Graph RAG | Node/edge topik, sumber, note, roadmap, task, dan context graph |
| Obsidian | Create/read/search/append Markdown note, daily note, backup sebelum overwrite |
| Life OS | Goal, task, reminder, money, workout, habit, daily check-in, daily review |
| Media WhatsApp | Baca dokumen, quoted attachment, OCR gambar, dan OCR PDF scan |
| Memory | Memory semantik user, pencarian memory, forget/update memory |
| Rules & Style | User rules lewat `/rule`, gaya jawaban lewat `/style` |
| HITL | Approval untuk aksi berdampak besar |
| Lightning | Feedback dan proposal perbaikan agent |
| WA MCP | Kirim pesan, pin, group tools, contact tools, media download |

---

## Prasyarat

Cara termudah adalah Docker.

Untuk Docker:

- Docker
- Docker Compose
- Flaz API key
- Akun WhatsApp untuk login Baileys

Untuk local development tanpa Docker:

- Python 3.11+
- `uv`
- Node.js 20+
- Yarn 1.x
- Flaz API key
- Playwright Chromium untuk fitur HEBAT browser automation

Opsional:

- `TAVILY_API_KEY` atau `SERPER_API_KEY` untuk web search
- `YOUTUBE_API_KEY` untuk YouTube search
- `HEBAT_USERNAME` dan `HEBAT_PASSWORD` untuk integrasi HEBAT
- Obsidian vault lokal

---

## Setup Environment

Buat file `.env` dari template root:

```bash
cp .env.example .env
```

Masukkan API key tanpa menampilkannya di terminal atau history shell:

```bash
cd services/ai
uv run python scripts/configure_flaz.py
```

Script memakai `getpass`, menyimpan key secara atomik ke root `.env`, dan mengatur permission file ke `600`.

Konfigurasi LLM minimal:

```env
FLAZ_API_KEY=your-secret-key
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
```

Flaz tetap menjadi default melalui `ChatOpenAI`. Registry juga mendukung OpenAI,
Anthropic, OpenRouter, Ollama, dan endpoint OpenAI-compatible kustom secara opt-in.
API key hanya berada di `.env`; pilihan provider/model pengguna disimpan tanpa
credential. Lihat panduan integrasi di `docs/AI_PROVIDERS_CODING_AGENTS_MCP.md`.

Variabel penting:

```env
# LLM
FLAZ_API_KEY=your-secret-key
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_TIMEOUT_SECONDS=120
FLAZ_MAX_RETRIES=2

# AI API
AI_API_KEY=
DATA_DIR=/app/data
SQLITE_PATH=/app/data/xninetzy.sqlite3
AGENT_DEBUG_ENDPOINTS=true

# WhatsApp
WA_LOGIN_MODE=qr
WA_PHONE_NUMBER=628xxxxxxxxxx
WA_COMMAND_PREFIX=!
WA_GROUP_TRIGGER_MODE=mention_or_prefix
AI_BASE_URL=http://127.0.0.1:8000
AI_API_URL=http://127.0.0.1:8000

# MCP
WA_MCP_BASE_URL=http://127.0.0.1:8081
WA_MCP_API_KEY=
MCP_API_KEY=
MCP_SERVER_ENABLED=true
MCP_HOST=0.0.0.0
MCP_PORT=8081

# Admin / Safety
ADMIN_JID=
ADMIN_NAMES=misbahul,misbahul muttaqin
DEEP_RESEARCH_ADMIN_ONLY=true
HITL_ENABLED=true

# Obsidian
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false

# HEBAT
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_NOTIFY_CHAT_ID=
HEBAT_AUTO_LOGIN=false

# Search providers
TAVILY_API_KEY=
SERPER_API_KEY=
YOUTUBE_API_KEY=
```

Untuk local development `wa-enggine`, set:

```env
AI_API_URL=http://localhost:8000
AI_BASE_URL=http://localhost:8000
```

Compose Linux menggunakan host networking, jadi endpoint antarproses tetap localhost:

```env
AI_API_URL=http://127.0.0.1:8000
AI_BASE_URL=http://127.0.0.1:8000
```

---

## Menjalankan dengan Docker

Isi `FLAZ_API_KEY` di `.env`, lalu jalankan:

```bash
cp .env.example .env
# edit .env dan isi FLAZ_API_KEY
docker compose up --build
```

Service yang berjalan:

| Service | URL host | Fungsi |
|---|---|---|
| `ai` | `http://localhost:8000` | FastAPI AI service |
| `wa-enggine` | `http://localhost:8081` | MCP server + WhatsApp worker |

Client CLI interaktif berjalan melalui profile `tools`:

```bash
docker compose --profile tools run --rm cli
```

CLI non-interaktif juga dapat dipakai untuk smoke test:

```bash
printf 'Balas hanya CLI_OK\n' | docker compose --profile tools run --rm -T cli
```

Lihat log WhatsApp:

```bash
docker compose logs -f wa-enggine
```

Lihat log AI:

```bash
docker compose logs -f ai
```

Stop service:

```bash
docker compose down
```

---

## Login WhatsApp

`wa-enggine` mendukung dua mode login Baileys.

### QR Mode

Di `.env`:

```env
WA_LOGIN_MODE=qr
```

Jalankan:

```bash
docker compose up --build wa-enggine ai
```

Lihat QR di log:

```bash
docker compose logs -f wa-enggine
```

### Pairing Code Mode

Di `.env`:

```env
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Jalankan:

```bash
docker compose up --build wa-enggine ai
```

Ambil pairing code dari log, lalu masukkan di:

```txt
WhatsApp > Linked Devices > Link with phone number instead
```

### Reset Session WhatsApp

Gunakan jika QR/pairing bermasalah atau ingin login ulang:

```bash
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```

Compose menggunakan `network_mode: host` pada Linux. Jangan jalankan Docker
`wa-enggine` dan `yarn dev` bersamaan untuk akun WhatsApp yang sama.

---

## Menjalankan Manual

### AI Service

Pastikan `FLAZ_API_KEY` sudah diisi di root `.env`, lalu jalankan:

```bash
cd services/ai
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### WhatsApp Engine

```bash
cd services/wa-enggine
cp .env.example .env
# set AI_API_URL=http://localhost:8000
yarn install
yarn dev
```

Build TypeScript:

```bash
cd services/wa-enggine
yarn build
```

Start hasil build:

```bash
cd services/wa-enggine
yarn start
```

---

## Cara Pakai dari WhatsApp

Private chat selalu diproses.

Group chat hanya diproses jika:

- bot di-mention,
- pesan memakai prefix command, default `!`,
- user membalas pesan bot,
- atau `WA_GROUP_ALLOW_ALL=true`.

Contoh pesan natural:

```txt
buat roadmap belajar Graph RAG 14 hari
cek tugas hebat
deadline terdekat apa
cari video tutorial sequence diagram
catat task: kerjakan bab 1 APSI deadline kamis
catat pengeluaran 25000 makan siang
simpan catatan ini ke Obsidian
ingatkan aku besok jam 8 buat belajar backend
```

Untuk dokumen WhatsApp, kirim file dengan caption seperti:

```txt
ringkas dokumen ini
apa poin penting dari PDF ini?
jadikan dokumen ini knowledge
```

---

## Slash Command

Slash command diproses deterministik oleh `app/ecosystem/command_router.py`.

| Command | Fungsi |
|---|---|
| `/helper` | Panduan kemampuan bot |
| `/helper <topic>` | Panduan kategori tertentu |
| `/today` | Task hari ini |
| `/tasks` | Alias task hari ini |
| `/goals` | Daftar goal |
| `/money` | Ringkasan keuangan |
| `/workout` | Ringkasan workout |
| `/review` | Daily review |
| `/hebat` | Digest akademik HEBAT |
| `/hebat-debug` | Debug login HEBAT aman |
| `/jadwal` | Baca snapshot jadwal lokal terenkripsi |
| `/portalinfo` | Status cache/session portal mahasiswa |
| `/krs-watcher` | Status watcher KRS read/notify-only |
| `/web-analysis [site]` | Status cache struktur web |
| `/web-refresh <site>` | Refresh struktur allowlisted secara read-only |
| `/research <topik>` | Research ringan |
| `/deep-research <topik>` | Deep research mode balanced |
| `/deep-research speed <topik>` | Deep research cepat |
| `/deep-research balanced <topik>` | Deep research seimbang |
| `/deep-research quality <topik>` | Deep research kualitas lebih tinggi |
| `/roadmaps` | Daftar roadmap |
| `/study-today` | Rencana belajar hari ini |
| `/study-review` | Review belajar mingguan |
| `/knowledge` | Knowledge search |
| `/skills` | Daftar skill |
| `/skill <name>` | Detail skill |
| `/approvals` | Daftar approval pending |
| `/approve <id>` | Approve request |
| `/reject <id>` | Reject request |
| `/media-info` | Info media terlampir |
| `/analyze-media` | Ekstrak dokumen atau OCR gambar terlampir/reply |
| `/rule list` | Daftar aturan user |
| `/rule add <aturan>` | Tambah aturan |
| `/rule off <id>` | Disable aturan |
| `/rule on <id>` | Enable aturan |
| `/rule delete <id>` | Hapus aturan |
| `/rule search <query>` | Cari aturan |
| `/style show` | Lihat style profile |
| `/style set <deskripsi>` | Set gaya jawaban |
| `/style reset` | Reset gaya jawaban |
| `/remember <isi>` | Simpan memory |
| `/memory` | Daftar memory |
| `/memory search <query>` | Cari memory |
| `/memory delete <id>` | Hapus memory |
| `/forget-memory <id>` | Alias hapus memory |
| `/feedback <koreksi>` | Kirim feedback untuk Lightning |
| `/agent-proposals` | Daftar proposal agent |
| `/agent-improve` | Review proposal perbaikan |
| `/agent-approve <id>` | Approve proposal agent |
| `/agent-reject <id>` | Reject proposal agent |
| `/agent-errors` | Trace error terbaru |
| `/test-lightning` | Healthcheck Lightning |
| `/test-rules` | Healthcheck rules |
| `/test-memory` | Healthcheck memory |

---

## HTTP API AI Service

Base URL Docker host:

```txt
http://localhost:8000
```

Endpoint utama:

| Method | Endpoint | Fungsi |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/api/chat` | Proses pesan chat |
| `GET` | `/api/reminders` | List reminder |
| `POST` | `/api/reminders` | Buat reminder |
| `DELETE` | `/api/reminders/{id}` | Cancel reminder |
| `GET` | `/api/debug/tools` | List tool debug |
| `GET` | `/api/debug/memory/{chat_id}` | Lihat recent memory chat |
| `DELETE` | `/api/debug/memory/{chat_id}` | Clear memory chat |
| `POST` | `/api/debug/invoke-tool/{tool_name}` | Invoke tool langsung |

Health check:

```bash
curl http://localhost:8000/health
```

Test chat:

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "test-chat",
    "sender_id": "test-user",
    "sender_name": "User",
    "message": "bantu jelasin REST API",
    "chat_type": "private",
    "group_name": null,
    "metadata": {}
  }'
```

Buat reminder:

```bash
curl -X POST http://localhost:8000/api/reminders \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "628xxxxxxxxxx@s.whatsapp.net",
    "sender_id": "628xxxxxxxxxx@s.whatsapp.net",
    "message": "ingatkan aku besok jam 8 buat belajar backend"
  }'
```

Jika `AI_API_KEY` diisi, endpoint yang memakai auth harus menyertakan:

```txt
Authorization: Bearer <AI_API_KEY>
```

---

## MCP Tool Server

MCP server berjalan di `wa-enggine` karena hanya service ini yang memiliki socket WhatsApp.

Base URL Docker host:

```txt
http://localhost:8081
```

Endpoint:

| Method | Endpoint | Fungsi |
|---|---|---|
| `GET` | `/health` | Health check MCP dan status socket |
| `GET` | `/mcp/tools` | Daftar tool |
| `POST` | `/mcp/call` | Panggil tool |

List tool:

```bash
curl http://localhost:8081/mcp/tools
```

Kirim pesan:

```bash
curl -X POST http://localhost:8081/mcp/call \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MCP_API_KEY>" \
  -d '{
    "tool": "send_text_message",
    "input": {
      "jid": "628xxxxxxxxxx@s.whatsapp.net",
      "text": "Halo dari MCP"
    }
  }'
```

Jika `MCP_API_KEY` diisi, request ke `/mcp/tools` dan `/mcp/call` harus memakai salah satu header:

```txt
Authorization: Bearer <MCP_API_KEY>
x-api-key: <MCP_API_KEY>
```

---

## Data dan Volume

Docker Compose mount beberapa data lokal:

| Host / Volume | Container | Isi |
|---|---|---|
| `./services/ai/data` | `/app/data` | SQLite, FAISS, HEBAT downloads, browser profile |
| `OBSIDIAN_VAULT_HOST_PATH` | `/app/obsidian-vault` | Obsidian vault |
| `wa-media` volume | `/app/data/wa-media` | Media WhatsApp shared antara AI dan WA engine |
| `./services/wa-enggine/sessions` | `/app/sessions` | Session Baileys WhatsApp |

Set `OBSIDIAN_VAULT_HOST_PATH` di `.env` ke absolute path vault pada host,
misalnya `/home/<user>/Documents/xninetzy`. Docker Compose menolak start jika
variable ini kosong, sehingga tidak membuat folder `~` literal secara tidak sengaja.

File data lokal seperti SQLite, WAL/SHM, session Baileys, browser storage state, dan media hasil download tidak boleh dicommit.

---

## Obsidian

Default vault container:

```txt
/app/obsidian-vault
```

Default host mount:

```txt
/absolute/path/to/obsidian-vault
```

Safety bawaan:

- path harus relatif terhadap vault,
- absolute path ditolak,
- path traversal `..` ditolak,
- `.env`, `.git`, `sessions`, `token`, `secret`, credential-like paths ditolak,
- extension write dibatasi ke `.md`, `.txt`, `.json`,
- delete disabled default,
- overwrite dapat membuat backup.

Tool Obsidian tersedia lewat agent, bukan endpoint REST khusus root saat ini.

---

## HEBAT / Moodle

Integrasi HEBAT memakai Playwright untuk login dan mengambil data Moodle.

Env penting:

```env
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_NOTIFY_CHAT_ID=
HEBAT_AUTO_LOGIN=false
HEBAT_BROWSER_HEADLESS=true
HEBAT_REQUIRE_CONFIRMATION=true
HEBAT_MAX_UPLOAD_BYTES=5242880
HEBAT_ALLOWED_FILE_TYPES=.pdf
```

Command WhatsApp yang umum:

```txt
/hebat
/hebat-debug
login hebat
sync course hebat
sync tugas hebat
cek deadline hebat
```

Upload tugas dirancang memakai token konfirmasi. Bot akan menyiapkan submission terlebih dahulu, lalu user harus mengirim konfirmasi token sebelum upload dijalankan.

---

## Local Web Analysis

Web Analysis Engine adalah modul single-owner: satu instalasi untuk satu pemilik dan
seluruh proses berjalan lokal di AI Docker service/background loop. Engine tidak
dirancang sebagai layanan cloud atau multi-tenant.

Structural cache (`analisis_web.md`) hanya memuat selector, path, nama field,
structure hash, serta metadata endpoint GET/HEAD yang sudah disanitasi. Jadwal,
nilai, cookie, dan data pribadi tidak masuk Markdown; snapshot akademik dan
`storage_state` disimpan terpisah dengan Fernet encryption.

Setup env penting tersedia lengkap di `.env.example`. Buat encryption key satu kali,
simpan hanya di `.env`, lalu login manual dari host yang punya display:

```bash
cd services/ai
uv run python -m app.xninetzy.os.web_analysis.cli login --site mahasiswa
uv run python -m app.xninetzy.os.web_analysis.cli login --site hebat
```

Analisis struktur publik dapat dijalankan tanpa session:

```bash
uv run python -m app.xninetzy.os.web_analysis.cli analyze --site mahasiswa --force
uv run python -m app.xninetzy.os.web_analysis.cli analyze --site hebat --force
```

CAPTCHA/OTP selalu diselesaikan manual. Analyzer tidak mengisi form, mengeklik
tombol, atau mengirim method selain GET/HEAD. KRS dibatasi permanen ke monitoring
dan notifikasi; submit tetap tindakan manual owner.

Planning dan kontrak teknis: `docs/plan/PLANNING_WEB_ANALYSIS_AGENT.md` dan
`docs/plan/design_tool.md`.

---

## Research

Search ringan:

```txt
/research topik yang mau dicari
```

Deep research:

```txt
/deep-research topik
/deep-research speed topik
/deep-research balanced topik
/deep-research quality topik
```

Deep research memakai:

- permission check admin,
- sub-planning,
- research session SQLite,
- web/YouTube/academic actions sesuai mode,
- brief generator,
- optional admin notification.

Secara default deep research admin-only.

---

## HITL Approval

Human-in-the-loop dipakai untuk aksi berdampak besar, seperti:

- upload tugas HEBAT,
- menyimpan research besar ke Obsidian/Knowledge,
- membuat roadmap aktif dengan banyak task,
- bulk task create,
- write Graph RAG.

Command:

```txt
/approvals
/approve <id>
/reject <id>
```

Approval admin dicek di service approval. Untuk deploy serius, gunakan `ADMIN_JID` yang eksplisit, bukan hanya nama admin.

---

## Testing

AI service memiliki test suite pytest untuk command router, research, HITL, Graph RAG, learning, media, memory, rules, style, dan Lightning.

```bash
cd services/ai
SQLITE_PATH=/tmp/xninetzy-pytest.sqlite3 \
  uv run --with pytest --with pytest-asyncio python -m pytest -q -o asyncio_mode=auto tests/
```

Build TypeScript:

```bash
cd services/wa-enggine
yarn build
```

WA engine memiliki smoke/unit test TypeScript (`yarn test`) dan build check (`yarn build`).

---

## Struktur Direktori Ringkas

```txt
.
├── docker-compose.yml
├── .env.example
├── services
│   ├── ai
│   │   ├── app
│   │   │   ├── agent
│   │   │   ├── api
│   │   │   ├── core
│   │   │   ├── db
│   │   │   ├── ecosystem
│   │   │   ├── graph_rag
│   │   │   ├── hitl
│   │   │   ├── knowledge
│   │   │   ├── learning
│   │   │   ├── media
│   │   │   ├── memory
│   │   │   ├── obsidian
│   │   │   ├── research
│   │   │   ├── rules
│   │   │   ├── skills
│   │   │   ├── style
│   │   │   └── tools
│   │   ├── docs
│   │   ├── tests
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── wa-enggine
│       ├── src
│       │   ├── ai
│       │   ├── config
│       │   ├── mcp
│       │   ├── types
│       │   ├── utils
│       │   └── whatsapp
│       ├── package.json
│       └── Dockerfile
```

---

## Troubleshooting

### AI service tidak bisa menghubungi model

Pastikan `FLAZ_API_KEY` terisi dan cek `FLAZ_BASE_URL` serta `FLAZ_MODEL`.
Nilai default endpoint adalah `https://ai.flaz.id/v1` dengan model
`deepseek-v4-pro`.

### WhatsApp tidak muncul QR/pairing code

Reset session:

```bash
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```

Lalu cek:

```bash
docker compose logs -f wa-enggine
```

### Bot tidak merespons di group

Cek konfigurasi:

```env
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

Gunakan mention bot, reply pesan bot, atau prefix `!`.

### AI tidak bisa memanggil tool WhatsApp

Cek MCP:

```bash
curl http://localhost:8081/health
```

Pastikan `WA_MCP_BASE_URL` di AI mengarah ke MCP server:

```env
WA_MCP_BASE_URL=http://127.0.0.1:8081
```

Untuk local manual, gunakan:

```env
WA_MCP_BASE_URL=http://localhost:8081
```

### Obsidian tidak bisa write

Cek:

```env
OBSIDIAN_ENABLED=true
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
```

Pastikan volume vault termount dan writable.

### HEBAT login gagal

Cek:

```env
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
```

Lalu jalankan dari WhatsApp:

```txt
/hebat-debug
```

---

## Catatan Keamanan

Sebelum deploy publik:

- isi `AI_API_KEY`,
- isi `MCP_API_KEY` dan `WA_MCP_API_KEY` dengan nilai yang sama,
- matikan atau lindungi `AGENT_DEBUG_ENDPOINTS`,
- jangan expose port `8000` dan `8081` ke publik tanpa reverse proxy/auth,
- gunakan `ADMIN_JID` eksplisit untuk admin,
- jangan mengandalkan nama display WhatsApp sebagai satu-satunya identitas admin,
- jangan commit `.env`, database, session Baileys, browser storage state, media download, atau WAL/SHM SQLite,
- rotasi key yang pernah masuk repository atau file contoh,
- review tool yang bisa write/upload/delete sebelum diberi akses ke agent.

File contoh `.env.example` sebaiknya hanya berisi placeholder, bukan token atau nomor pribadi yang aktif.

---

## Status Repo

Repo ini sudah memiliki banyak modul fitur, tetapi beberapa area masih perlu diperketat sebelum production:

- auth debug endpoint,
- auth chat endpoint jika terekspos,
- mandatory MCP auth,
- CI untuk Python dan TypeScript,
- sinkronisasi README/dokumentasi service,
- repo hygiene untuk data lokal.

Untuk development lokal, Docker Compose adalah jalur paling praktis. Untuk production, jalankan service di jaringan private, batasi port publik, dan aktifkan API key.

---

## Multi-provider, Coding Agent, dan MCP

Chat AI dapat dipilih per pengguna dari provider/model yang diaktifkan operator:

```text
/llm list
/llm use flaz deepseek-v4-pro
```

Codex, Claude Code, atau OpenCode dapat dipilih sebagai runtime coding lokal yang terpisah:

```text
/agent list
/agent use codex
/code jalankan test terkait lalu perbaiki kegagalannya
```

Runtime coding dinonaktifkan secara default dan dapat dibatasi ke admin serta satu allowed workspace. Repository juga menyertakan MCP stdio Xninetzy untuk memberi Codex, Claude Code, dan OpenCode akses terkurasi ke Obsidian, knowledge, task, dan reminder:

- Codex: `.codex/config.toml`
- Claude Code: `.mcp.json`
- OpenCode: `opencode.json`
- Server: `services/ai/app/xninetzy/interfaces/mcp_server.py`

Panduan setup, keamanan, command, Docker, dan troubleshooting: [Provider LLM, Coding Agent, dan MCP](docs/AI_PROVIDERS_CODING_AGENTS_MCP.md).
