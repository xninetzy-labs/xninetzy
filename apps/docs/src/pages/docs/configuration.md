---
layout: ../../layouts/DocsLayout.astro
title: Konfigurasi environment
description: Peta konfigurasi service, provider, persistence, dan guard yang aman untuk instalasi baru.
section: Mulai
---

Root `.env.example` adalah kontrak konfigurasi seluruh monorepo. Salin menjadi `.env`; jangan mengubah template dengan nilai rahasia.

Setiap clone memakai SQLite lokal yang berbeda. Tidak ada database runtime di
repository. Startup membuat/migrasikan database pada `SQLITE_PATH`; lihat
[Local data per installation](/docs/local-data/).

## Konfigurasi inti

```dotenv
APP_ENV=development
APP_TIMEZONE=Asia/Jakarta
LOG_LEVEL=INFO
HOST_UID=1000
HOST_GID=1000
```

Gunakan UID/GID pemilik repository dan vault. Ini mencegah file Docker dimiliki root.

## AI dan provider

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_API_KEY=
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

`*_MODELS` adalah allowlist model yang dipisahkan koma. Lihat [Provider LLM](/docs/providers/) untuk konfigurasi multi-provider.

## WhatsApp

```dotenv
AI_API_URL=http://127.0.0.1:8000
WA_LOGIN_MODE=qr
WA_PHONE_NUMBER=
WA_GROUP_TRIGGER_MODE=mention_or_prefix
WA_COMMAND_PREFIX=!
WA_GROUP_ALLOW_ALL=false
```

Untuk local development, path session/media harus absolute dan menunjuk lokasi yang sama bagi kedua service:

```dotenv
WA_AUTH_DIR=/absolute/path/to/xninetzy/services/wa-enggine/sessions
WA_MEDIA_DIR=/absolute/path/to/xninetzy/services/ai/data/wa-media
```

## Obsidian

```dotenv
OBSIDIAN_ENABLED=true
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/vault
OBSIDIAN_VAULT_PATH=/app/obsidian-vault
OBSIDIAN_ALLOW_WRITE=true
OBSIDIAN_ALLOW_DELETE=false
OBSIDIAN_BACKUP_BEFORE_WRITE=true
OBSIDIAN_FOLDERING_ENABLED=true
OBSIDIAN_CANONICAL_SCHEMA_VERSION=1
OBSIDIAN_ORGANIZE_MODE=hybrid
OBSIDIAN_REQUIRE_ORGANIZE_APPROVAL=true
OBSIDIAN_AUTO_REFRESH_MOC=true
OBSIDIAN_PERSIST_ACADEMIC_SENSITIVE=false
OBSIDIAN_LEGACY_PATH_COMPATIBILITY=true
```

`OBSIDIAN_VAULT_HOST_PATH` dipakai Docker host. `OBSIDIAN_VAULT_PATH` adalah mount path di container.

## HEBAT / Moodle

```dotenv
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_BASE_URL=https://hebat.elearning.unair.ac.id
HEBAT_LOGIN_URL=https://hebat.elearning.unair.ac.id/login/index.php
HEBAT_BROWSER_HEADLESS=true
HEBAT_AUTO_LOGIN=false
HEBAT_REQUIRE_CONFIRMATION=true
HEBAT_ALLOW_AUTO_SUBMIT=false
```

Credential hanya boleh berada di `.env` lokal. Session browser dan file download diabaikan Git.

## Internal service authentication

```dotenv
MCP_API_KEY=generate-a-long-random-secret
WA_MCP_API_KEY=generate-the-same-secret
AI_API_KEY=another-long-random-secret
AI_API_AUTH_REQUIRED=true
AGENT_DEBUG_ENDPOINTS=false
SINGLE_OWNER_MODE=true
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
OWNER_ALLOWED_JIDS=
```

`MCP_API_KEY` dan `WA_MCP_API_KEY` harus sama. `AI_API_KEY` wajib dikirim oleh WA
engine dan CLI ke chat, reminder, dan debug API. Buat key acak, misalnya dengan
`openssl rand -hex 32`; jangan menggunakan password akun atau API key provider.

Untuk instalasi lokal, jalankan `uv run python scripts/configure_internal_auth.py`
dari `services/ai`. Script menambah konfigurasi yang belum ada, membuat key
internal secara kriptografis aman, tidak mencetak secret, dan tidak menimpa nilai
yang sudah terisi.

`ADMIN_JID` adalah identitas owner utama. `OWNER_ALLOWED_JIDS` hanya untuk alias
owner yang memang diperlukan, misalnya JID `@lid`; pisahkan dengan koma.

Startup menu WhatsApp dikendalikan dengan:

```dotenv
WA_STARTUP_MENU_ENABLED=true
WA_STARTUP_MENU_DELAY_MS=1500
```

Target selalu `ADMIN_JID`; LLM tidak dapat memilih penerimanya. Delay memberi
waktu singkat agar socket stabil setelah connection `open`. Nilai `false`
menonaktifkan menu tanpa memengaruhi approval atau notifikasi lain.

WA engine juga mencoba memetakan Baileys `@lid` ke phone JID sebelum request
masuk ke AI. Jika WhatsApp tidak menyediakan mapping, tambahkan alias `@lid`
owner secara eksplisit ke `OWNER_ALLOWED_JIDS`.

## Cyber Campus dan token nilai

```dotenv
CYBER_CAMPUS_ENABLED=false
CYBER_CAMPUS_BASE_URL=https://mahasiswa.unair.ac.id
CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat
CYBER_CAMPUS_BROWSER_HEADLESS=true
CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS=180
CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS=3
CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS=180
CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS=3
CYBER_CAMPUS_ENTRY_YEAR=0
```

Cyber Campus mengambil username/password langsung dari `HEBAT_USERNAME` dan
`HEBAT_PASSWORD` hanya saat login. CAPTCHA dikirim ke WhatsApp admin dan harus
dijawab manual. Owner dapat reply gambar dengan nilai, mengirim nilai tunggal
selama challenge aktif, atau memakai `/captcha <id> <jawaban>`. Token nilai juga
hanya diterima dari WhatsApp admin melalui challenge berumur pendek dan tidak
pernah dipersistenkan.

`CYBER_CAMPUS_ENTRY_YEAR` mengaktifkan alias seperti `/nilai semester 1`.
Nilai `0` membuat Xninetzy mencoba menurunkan tahun masuk dari format NIM UNAIR.
Target semester dipilih secara deterministik, tetapi dropdown portal baru diisi
setelah verified token diterima pada challenge yang sama.

## Replay safety dan backup

```dotenv
WA_PROCESSING_DIR=/app/data/wa-processing
WA_MESSAGE_LEASE_MS=120000
WA_MESSAGE_RETRY_DELAY_MS=30000
WA_MESSAGE_RETENTION=10000
BACKUP_DIR=/app/data/backups
BACKUP_RETENTION=14
```

WA engine menyimpan claim dan reply outbox agar pengiriman ulang event tidak
menjalankan LLM/tool yang sama. Direktori ini harus persisten dan hanya dapat
dibaca owner. Lihat [Backup dan restore](/docs/backup-restore/) untuk recovery.

## Scheduled Personal OS

```dotenv
OS_SCHEDULER_ENABLED=true
OS_SCHEDULER_STARTUP_DELAY_SECONDS=30
OS_NOTIFY_CHAT_ID=628xxxxxxxxxx@s.whatsapp.net
MORNING_BRIEFING_HOUR=7
EVENING_CHECKIN_HOUR=20
WEEKLY_REVIEW_WEEKDAY=6
WEEKLY_REVIEW_HOUR=20
HEBAT_PERIODIC_SYNC_ENABLED=false
```

Gunakan [Automation dan scheduled jobs](/docs/automation/) untuk memahami lease,
at-most-once delivery, ambiguous status, dan periodic HEBAT sync.

## MCP runtime path

Saat server MCP berjalan di host, path container perlu dipetakan ke data host:

```dotenv
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

Mode `auto` meng-resolve layout repository standar. Isi override hanya jika data berada di tempat lain.

## Coding runtime

```dotenv
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=opencode
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_EXECUTION_MODE=host_bridge
CODING_AGENT_HOST_BRIDGE_URL=http://host.docker.internal:8765
CODING_AGENT_HOST_BRIDGE_TOKEN=
CODING_AGENT_HOST_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_HOST_ALLOWED_ROOT=/absolute/path/to/xninetzy
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_SANDBOX=workspace-write
```

`/code` tidak menjalankan Codex, Claude Code, atau OpenCode di dalam container.
AI service mengirim task terautentikasi ke host bridge, lalu bridge menjalankan
CLI host pada workspace yang diizinkan dan mengembalikan output terbatas ke
WhatsApp. Token bridge harus sama di `.env` host dan container, tetapi tidak
pernah diteruskan ke subprocess coding.

Linux dapat mengaktifkan bridge saat login dan setelah reboot:

```bash
bash scripts/install_host_agent_bridge.sh
loginctl enable-linger "$USER"
systemctl --user status xninetzy-host-agent-bridge
curl -s http://127.0.0.1:8765/health
```

Untuk menjalankan sementara:

```bash
bash scripts/run_host_agent_bridge.sh
```

Bridge melakukan MCP preflight dari host. Jika konfigurasi `xninetzy` tidak
tersedia pada CLI yang dipilih, task dihentikan dan tidak dijalankan tanpa OS
access. Pilih runtime dari WhatsApp dengan `/agent use codex`,
`/agent use claude-code`, atau `/agent use opencode`, lalu jalankan `/code ...`.

## Validasi

```bash
docker compose config -q
cd services/ai && uv run python -c "from app.xninetzy.core.config import get_settings; print(get_settings().app_env)"
```

Jangan mencetak object settings lengkap karena dapat memuat secret.

The vault folder policy is shared by all interfaces. Use the Obsidian organization preview before applying a legacy migration.


<div data-localized-body data-locale="en">

## GraphRAG and Neo4j projection

```dotenv
GRAPHRAG_V3_ENABLED=false
NEO4J_ENABLED=false
NEO4J_AUTOSTART_ENABLED=true
NEO4J_AUTOSTART_COMMAND_TIMEOUT_SECONDS=8
NEO4J_AUTOSTART_READINESS_TIMEOUT_SECONDS=10
NEO4J_CONNECT_TIMEOUT_SECONDS=3
NEO4J_FAILURE_COOLDOWN_SECONDS=60
```

SQLite is the canonical source of truth. Neo4j and FAISS are rebuildable
projections and may be offline. When autostart fails, later requests do not
repeat Docker boot during the cooldown; retrieval falls back to SQLite/FAISS.
Enable NEO4J_ENABLED only when the graph compose profile is available.

</div>

<div data-locale="id" hidden>

## GraphRAG dan Neo4j projection

```dotenv
GRAPHRAG_V3_ENABLED=false
NEO4J_ENABLED=false
NEO4J_AUTOSTART_ENABLED=true
NEO4J_AUTOSTART_COMMAND_TIMEOUT_SECONDS=8
NEO4J_AUTOSTART_READINESS_TIMEOUT_SECONDS=10
NEO4J_CONNECT_TIMEOUT_SECONDS=3
NEO4J_FAILURE_COOLDOWN_SECONDS=60
```

SQLite adalah canonical source of truth. Neo4j dan FAISS hanya projection yang
boleh offline. Saat autostart gagal, request berikutnya tidak mengulang boot
Docker selama cooldown; retrieval turun ke SQLite/FAISS. Set NEO4J_ENABLED=true
hanya jika compose profile graph memang tersedia.
</div>
