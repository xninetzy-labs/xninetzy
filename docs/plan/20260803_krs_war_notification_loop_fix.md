# Incident 2026-08-03 — KRS War Notification Loop (WA Spam ke Admin)

Status: **resolved & verified**
Severity: high (spam 2 pesan WA/~12 detik, ±226 kiriman dalam 25 menit)
Detected: 2026-08-03 07:00–07:25 WIB (burst), fixed ±07:46 WIB

## Goal

Hentikan pengiriman pesan WhatsApp berulang tanpa henti ke admin saat window
KRS aktif, tanpa mengubah perilaku reminder/jadwal lain, dan tanpa mengganggu
fungsi KRS War itu sendiri (tetap mencoba mengambil slot kelas).

## Timeline (WIB)

| Waktu | Kejadian |
|---|---|
| 07:00–07:25 | Burst spam WA: pola ±2 pesan per ±12 detik (2 notifikasi per tick watcher) |
| 07:34 | Investigasi dimulai: scheduler reminders, os_jobs, prayer, echo loop disingkirkan |
| 07:35 | Reminder id 18 & 19 dihapus dari DB (sudah `cancelled`, tetap dihapus permanen per permintaan user) — backup dibuat sebelum hapus |
| 07:38–07:43 | Root cause ditemukan: `krs_war.py::run_krs_war_if_armed` memanggil `notify_admin` tanpa guard pada tiap tick; `krs_war_actions` 2313 → 2403 |
| 07:43 | Restart `docker compose restart ai` (masih kode lama: 12 pesan baru dalam 90 detik, 51→63) |
| 07:46 | Restart kedua (ai + wa-enggine) dengan kode fix aktif |
| 07:46–07:48+ | Verifikasi: `send_text_message` baru = **0** dalam pengamatan 2+ menit; `krs_war_actions` 2553 |

## Root cause

`run_krs_war_if_armed` dieksekusi **setiap tick** watcher KRS
(`KRS_WATCHER_WINDOW_INTERVAL_SECONDS=10`) selama window KRS (03–08 Agu).
Setiap eksekusi memanggil, tanpa guard:

- `notify_admin("krs_war_started")`
- `notify_admin("krs_war_taken")`

Karena status war tetap `partial` ("target not found" ×11, session Cyber Campus
kedaluwarsa), short-circuit `already_run` tidak pernah aktif → loop mengirim
notifikasi selamanya. Bukti: 2553 baris `krs_war_actions` (run_done berulang
tiap ±10 detik), `send_text_message` naik 51→63→226.

Bukan penyebab (semua disingkirkan dengan bukti): reminder scheduler (store
idempotent, semua reminder lama `failed`), os_jobs/prayer (tidak disentuh),
echo loop (`message_flow_skipped` 268, bukan pemicu), cron/timer/worker ganda
(satu proses uvicorn per container).

## Fix (applied)

File: `services/ai/app/xninetzy/os/academic/mahasiswa_portal/krs_war.py`

```python
first_run_for_window = state["last_run_window"] != window_key
```

- `krs_war_started` → hanya bila `first_run_for_window` (sekali per window)
- `krs_war_taken` → hanya bila `first_run_for_window or state["last_status"] != status`
- `krs_war_error` (2 tempat) → hanya bila `first_run_for_window or state["last_status"] != "error"`

Prinsip: **notifikasi transisi status, bukan per eksekusi.** Idempotensi
dipindah ke level notifikasi (state-driven), bukan level run.

## Verification

- `uv run ruff check .../krs_war.py` → pass
- `uv run pytest tests/os/academic/test_krs_war.py -q` → 21 passed (13.51s)
- Restart: `docker compose restart ai` → `xninetzy-ai-1`, `xninetzy-wa-enggine-1` Up
- Kode baru aktif via volume mount `./:/app/xninetzy` (tanpa rebuild)
- Pasca-restart 2+ menit: `docker logs wa-enggine | grep send_text_message` baru = 0
- Loop KRS war internal masih berjalan (desain: war armed menunggu slot kelas
  I1) tapi **diam** — tidak ada notifikasi baru

## Data cleanup

- `DELETE FROM reminders WHERE id IN (18,19) AND remind_at LIKE '2026-08-03%'` → 2 rows
- Backup: `/tmp/opencode/xninetzy.sqlite3.bak-20260803-073536` (3.350.528 bytes)
- Sisa reminder 03 Agu: tidak ada; tidak ada reminder pending/processing/sent tersisa

## Open item (opsional)

Loop `partial` (taken=0, already_taken=0, skipped=11, target not found=11)
kemungkinan karena session Cyber Campus kedaluwarsa
(`krs_watcher_state.session_expired_notified=1`). Untuk menghentikan loop
teknis: login ulang via `/cyber-login` atau disarm KRS War sementara.

## Guard rules (pelajaran)

1. Notifikasi eksternal harus **transisi-state-driven**, bukan per-eksekusi loop.
2. Semua event notifikasi perlu idempotency key / dedupe window.
3. Loop periodik dengan side effect eksternal wajib punya short-circuit status.
