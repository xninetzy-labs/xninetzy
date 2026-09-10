# Design: Session Lifecycle Probe untuk Portal Akademik (Cyber Campus + UACC)

- **Tanggal:** 2026-08-24
- **Status:** Draft — menunggu review owner
- **Scope:** `services/ai/app/xninetzy/os/academic/mahasiswa_portal/` dan `os/web_analysis/`
- **Keputusan terkait:** OCR/auto-solve CAPTCHA ditolak (CAPTCHA bypass termasuk daftar
  Prohibited pada skill `xninetzy-academic-safety`, invariant AGENTS.md, dan
  `agent/prompts.py`). Desain ini mencapai tujuan yang sama — login minim friksi —
  tanpa menyentuh batas tersebut.

## 1. Latar belakang dan masalah

Kondisi saat ini:

- `SessionManager` menyimpan `storage_state` Playwright terenkripsi (Fernet) dengan
  metadata `saved_at` dan `age_seconds`.
- `session_watchdog.py` menjalankan loop background yang hanya mengecek **umur file**
  session. Session bisa mati di sisi server padahal file "fresh", atau masih hidup
  padahal dianggap stale.
- Tidak ada keep-alive: cookie SSO meng-expire setelah beberapa jam idle, sehingga
  owner harus login ulang berkala.
- Saat session mati, owner harus aktif mengetik `/cyber-login` atau `/uacc-login`
  sebelum CAPTCHA dikirim.

Akibatnya owner sering diminta login ulang meskipun sistem sudah punya mekanisme
session tersimpan.

## 2. Tujuan dan non-tujuan

### Tujuan

1. Validasi **live**: watchdog memeriksa apakah session benar-benar masih hidup di
   sisi portal, bukan sekadar umur file.
2. **Keep-alive**: ping GET ringan berkala agar cookie idle tidak expired, sehingga
   session bertahan selama service berjalan.
3. **Auto-kirim CAPTCHA**: ketika session terdeteksi mati, challenge login dimulai
   otomatis dan gambar CAPTCHA dikirim ke WhatsApp owner. Owner hanya menjawab
   CAPTCHA secara manual — tidak ada langkah `/cyber-login` intermediat.

### Non-tujuan

- Menyelesaikan, menebak, atau melakukan prefill jawaban CAPTCHA oleh mesin (OCR
  maupun metode lain). Jawaban CAPTCHA selalu dari manusia owner.
- Mengubah flow login manual yang sudah ada (`portal_login_start`,
  `uacc_login_start`, submit captcha).
- Membuat loop background kedua; watchdog existing tetap satu-satunya scheduler.
- Retry otomatis atas aksi non-idempotent ke portal.

## 3. Keputusan desain

| Keputusan | Pilihan | Alasan |
|---|---|---|
| Cara validasi sesi | Live check via HTTP GET dengan cookie tersimpan | Paling akurat; httpx sudah jadi dependency |
| Keep-alive | Ya, probe berkala sekaligus menjadi aktivitas perpanjangan | Menghilangkan penyebab utama login ulang |
| Respons saat sesi mati | Auto-mulai challenge + kirim CAPTCHA ke WA owner | Satu langkah lebih sedikit bagi owner; preseden `krs_watcher._request_login_captcha` |
| Pendekatan arsitektur | Perluas watchdog + modul prober baru (Opsi A) | Satu loop, reuse maksimal, YAGNI |

## 4. Arsitektur

### 4.1 Komponen baru

**`os/academic/mahasiswa_portal/session_prober.py`**

```python
@dataclass(frozen=True)
class ProbeResult:
    status: str          # "alive" | "dead" | "error"
    http_status: int | None
    final_url: str | None
    detected_at: datetime
    detail: str          # pesan singkat untuk log/status, tanpa nilai cookie

async def probe_site(site_slug: str) -> ProbeResult: ...
async def confirm_alive(site_slug: str, response_cookies) -> None: ...
```

Perilaku `probe_site`:

1. Muat `storage_state` via `SessionManager`; ekstrak cookies ke
   `httpx.AsyncClient`. Jika tidak ada session → caller menangani (jalur missing).
2. GET URL probe = `site.base_url` + `site.session_probe_path` (path halaman yang
   hanya dapat diakses saat login).
3. Keputusan:
   - Konten cocok `looks_like_login(html, url)` → `dead`.
   - Redirect keluar origin (`is_allowed_url` gagal pada URL akhir) → `dead`,
     log level warning.
   - Selain itu → `alive`.
4. Timeout `ACADEMIC_SESSION_PROBE_TIMEOUT_SECONDS` (default 15), ukuran respons
   dibatasi, error jaringan/timeout/5xx → `error` (tidak pernah `dead`).

Perilaku `confirm_alive`:

- Gabungkan cookie dari respons probe ke envelope session, tulis field
  `last_confirmed_alive_at`, naikkan envelope ke `schema_version: 2`.
- Pembacaan envelope v1 tetap didukung (field opsional).

### 4.2 Modifikasi komponen existing

| File | Perubahan |
|---|---|
| `session_watchdog.py` | Tambah tahap live-probe dalam `run_session_watchdog`; auto-challenge saat `dead`; notifikasi degraded saat K error berturut-turut |
| `mahasiswa_portal/tools.py` | Helper bersama `request_owner_login_challenge(site_slug)`: resolve owner via `admin_jid()` + `normalize_whatsapp_jid` (pola `krs_watcher`), `LOGIN_COORDINATOR.start(owner_id, site_slug)`, lalu delivery memakai `_deliver_captcha` yang sudah ada di file yang sama |
| `krs_watcher.py` | `_request_login_captcha` diganti pemanggilan helper bersama `request_owner_login_challenge` (paritas domain behavior) |
| `os/web_analysis/session_manager.py` | Envelope `schema_version: 2` + field opsional `last_confirmed_alive_at`; `session_info` mengekspos field tersebut |
| `os/web_analysis/sites.py` | Field opsional `session_probe_path` per situs |
| `core/config.py` + `.env.example` | Setting baru (lihat Bagian 6) |
| `tools.py` (`portal_info`, `portal_session_status`) | Tampilkan waktu & hasil probe terakhir |

### 4.3 Alur data watchdog

```
watchdog tick (tiap ACADEMIC_SESSION_PROBE_INTERVAL_SECONDS)
└─ untuk tiap situs aktif (mahasiswa, uacc):
     file session ada?
       ├─ TIDAK → notifikasi "missing" (cooldown existing)
       └─ YA → probe_site()
            ├─ alive → confirm_alive(): simpan cookie baru +
            │           last_confirmed_alive_at → selesai (keep-alive)
            ├─ dead  → dalam cooldown auto-challenge?
            │           ├─ ya → skip
            │           └─ tidak → request_owner_login_challenge(site)
            │                       → kirim PNG CAPTCHA ke WA owner
            │                       → gagal kirim? cancel challenge,
            │                         fallback notifikasi teks
            └─ error → hitung error berturut-turut;
                        < K → log saja
                        ≥ K → notifikasi "degraded" sekali (cooldown sendiri),
                              reset saat probe sukses/error berubah status
```

## 5. Safety

- **GET-only.** Probe tidak pernah POST, tidak mengisi form, tidak men-submit apa pun.
- **Origin enforcement.** URL permintaan dan URL akhir redirect wajib lolos
  `is_allowed_url`.
- **Tanpa kredensial.** Probe hanya membawa cookie tersimpan; username/password tidak
  disentuh jalur probe.
- **Bound.** Timeout 15 detik default; ukuran respons dibatasi; satu GET per situs
  per interval (~48 req/hari/situs pada default 30 menit).
- **Batas CAPTCHA tetap utuh.** Auto-challenge hanya membuat challenge dan mengirim
  gambar ke chat owner sendiri. Tidak ada pengisian/pengiriman jawaban oleh mesin.
  Ini setara dengan perilaku `krs_watcher` yang sudah direview dan diterima.
- **Anti-spam.** Tiga cooldown independen: notifikasi existing
  (`ACADEMIC_SESSION_WATCHDOG_NOTIFY_COOLDOWN_HOURS`), auto-challenge
  (`ACADEMIC_SESSION_AUTO_CHALLENGE_COOLDOWN_HOURS`, default 1 jam), dan notifikasi
  degraded (memakai cooldown notifikasi existing).
- **Fail-closed.** `SessionEncryptionUnavailable` → watchdog idle seperti sekarang.
- **Higiene log.** Hanya `site_slug`, status, dan URL; nilai cookie tidak pernah
  masuk log.

## 6. Konfigurasi baru (`config.py` + `.env.example`, tanpa secret)

| Setting | Default | Batas |
|---|---|---|
| `ACADEMIC_SESSION_PROBE_INTERVAL_SECONDS` | `1800` | min `300` |
| `ACADEMIC_SESSION_PROBE_TIMEOUT_SECONDS` | `15` | min `5`, max `60` |
| `ACADEMIC_SESSION_AUTO_CHALLENGE_COOLDOWN_HOURS` | `1` | min `0.25` |
| `ACADEMIC_SESSION_PROBE_ERROR_THRESHOLD` | `3` | min `1` |

## 7. Error handling

| Kondisi | Perlakuan |
|---|---|
| Network error / timeout / 5xx | `status=error`; tidak pernah disimpulkan `dead` (mencegah siklus logout palsu) |
| Error ≥ K berturut-turut | Notifikasi degraded sekali per periode cooldown; counter reset saat status berubah |
| Redirect ke origin asing | `dead` + log warning (anomali) |
| Gagal memulai challenge | Cleanup challenge, fallback notifikasi teks |
| `WaToolError` saat kirim CAPTCHA | Cancel challenge dulu, lalu fallback notifikasi (pola existing `krs_watcher`) |
| Exception di loop watchdog | Sudah tertangani + dilog struktur existing; tidak berubah |

## 8. Testing

1. **Unit `session_prober`** (transport httpx di-mock):
   - alive / dead / redirect keluar origin / error jaringan;
   - `confirm_alive` menggabungkan cookie dan menulis `last_confirmed_alive_at`;
   - envelope v1 dibaca benar oleh kode v2.
2. **Unit orkestrasi watchdog** (prober + coordinator di-mock):
   - alive → `confirm_alive` terpanggil, tanpa notifikasi;
   - dead → challenge terkirim tepat sekali; tick berikutnya dalam cooldown di-skip;
   - error 1× diam; error ≥ K → degraded notify sekali;
   - missing session → notifikasi missing (perilaku existing).
3. **Paritas helper**: `krs_watcher` memakai helper bersama yang sama.
4. **Verifikasi repo**: `uv run ruff check app tests` lalu `uv run pytest` penuh di
   `services/ai`.

## 9. Kriteria selesai

- Watchdog memutuskan berdasarkan hasil live probe, bukan umur file semata.
- Session yang aktif dipakai tidak lagi memicu permintaan login ulang palsu.
- Session mati memicu CAPTCHA di WhatsApp owner tanpa perintah manual, dengan
  cooldown anti-spam.
- Tidak ada kode yang membaca/menebak/mengisi jawaban CAPTCHA.
- Semua test lulus dan `.env.example` memuat setting baru tanpa secret.
