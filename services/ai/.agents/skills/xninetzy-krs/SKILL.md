---
name: xninetzy-krs
description: Plan, validate, prepare, and safely commit KRS selections using curriculum, roster, prerequisites, conflicts, credit limits, and explicit confirmation.
metadata:
  owner: xninetzy
  version: "1.1.0"
---

# KRS

## Inputs

Retrieve:

* curriculum;
* completed courses;
* failed or repeated courses;
* prerequisites;
* offered classes;
* roster;
* schedule;
* credit limit;
* capacity when available;
* user goals;
* class preferences.

## Candidate generation

Produce:

1. safest candidate;
2. preferred candidate;
3. fallback candidate.

Show:

* total credits;
* conflicts;
* prerequisites;
* class choices;
* trade-offs;
* uncertainty.

## Deterministic validation

Return errors such as:

* `PREREQUISITE_MISSING`
* `TIME_CONFLICT`
* `CREDIT_LIMIT_EXCEEDED`
* `DUPLICATE_COURSE`
* `CLASS_NOT_OFFERED`
* `PORTAL_STATE_CHANGED`
* `CAPACITY_UNKNOWN`
* `CAPACITY_FULL`

## Commit

1. show exact added and removed diff;
2. require explicit confirmation;
3. bind confirmation to exact diff;
4. commit once;
5. re-read KRS;
6. compare actual and expected;
7. store receipt.

Never silently choose replacement classes.

## KRS War (auto-commit)

Operasi otomatis terverifikasi (mahasiswa.unair.ac.id, semester Ganjil 2026/2027):

### Komponen

* `krs_war.py` — plan parsing, take/upgrade, status; plan diambil dari Obsidian `Akademik/KRS_Plan_Semester_5.md` (frontmatter `war_mode: armed`, tabel MK target dengan kelas goal).
* `krs_watcher.py` — polling tiap interval; memanggil `run_krs_war_if_armed` hanya saat `in_window` (pengumuman berisi hari ini atau `kprs_opened`).
* State internal: tabel `krs_war_state` (armed, plan_hash, last_status), `krs_war_actions` (jejak aksi), `krs_war_calibration`, `krs_watcher_state`.

### Endpoint portal (hanya POST form-urlencoded, relatif dari halaman)

* `proses/_akademik-krs_ditambah.php` — `aksi=tampil` (penawaran); `aksi=input&kelas=<id_kelas>&id_kur_mk=<id_kur>&sid=<sid>` (ambil).
* `proses/_akademik-krs_dilihat.php` — `aksi=tampil` (MK terambil: kode, nama, sks, kelas, status).
* `proses/_akademik-krs_hapus.php` — `aksi=tampil` (MK terambil + tombol hapus `krstambah_hapus(<pengambilan_mk>)`); `aksi=hapus&pengambilan_mk=<id>` (hapus).

### Aturan teknis (dari observasi live)

* JANGAN eksekusi via `page.evaluate` memanggil fungsi jQuery (`krstambah_kirim`/`krshapus_kirim` pakai `$.ajax`; `$` undefined di main world). Pakai fetch relatif di dalam page setelah `goto akademik-krs.php`, dengan `sid` yang diambil dari HTML halaman (regex `&sid=([a-z0-9]+)`).
* Respons server: `Proses berhasil`, `MK sudah ada` (duplikat ditolak — tidak bisa test-take), `Jadwal tabrakan dengan kode mata kuliah <X>`, `Mta tidak ditawarkan`, `hapus berhasil`.
* Penawaran menyembunyikan MK yang sudah diambil user; MK muncul kembali setelah dihapus. Kelas goal MK terambil hanya terlihat setelah drop → pola upgrade: hapus kelas lama → refresh penawaran → ambil kelas goal, atau ambil balik kelas lama jika goal penuh. Jangan pernah membiarkan MK kosong.
* `pengambilan_mk` ID berubah setiap hapus-ambil ulang → selalu ambil fresh dari `krs_hapus.php?aksi=tampil`, jangan hardcode.
* Status war: `done` hanya saat semua MK plan terambil sesuai goal; selain itu `partial` → dicoba lagi tiap interval. Upgrade per MK diberi cooldown (krs_war_actions) agar tidak drop berulang.
* BAE112 (Bahasa Inggris II): kelas `BCDLITS1`/`BCDLITS2` = Jumat jam 05 (hindari mendekati sholat Jumat); `BCDLITS3`–`BCDLITS6` = Selasa jam 07 (aman). Regex kelas yang valid: `^(?:I\d|BCDLITS\d+)$`.
* Verifikasi: selalu re-read `_akademik-krs_dilihat.php?aksi=tampil` setelah aksi; jejak di `krs_war_actions` dan log `System/Logs/krs-war.md`.
* Kode tambahan untuk war ditulis tanpa komentar (instruksi owner).
