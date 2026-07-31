---
layout: ../../layouts/DocsLayout.astro
title: Cyber Campus dan token nilai
description: Login headless dengan CAPTCHA manual, session terenkripsi, dan verifikasi melalui WhatsApp admin.
section: Learning OS
---

Integrasi Cyber Campus dibangun sebagai adapter akademik terpisah dari HEBAT.
HEBAT menangani course dan materi Moodle; Cyber Campus menangani data akademik,
nilai, jadwal, dan rencana KRS.

## Status saat ini

- Credential provider memakai `HEBAT_USERNAME` dan `HEBAT_PASSWORD` secara
  in-memory tanpa menyalinnya ke SQLite atau MCP.
- `/cyber-login` membuka browser Chromium headless dan mengisi credential.
- Gambar CAPTCHA dikirim ke `ADMIN_JID` WhatsApp.
- Reply image dengan nilai, nilai tunggal selama challenge aktif, atau
  `/captcha <challenge-id> <jawaban>` menyelesaikan login secara manual.
- Salah ketik `/catchpa` dinormalisasi sebelum request mencapai AI.
- Challenge memiliki TTL, owner binding, dan batas percobaan.
- Session berhasil disimpan melalui encrypted session manager.
- Authenticated crawler memprioritaskan struktur KRS, KPRS, nilai, jadwal, dan
  draft akademik, termasuk menu yang berada di frame.
- `/jadwal` membaca jadwal real-time secara deterministik dari session owner.
- `/cyber-profile` membaca hanya nama, NIM, fakultas, dan program studi.
- `/status-akademik` membaca riwayat status akademik per semester.
- `/krs status` membaca mata kuliah, kelas, status, dan total SKS aktif tanpa
  mengubah portal.
- `/nilai` membuka halaman KHS agar Cyber Campus mengirim token melalui akun
  Telegram yang terdaftar pada portal, lalu mengirim challenge balasan ke
  WhatsApp admin.
- Reply token diteruskan langsung ke reader KHS tanpa LLM, MCP, persistence,
  Telegram Bot Token, atau Telegram Engine milik Xninetzy.
- KRS write/final submit belum diaktifkan sampai bound approval dan selector
  portal memiliki fixture serta test yang memadai.

## Alur login

```text
/cyber-login di WhatsApp admin
  -> Chromium headless membuka portal
  -> credential HEBAT diisi dari secret lokal
  -> CAPTCHA di-screenshot
  -> image dikirim ke ADMIN_JID
  -> owner membalas image/nilai langsung atau /captcha <id> <jawaban>
  -> halaman divalidasi
  -> session terenkripsi disimpan
```

Agent tidak menjalankan OCR untuk CAPTCHA, tidak menebak jawaban, dan tidak
mencoba melewati challenge. Jika challenge salah atau kedaluwarsa, owner menerima
CAPTCHA baru atau memulai ulang login.

Nilai tunggal hanya diubah menjadi command selama challenge aktif dan hanya jika
sender sama dengan `ADMIN_JID`. JID WhatsApp dinormalisasi agar suffix perangkat
Baileys seperti `:7@s.whatsapp.net` tetap terikat ke owner yang benar.

Setelah session tersedia, jalankan:

```text
/portal-nav
/krs-capabilities
/web-refresh mahasiswa
/web-analysis mahasiswa
/portalinfo
/cyber-profile
/status-akademik
/krs status
/jadwal
/nilai
```

Kemampuan read-only ini berada di shared Cyber Campus adapter. WhatsApp memakai
slash command langsung, natural chat memakai LangGraph, sedangkan Codex, Claude
Code, dan OpenCode memakai tool MCP `portal_profile`,
`portal_academic_status`, `portal_current_krs`, dan `portal_schedule`. Semua
interface membaca struktur dan session yang sama. Profil dibatasi ke empat field
akademik; data biodata lain tidak dikembalikan atau disimpan.

Untuk site `mahasiswa`, `/web-refresh` otomatis memakai encrypted owner session.
Crawler hanya meneruskan GET/HEAD, memblokir request mutasi, menolak URL submit,
logout, delete, dan query sensitif, lalu menyimpan struktur tanpa nilai field,
credential, cookie, token, atau data akademik terlihat.

## Struktur KRS yang sudah diverifikasi

Audit read-only terhadap portal aktif menemukan halaman berikut:

```text
/modul/mhs/akademik-krs.php
/modul/mhs/akademik-kprs.php
/modul/mhs/akademik-khs.php
/modul/mhs/akademik-transkrip.php
/modul/mhs/akademik-jadwal.php
/modul/mhs/akademik-draft.php
```

Halaman KRS memiliki tahap **Penawaran MK**, **MK Lintas Rumpun**,
**MK Terambil**, dan **Cetak KRS**. Pada saat periode KRS tidak aktif, portal
tidak menampilkan form atau checkbox pilihan. Xninetzy hanya melaporkan status
tersebut; ia tidak mencoba memanggil endpoint POST internal.

Pembacaan `MK Terambil` memakai endpoint tampilan fixed dengan payload
`aksi=tampil`, lalu memvalidasi header enam kolom sebelum membentuk model typed.
Status akademik juga divalidasi terhadap header portal. Jika struktur berubah,
reader gagal secara eksplisit dan tidak menebak posisi kolom.

Implementasi write KRS belum aktif. Target workflow adalah: baca penawaran dan
status akademik, susun plan tanpa mutasi, minta approval WhatsApp untuk perubahan,
validasi ulang portal, terapkan pilihan, lalu minta approval final yang berbeda.

`/portal-nav` membaca anchor dan handler menu di seluruh frame, menyimpan hanya
label/path same-origin, lalu menandai setiap item sebagai `read_only`,
`krs_guarded`, atau `blocked_write`. `/krs-capabilities` membaca form, control,
tab, target internal, dan menghasilkan structure hash baru setiap kali DOM atau
JavaScript portal berubah. Raw script tidak masuk prompt dan tidak dijalankan
sebagai kode dari LLM.

## Konfirmasi dan media

Semua confirmation, approval KRS, upload, dan verifikasi dikirim ke WhatsApp
admin. WA engine mendukung tombol Approve/Reject serta fallback command teks.
Image dan document dari chat asal dapat diteruskan ke admin melalui durable media
store; tool tidak menerima file path bebas dari LLM.

## Token nilai melalui WhatsApp

Token nilai hanya diterima dari `ADMIN_JID` WhatsApp. Input terikat ke challenge
berumur pendek, tidak melewati LLM, tidak disimpan, dan hanya dapat digunakan
untuk satu percobaan pembacaan nilai.

Cyber Campus sendiri menyatakan bahwa token KHS dikirim ke akun Telegram yang
terdaftar pada portal. Itu adalah kanal resmi milik Cyber Campus, bukan integrasi
Telegram Xninetzy. Project tidak membutuhkan `TELEGRAM_BOT_TOKEN`. Setelah token
resmi diterima, owner meneruskannya dengan membalas prompt WhatsApp admin.

## Urutan wajib pembacaan KHS

Cyber Campus memvalidasi verified token terhadap urutan interaksi halaman.
Karena itu, Xninetzy menjalankan tahapan berikut secara berurutan pada satu
browser page yang sama:

```text
1. Buka halaman KHS
2. Tunggu verified token terbaru
3. Isi field token
4. Pilih dropdown semester
5. Ambil dan parse tabel KHS
```

Jangan memilih semester sebelum token diisi. Melakukannya akan memanggil handler
KHS dengan token kosong dan token berikutnya dapat ditolak portal. Pemilihan
`/nilai semester 1` hanya mengikat target periode ke challenge; dropdown tetap
bernilai default sampai owner mengirim token.

Kirim `/nilai` untuk semester terbaru, `/nilai semester 1` untuk semester kuliah
pertama, atau `/nilai <kode-periode>` untuk periode tertentu. Setelah halaman
terbuka, reply pesan **Verified Token Cyber Campus** dengan token angka. Reader
baru mengisi token dan mengatur dropdown semester setelah balasan token masuk.
Prompt selalu menampilkan label semester yang akan dipilih.
Alternatif eksplisitnya adalah `/grade-token <challenge-id> <token>`.
Command privat ini tidak masuk registry dan tidak diekspos ke Codex, Claude Code,
OpenCode, atau LangGraph. MCP hanya dapat memulai `portal_grades`, sedangkan token
tetap harus datang dari WhatsApp admin.
Selain balasan WhatsApp admin, client MCP/CLI yang terautentikasi sebagai owner
lokal dapat mengirim token lewat tool `portal_grade_token_submit`; token tidak
pernah disimpan atau ditulis ke log.

Browser KHS tetap hidup selama challenge agar pembukaan halaman kedua tidak
mengganti token portal. Urutannya adalah: buka halaman, tunggu token, isi token,
baru atur nilai dropdown, lalu jalankan `fetch` same-origin ke endpoint tampilan
KHS. Alur ini tidak bergantung pada jQuery halaman.

Jadwal nyata yang diverifikasi pada 29 Juli 2026 menghasilkan 10 mata ajar untuk
Semester Genap 2025/2026. Nilai hanya dinyatakan berhasil setelah token aktif
menghasilkan tabel KHS; token salah atau kedaluwarsa tidak menghasilkan klaim.

## Snapshot dan perubahan nilai

Pembacaan KHS yang berhasil dinormalisasi menjadi identitas mata kuliah, kode,
SKS, nilai, dan field sumbernya. Xninetzy menghitung hash isi sebelum menyimpan
snapshot ke SQLite lokal. Hasil yang identik bersifat replay-safe dan tidak
membuat snapshot duplikat.

```text
/nilai changes
/nilai perubahan
```

Kedua command membandingkan dua snapshot berbeda terakhir pada periode yang
sama. Perubahan diklasifikasikan sebagai mata kuliah baru, nilai berubah, atau
mata kuliah hilang dari snapshot. Snapshot pertama menjadi baseline dan tidak
dianggap sebagai perubahan. Codex, Claude Code, OpenCode, dan LangGraph memakai
tool bersama `portal_grade_changes` melalui registry dan MCP yang sama.

Verified token tidak disimpan bersama snapshot. Database hanya berada pada
instalasi owner dan tetap diabaikan Git.

## Konfigurasi

```dotenv
CYBER_CAMPUS_ENABLED=true
CYBER_CAMPUS_BASE_URL=https://mahasiswa.unair.ac.id
CYBER_CAMPUS_CREDENTIAL_SOURCE=hebat
CYBER_CAMPUS_BROWSER_HEADLESS=true
CYBER_CAMPUS_LOGIN_CHALLENGE_TTL_SECONDS=180
CYBER_CAMPUS_LOGIN_MAX_ATTEMPTS=3
WEB_ANALYSIS_ENCRYPTION_KEY=
WEB_ANALYSIS_AUTHENTICATED_CRAWL_ENABLED=true
ADMIN_JID=628xxxxxxxxxx@s.whatsapp.net

CYBER_CAMPUS_GRADE_TOKEN_TTL_SECONDS=180
CYBER_CAMPUS_GRADE_TOKEN_MAX_ATTEMPTS=3
CYBER_CAMPUS_ENTRY_YEAR=0
```

`CYBER_CAMPUS_ENTRY_YEAR` dipakai untuk alias `semester 1`, `semester 2`, dan
seterusnya. Nilai `0` mencoba membaca tahun angkatan dari format NIM UNAIR;
instalasi dengan format akun berbeda harus mengisinya secara eksplisit.

Jangan aktifkan Cyber Campus sebelum encryption key dan admin JID tersedia.

Setup aman untuk instalasi lokal:

```bash
cd services/ai
uv run python scripts/configure_internal_auth.py --enable-cyber-campus
```

Script memvalidasi credential HEBAT serta `ADMIN_JID`, membuat Fernet key jika
belum ada, mengaktifkan authenticated crawl GET/HEAD-only, dan tidak mencetak
secret.
