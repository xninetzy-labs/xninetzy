# WhatsApp Media + Docker Repair Plan

## Objective

Menjalankan `ai` dan `wa-enggine` secara konsisten melalui Docker Compose,
memakai Flaz sebagai provider LLM OpenAI-compatible melalui HTTPS, dan membuat alur
attachment WhatsApp tahan restart untuk dokumen, gambar berteks, quoted media,
serta PDF hasil scan.

## Target Topology

```text
Flaz API (HTTPS)
        |
        v
Docker ai :8000 <---- Docker wa-enggine :8081 <---- WhatsApp
        |                         |
        +---- shared wa-media ----+
                  volume
```

Session Baileys disimpan dalam named volume `wa-session`. File media disimpan
lebih awal dalam named volume `wa-media`, sebelum request dikirim ke AI. Dengan
begitu pembacaan tidak bergantung pada cache RAM atau umur proses WA Engine.

## Repair Sequence

### Phase 1 — Configuration and secrets

1. Sanitasi `.env.example`: kosongkan API key, password, nomor telepon, JID, dan
   identitas personal.
2. Konfigurasikan `FLAZ_BASE_URL` dan `FLAZ_MODEL` secara eksplisit.
3. Simpan `FLAZ_API_KEY` hanya di `.env` lokal yang diabaikan Git.
4. Gunakan bridge network Compose untuk komunikasi internal AI, WA, dan CLI;
   publish port `8000` dan `8081` hanya ke loopback host.

### Phase 2 — Docker reliability

1. Tambahkan healthcheck AI dan WA Engine.
2. Mulai WA Engine setelah AI sehat.
3. Ganti bind mount session menjadi named volume `wa-session` agar ownership
   host tidak memblokir update credential.
4. Pertahankan `wa-media` sebagai shared named volume pada path identik
   `/app/data/wa-media`.
5. Jalankan client CLI melalui service DNS `ai` ketika profile `tools` dipakai.

### Phase 3 — Durable WhatsApp media

1. Download attachment relevan sebelum request AI.
2. Simpan file dan manifest secara atomik berdasarkan `chat_id/message_id`.
3. Saat MCP dipanggil, baca persistent manifest lebih dulu, cache RAM sebagai
   fallback kedua, lalu download dari WhatsApp jika dibutuhkan.
4. Terapkan batas ukuran dan validasi path.
5. Terapkan jalur yang sama untuk quoted document/image.

### Phase 4 — AI media understanding

1. Paksa attachment masuk route `agent` secara deterministik.
2. Pertahankan parser dokumen teks yang sudah ada.
3. Tambahkan OCR image untuk PNG/JPEG/WebP/TIFF/BMP.
4. Tambahkan OCR fallback untuk PDF scan tanpa text layer.
5. Tambahkan tool `media_read_image` dan dukungan image pada `/analyze-media`.
6. Jika OCR tidak menemukan teks, jawab jujur; jangan mengarang isi visual.

### Phase 5 — Verification

1. Unit test parser, quoted metadata, persistent store, readiness, dan routing.
2. Python lint + full pytest.
3. TypeScript typecheck/build/test.
4. Docker Compose config/build/up.
5. Smoke test health, AI chat, MCP readiness, document parser, dan image OCR.
6. Real WhatsApp E2E setelah user menyelesaikan pairing.

## Acceptance Criteria

- `docker compose up -d` menyalakan AI dan WA Engine tanpa permission error.
- AI dapat menghubungi Flaz API dan WA MCP melalui network Docker.
- `/health` AI sukses dan health WA membedakan process-ready dari socket-open.
- Attachment tersimpan persisten sebelum AI memproses pesan.
- Dokumen teks dan PDF teks dapat dibaca.
- Screenshot/gambar berteks serta PDF scan dapat dibaca lewat OCR.
- Quoted attachment tetap dapat dibaca setelah cache RAM kosong selama file
  persistent masih ada.
- Image tanpa teks menghasilkan respons keterbatasan yang eksplisit.
- `.env.example` tidak mengandung credential atau identitas personal aktif.

## Operational Gate

Koneksi WhatsApp nyata memerlukan satu tindakan manual: scan QR atau masukkan
pairing code. Sampai tindakan itu selesai, container tetap sehat sebagai proses,
namun `socket_ready` harus bernilai `false` dan tool yang butuh socket ditolak.

## Rollback

1. Hentikan stack dengan `docker compose down` tanpa `-v` agar named volume tidak
   terhapus.
2. Revert file source/config terkait repair.
3. Bind mount session lama dapat dipasang kembali jika memang memiliki credential
   yang valid; jangan menghapus volume/session tanpa backup dan persetujuan.
