# Design Tool — Local Web Analysis Engine

## 1. Contract

Input analyzer hanya `site_slug`, opsi `authenticated`, dan `force`. Tidak ada
arbitrary URL. `site_slug` di-resolve oleh registry internal menjadi satu origin
HTTPS yang telah diizinkan.

Output analyzer:

```json
{
  "status": "completed|cache_fresh|human_verification_required|configuration_required|busy|failed",
  "site_slug": "hebat|mahasiswa",
  "analysis_path": "/app/data/web-analysis/analyses/.../analisis_web.md",
  "pages_analyzed": 1,
  "auth_status": "public|authenticated|auth_required|human_verification_required",
  "message": "safe status text"
}
```

Analyzer tidak mengembalikan HTML, cookie, token, response body, atau query value.

## 2. Crawl Algorithm

1. Resolve slug dari allowlist.
2. Jika cache belum stale dan `force=false`, return `cache_fresh`.
3. Ambil file lease atomic agar satu situs tidak dianalisis paralel.
4. Jika authenticated, load encrypted local-owner session. Missing key/session
   menghasilkan `configuration_required`; tidak ada auto-login.
5. Buat Playwright context.
6. Install route guard: `GET`/`HEAD` continue, method lain abort.
7. Buka seed URL dengan `goto`; tidak ada click/fill/submit.
8. Ekstrak selector/tag/field name dan bentuk `structure_hash`.
9. Jika CAPTCHA/human verification terlihat: simpan status, stop segera.
10. Jika login page terlihat pada authenticated run: set `auth_required`, stop;
    tidak ada retry credential.
11. Temukan link same-origin, tolak path mutating, batasi jumlah halaman.
12. Tulis structural JSON dan Markdown secara atomic dengan permission `0644` agar
    owner host dapat membacanya; encrypted session/snapshot tetap `0600`.

## 3. Sanitization

Yang boleh masuk `analisis_web.md`:

- nama modul generik (`schedule`, `grades`, `assignments`, dan sejenisnya);
- URL path tanpa origin lain;
- selector CSS yang memang ada;
- nama field form, tanpa value;
- endpoint GET/HEAD path;
- nama query non-sensitif, tanpa value;
- status HTTP/content type;
- structure hash dan timestamp.

Yang dilarang:

- HTML/body response;
- visible values seperti nama, NIM, mata kuliah, nilai, jadwal;
- cookie/storage state;
- credential, token, sesskey, auth code;
- query value;
- screenshot authenticated secara otomatis.

## 4. Local Session Flow

`WEB_ANALYSIS_PROFILE_ID` merepresentasikan satu owner lokal. Ia bukan user/tenant.

1. Owner membuat Fernet key satu kali dan menyimpannya di `.env` lokal.
2. Owner menjalankan CLI `login` pada host yang punya display.
3. Playwright hanya membuka login page.
4. Owner sendiri mengisi credential/CAPTCHA/OTP dan klik login.
5. Setelah owner menekan Enter di terminal, tool memeriksa:
   - final URL masih di origin target;
   - login form tidak lagi tampil;
   - human verification tidak lagi tampil.
6. `storage_state` dienkripsi, ditulis atomic dengan mode `0600`.

Jika key hilang, session tidak bisa dipulihkan. Tidak ada backdoor atau fallback
plaintext. Owner harus login manual lagi.

## 5. Structure Cache vs Personal Snapshot

```mermaid
flowchart LR
    HTML[Rendered page] --> STRUCT[Structure extractor]
    STRUCT --> SAFE[analysis.json + analisis_web.md]

    HTML --> COLLECT[Validated site-specific collector]
    COLLECT --> PERSONAL[Encrypted snapshot]
    PERSONAL --> TOOLS[/jadwal and agent context]
```

`Structure extractor` generic dapat berjalan sekarang. `Collector` harus spesifik
situs dan baru dibuat setelah manual authenticated inspection. Pemisahan ini
mencegah agent menganggap selector sebagai data jadwal.

Snapshot schema minimum:

```json
{
  "schema_version": 1,
  "module": "schedule",
  "captured_at": "ISO-8601",
  "items": [
    {"when": "normalized local time", "label": "course/activity", "source_path": "/safe/path"}
  ]
}
```

Source path tidak boleh berisi token/sesskey. Snapshot seluruhnya terenkripsi.

## 6. Background Job

Job berada di proses AI lokal, bukan cloud scheduler. Default:

- startup delay 15 detik;
- interval 360 menit;
- cache TTL 14 hari;
- public analysis saja;
- delay antar-page 2 detik;
- maksimum 10 halaman per run.

Karena cache TTL lebih panjang daripada interval, sebagian besar tick hanya membaca
metadata lokal dan return `cache_fresh` tanpa request ke situs.

Authenticated background tetap off sampai owner telah login manual dan memilih
menyalakannya. Satu install hanya memiliki satu local profile.

## 7. KRS Watcher Contract

Watcher masa depan hanya boleh:

1. GET halaman/status allowlisted;
2. parse jumlah/status slot;
3. bandingkan dengan snapshot sebelumnya;
4. kirim satu notifikasi saat state berubah;
5. sertakan deep link yang dibuka manual owner.

Watcher dilarang mengisi form, mengeklik tombol, mengirim POST/PUT/PATCH/DELETE,
menjalankan submit via GET, memecahkan CAPTCHA, mempercepat polling untuk kompetisi,
atau menyimpan credential.

## 8. Validation Gates sebelum Collector Live

- manual login berhasil dan encrypted file dapat dibaca ulang;
- structural cache tidak mengandung nilai credential/token/NIM;
- selector diverifikasi pada minimal dua load halaman;
- expired session menghasilkan `auth_required` tanpa auto-login;
- halaman CAPTCHA menghasilkan `human_verification_required`;
- parser dites dengan fixture HTML yang sudah disanitasi;
- snapshot terenkripsi dan `/jadwal` membaca snapshot, bukan structural Markdown;
- request log membuktikan tidak ada method mutating.
