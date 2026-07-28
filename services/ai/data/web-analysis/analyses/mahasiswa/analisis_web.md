# Analisis Web: Cybercampus Mahasiswa UNAIR

- URL: https://mahasiswa.unair.ac.id
- Terakhir dianalisis: 2026-07-21T01:51:55.087876+00:00
- Status auth: human_verification_required
- Versi skema: v1
- Catatan privasi: file ini hanya memuat struktur; data akademik owner disimpan terpisah dan terenkripsi.

## Modul Terdeteksi

### login
- Path: `/`
- Klasifikasi: contains_action
- Selector: `table`, `form`
- Field names: `captcha`, `csrf_token`, `mode`, `password`, `username`
- Structure hash: `49a6ff2a0bee70771e85f292bfc66a177bcf51e9313dc1df2b86332c9fcc6bf4`

## Endpoint Read-only Terdeteksi
- GET `/` (200)

## Flag Perlindungan (DO NOT AUTOMATE)
- Submit KRS adalah aksi kompetitif dan dilindungi human verification. Sistem hanya boleh membaca status slot dan mengirim notifikasi; klik/submit tetap manual.

## Catatan Login
- Session hanya berasal dari login manual owner dan disimpan terenkripsi untuk local profile.
- Credential, cookie, token, query value, dan isi data akademik tidak ditulis ke analisis_web.md.
- Saat human verification terdeteksi, crawl dihentikan tanpa solve atau retry otomatis.
