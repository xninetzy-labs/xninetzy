# WA Enggine

WhatsApp worker untuk Xninetzy AI. Service ini mendukung dua mode login Baileys: QR dan pairing code.

## Session Path

Docker menyimpan session di container:

```txt
/app/sessions
```

Folder itu di-bind ke host:

```txt
services/wa-enggine/sessions
```

Local dev fallback juga memakai:

```txt
services/wa-enggine/sessions
```

Jangan jalankan Docker `wa-enggine` dan `yarn dev` bersamaan untuk akun WhatsApp yang sama karena keduanya bisa memakai session folder yang sama.

## QR Mode

Edit root `.env`:

```env
WA_LOGIN_MODE=qr
# WA_PHONE_NUMBER boleh tetap ada, akan diabaikan di QR mode
```

Reset session dan jalankan:

```bash
cd ~/code/xninetzy
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```

Expected log:

```txt
config_loaded loginMode=qr qrMode=true pairingMode=false
qr_login_required
qr_generated
```

## Pairing Code Mode

Edit root `.env`:

```env
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=6285869243845
```

Reset session dan jalankan:

```bash
cd ~/code/xninetzy
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```

Ambil code dari log:

```txt
pairing_code_generated
```

Masukkan di WhatsApp:

```txt
WhatsApp > Linked Devices > Link with phone number instead
```

## Local Dev

```bash
cd ~/code/xninetzy/services/wa-enggine
yarn dev
```

Local dev akan mencoba membaca root `.env` dan memakai fallback session `./sessions`.

## MCP Tool Server

WA engine juga menjalankan HTTP MCP-style tool server di proses yang sama dengan Baileys socket, karena hanya service ini yang punya akses langsung ke WhatsApp.

Default:

```env
MCP_SERVER_ENABLED=true
MCP_HOST=0.0.0.0
MCP_PORT=8081
MCP_API_KEY=
```

Endpoint:

```txt
GET  /health
GET  /mcp/tools
POST /mcp/call
```

Contoh call:

```bash
curl -X POST http://localhost:8081/mcp/call \
  -H "Content-Type: application/json" \
  -d '{
    "tool": "send_text_message",
    "input": {
      "jid": "628xxxxxxxxxx@s.whatsapp.net",
      "text": "Tes dari MCP"
    }
  }'
```

Jika `MCP_API_KEY` diisi, request ke `/mcp/tools` dan `/mcp/call` harus memakai salah satu header:

```txt
Authorization: Bearer <key>
x-api-key: <key>
```

Tool yang sudah tersedia mencakup kirim pesan/media, polling, kontak, profil, group metadata/member/admin/settings/invite, dan label internal. Tool `download_media`, `get_media_url`, dan memory tools sudah didaftarkan sebagai placeholder eksplisit karena butuh message store/media pipeline atau AI memory service.

## Reset Session

```bash
cd ~/code/xninetzy
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```
