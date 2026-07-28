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
- MCP stdio menyediakan 22 tool vault, knowledge, task, dan reminder.
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

Tool yang tersedia:

- Obsidian: list, search, read, create, append, update section, todos, backlinks, headings, tags, dan frontmatter.
- Knowledge: search, answer context, list sources, dan ingest text.
- Tasks: list, today, capture, dan complete.
- Reminders: list, create, dan cancel.

`coding_agent_run` sengaja tidak diekspos ke MCP. Codex/Claude/OpenCode sudah merupakan coding agent; mengekspos `/code` kepada mereka akan membuat recursion dan memperluas dampak eksekusi.

### Codex

Konfigurasi project ada di `.codex/config.toml`:

```toml
[mcp_servers.xninetzy]
command = "uv"
args = ["run", "--directory", "services/ai", "python", "-m", "app.xninetzy.interfaces.mcp_server"]
cwd = "."
startup_timeout_sec = 30
tool_timeout_sec = 120
```

Verifikasi dari root repository:

```bash
codex mcp list
```

Dokumentasi resmi: [Codex MCP](https://developers.openai.com/codex/mcp/), [Codex non-interactive mode](https://developers.openai.com/codex/non-interactive/), dan [Codex SDK](https://developers.openai.com/codex/sdk/).

### Claude Code

Konfigurasi project ada di `.mcp.json`. Claude Code akan menemukan server saat dijalankan dari repository ini.

```bash
claude mcp list
```

Dokumentasi resmi: [Claude Code MCP](https://code.claude.com/docs/en/mcp) dan [Claude Code CLI usage](https://code.claude.com/docs/en/cli-usage).

### OpenCode

Konfigurasi project ada di `opencode.json` pada key `mcp.xninetzy`. Konfigurasi ini hanya mendaftarkan MCP; provider/model OpenCode tetap bebas dikelola oleh pengguna OpenCode.

Dokumentasi resmi: [OpenCode MCP servers](https://opencode.ai/docs/mcp-servers), [OpenCode providers](https://opencode.ai/docs/providers), dan [OpenCode server](https://opencode.ai/docs/server/).

## Docker

Ada dua mode yang disarankan:

1. Chat provider di Docker, coding agent tetap nonaktif. Ini mode default dan paling sederhana.
2. AI service dijalankan di host untuk memakai login CLI host, sedangkan WA engine tetap di Docker/host sesuai kebutuhan.

Jangan mount seluruh home directory ke container hanya untuk mengambil session CLI. Jika coding agent harus berada dalam container, buat image khusus, install binary tertentu, mount credential seminimal mungkin, dan pertahankan `CODING_AGENT_ALLOWED_ROOT` pada satu workspace.

Jika Ollama berjalan di host dan service AI memakai `network_mode: host`, gunakan base URL host yang sesuai. Pada konfigurasi Docker bridge, `127.0.0.1` merujuk ke container sendiri.

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
