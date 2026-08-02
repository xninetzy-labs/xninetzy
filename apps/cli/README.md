# Xninetzy CLI

Dark fullscreen terminal client untuk Xninetzy AI.

## Current UI

- Full terminal TUI
- Dark/deep-space background
- Xninetzy ASCII header
- Full-width chat area
- Full-width input area
- White text
- Purple logo/border accent
- Orange node/event horizon accent
- Live chat ke endpoint FastAPI `/api/chat`
- Mendukung pasted block sebagai konteks pesan
- Timeout dan error state yang terlihat di status bar

## Run

```bash
yarn dev
```

## Build

```bash
yarn build
yarn start
```

## Link Command

```bash
yarn link
xninetzy
```

## Configuration

Run configuration commands from the repository host. The command manages the
same root `.env` consumed by Docker, the AI service, WhatsApp, and the terminal
client.

```bash
xninetzy config list
xninetzy config get LLM_DEFAULT_PROVIDER
xninetzy config set LLM_DEFAULT_PROVIDER flaz
xninetzy config set FLAZ_API_KEY
xninetzy config validate
```

Use `--stdin` for automation and `--env-file path/to/.env` for another local
installation. Secret values use a no-echo prompt, remain redacted in command
output, and are never printed by `get` or `list`.
## Setup and diagnostics

```bash
xninetzy setup --provider ollama --model qwen2.5:7b --deployment native --no-prompt
xninetzy setup --provider flaz --model deepseek-v4-pro --deployment docker
xninetzy doctor
xninetzy doctor --docker --services
xninetzy doctor --mcp
```

`setup` asks for provider secrets with a no-echo prompt when required. `doctor`
is read-only by default; Docker, local service, and coding-runtime MCP probes
require explicit flags. Both deployment profiles keep `XNINETZY_AI_URL` on
`127.0.0.1` for the host CLI. Docker Compose changes its internal CLI target to
`http://ai:8000` and its AI MCP mode to `container` only inside the container.
The root `.env` must use `MCP_RUNTIME_MODE=auto` or `host` so Codex, Claude
Code, and OpenCode can use the shared host MCP server.


## Docker

Jalankan AI terlebih dahulu, lalu buka CLI interaktif:

```bash
docker compose --profile tools run --rm cli
```

Smoke test non-interaktif:

```bash
printf 'Balas hanya CLI_OK\n' | docker compose --profile tools run --rm -T cli
```

## Inputs

```txt
halo
/help
/clear
```
