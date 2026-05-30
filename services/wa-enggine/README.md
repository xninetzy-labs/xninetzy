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

## Reset Session

```bash
cd ~/code/xninetzy
docker compose down
rm -rf services/wa-enggine/sessions
mkdir -p services/wa-enggine/sessions
docker compose up --build wa-enggine ai
```
