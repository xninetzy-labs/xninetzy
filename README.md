# Xninetzy AI WhatsApp Bot

MVP WhatsApp AI assistant untuk learning management, task management, breakdown tugas, penjelasan materi, dan draft jawaban edukatif.

Struktur service:

```txt
services/
├── ai
└── wa-enggine
```

`services/ai` berisi FastAPI + LangChain + DeepSeek. `services/wa-enggine` berisi WhatsApp worker Node.js + TypeScript + Baileys.

Prompt utama AI disimpan di:

```txt
services/ai/app/prompts/prompts.md
```

Kode Python hanya memuat prompt lewat `services/ai/app/services/prompt_service.py`, supaya prompt bisa dirawat tanpa edit file Python.

WA MCP-style tool server berjalan di dalam `wa-enggine` pada port default `8081`, karena service itu yang memegang socket Baileys. Endpoint utamanya:

```txt
GET  /mcp/tools
POST /mcp/call
```

## Cara Run AI Manual

```bash
cd services/ai
cp .env.example .env
uv sync
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Cara Run WhatsApp Worker Manual

```bash
cd services/wa-enggine
cp .env.example .env
yarn install
yarn dev
```

Untuk local development tanpa Docker, gunakan:

```env
AI_API_URL=http://localhost:8000
```

## Cara Run Docker

```bash
cp .env.example .env
docker compose up --build
```

Untuk Docker Compose, gunakan:

```env
AI_API_URL=http://ai:8000
```

## Test Health

```bash
curl http://localhost:8000/health
```

## Test Chat API

```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "chat_id": "test-chat",
    "sender_id": "test-user",
    "sender_name": "Misbahul",
    "message": "bantu jelasin REST API",
    "chat_type": "private",
    "group_name": null
  }'
```

## Behavior Bot

Private chat langsung diproses dan dibalas.

Group chat hanya diproses kalau bot di-mention. Pesan grup tanpa mention akan diabaikan.

## Skill Engine

AI service punya Skill Engine modular di `services/ai/app/skills`.

Skill bawaan:
- `learning`
- `reminder`
- `calculation`
- `idea_analysis`
- `task_breakdown`
- `workflow`
- `obsidian`
- `note_generation`
- `planning`

Debug API:

```bash
curl http://localhost:8000/api/skills

curl -X POST http://localhost:8000/api/skills/calculation/run \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"debug","message":"kalau 15 dari 40 itu berapa persen?"}'
```

Jika `AI_API_KEY` diisi, semua endpoint debug skill/obsidian/reminder harus memakai:

```txt
Authorization: Bearer <AI_API_KEY>
```

## Obsidian Integration

Vault host default:

```txt
~/Documents/xninetzy
```

Di Docker, vault dimount ke:

```txt
/app/obsidian-vault
```

Compose memakai:

```yaml
volumes:
  - ./services/ai/data:/app/data
  - ~/Documents/xninetzy:/app/obsidian-vault
```

Jika `~` tidak resolve di environment Docker kamu, ganti dengan absolute path:

```yaml
  - /home/misbahul45/Documents/xninetzy:/app/obsidian-vault
```

Safety:
- Semua path harus tetap di dalam vault.
- Path traversal seperti `../.env` ditolak.
- `.env`, `.git`, `sessions`, private key, token, dan secret ditolak.
- Delete disabled by default.
- Overwrite membuat backup ke `.backup/YYYY-MM-DD/`.
- Operasi file dicatat di SQLite table `file_operations`.

Contoh:

```bash
curl -X POST http://localhost:8000/api/obsidian/create \
  -H "Content-Type: application/json" \
  -d '{"path":"Learning/test.md","content":"# Test","overwrite":false}'

curl -X POST http://localhost:8000/api/obsidian/search \
  -H "Content-Type: application/json" \
  -d '{"query":"langgraph"}'
```

## Reminder System

Reminder disimpan di SQLite table `reminders`. Scheduler background mengecek reminder due dan mengirim notifikasi lewat WA MCP tool `send_text_message`.

```bash
curl -X POST http://localhost:8000/api/reminders \
  -H "Content-Type: application/json" \
  -d '{"chat_id":"628xxxx@s.whatsapp.net","message":"ingatkan aku besok jam 8 buat belajar backend"}'
```

## Workflow Automation

Workflow skill saat ini membuat draft workflow, trigger, steps, dan daftar tool. Workflow berulang atau aksi eksternal tetap harus lewat confirmation policy.
