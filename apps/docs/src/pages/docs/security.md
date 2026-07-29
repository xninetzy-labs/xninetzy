---
layout: ../../layouts/DocsLayout.astro
title: Keamanan dan hardening
description: Checklist secret, network, identity, filesystem, HEBAT, WhatsApp, MCP, dan coding runtime.
section: Operasional
---

Xninetzy memproses data personal dan dapat menjalankan aksi eksternal. Default ditujukan untuk mesin milik satu user, bukan public multi-tenant deployment.

## Checklist minimum

- [ ] `.env` permission `600` dan diabaikan Git.
- [ ] Secret tidak berada di README, docs, screenshot, atau chat log.
- [ ] `MCP_API_KEY` dan `WA_MCP_API_KEY` terisi serta sama.
- [ ] `AI_API_KEY` terisi dan `AI_API_AUTH_REQUIRED=true`.
- [ ] `AGENT_DEBUG_ENDPOINTS=false`.
- [ ] Port `8000` dan `8081` tidak terbuka ke internet.
- [ ] `ADMIN_JID` eksplisit; display name bukan satu-satunya identity.
- [ ] `OBSIDIAN_ALLOW_DELETE=false`.
- [ ] `HEBAT_ALLOW_AUTO_SUBMIT=false` dan confirmation aktif.
- [ ] Coding runtime admin-only dengan allowed root sempit.
- [ ] Vault dan database memiliki backup yang pernah diuji restore.
- [ ] Secret yang pernah terekspos sudah dirotasi.

## Secret management

Gunakan `.env` lokal dan input tersembunyi:

```bash
cp .env.example .env
chmod 600 .env
cd services/ai && uv run python scripts/configure_flaz.py
```

Jangan menambahkan API key ke MCP config global. Server MCP menjalankan project dan membaca environment yang sama.

## Network boundary

`/api/chat`, reminder API, dan debug route memakai bearer `AI_API_KEY`. Dengan
`AI_API_AUTH_REQUIRED=true`, service menolak request saat key server belum
dikonfigurasi. Health check tetap publik. Authentication aplikasi tidak
menggantikan firewall: bind ke loopback/private network dan gunakan VPN atau
reverse proxy dengan TLS untuk akses lintas host.

Docker Compose memakai host networking. Firewall host adalah bagian dari security model.

## WhatsApp identity

Gunakan JID lengkap:

```dotenv
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
```

Display name dapat berubah atau dipalsukan. Group trigger sebaiknya tidak memproses semua pesan.

Dalam `SINGLE_OWNER_MODE=true`, `/api/chat` juga memeriksa `sender_id` terhadap
`ADMIN_JID` dan `OWNER_ALLOWED_JIDS`. Header yang valid tidak membuat caller
menjadi owner; keduanya adalah boundary yang berbeda.

## Filesystem dan Obsidian

- Semua tool path relatif terhadap vault.
- Traversal dan absolute path ditolak.
- Delete disabled secara default.
- Backup-before-write bukan backup system penuh.
- Gunakan [backup dan restore](/docs/backup-restore/) untuk SQLite/FAISS, serta
  backup terpisah untuk vault.
- Samakan UID/GID, jangan gunakan permission `777`.

## HEBAT

Browser session setara dengan authenticated credential. Lindungi browser profile, cookie, screenshot debug, dan download materi. Submission harus selalu direview oleh pemilik.

## MCP global

Global config memberi setiap project pada client tersebut akses ke tool personal Xninetzy. Konsekuensinya:

- review prompt dari repository tidak dipercaya;
- pertahankan approval policy client;
- jangan mengizinkan tool write secara otomatis tanpa memahami scope;
- hapus/disable MCP pada mesin bersama;
- perbarui path setelah repository dipindah.

Codex, Claude, dan OpenCode memiliki policy approval berbeda. Global availability bukan global authorization untuk setiap aksi.

## Coding runtime

Coding agent memiliki risiko tertinggi. Gunakan:

```dotenv
CODING_AGENT_ADMIN_ONLY=true
CODING_AGENT_ALLOWED_ROOT=/absolute/path/to/single-workspace
CODING_AGENT_SANDBOX=workspace-write
CODING_AGENT_TIMEOUT_SECONDS=600
```

Jangan mount home directory, SSH keys, cloud credentials, atau Docker socket ke service tanpa kebutuhan dan threat review.

## Data yang tidak boleh masuk Git

- `.env` dan credential;
- SQLite, WAL, SHM;
- FAISS runtime index jika berisi data personal;
- browser profile/storage state;
- session Baileys;
- media WhatsApp;
- course downloads dan submission files;
- audit output yang memuat prompt sensitif.

Seluruh `services/ai/data/**` bersifat privat per instalasi dan di-ignore, kecuali
README kebijakan. Menghapus data dari branch terbaru tidak membersihkan Git
history; lakukan rotasi serta sanitasi history sebelum publikasi bila pernah
ter-push.

## Incident response sederhana

Jika secret terekspos:

1. revoke/rotate di provider;
2. hentikan service terkait;
3. hapus dari working tree dan history jika pernah commit;
4. invalidasi WhatsApp/HEBAT session bila relevan;
5. audit log serta recent action;
6. restart dengan secret baru;
7. dokumentasikan root cause tanpa menyalin secret.
