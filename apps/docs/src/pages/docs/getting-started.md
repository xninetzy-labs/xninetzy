---
layout: ../../layouts/DocsLayout.astro
title: Quick start
description: Instalasi satu perintah untuk Linux, macOS, dan Windows hingga chat WhatsApp pertama.
section: Mulai
---

Jalur Docker menjalankan AI service dan WA engine secara konsisten melalui
bridge network Compose. Port hanya dipublikasikan ke loopback host, sehingga
konfigurasi yang sama bekerja di Linux, macOS, Windows, dan WSL2.

## Prasyarat

- Linux: Docker Engine dan Docker Compose plugin.
- macOS: Docker Desktop.
- Windows 10/11: Docker Desktop dengan WSL2 backend atau PowerShell 7.
- Git. Installer Unix juga memerlukan OpenSSL.
- Flaz API key atau credential provider LLM lain.
- Absolute path menuju Obsidian vault.
- Akun WhatsApp yang dapat ditautkan sebagai linked device.

Untuk development lokal, gunakan Python 3.11+, `uv`, Node.js 22.12+, Yarn 1.22, Chromium Playwright, dan Tesseract untuk OCR.

## Instalasi satu perintah

Linux, macOS, atau WSL2:

```bash
curl -fsSL https://raw.githubusercontent.com/misbahul45/xninetzy/main/scripts/install.sh | bash
```

Windows PowerShell:

```powershell
irm https://raw.githubusercontent.com/misbahul45/xninetzy/main/scripts/install.ps1 | iex
```

Installer akan clone atau memakai checkout aktif, membuat `.env`, meminta vault,
nomor WhatsApp admin, dan Flaz API key, menghasilkan key internal secara acak,
menjalankan validasi Compose, lalu membangun dan menyalakan service. API key
dibaca tanpa echo dan tidak dicetak. Setelah selesai, ikuti log WA untuk scan QR.

Audit isi script dari GitHub sebelum memakai pola pipe-to-shell pada mesin yang
tidak sepenuhnya Anda kontrol. Jalur manual berikut memberikan hasil yang sama.

## Dukungan platform

| Platform | Runtime | Startup otomatis |
|---|---|---|
| Linux | Docker Engine + Compose | Aktifkan service Docker melalui systemd |
| macOS | Docker Desktop | Aktifkan “Start Docker Desktop when you sign in” |
| Windows | Docker Desktop + WSL2 | Aktifkan “Start Docker Desktop when you sign in” |
| WSL2 | Docker Desktop integration | Mengikuti startup Docker Desktop Windows |

Volume vault memakai absolute path native platform. Jangan memakai path network
yang belum dibagikan ke Docker Desktop.

## 1. Siapkan environment secara manual

Dari root repository:

```bash
cp .env.example .env
chmod 600 .env
```

Jangan menaruh password, token, cookie, atau API key asli di `.env.example`.

## 2. Masukkan Flaz API key dengan aman

```bash
cd services/ai
uv run python scripts/configure_flaz.py
cd ../..
```

Script memakai prompt `getpass`, tidak mencetak key, menulis `.env` secara atomik, dan menjaga permission `600`.

Konfigurasi default:

```dotenv
LLM_DEFAULT_PROVIDER=flaz
LLM_ENABLED_PROVIDERS=flaz
FLAZ_BASE_URL=https://ai.flaz.id/v1
FLAZ_MODEL=deepseek-v4-pro
```

Lengkapi autentikasi internal tanpa menampilkan secret:

```bash
cd services/ai
uv run python scripts/configure_internal_auth.py
cd ../..
```

## 3. Hubungkan data host

Cari identitas user host:

```bash
id -u
id -g
```

Isi `.env`:

```dotenv
HOST_UID=1000
HOST_GID=1000
OBSIDIAN_VAULT_HOST_PATH=/absolute/path/to/obsidian-vault
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net
ADMIN_NAMES=your_name
APP_TIMEZONE=Asia/Jakarta
WA_STARTUP_MENU_ENABLED=true
WA_STARTUP_MENU_DELAY_MS=1500
```

`OBSIDIAN_VAULT_HOST_PATH` harus absolute. Compose menolak start ketika nilainya kosong.

## 4. Pilih login WhatsApp

QR mode:

```dotenv
WA_LOGIN_MODE=qr
```

Atau pairing code:

```dotenv
WA_LOGIN_MODE=pairing_code
WA_PHONE_NUMBER=628xxxxxxxxxx
```

Nomor memakai kode negara tanpa `+`, spasi, atau tanda baca.

## 5. Jalankan service

```bash
docker compose config -q
docker compose up --build -d ai wa-enggine
docker compose ps
docker compose logs -f wa-enggine
```

Selesaikan QR atau pairing melalui **WhatsApp → Linked devices**.

Setelah koneksi pertama berstatus `open`, admin menerima lima kartu menu berisi
15 tombol command. Menu hanya dikirim sekali untuk setiap process launch, bukan
setiap reconnect. Jika button tidak didukung, sistem mengirim fallback teks.

## Startup otomatis saat laptop boot atau login

Pada Linux dengan systemd:

```bash
sudo systemctl enable --now docker
systemctl is-enabled docker
systemctl is-active docker
```

Compose menetapkan `restart: unless-stopped` untuk AI dan WA engine. Setelah
container dibuat, keduanya kembali hidup bersama Docker saat laptop boot. Hindari
`docker compose down` apabila container harus tetap terdaftar untuk startup
otomatis.

Pada macOS dan Windows, buka Docker Desktop → Settings → General, lalu aktifkan
startup saat login. Pada WSL2, pastikan integration distro aktif. Container akan
dipulihkan oleh Docker Desktop dengan policy yang sama.

## 6. Verifikasi health

```bash
curl -s http://127.0.0.1:8000/health
curl -s http://127.0.0.1:8081/health
```

AI service seharusnya mengembalikan:

```json
{"status":"ok","service":"xninetzy-ai"}
```

Health WA menampilkan status socket serta koneksi WhatsApp.

## 7. Coba dari WhatsApp

```text
/helper
buat roadmap belajar machine learning 14 hari
ingatkan aku besok jam 08.00 untuk review tugas
simpan ringkasan percakapan ini ke Obsidian
```

## Development lokal

AI service:

```bash
cd services/ai
uv sync
uv run playwright install chromium
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

WA engine di terminal kedua:

```bash
cd services/wa-enggine
yarn install --frozen-lockfile
yarn dev
```

Jangan jalankan instance Docker dan lokal bersamaan pada port atau akun WhatsApp yang sama.
