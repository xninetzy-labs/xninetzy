# Provider LLM, Coding Agent, dan MCP Xninetzy

Dokumen ini menjelaskan dua jenis pilihan AI yang berbeda dan cara menghubungkan Xninetzy ke Codex, Claude Code, serta OpenCode.

## Konsep

Xninetzy sekarang memiliki dua jalur yang independen:

```text
Pesan WhatsApp / CLI
├── Chat LLM provider
│   ├── Flaz (default)
│   ├── OpenAI
│   ├── Anthropic
│   ├── OpenRouter
│   ├── Ollama
│   └── OpenAI-compatible custom endpoint
│
└── Coding-agent runtime (opsional, command /code)
    ├── Codex CLI
    ├── Claude Code CLI
    └── OpenCode CLI

Codex / Claude Code / OpenCode
└── Xninetzy MCP stdio
    ├── Obsidian vault
    ├── Knowledge base
    ├── Tasks
    └── Reminders
```

`Chat LLM provider` menjawab chat dan menjalankan ReAct tools Xninetzy. `Coding-agent runtime` adalah proses CLI lokal yang dapat membaca atau mengubah repository. Mengganti provider chat tidak otomatis mengganti model milik Codex/Claude Code/OpenCode; masing-masing CLI tetap memakai autentikasi dan konfigurasi modelnya sendiri.

## Status implementasi

- Registry provider dan allowlist model sudah aktif.
- Pilihan provider/model disimpan per pengguna di SQLite, tanpa menyimpan API key.
- Pilihan diteruskan ke orchestrator, direct response, dan ReAct agent.
- Adapter subprocess tersedia untuk Codex, Claude Code, dan OpenCode.
- Setiap coding run memiliki audit row di `coding_agent_runs`.
- MCP stdio mengekspos seluruh tool dari registry Xninetzy.
- Konfigurasi project tersedia untuk Codex, Claude Code, dan OpenCode.

## Menyiapkan provider chat

Credential hanya boleh berada di `.env` milik deployment. Jangan mengirim API key melalui WhatsApp dan jangan menyimpan key per pengguna di database.

Flaz sebagai default:

```env
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
LLM_TIMEOUT_SECONDS=120
LLM_MAX_RETRIES=2

FLAZ_API_KEY=secret-lokal
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
FLAZ_MODELS=deepseek-v4-pro
```

Contoh mengaktifkan beberapa provider:

```env
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz,openai,anthropic,openrouter,ollama,generic

OPENAI_API_KEY=
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_MODEL=
OPENAI_MODELS=

ANTHROPIC_API_KEY=
ANTHROPIC_MODEL=
ANTHROPIC_MODELS=

OPENROUTER_API_KEY=
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=
OPENROUTER_MODELS=

OLLAMA_BASE_URL=http://127.0.0.1:11434/v1
OLLAMA_MODEL=
OLLAMA_MODELS=

GENERIC_OPENAI_API_KEY=
GENERIC_OPENAI_BASE_URL=
GENERIC_OPENAI_MODEL=
GENERIC_OPENAI_MODELS=
```

Isi `*_MODEL` dengan model default dan `*_MODELS` dengan daftar model yang boleh dipilih, dipisahkan koma. Provider baru dianggap siap jika provider masuk `LLM_ENABLED_PROVIDERS`, model tersedia, base URL tersedia untuk provider compatible, dan credential wajib sudah terisi.

Command pengguna:

```text
/llm
/llm list
/llm use flaz deepseek-v4-pro
/llm use openrouter provider/model
```

`/llm list` tidak pernah menampilkan nilai API key. Database hanya menyimpan `user_id`, `chat_provider`, `chat_model`, `coding_agent`, dan waktu pembaruan.

## Menyiapkan coding-agent runtime

Coding agent dinonaktifkan secara default karena ia dapat mengubah file. Jalankan service AI langsung di host jika binary dan autentikasi CLI berada di host. Container Docker standar tidak otomatis memiliki binary atau session login host.

```env
CODING_AGENT_ENABLED=true
CODING_AGENT_DEFAULT=codex
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/xninetzy
CODING_AGENT_WORKSPACE=/absolute/path/to/xninetzy
CODING_AGENT_TIMEOUT_SECONDS=600
CODING_AGENT_MAX_OUTPUT_CHARS=12000
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_REQUIRE_XNINETZY_MCP=true
CODING_AGENT_MCP_SERVER_NAME=xninetzy
CODING_AGENT_MCP_PREFLIGHT_TIMEOUT_SECONDS=15
CODING_AGENT_ENV_ALLOWLIST=PATH,HOME,USER,LOGNAME,LANG,LC_ALL,TERM,TMPDIR,XDG_CONFIG_HOME,XDG_DATA_HOME,XDG_CACHE_HOME,SSL_CERT_FILE,SSL_CERT_DIR,CODEX_HOME

CODEX_BIN=codex
CODEX_MODEL=
CLAUDE_CODE_BIN=claude
CLAUDE_CODE_MODEL=
OPENCODE_BIN=opencode
OPENCODE_MODEL=
```

Pastikan `ADMIN_JID` atau `ADMIN_NAMES` benar. Jika `CODING_AGENT_ADMIN_ONLY=true`, hanya admin utama yang dapat menjalankan `/code`.

Command pengguna:

```text
/agent
/agent list
/agent use codex
/agent use claude-code
/agent use opencode
/code perbaiki test provider lalu jalankan test terkait
```

Kebijakan runtime:

- Subprocess dibuat tanpa shell, sehingga task tidak dieksekusi sebagai shell interpolation.
- Subprocess menerima environment minimal dari `CODING_AGENT_ENV_ALLOWLIST`; credential Flaz, WhatsApp, HEBAT, dan provider chat tidak diwariskan secara default.
- Workspace di-resolve dan harus berada di bawah `CODING_AGENT_ALLOWED_ROOT`.
- Codex memakai `--sandbox workspace-write` dan session ephemeral.
- Claude Code memakai mode noninteraktif `-p`, output JSON, session tanpa persistensi, dan `acceptEdits`.
- OpenCode memakai output JSON tanpa `--auto`; kebijakan izin OpenCode tetap berlaku.
- Tidak ada adapter yang memakai flag bypass permission berbahaya.
- Timeout, output cap, exit status, stderr, dan audit run diterapkan.

Model CLI dapat diatur lewat `CODEX_MODEL`, `CLAUDE_CODE_MODEL`, dan `OPENCODE_MODEL`. Jika kosong, CLI memakai konfigurasi/default miliknya sendiri.

## MCP Xninetzy

Entry point server:

```bash
uv run --directory services/ai python -m app.xninetzy.interfaces.mcp_server
```

Server memakai transport MCP `stdio`. Jangan menulis log aplikasi ke stdout ketika menjalankan server secara manual karena stdout digunakan untuk protocol frame.

Path runtime otomatis dibedakan:

- Di Docker, konfigurasi `/app/data` tetap digunakan.
- Di host, nilai `/app/data` otomatis dipetakan ke `services/ai/data`.
- Path host eksplisit yang sudah dikonfigurasi tidak akan ditimpa.

Konfigurasi opsional:

```env
MCP_RUNTIME_MODE=auto
MCP_HOST_DATA_DIR=
MCP_HOST_SQLITE_PATH=
```

Gunakan `MCP_RUNTIME_MODE=host` untuk memaksa host fallback atau
`MCP_RUNTIME_MODE=container` untuk mempertahankan path container. Jika field
host dikosongkan, database host default adalah
`services/ai/data/xninetzy.sqlite3`.

MCP mengambil katalog langsung dari `tools/registry.py`, sehingga penambahan tool
Xninetzy baru otomatis tersedia tanpa membuat wrapper MCP manual. Katalog mencakup
seluruh domain Xninetzy: Obsidian, knowledge, task, reminder, research, learning
roadmap, Graph RAG, media, workflow, rules, memory, provider AI, coding agent,
HEBAT, portal mahasiswa, dan tool pendukung lainnya.

MCP stdio mewakili owner lokal instalasi. `sender_id`, `sender_name`, `chat_id`,
`chat_type`, dan `metadata` diinjeksi server dan disembunyikan dari schema tool
dinamis. Client tidak boleh memakai parameter buatan sendiri untuk menyamar
sebagai chat atau pengguna lain. Override opsional tersedia melalui:

```env
MCP_PRINCIPAL_ID=
MCP_PRINCIPAL_NAME=
MCP_DEFAULT_CHAT_ID=
```

Nilai kosong memakai `ADMIN_JID`, `BOT_OWNER`, dan namespace owner lokal yang
stabil.

### Kontrak retrieval dan grounding

`knowledge_search` mengembalikan evidence bundle untuk inspeksi. Ia bukan jawaban
akhir. `knowledge_answer` menjalankan hybrid FAISS + FTS, reciprocal-rank fusion,
deduplikasi, pembatasan context, sintesis model, dan validasi sitasi `[K1]`.

LangGraph memakai kontrak yang sama untuk permintaan penjelasan knowledge,
akademik, dan IT learning yang relevan. Jika bukti internal tidak cukup, agent
harus menyatakannya dan tidak boleh membuat jawaban umum terlihat berasal dari
vault. Isi source diperlakukan sebagai data tidak tepercaya, bukan instruksi.

Connector HEBAT memakai konfigurasi credential dan session lokal yang sama dengan
service AI. Tool untuk status/login, sinkronisasi course dan activity, materi,
assignment, PDF, serta academic digest dapat dipanggil langsung oleh client MCP.
Aksi sensitif seperti upload submission tetap tunduk pada confirmation token,
approval, allowlist, dan guard yang sudah diterapkan pada tool Xninetzy.

Karena `coding_agent_run` juga merupakan tool Xninetzy, tool tersebut ikut
diekspos. Gunakan hanya jika memang ingin mendelegasikan pekerjaan ke runtime
coding lain; pembatasan workspace, admin, timeout, dan audit tetap berlaku.

### Akses HEBAT dan course

Credential HEBAT hanya disimpan pada `.env` lokal:

```env
HEBAT_USERNAME=
HEBAT_PASSWORD=
HEBAT_DATA_DIR=/app/data/hebat
HEBAT_DOWNLOAD_DIR=/app/data/hebat/downloads
```

Jangan menaruh nilai credential pada `.env.example`, dokumentasi, database,
atau pesan WhatsApp. MCP memakai session dan database yang sama dengan service
AI. Alur yang direkomendasikan:

1. `hebat_start_login(chat_id)` untuk membuat atau memperbarui session.
2. `hebat_sync_courses(chat_id)` untuk mengambil seluruh course melalui
   endpoint AJAX Moodle.
3. `hebat_sync_course_activities(chat_id, course_id)` untuk menyimpan resource,
   assignment, URL, dan activity lain.
4. `hebat_download_material(chat_id, activity_id_or_url)` untuk me-resolve
   activity ke `pluginfile.php` dan mengunduh file sebenarnya.
5. `hebat_read_pdf(file_path)` untuk membaca file PDF yang sudah ada.

Pada host, file hasil download disimpan di
`services/ai/data/hebat/downloads/<course-id>/<activity>/`. Output tool
menampilkan `Lokasi` absolut agar client dapat memverifikasi file fisik.
Upload submission tetap membutuhkan confirmation token dan guard admin.

Dari WhatsApp, gunakan bahasa natural seperti `login hebat`,
`sync course hebat`, `cek tugas hebat`, atau `/hebat`. Tool MCP yang sama
dapat dipanggil langsung oleh Codex, Claude Code, dan OpenCode.

### Permission host dan Docker

Service `ai` pada Docker Compose berjalan sebagai
`${HOST_UID:-1000}:${HOST_GID:-1000}`. Sesuaikan pada `.env` bila UID/GID
host berbeda:

```bash
id -u
id -g
```

Jika data lama sudah telanjur dimiliki root, perbaiki satu kali:

```bash
docker run --rm \
  -v "$PWD/services/ai/data:/data" \
  alpine:latest chown -R "$(id -u):$(id -g)" /data
```

Lakukan hal setara pada vault hanya jika folder vault lama memang root-owned.
Jangan menjalankan `chmod 777`; samakan ownership dengan user service.

### Coding agent melalui WhatsApp dan MCP

Aktifkan runtime pada environment service AI:

```env
CODING_AGENT_ENABLED=true
CODING_AGENT_ALLOWED=internal,codex,claude-code,opencode
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_WORKSPACE=/path/absolut/ke/xninetzy
CODING_AGENT_ALLOWED_ROOT=/path/absolut/ke/xninetzy
```

Command WhatsApp:

```text
/agent list
/agent use codex
/agent use claude-code
/agent use opencode
/code perbaiki test yang gagal
```

Command tersebut dirutekan ke `coding_agent_list`, `coding_agent_use`, dan
`coding_agent_run`; ketiganya juga tersedia melalui MCP Xninetzy. Setiap CLI
dijalankan dari workspace yang dibatasi. Konfigurasi MCP Xninetzy berada pada
scope global/user agar Codex, Claude Code, dan OpenCode dapat mengaksesnya dari
folder mana pun.

Sebelum subprocess coding dijalankan, Xninetzy melakukan preflight MCP:

- Codex: `codex mcp get xninetzy`;
- Claude Code: `claude mcp get xninetzy`;
- OpenCode: `opencode mcp list` dan verifikasi status server.

Jika server tidak ditemukan, belum disetujui, atau disconnected, `/code` gagal
dengan pesan konfigurasi dan tidak menjalankan runtime tanpa akses OS. Task yang
lolos preflight otomatis diberi kontrak untuk membaca `AGENTS.md`, memakai MCP
untuk state Xninetzy, dan memakai `knowledge_answer` untuk jawaban knowledge.

Binary serta autentikasi CLI harus tersedia pada environment tempat service AI
berjalan. Gunakan absolute path ke binary `uv` dan directory `services/ai` pada
semua global config. API key tidak perlu disalin ke konfigurasi MCP.

### Codex

Tambahkan konfigurasi user:

```bash
codex mcp add xninetzy -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy/services/ai \
  python -m app.xninetzy.interfaces.mcp_server
```

Lalu tambahkan timeout pada entry `~/.codex/config.toml`:

```toml
startup_timeout_sec = 30
tool_timeout_sec = 120
```

Verifikasi dari luar repository:

```bash
cd /tmp
codex mcp get xninetzy
codex mcp list
```

Dokumentasi resmi: [Codex MCP](https://developers.openai.com/codex/mcp/), [Codex non-interactive mode](https://developers.openai.com/codex/non-interactive/), dan [Codex SDK](https://developers.openai.com/codex/sdk/).

### Claude Code

Gunakan scope `user`:

```bash
claude mcp add --scope user xninetzy \
  -e PYTHONUNBUFFERED=1 -- \
  /home/you/.local/bin/uv run \
  --directory /home/you/code/xninetzy/services/ai \
  python -m app.xninetzy.interfaces.mcp_server

cd /tmp
claude mcp get xninetzy
claude mcp list
```

Output harus menunjukkan `Scope: User config` dan `Connected`.

Dokumentasi resmi: [Claude Code MCP](https://code.claude.com/docs/en/mcp) dan [Claude Code CLI usage](https://code.claude.com/docs/en/cli-usage).

### OpenCode

Tambahkan `mcp.xninetzy` pada `~/.config/opencode/opencode.jsonc`:

```json
{
  "mcp": {
    "xninetzy": {
      "type": "local",
      "command": [
        "/home/you/.local/bin/uv",
        "run",
        "--directory",
        "/home/you/code/xninetzy/services/ai",
        "python",
        "-m",
        "app.xninetzy.interfaces.mcp_server"
      ],
      "enabled": true,
      "timeout": 120000
    }
  }
}
```

Merge key tersebut tanpa menimpa config lain, lalu verifikasi:

```bash
cd /tmp
opencode mcp list
opencode debug config
```

Dokumentasi resmi: [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers), [OpenCode providers](https://opencode.ai/docs/providers), dan [OpenCode server](https://opencode.ai/docs/server/).

## Docker

Ada dua mode yang disarankan:

1. Chat provider di Docker, coding agent tetap nonaktif. Ini mode default dan paling sederhana.
2. AI service dijalankan di host untuk memakai login CLI host, sedangkan WA engine tetap di Docker/host sesuai kebutuhan.

Jangan mount seluruh home directory ke container hanya untuk mengambil session CLI. Jika coding agent harus berada dalam container, buat image khusus, install binary tertentu, mount credential seminimal mungkin, dan pertahankan `CODING_AGENT_ALLOWED_ROOT` pada satu workspace.

Jika Ollama berjalan di host, Compose memakai
`OLLAMA_DOCKER_BASE_URL=http://host.docker.internal:11434/v1`. Nama host itu
dipetakan melalui `host-gateway` di Linux dan tersedia melalui Docker Desktop di
macOS/Windows. `127.0.0.1` di dalam container merujuk ke container sendiri.

## Pengujian dan diagnosis

```bash
cd services/ai
uv run pytest -q tests/core/test_flaz_llm.py \
  tests/core/test_llm_providers.py \
  tests/core/test_coding_agents.py \
  tests/agent/test_ai_runtime_commands.py \
  tests/interfaces/test_mcp_server.py
```

Diagnosis umum:

- `Provider ... belum diaktifkan`: tambahkan nama ke `LLM_ENABLED_PROVIDERS`.
- `Provider ... belum siap`: isi env credential/base URL/model yang disebutkan.
- `Model ... tidak diizinkan`: tambahkan model ke `*_MODELS` lalu restart service.
- `Binary ... tidak ditemukan`: jalankan AI service pada environment yang memiliki CLI atau perbaiki `*_BIN`.
- `Workspace harus berada di dalam ...`: sesuaikan root dan workspace dengan path absolut yang benar.
- MCP tidak muncul: jalankan entry point secara manual, lalu cek konfigurasi dari root repository.
- Tool Obsidian gagal: cek `OBSIDIAN_VAULT_PATH`, volume mount, dan flag `OBSIDIAN_ALLOW_WRITE`.

## Rencana lanjutan

Implementasi saat ini menggunakan subprocess CLI karena menyatukan tiga runtime di bawah kontrak yang sama. Untuk deployment dengan concurrency tinggi, tahap berikutnya dapat memindahkan Codex ke Codex SDK/App Server, Claude ke Agent SDK, dan OpenCode ke server mode persisten. Kontrak `run_coding_agent` dan tabel audit sengaja dipisahkan agar migrasi tersebut tidak mengubah command pengguna.
