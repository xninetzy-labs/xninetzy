# Xninetzy CLI

Terminal UI mock untuk Xninetzy.

## Development

```bash
cd apps/cli
yarn install
yarn dev
```

## Build

```bash
yarn build
yarn start
```

## Link command

```bash
yarn link
xninetzy
```

## Docker Compose

```bash
docker compose --profile tools run --rm cli
```

The Compose service reads the root `.env` through `env_file: .env`.
The local command also searches upward for the repo root `.env` and loads it for future AI/API connection settings.

## Current MVP

- OpenCode-like TUI
- Xninetzy cosmic purple theme
- Local mock chat
- Root `.env` config loader
- No AI/API call yet

Input:

```txt
halo
```

Response:

```txt
hei yoi this is xninetzy
```

Compatibility alias:

```bash
chat
```
