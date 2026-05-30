# Xninetzy AI WhatsApp Bot

MVP WhatsApp AI assistant untuk learning management, task management, breakdown tugas, penjelasan materi, dan draft jawaban edukatif.

Struktur service:

```txt
services/
├── ai
└── wa-enggine
```

`services/ai` berisi FastAPI + LangChain + DeepSeek. `services/wa-enggine` berisi WhatsApp worker Node.js + TypeScript + Baileys.

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
