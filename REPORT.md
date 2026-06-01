# Full Repository Understanding Report

## 1. Executive Summary

**Xninetzy AI** adalah MVP (Minimum Viable Product) WhatsApp AI assistant yang dirancang untuk membantu learning management, task management, breakdown tugas, penjelasan materi, dan draft jawaban edukatif.

Project ini terdiri dari **2 service utama**:

| Service | Peran | Teknologi |
|---------|-------|-----------|
| **AI Service** | Backend AI yang memproses chat menggunakan LLM | FastAPI + LangChain + DeepSeek |
| **WA Engine** | WhatsApp worker yang menghubungkan bot ke WhatsApp via Baileys | Node.js + TypeScript + Baileys |

**Cara kerja umum:** User mengirim pesan WhatsApp -> WA Engine menerima via Baileys socket -> WA Engine mengirim ke AI Service -> AI Service memproses dengan LLM (DeepSeek) -> Balasan dikirim kembali ke user WhatsApp.

**Status project:** MVP / tahap pengembangan awal. Belum memiliki frontend, database permanen, autentikasi, testing, atau CI/CD. Struktur kode sudah cukup rapi dengan pemisahan concern yang baik di WA Engine.

---

## 2. Repository Structure

```txt
xninetzy/
├── apps/                            -> (kosong) - belum ada frontend
├── infra/                           -> (kosong) - belum ada konfigurasi infrastruktur
├── services/
│   ├── ai/                          -> AI Service (FastAPI + LangChain + DeepSeek)
│   │   ├── app/
│   │   │   ├── api/routes/          -> Endpoint API (health, chat)
│   │   │   ├── core/                -> Config dan logging
│   │   │   ├── memory/              -> In-memory chat history (sementara)
│   │   │   ├── schemas/             -> Pydantic models untuk request/response
│   │   │   ├── services/            -> LLM service dan prompt builder
│   │   │   └── main.py              -> Entry point FastAPI
│   │   ├── Dockerfile
│   │   ├── pyproject.toml           -> Dependency Python
│   │   └── uv.lock
│   └── wa-enggine/                  -> WhatsApp Worker (Node.js + Baileys)
│       ├── src/
│       │   ├── ai/                  -> HTTP client ke AI Service
│       │   ├── config/              -> Environment config
│       │   ├── types/               -> TypeScript types
│       │   ├── utils/               -> Utility (logger, jid, observability)
│       │   ├── whatsapp/            -> Baileys socket, auth, handler, trigger
│       │   └── app.ts               -> Entry point
│       ├── sessions/                -> WhatsApp session files (ter-commit!)
│       ├── Dockerfile
│       ├── package.json
│       └── tsconfig.json
├── docker-compose.yml               -> Orkestrasi 2 service
├── .env                             -> Environment variable (berisi API key asli!)
├── .env.example                     -> Template environment
├── README.md
└── .gitignore
```

### Fungsi setiap folder:

- **`apps/`** — Direncanakan untuk frontend, saat ini masih kosong.
- **`infra/`** — Direncanakan untuk konfigurasi infrastruktur (nginx, dll), saat ini kosong.
- **`services/ai/`** — AI backend service. Menerima request chat dari WA Engine, memproses dengan DeepSeek LLM via LangChain, mengembalikan response.
- **`services/wa-enggine/`** — WhatsApp worker. Menjaga koneksi WebSocket ke WhatsApp via Baileys, menerima pesan, meneruskan ke AI service, dan mengirim balasan.

### Entry point utama:
- **AI Service:** `services/ai/app/main.py` — FastAPI app
- **WA Engine:** `services/wa-enggine/src/app.ts` — Node.js app

### Relasi antar service:
- WA Engine **bergantung pada** AI Service (WA Engine mengirim HTTP request ke AI Service)
- Tidak ada dependensi sebaliknya
- WA Engine melakukan retry dan fallback jika AI Service tidak merespon

---

## 3. Tech Stack

| Komponen | Teknologi | Bukti dari Repo | Fungsi |
|----------|-----------|-----------------|--------|
| AI Backend | FastAPI + Python 3.11+ | `pyproject.toml`, `app/main.py` | REST API untuk chat AI |
| LLM Framework | LangChain + LangChain OpenAI | `pyproject.toml`, `llm_service.py` | Abstraction untuk LLM calls |
| LLM Model | DeepSeek (via API OpenAI-compatible) | `config.py: DEEPSEEK_MODEL`, `llm_service.py: ChatOpenAI` | Model AI utama |
| WA Worker | Node.js 20 + TypeScript | `package.json`, `tsconfig.json` | WhatsApp client via Baileys |
| WA Library | @whiskeysockets/baileys v7.0.0-rc13 | `package.json` | WhatsApp WebSocket library |
| HTTP Client (WA) | Axios | `package.json`, `ai-client.ts` | HTTP call ke AI Service |
| Logging (WA) | Pino | `package.json`, `logger.ts` | Structured logging |
| Logging (AI) | Python logging | `logging.py` | Logging standar |
| QR Code | qrcode-terminal | `package.json`, `connection-handler.ts` | Menampilkan QR code di terminal |
| Serialization | Pydantic v2 | `pyproject.toml`, `schemas/chat.py` | Validasi request/response |
| Auth State | Baileys multi-file auth | `auth.ts: useMultiFileAuthState` | Simpan session WhatsApp |
| Package Manager (AI) | uv | `pyproject.toml`, `Dockerfile` | Python package manager |
| Package Manager (WA) | Yarn | `package.json`, `yarn.lock` | Node package manager |
| Orchestration | Docker Compose | `docker-compose.yml` | Menjalankan 2 service |

---

## 4. Main Services

### 4.1 AI Service (FastAPI + LangChain + DeepSeek)

**Entry point:** `services/ai/app/main.py`

Service ini adalah REST API yang menyediakan endpoint chat. Menerima request dari WA Engine, membangun prompt dengan konteks, memanggil DeepSeek LLM via LangChain, dan mengembalikan hasil.

**Struktur internal:**

```txt
services/ai/app/
├── api/routes/
│   ├── health.py       -> GET /health
│   └── chat.py         -> POST /api/chat
├── core/
│   ├── config.py       -> Settings via pydantic-settings (baca .env)
│   └── logging.py      -> Konfigurasi logging
├── memory/
│   └── simple_memory.py -> In-memory chat history (max 10 pesan per chat_id)
├── schemas/
│   └── chat.py         -> ChatRequest, ChatResponse
├── services/
│   ├── llm_service.py  -> LLMService: generate_reply via LangChain
│   └── prompt_service.py -> build_system_prompt: sistem prompt untuk bot
└── main.py             -> FastAPI app dengan router
```

**Alur chat:**
1. WA Engine mengirim `POST /api/chat` dengan payload `ChatRequest`
2. `LLMService.generate_reply()` dipanggil
3. System prompt dibangun dari `prompt_service.py` — berisi instruksi lengkap tentang peran bot, gaya bahasa, format jawaban WhatsApp, dan batasan sistem
4. Riwayat chat (max 10 pesan) diambil dari in-memory storage
5. Pesan user ditambahkan sebagai `HumanMessage`
6. `ChatOpenAI` (LangChain) memanggil DeepSeek API
7. Response disimpan ke in-memory history
8. Balasan dikembalikan sebagai `ChatResponse`

### 4.2 WhatsApp Engine (Node.js + Baileys)

**Entry point:** `services/wa-enggine/src/app.ts`

Service ini adalah WhatsApp client worker yang menggunakan library Baileys untuk terhubung ke WhatsApp via WebSocket. Mendukung dua mode login: QR code dan pairing code.

**Struktur internal:**

```txt
services/wa-enggine/src/
├── ai/
│   ├── ai-client.ts     -> HTTP client ke AI Service (axios)
│   └── ai-payload.ts   -> Builder payload untuk request AI
├── config/
│   └── env.ts          -> Environment config + validasi
├── types/
│   ├── ai.ts           -> Type AI payload/response
│   ├── chat.ts         -> ChatType definition
│   └── message.ts      -> ChatPayload definition
├── utils/
│   ├── jid.ts          -> JID (WhatsApp ID) utilities
│   ├── logger.ts       -> Pino logger
│   ├── observability.ts -> Trace ID, masking JID/phone
│   └── sleep.ts        -> Sleep helper
├── whatsapp/
│   ├── auth.ts            -> MultiFileAuthState manager
│   ├── connection-handler.ts -> Handle connection update, QR, disconnect
│   ├── disconnect-utils.ts   -> Utility disconnect status code
│   ├── message-listener.ts   -> Listener pesan masuk, trigger AI
│   ├── message-parser.ts     -> Parse berbagai format pesan WA
│   ├── message-sender.ts     -> Kirim pesan teks WA
│   ├── pairing-manager.ts    -> Pairing code manager
│   ├── process-handlers.ts   -> Handler unhandledRejection/uncaughtException
│   ├── reconnect-manager.ts  -> Exponential backoff reconnect
│   ├── reply-context.ts      -> Kirim balasan dengan quoted message
│   ├── socket-factory.ts     -> Factory untuk create WASocket
│   ├── socket-state.ts       -> State management socket
│   ├── socket.ts             -> Start WhatsApp socket (orchestrator)
│   └── trigger.ts            -> Trigger logic (mention, prefix, reply)
└── app.ts               -> Entry point, validasi env, start socket
```

---

## 5. How The System Works

### Alur End-to-End:

```txt
[User WhatsApp]
     |
     v
[Baileys WebSocket]  <-- WA Engine (wa-enggine)
     |
     v
[Message Listener]  -->  [Trigger Check]
     |                        |
     |                   (private: always process)
     |                   (group: only if mentioned / prefixed / replied)
     |
     v
[AI Payload Builder]
     |
     v
[HTTP POST /api/chat]  -->  [AI Service (FastAPI)]
     |                              |
     |                         [Prompt Builder]
     |                              |
     |                         [Chat History (in-memory)]
     |                              |
     |                         [LangChain ChatOpenAI]
     |                              |
     |                         [DeepSeek API]
     |                              |
     |                         [Response]
     |                              |
     v                              v
[Send WhatsApp Reply]  <--  [ChatResponse]
     |
     v
[User WhatsApp]
```

### Penjelasan detail:

1. **Koneksi WhatsApp:** WA Engine memulai koneksi ke WhatsApp via Baileys WebSocket. Jika belum terdaftar, akan menampilkan QR code atau pairing code tergantung mode login.

2. **Penerimaan pesan:** Event `messages.upsert` dari Baileys menangkap semua pesan baru.

3. **Filter pesan:**
   - Pesan dari bot sendiri diabaikan (tracked via `botSentMessageIds`)
   - Hanya chat type `private` dan `group` yang diproses
   - **Private chat:** Selalu diproses
   - **Group chat:** Diproses hanya jika:
     - Bot di-mention (`@nomor_bot`)
     - Ada prefix command (default `!`)
     - Pesan reply ke pesan bot
     - Mode `groupAllowAll=true` (semua pesan grup diproses)

4. **Kirim ke AI:** Pesan yang lolos filter dikirim ke AI Service via HTTP POST `/api/chat`

5. **Proses AI:** AI Service membangun prompt dengan sistem prompt, riwayat chat, dan pesan user, lalu memanggil DeepSeek LLM

6. **Balas pesan:** Hasil dari AI dikirim kembali ke WhatsApp dengan me-reply pesan asli user

7. **Error handling:** Jika AI gagal, WA Engine mengirim pesan fallback "Maaf, AI sedang bermasalah"

---

## 6. Request Flow

### Flow untuk chat private:

```txt
1. User kirim pesan private ke nomor WhatsApp bot
2. Baileys WebSocket menerima event messages.upsert
3. Message Listener memproses:
   a. Skip jika dariMe (bot sendiri)
   b. Validasi remoteJid
   c. Validasi chatType (hanya private/group)
   d. Parse teks pesan
4. Trigger: private_chat -> always process
5. Build AI payload (chat_id, sender_id, sender_name, message, chat_type)
6. HTTP POST /api/chat ke AI Service (timeout 60s)
7. AI Service:
   a. Validasi request dengan Pydantic
   b. Bangun system prompt
   c. Ambil history chat dari in-memory
   d. Panggil DeepSeek via LangChain
   e. Simpan response ke history
   f. Return ChatResponse { reply }
8. WA Engine kirim reply ke WhatsApp via sendMessage
9. User terima balasan
```

### Flow untuk group chat:

```txt
1. User kirim pesan di grup (mention bot / pakai prefix / reply ke bot)
2. Sama seperti private, tapi ada step tambahan:
   a. Trigger check: mention detection, prefix detection, reply detection
   b. Text dinormalisasi (hapus mention @number, hapus prefix)
3. Jika tidak memenuhi trigger -> skip (log reason)
4. Jika mention saja tanpa teks -> kirim "Halo! Ada yang bisa saya bantu?"
5. Jika ada teks -> lanjut ke AI service
6. Sisa flow sama seperti private chat
```

---

## 7. Data Flow

```txt
Input (WhatsApp Message)
  --> extractMessageText() -> string
  --> shouldProcessMessage() -> { shouldProcess, normalizedText }
  --> buildAIChatPayload() -> AIChatPayload
  --> HTTP POST /api/chat (JSON)
  --> Pydantic validation -> ChatRequest
  --> build_system_prompt() + get_history() + HumanMessage
  --> LangChain ChatOpenAI.ainvoke() -> DeepSeek API
  --> append_message() to in-memory history
  --> Pydantic serialization -> ChatResponse { reply }
  --> sendWhatsAppReply() -> Baileys sendMessage
Output (WhatsApp Message)
```

**Catatan penting:** Tidak ada database persisten. Semua data disimpan di in-memory:
- Chat history: `dict[str, list[dict]]` di `simple_memory.py` (max 10 pesan per chat_id)
- Bot message IDs: `Set<string>` di `message-listener.ts` (max 500 IDs)
- Socket state: variabel module-level

---

## 8. API Analysis

### AI Service Endpoints:

| Method | Endpoint | Handler | Fungsi | Auth | Input | Output |
|--------|----------|---------|--------|------|-------|--------|
| GET | `/health` | `health_check` | Health check service | Tidak | - | `{"status":"ok","service":"xninetzy-ai"}` |
| POST | `/api/chat` | `chat` | Proses chat dan dapatkan balasan AI | Tidak | `ChatRequest` JSON | `ChatResponse` JSON |

### ChatRequest Schema:

```json
{
  "chat_id": "string (required, min 1 char)",
  "sender_id": "string | null",
  "sender_name": "string | null",
  "message": "string (required, min 1 char)",
  "chat_type": "'private' | 'group'",
  "group_name": "string | null",
  "metadata": "object (optional)"
}
```

### ChatResponse Schema:

```json
{
  "reply": "string"
}
```

### Catatan API:
- Tidak ada authentication pada endpoint AI Service
- WA Engine mengakses AI Service via internal Docker network (`http://ai:8000`)
- WA Engine tidak memiliki HTTP server (hanya WhatsApp client)
- Tidak ada endpoint untuk manage session WhatsApp (connect/disconnect/status/send-message via REST)

---

## 9. Database Analysis

**Tidak ada database persisten pada repository ini.**

Project ini menggunakan **in-memory storage** saja:

| Storage | Lokasi | Fungsi | Data |
|---------|--------|--------|------|
| Chat History | `services/ai/app/memory/simple_memory.py` | Menyimpan riwayat chat per sesi | `dict[chat_id, list[{role, content}]]` |
| Bot Message IDs | `services/wa-enggine/src/whatsapp/message-listener.ts` | Mencegah loop pesan bot | `Set<string>` (max 500) |

**Implikasi:**
- Riwayat chat hilang saat AI Service restart
- Tidak ada persistensi data user, pesan, atau session
- Tidak bisa melakukan query historis

**Tidak ditemukan:**
- Prisma schema
- Migration files
- SQL files
- ORM configuration
- Repository layer
- Database in docker-compose (tidak ada PostgreSQL, MySQL, SQLite)

---

## 10. Environment Variables

### Root `.env`:

| Variable | Digunakan Oleh | Fungsi | Wajib? |
|----------|---------------|--------|--------|
| `DEEPSEEK_API_KEY` | AI Service | API key untuk DeepSeek LLM | Yes |
| `DEEPSEEK_BASE_URL` | AI Service | Base URL API DeepSeek | Yes (default: `https://api.deepseek.com`) |
| `DEEPSEEK_MODEL` | AI Service | Nama model DeepSeek | Yes (default: `deepseek-v4-flash`) |
| `AI_API_HOST` | AI Service | Host binding FastAPI | Yes (default: `0.0.0.0`) |
| `AI_API_PORT` | AI Service | Port FastAPI | Yes (default: `8000`) |
| `WA_SESSION_DIR` | WA Engine | Lokasi penyimpanan session WhatsApp | Yes (default: `./sessions`) |
| `WA_LOGIN_MODE` | WA Engine | Mode login (`qr` / `pairing_code`) | Yes (default: `qr`) |
| `WA_PHONE_NUMBER` | WA Engine | Nomor telepon untuk pairing code | Yes jika pairing mode |
| `WA_PAIRING_WAIT_MS` | WA Engine | Waktu tunggu pairing code | No (default: `90000`) |
| `WA_PAIRING_RECONNECT_DELAY_MS` | WA Engine | Delay reconnect setelah pairing | No (default: `30000`) |
| `WA_GROUP_TRIGGER_MODE` | WA Engine | Mode trigger grup | No (default: `mention_or_prefix`) |
| `WA_COMMAND_PREFIX` | WA Engine | Prefix command | No (default: `!`) |
| `WA_GROUP_ALLOW_ALL` | WA Engine | Proses semua pesan grup | No (default: `false`) |
| `WA_GROUP_TREAT_ANY_MENTION_AS_BOT` | WA Engine | Treat any mention as bot mention | No (default: `true`) |
| `AI_BASE_URL` / `AI_API_URL` | WA Engine | URL AI Service | Yes (default: `http://ai:8000`) |
| `AI_CHAT_ENDPOINT` | WA Engine | Endpoint chat AI | No (default: `/api/chat`) |
| `AI_TIMEOUT_MS` | WA Engine | Timeout request AI | No (default: `60000`) |
| `BOT_NAME` | AI Service + WA Engine | Nama bot | No (default: `Xninetzy AI`) |
| `BOT_OWNER` | AI Service + WA Engine | Pemilik bot | No (default: `Misbahul Muttaqin`) |

### Tambahan dari `services/wa-enggine/.env.example`:

| Variable | Fungsi | Wajib? |
|----------|--------|--------|
| `WA_AUTH_DIR` | Lokasi auth state (fallback dari WA_SESSION_DIR) | No |
| `WA_CONNECT_TIMEOUT_MS` | Timeout koneksi WhatsApp | No (default: `60000`) |
| `WA_QUERY_TIMEOUT_MS` | Timeout query WhatsApp | No (default: `60000`) |
| `WA_KEEP_ALIVE_INTERVAL_MS` | Interval keep-alive | No (default: `30000`) |
| `WA_LOG_LEVEL` | Level logging WA Engine | No (default: `info`) |
| `WA_BAILEYS_LOG_LEVEL` | Level logging Baileys | No (default: `warn`) |

### ⚠️ Sensitive variables:
- **`DEEPSEEK_API_KEY`** — API key asli ada di `.env` (RAHASIA, jangan commit)
- **WA Session files** di folder `sessions/` berisi credential WhatsApp (sudah ter-commit!)

---

## 11. Docker & Deployment

### docker-compose.yml:

```yaml
services:
  ai:
    build:
      context: ./services/ai
    env_file:
      - .env
    ports:
      - "8000:8000"

  wa-enggine:
    build:
      context: ./services/wa-enggine
    env_file:
      - .env
    environment:
      WA_AUTH_DIR: /app/sessions
      AI_BASE_URL: http://ai:8000
      AI_CHAT_ENDPOINT: /api/chat
      AI_TIMEOUT_MS: "60000"
      WA_PAIRING_WAIT_MS: "90000"
      WA_PAIRING_RECONNECT_DELAY_MS: "30000"
      WA_GROUP_TRIGGER_MODE: mention_or_prefix
      WA_COMMAND_PREFIX: "!"
    depends_on:
      - ai
    restart: unless-stopped
    volumes:
      - ./services/wa-enggine/sessions:/app/sessions
```

### Service detail:

| Service | Build Context | Port Internal | Port External | Fungsi |
|---------|--------------|---------------|---------------|--------|
| `ai` | `./services/ai` | 8000 | 8000 | AI FastAPI |
| `wa-enggine` | `./services/wa-enggine` | - | - | WhatsApp worker |

### Dockerfile:

**AI Service** (`services/ai/Dockerfile`):
- Multi-stage: menggunakan `ghcr.io/astral-sh/uv:python3.11-bookworm-slim`
- Install dependency dengan `uv sync --no-dev`
- Copy folder `app/`
- Run: `uv run uvicorn app.main:app --host 0.0.0.0 --port 8000`

**WA Engine** (`services/wa-enggine/Dockerfile`):
- Multi-stage: `node:20-alpine`
- Stage 1 (deps): Install semua dependency, build TypeScript
- Stage 2 (production): Copy hanya `dist/` dan production dependencies
- Run: `node dist/app.js`

### Network:
- Service berkomunikasi via Docker internal network (default bridge)
- WA Engine mengakses AI Service via `http://ai:8000`
- **Tidak ada reverse proxy (nginx)** — AI Service terekspos langsung ke host di port 8000

### Volume:
- WA Engine session: `./services/wa-enggine/sessions:/app/sessions` — session WhatsApp tetap ada setelah restart

### Startup order:
1. `ai` service (WA Engine memiliki `depends_on: ai`)
2. `wa-enggine` service mulai setelah AI siap (tidak ada healthcheck, hanya depends_on)

### Urutan booting:
```txt
docker compose up --build
  -> ai (FastAPI on port 8000)
  -> wa-enggine (WhatsApp client, connects via http://ai:8000)
```

### Cara menjalankan:

**Docker:**
```bash
cp .env.example .env
# edit .env dengan DEEPSEEK_API_KEY
docker compose up --build
```

**Local development (AI Service):**
```bash
cd services/ai
cp .env.example .env
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Local development (WA Engine):**
```bash
cd services/wa-enggine
cp .env.example .env
yarn install
yarn dev
```

---

## 12. WhatsApp Engine Analysis

### Cara kerja WA Engine:

1. **Startup:**
   - Validasi environment variables
   - Load auth state dari `useMultiFileAuthState` (Baileys)
   - Buat WASocket via `socket-factory.ts`
   - Daftarkan event listener: `creds.update`, `connection.update`, `messages.upsert`
   - Jika belum terdaftar, tampilkan QR atau request pairing code

2. **Session storage:**
   - Menggunakan `useMultiFileAuthState` — session disimpan sebagai file JSON di folder `sessions/`
   - Multi-file: creds.json, pre-key-*.json, session-*.json, sender-key-*.json, dll.
   - Session di-bind ke volume Docker (`/app/sessions`)

3. **Multi-account support:**
   - **Tidak mendukung multi-account** — hanya satu session per instance service
   - Satu folder session untuk satu nomor WhatsApp
   - Untuk multi-account perlu multiple instance WA Engine

4. **QR generation:**
   - Jika `WA_LOGIN_MODE=qr`, QR code ditampilkan di terminal via `qrcode-terminal`
   - Event `connection.update` dengan field `qr` diproses

5. **Pairing code:**
   - Jika `WA_LOGIN_MODE=pairing_code` dan `WA_PHONE_NUMBER` diisi
   - Memanggil `sock.requestPairingCode(phoneNumber)`
   - Pairing code ditampilkan di log
   - Memiliki `pairing window` management (timeout dan reconnect logic)

6. **Private chat handling:**
   - Semua pesan private diproses (tanpa filter)

7. **Group chat handling:**
   - Filter berdasarkan `WA_GROUP_TRIGGER_MODE`:
     - `mention_only`: hanya jika bot di-mention atau reply ke bot
     - `prefix_only`: hanya jika pesan dimulai dengan prefix (default `!`)
     - `mention_or_prefix` (default): mention ATAU prefix
     - `all`: semua pesan grup diproses
   - Jika `WA_GROUP_ALLOW_ALL=true`, semua pesan grup diproses
   - Mention detection via contextInfo.mentionedJid dan text mention (@number)
   - Reply detection via stanzaId + participant match dengan bot identity

8. **Mention di grup:**
   - Filter mention menggunakan `detectBotMention()`: cek `mentionedJid` dari context info dan teks `@number`
   - Bot identity diambil dari `sock.user.id` dan `sock.user.lid`
   - Jika mention saja tanpa teks, bot membalas "Halo! Ada yang bisa saya bantu?"

9. **Send message:**
   - Menggunakan `sock.sendMessage(jid, { text }, { quoted })`
   - Jika quoted reply gagal, retry tanpa quoted message

10. **Reconnect logic:**
    - Exponential backoff: `min(30_000, 2_000 * attempts)` ms
    - Reset attempts saat koneksi berhasil (`connection === "open"`)
    - Jika `loggedOut` atau `401` atau `403` atau `bad session` -> reset auth state (hapus session)
    - Jika recoverable error (408, 515, timeout, stream error) -> reconnect
    - Handler untuk `unhandledRejection` dan `uncaughtException` untuk error Baileys yang recoverable

11. **Status connection:**
    - Disimpan di variabel module `currentSocket` (socket-state.ts)
    - Event `connection.update` memberikan status: `connecting`, `open`, `close`

12. **Tidak ada REST API endpoint:**
    - WA Engine tidak memiliki HTTP server
    - Tidak ada endpoint untuk connect/disconnect/status/send-message via HTTP
    - Hanya berjalan sebagai worker yang terhubung ke WhatsApp

### Flow WA Engine:

```txt
[WhatsApp Message]
     |
     v
[Baileys Socket]  <-- [Socket Factory]
     |
     v
[Message Listener] (messages.upsert)
     |
     v
[Handle Incoming Message]
     |
     ├── Skip if fromMe (bot sendiri)
     ├── Skip if missing remoteJid
     ├── Skip if unsupported chat type
     ├── Skip if message not decrypted
     ├── Skip if no text
     |
     v
[Trigger Check]
     ├── Private -> always process
     └── Group  -> mention / prefix / reply?
                      |
                      v (if not triggered -> skip)
     |
     v
[Build AI Payload]
     |
     v
[HTTP POST /api/chat]  -->  [AI Service]
     |
     v
[Send WhatsApp Reply]
     |
     └── Try quoted reply
         └── Fallback: reply without quoted
```

### Risiko WA Engine:

| Risiko | Deskripsi | Severity |
|--------|-----------|----------|
| **Session ter-commit** | Folder `sessions/` berisi file credential WhatsApp yang sudah ter-commit ke git | **HIGH** |
| **Banned number** | Penggunaan Baileys melanggar ToS WhatsApp, resiko banned | Medium |
| **Memory leak** | In-memory sets untuk botMessageIds (max 500) aman, tapi multiple session bisa jadi issue | Low |
| **Scaling multi-account** | Tidak ada arsitektur untuk multi-account, perlu multiple container | Medium |
| **Reconnect loop** | Reconnect logic sudah baik dengan exponential backoff dan max attempts | Low |
| **Rate limit** | Tidak ada rate limiting untuk pesan masuk | Medium |
| **Compliance** | WhatsApp policy melarang third-party client | High (legal risk) |
| **Single point of failure** | Tidak ada healthcheck di compose, WA Engine restart if crash | Medium |

---

## 13. AI Engine / Agent Analysis

### Entry point:

`services/ai/app/main.py` — FastAPI application

### Endpoint AI:

| Method | Endpoint | Fungsi |
|--------|----------|--------|
| GET | `/health` | Health check |
| POST | `/api/chat` | Generate reply dari LLM |

### Prompt yang digunakan:

System prompt dibangun oleh `prompt_service.py` yang berisi instruksi lengkap untuk bot Xninetzy AI:
- **Peran:** Asisten pintar untuk learning management, task management, penjelasan materi
- **Gaya bahasa:** Bahasa Indonesia, santai, to the point, boleh ekspresi casual ("siap", "gas", "prei")
- **Format jawaban:** Format WhatsApp (bold `*text*`, italic `_text_`, strikethrough `~text~`, code `` ``` ``` ``)
- **Batasan sistem (MVP):** Tidak ada database permanen, tidak ada integrasi kalender, tidak bisa akses file/browsing
- **Penanganan pertanyaan aneh:** Respons dengan gaya "prei" (santai, lucu, minta klarifikasi)

### Model yang digunakan:

- DeepSeek via API yang kompatibel dengan OpenAI
- Model: `deepseek-v4-flash` (dari env `DEEPSEEK_MODEL`)
- Temperature: 0.3
- Base URL: `https://api.deepseek.com`

### Tools yang tersedia untuk agent:

**Tidak ada tool calling.** Project ini belum mengimplementasikan:
- Function calling / tool use
- Web browsing
- File/document processing
- Integrasi eksternal (kalender, database, dll.)

### Memory / Vector database:

- **Tidak ada vector database**
- Chat history menggunakan in-memory dictionary dengan max 10 pesan per chat_id
- History hilang saat service restart

### RAG Pipeline:

**Tidak ada RAG pipeline.** Belum ada:
- Document ingestion
- Vector store
- Retrieval mechanism
- Context augmentation

### Alur request AI:

```txt
[WA Engine HTTP POST /api/chat]
     |
     v
[AI Service FastAPI]
     |
     v
[ChatRequest validation (Pydantic)]
     |
     v
[LLMService.generate_reply()]
     |
     ├── build_system_prompt() -> SystemMessage
     ├── get_history(chat_id) -> history messages
     ├── format user message -> HumanMessage
     ├── llm.ainvoke([System, History..., Human])
     ├── append_message() to history
     |
     v
[ChatResponse { reply }]
     |
     v
[Return to WA Engine]
```

### Error handling AI:
- Tidak ada error handling spesifik di level service (langsung throw)
- WA Engine menangkap error HTTP dan mengirim fallback reply
- Timeout: 60 detik (dari env `AI_TIMEOUT_MS`)

### Logging AI:
- Menggunakan Python logging dengan format `%(asctime)s %(levelname)s [%(name)s] %(message)s`
- Level: INFO (dari `configure_logging`)
- Tidak ada structured logging (JSON), tidak ada tracing

---

## 14. Authentication & Security

### Analisis Keamanan:

| Area | Kondisi Saat Ini | Risiko | Rekomendasi |
|------|-----------------|--------|-------------|
| **API Key exposure** | `DEEPSEEK_API_KEY` asli ada di `.env` yang **ter-commit** | API key bisa dicuri, biaya LLM tidak terkendali | Rotasi key segera, pastikan `.env` masuk `.gitignore` |
| **WA Session exposure** | Folder `sessions/` dengan `creds.json` dan ratusan file JSON **ter-commit** | WhatsApp session bisa dicuri, akun bisa diakses pihak lain | Hapus dari git, tambahkan ke `.gitignore`, gunakan `.gitattributes` |
| **Auth (AI Service)** | **Tidak ada authentication** pada endpoint AI Service | Siapa pun bisa akses `/api/chat` jika port terbuka | Tambahkan API key atau JWT |
| **Auth (WA Engine)** | Tidak ada HTTP server (tidak terekspos) | Aman (tidak ada port terbuka) | - |
| **Input validation** | Pydantic validation di AI Service (min_length, Literal type) | Baik untuk MVP | - |
| **CORS** | Tidak dikonfigurasi (tidak relevan karena tidak ada frontend) | Rendah | - |
| **SQL Injection** | Tidak ada database | Tidak relevan | - |
| **Rate limiting** | **Tidak ada** | Bisa spam AI, biaya membengkak | Tambahkan rate limiter |
| **Sensitive logging** | Log mencakup messageId, jid (di-mask), phone (di-mask) | Cukup baik, masking diterapkan | - |
| **Docker port exposure** | AI Service port 8000 terekspos ke host | Service bisa diakses dari luar jika firewall tidak diatur | Batasi akses atau gunakan internal network saja |
| **Environment validation** | Validasi environment di WA Engine, tidak di AI Service | AI Service bisa jalan tanpa API key, akan error saat dipanggil | Tambahkan startup validation |

### ⚠️ Kritis: Commit Secret

File `.env` berisi `DEEPSEEK_API_KEY=sk-6574c78f7b104c3688234d5ae202b07a` yang sudah ter-commit ke git history. Ini adalah **security incident** yang harus segera ditangani:
1. Rotasi key di DeepSeek dashboard
2. Hapus dari git history (BFG Repo-Cleaner)
3. Pastikan `.env` masuk `.gitignore`

### ⚠️ Kritis: WA Session Ter-commit

Folder `services/wa-enggine/sessions/` berisi **ratusan file JSON** yang merupakan credential WhatsApp session, termasuk `creds.json` dengan informasi login. Ini sudah ter-commit ke git. Risiko:
- Siapa pun yang punya akses ke repo bisa mengambil alih session WhatsApp
- Nomor WhatsApp bisa digunakan tanpa otorisasi

---

## 15. Code Quality Review

| Aspek | Penilaian | Catatan |
|-------|-----------|---------|
| **Struktur folder** | **Baik** | Pemisahan service jelas (ai vs wa-enggine). WA Engine memiliki pemisahan concern yang baik (types, utils, whatsapp, ai, config). AI Service terstruktur dengan routes, services, schemas, core. |
| **Error handling** | **Baik (WA) / Cukup (AI)** | WA Engine: comprehensive error handling dengan disconnect status codes, recoverable errors, reconnect logic, fallback messages, unhandled rejection/exception handlers. AI Service: minimal, hanya throw error tanpa catch di level service. |
| **Logging** | **Baik (WA) / Cukup (AI)** | WA Engine: structured JSON logging dengan Pino, context-rich logs (step, traceId, duration), masking sensitive data. AI Service: basic Python logging, tidak ada structured logging atau tracing. |
| **Modularity** | **Baik** | WA Engine: sangat modular dengan single-responsibility files (auth.ts, trigger.ts, message-parser.ts, dll). AI Service: cukup modular dengan pemisahan routes, services, schemas. |
| **Testing** | **Kurang** | **Tidak ada test sama sekali.** Tidak ada test files, test framework, atau test configuration. |
| **Type safety** | **Baik (WA) / Baik (AI)** | WA Engine: TypeScript strict mode, tipe didefinisikan dengan baik. AI Service: Pydantic v2 dengan type hints. |
| **Code duplication** | **Baik** | Minimal duplication. Beberapa duplikasi di process-handlers.ts (logika serupa untuk 515, 408, timeout). |
| **Naming convention** | **Baik** | Nama file dan fungsi deskriptif (message-listener.ts, reconnect-manager.ts, dll). Konsisten camelCase (TS) dan snake_case (Python). |
| **Configuration management** | **Baik** | Environment variables terpusat di `env.ts` (WA) dan `config.py` (AI). Default values tersedia. |
| **Dependency injection** | **Cukup** | AI Service menggunakan `Depends` FastAPI dan `lru_cache` untuk singleton. WA Engine menggunakan module-level singletons. |
| **Security awareness** | **Kurang** | Credentials ter-commit di git. Tidak ada auth pada endpoint API. Tidak ada rate limiting. |

---

## 16. Risks & Issues

### 🔴 High Priority

| # | Issue | File/Lokasi | Dampak |
|---|-------|-------------|--------|
| 1 | **API Key ter-commit** | `.env` berisi `DEEPSEEK_API_KEY` asli di git history | Penyalahgunaan API key, biaya tidak terkendali |
| 2 | **WA Session ter-commit** | `services/wa-enggine/sessions/` berisi 200+ file session termasuk `creds.json` | Akun WhatsApp bisa diakses tanpa otorisasi |
| 3 | **Tidak ada database** | Tidak ada PostgreSQL/MariaDB/SQLite | Data hilang saat restart, tidak bisa scale |
| 4 | **Tidak ada testing** | Tidak ada test files sama sekali | Tidak bisa memastikan kualitas dan regresi |
| 5 | **Tidak ada auth di AI Service** | `/api/chat` tanpa autentikasi | Siapa pun bisa memanggil API jika port terbuka |

### 🟡 Medium Priority

| # | Issue | Dampak |
|---|-------|--------|
| 6 | WA Engine tidak punya HTTP server | Tidak ada cara REST untuk manage session, cek status, kirim peson |
| 7 | Tidak ada rate limiting | Bisa spam AI dan menyebabkan biaya membengkak |
| 8 | Tidak ada healthcheck di docker-compose | WA Engine bisa start sebelum AI siap |
| 9 | Chat history in-memory (max 10 msg) | Konteks percakapan sangat terbatas |
| 10 | Tidak ada monitoring/observability | Tidak ada metrics, tracing, atau alerting |
| 11 | AI Engine tidak ada startup validation | Bisa jalan tanpa API key, error saat dipanggil |
| 12 | Port 8000 terekspos ke host | Akses langsung ke AI Service tanpa auth |

### 🟢 Low Priority

| # | Issue | Dampak |
|---|-------|--------|
| 13 | Tidak ada dokumentasi API (OpenAPI/Swagger) | Developer baru harus baca source code |
| 14 | Tidak ada CI/CD | Manual build dan deploy |
| 15 | Tidak ada frontend | Bot hanya bisa diakses via WhatsApp |
| 16 | `apps/` dan `infra/` folder kosong | Kebingungan struktur |

---

## 17. Recommendations

### 🔴 High Priority

1. **Rotasi API Key** — Segera ganti `DEEPSEEK_API_KEY` di DeepSeek dashboard, hapus `.env` dari git history dengan BFG Repo-Cleaner
2. **Hapus WA Session dari git** — `git rm -r services/wa-enggine/sessions/`, tambahkan pattern ke `.gitignore`, hapus dari git history
3. **Tambahkan database** — Implementasi PostgreSQL/SQLite dengan Prisma atau SQLAlchemy untuk persistensi chat history, user data, session management
4. **Tambahkan testing** — Minimal unit test untuk trigger logic, message parser, AI payload builder
5. **Tambahkan authentication** — API key atau JWT untuk akses AI Service endpoint

### 🟡 Medium Priority

6. **Tambahkan rate limiter** — SlowRate atau Token Bucket untuk mencegah abuse
7. **Tambahkan healthcheck di compose** — Pastikan WA Engine menunggu AI benar-benar siap
8. **Ubuntu memory ke persistent storage** — Chat history pindah ke Redis atau Database
9. **Tambahkan monitoring** — Integrasi dengan OpenTelemetry, log aggregation (Loki/CloudWatch)
10. **Tambahkan REST API di WA Engine** — Express/Fastify untuk manage session, cek status, kirim pesan via HTTP
11. **Validasi startup AI Service** — Cek DEEPSEEK_API_KEY saat startup
12. **Batasi port exposure** — Jangan expose port AI Service ke host jika tidak perlu

### 🟢 Low Priority

13. **Generate OpenAPI docs** — FastAPI sudah otomatis, manfaatkan `/docs`
14. **Setup CI/CD pipeline** — GitHub Actions untuk lint, test, build
15. **Buat frontend minimal** — Next.js atau SvelteKit untuk dashboard
16. **Bersihkan folder kosong** — Hapus atau isi `apps/` dan `infra/`
17. **Docker multi-stage optimization** — Sudah cukup baik, bisa optimize dengan cache mount

---

## 18. Architecture Diagram

```txt
+------------------------------------------------------------------+
|                        DOCKER NETWORK                             |
|                                                                   |
|  +---------------------------+    +----------------------------+  |
|  |      AI SERVICE           |    |     WA ENGINE              |  |
|  |  (FastAPI + LangChain)    |    |  (Node.js + TypeScript     |  |
|  |                           |    |   + Baileys)               |  |
|  |  Port: 8000               |    |                            |  |
|  |  Host port: 8000          |    |  No HTTP server            |  |
|  |                           |    |                            |  |
|  |  GET  /health          <--+----+  HTTP POST /api/chat       |  |
|  |  POST /api/chat        ---+---->  (axios client)            |  |
|  |                           |    |                            |  |
|  |  [DeepSeek API]           |    |  [Baileys WebSocket]       |  |
|  |      ^                    |    |      |                     |  |
|  |      | (HTTP)             |    |      v                     |  |
|  |  https://api.deepseek.com |    |  [WhatsApp Servers]        |  |
|  +---------------------------+    +----------------------------+  |
+------------------------------------------------------------------+
                                    |
                                    v
                          +---------------------+
                          |   WHATSAPP USER     |
                          | (Private / Group)   |
                          +---------------------+
```

---

## 19. Sequence Flow

### Sequence 1: User kirim private chat

```txt
User                    WA Engine                   AI Service              DeepSeek
  |                         |                          |                       |
  |--(1) WhatsApp Message-->|                          |                       |
  |                         |--(2) Parse & Validate    |                       |
  |                         |--(3) Trigger Check       |                       |
  |                         |   (private -> process)   |                       |
  |                         |--(4) Build AI Payload    |                       |
  |                         |                          |                       |
  |                         |--(5) POST /api/chat------>|                       |
  |                         |                          |--(6) Build Prompt     |
  |                         |                          |--(7) Get History      |
  |                         |                          |--(8) Call DeepSeek---->|
  |                         |                          |                       |
  |                         |                          |<---(9) AI Response ---|
  |                         |                          |                       |
  |                         |<---(10) ChatResponse ----|                       |
  |                         |                          |                       |
  |                         |--(11) Send Reply         |                       |
  |<--(12) Reply Message ---|                          |                       |
```

### Sequence 2: User kirim pesan grup (mention bot)

```txt
User (Group)            WA Engine                   AI Service
  |                         |                          |
  |--(1) Group Message      |                          |
  |    (@bot + text)        |                          |
  |                         |--(2) Parse & Validate    |
  |                         |--(3) Trigger Check       |
  |                         |   (group + mention ->    |
  |                         |    process)              |
  |                         |--(4) Clean Text          |
  |                         |   (remove @mention)      |
  |                         |--(5) Build AI Payload    |
  |                         |                          |
  |                         |--(6) POST /api/chat------>|
  |                         |                          |
  |                         |<---(7) ChatResponse -----|
  |                         |                          |
  |                         |--(8) Send Reply (quoted) |
  |<--(9) Reply Message ----|                          |
```

### Sequence 3: Reconnect / Error handling

```txt
WA Engine
  |
  |-- Connection closed
  |   |
  |   +-- loggedOut / 401 / 403 / bad session?
  |   |     YES -> Reset auth state, clear sessions
  |   |     NO  -> Schedule reconnect (exponential backoff)
  |   |
  |   +-- Inside pairing window?
  |         YES -> Use WA_PAIRING_RECONNECT_DELAY_MS
  |         NO  -> Normal backoff
  |
  |-- Unhandled rejection / exception
  |   |
  |   +-- Recoverable Baileys error (408, 515, timeout)?
  |         YES -> Schedule reconnect
  |         NO  -> process.exit(1)
```

---

## 20. Developer Onboarding Guide

### Prerequisites

- Docker & Docker Compose (cara termudah)
- Atau: Python 3.11+, Node.js 20+, Yarn, uv

### Setup Environment

```bash
# Clone repository
git clone <repo-url>
cd xninetzy

# Copy environment file
cp .env.example .env

# EDIT .env - isi DEEPSEEK_API_KEY dengan key valid
nano .env
```

### Run with Docker (recommended)

```bash
docker compose up --build
```

Service akan berjalan:
- AI Service: http://localhost:8000
- WA Engine: tidak ada port, hanya WhatsApp client

### Run Manual (local development)

**Terminal 1 - AI Service:**
```bash
cd services/ai
cp .env.example .env
# edit .env dengan DEEPSEEK_API_KEY
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal 2 - WA Engine:**
```bash
cd services/wa-enggine
cp .env.example .env
# set AI_BASE_URL=http://localhost:8000 di .env
yarn install
yarn dev
```

### Test Health

```bash
curl http://localhost:8000/health
# Output: {"status":"ok","service":"xninetzy-ai"}
```

### Test Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "test-chat",
    "sender_id": "test-user",
    "sender_name": "Test User",
    "message": "bantu jelasin REST API",
    "chat_type": "private"
  }'
```

### Cek Log

```bash
# AI Service logs
docker compose logs -f ai

# WA Engine logs
docker compose logs -f wa-enggine
```

### Common Issues

| Problem | Solution |
|---------|----------|
| AI Service error "DEEPSEEK_API_KEY not set" | Pastikan `.env` berisi API key valid |
| WA Engine tidak bisa connect WhatsApp | Hapus folder `services/wa-enggine/sessions/` lalu restart |
| QR code tidak muncul | Set `WA_LOGIN_MODE=qr` di `.env` |
| WA Engine error "PORT already in use" | Tidak ada port, cek log lain |
| AI Service tidak merespon | Cek `docker compose logs ai` |

### Reset WhatsApp Session

```bash
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build
```

---

## 21. Final Conclusion

### Kondisi Repository

**Xninetzy AI** adalah project MVP yang sudah memiliki struktur dan arsitektur yang cukup baik untuk tahap awal:

**Kelebihan:**
- ✅ Pemisahan service yang jelas (AI + WA Engine)
- ✅ Struktur kode WA Engine sangat rapi dengan single-responsibility files
- ✅ Error handling WA Engine comprehensive (reconnect logic, disconnect handling, fallback)
- ✅ Logging WA Engine dengan Pino sangat baik (structured, traceable)
- ✅ Type safety dengan TypeScript strict dan Pydantic v2
- ✅ Build system modern (uv, yarn) dan Docker multi-stage

**Kekurangan:**
- ❌ **KRITIS: Credentials ter-commit di git** (API key + WhatsApp session)
- ❌ Tidak ada database persisten (data hilang saat restart)
- ❌ Tidak ada testing
- ❌ Tidak ada authentication pada API endpoint
- ❌ Tidak ada rate limiting
- ❌ WA Engine tidak memiliki HTTP server (tidak bisa manage via REST)
- ❌ AI Service tidak memiliki startup validation
- ❌ Belum ada frontend
- ❌ Belum ada CI/CD

### Prioritas Perbaikan

1. **Segera:** Rotasi API key, hapus session dari git, hapus credentials dari history
2. **Segera:** Tambahkan database untuk persistensi
3. **Minggu ini:** Tambahkan testing (minimal unit test untuk trigger logic)
4. **Minggu ini:** Tambahkan autentikasi di AI Service
5. **Bulan ini:** Tambahkan REST API di WA Engine, rate limiting, monitoring
6. **Kedepan:** Frontend, CI/CD, multi-account support, file processing, RAG pipeline

### Pertanyaan Lanjutan untuk Developer

1. Apakah ada rencana untuk menambahkan database? Jika ya, database apa yang dipilih?
2. Apakah WA Engine direncanakan untuk multi-account?
3. Apakah ada rencana untuk menambahkan REST API di WA Engine?
4. Apakah endpoint `/api/chat` perlu auth? Atakah hanya diakses dari internal network?
5. Apakah ada rencana untuk menambahkan frontend?
6. Framework testing apa yang preferred (Vitest, Jest, pytest)?
7. Apakah folder `apps/` dan `infra/` memang sengaja dibiarkan kosong?
8. Apakah ada rencana untuk WhatsApp Business API (resmi) atau tetap menggunakan Baileys?
9. Apakah perlu support untuk file/media processing?
10. Apakah ada rencana untuk RAG atau knowledge base?
