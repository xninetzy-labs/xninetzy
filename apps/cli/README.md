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
