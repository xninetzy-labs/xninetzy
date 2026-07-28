# Analisis Web: HEBAT (Moodle UNAIR)

- URL: https://hebat.elearning.unair.ac.id
- Terakhir dianalisis: 2026-07-21T01:51:41.275990+00:00
- Status auth: auth_required
- Versi skema: v1
- Catatan privasi: file ini hanya memuat struktur; data akademik owner disimpan terpisah dan terenkripsi.

## Modul Terdeteksi

### page_structure
- Path: `/hebat-v2/`
- Klasifikasi: read_only
- Selector: `nav`, `main`
- Field names: -
- Structure hash: `358b53e156e9b9e1b06230db008af84f3de073c996b31b2f9a0071e37f389fdb`

### page_structure
- Path: `/hebat-v2/index.html`
- Klasifikasi: read_only
- Selector: -
- Field names: -
- Structure hash: `ca72d150247368ab9dd3ad6c9242f9897f1bd9f30ab4a394020ceb455a5a3881`

### login
- Path: `/login/`
- Klasifikasi: contains_action
- Selector: `form`, `[role='main']`, `[data-region]`
- Field names: `anchor`, `logintoken`, `password`, `username`
- Structure hash: `2c7c5d40f3b04331aa7638139eef428c25b75a39044f874243812468c3df1491`

### login
- Path: `/login/forgot_password.php`
- Klasifikasi: read_only
- Selector: -
- Field names: -
- Structure hash: `a5e4164da922df3a9339f6fa3e8ab66dd4bf1aa43b6c7656791a30735f0dc62c`

### page_structure
- Path: `/admin/tool/dataprivacy/summary.php`
- Klasifikasi: read_only
- Selector: `nav`, `[role='main']`, `[data-region]`
- Field names: -
- Structure hash: `9b01cf05a5de72ef05cce2e1f0f087b3da87bc5f2e4fe406e352cf1b69df9c31`

### login
- Path: `/login/index.php`
- Klasifikasi: contains_action
- Selector: `form`, `[role='main']`, `[data-region]`
- Field names: `anchor`, `logintoken`, `password`, `username`
- Structure hash: `322011cbb500fa3e1258c8114d2a435a268fc8f1ec9028510369cd589b6a1ce3`

## Endpoint Read-only Terdeteksi
- GET `/hebat-v2/` (200)
- GET `/hebat-v2/index.html` (404)
- GET `/login` (301)
- GET `/login/` (200)
- GET `/lib/ajax/service-nologin.php?args&info` (200)
- GET `/login/forgot_password.php` (200)
- GET `/admin/tool/dataprivacy/summary.php` (200)
- GET `/` (302)
- GET `/login/index.php` (200)

## Flag Perlindungan (DO NOT AUTOMATE)
- Tidak ada flag tambahan; semua aksi mutasi tetap dinonaktifkan oleh engine.

## Catatan Login
- Session hanya berasal dari login manual owner dan disimpan terenkripsi untuk local profile.
- Credential, cookie, token, query value, dan isi data akademik tidak ditulis ke analisis_web.md.
- Saat human verification terdeteksi, crawl dihentikan tanpa solve atau retry otomatis.
