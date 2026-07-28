# WhatsApp Media Ingestion

Status: documents, image OCR, scanned-PDF OCR, dan quoted media didukung. Audio dan video belum ditranskripsi.

## Tujuan

Pengguna dapat mengirim atau me-reply dokumen/gambar WhatsApp dengan pertanyaan. WA engine menyimpan attachment secara durable, AI mengekstrak teksnya, lalu agent menjawab berdasarkan isi file tersebut. Dokumen juga dapat dimasukkan ke knowledge base.

## Alur

```text
WhatsApp attachment atau reply ke attachment
 -> wa-enggine mengunduh media saat pesan masuk
 -> file + manifest disimpan di shared volume /app/data/wa-media
 -> payload AI membawa metadata media saat ini dan quoted media
 -> orchestrator merutekan attachment langsung ke agent
 -> agent memilih media_read_document atau media_read_image
 -> parser mengekstrak teks; PDF tanpa text layer memakai OCR
 -> hasil dicatat di tabel media_items
 -> agent menjawab dari teks hasil ekstraksi
 -> opsional: media_ingest_to_knowledge menyimpan dokumen ke knowledge base
```

MCP `download_media_message` tetap menjadi fallback ketika file belum ada di persistent media store. Media store diprioritaskan agar file tetap dapat dibaca setelah cache pesan hilang atau proses WA restart.

## Komponen

- `interfaces/media/document_parser.py`: PDF, TXT, Markdown, CSV, JSON, DOCX, XLSX, dan PPTX. PDF scan dirender per halaman lalu diproses Tesseract.
- `interfaces/media/image_parser.py`: OCR PNG, JPEG, WebP, TIFF, dan BMP dengan batas ukuran pixel.
- `interfaces/media/media_tools.py`:
  - `media_read_document(chat_id, message_id)`
  - `media_read_image(chat_id, message_id)`
  - `media_info(metadata)`
  - `analyze_media(chat_id, metadata)`
  - `media_ingest_to_knowledge(chat_id, message_id, title)`
- `wa-enggine/src/mcp/durable-media.ts`: penyimpanan file, manifest, validasi path, checksum, dan atomic write.
- `wa-enggine/src/mcp/media-store.ts`: download Baileys, validasi batas byte, dan durable storage.

## Perintah WhatsApp

- `/media-info`: menampilkan informasi current atau quoted attachment.
- `/analyze-media`: membaca dokumen atau menjalankan OCR gambar.
- Pesan natural dengan attachment juga otomatis diarahkan ke agent media.

## Konfigurasi

```env
WA_MEDIA_DIR=/app/data/wa-media
WA_MEDIA_MAX_BYTES=26214400
OCR_ENABLED=true
OCR_LANGUAGES=eng+ind
OCR_MAX_PDF_PAGES=20
OCR_MAX_IMAGE_PIXELS=25000000
```

Container AI dan WA harus memasang volume `wa-media` pada path yang sama. Docker image AI memasang Tesseract beserta language pack Inggris dan Indonesia.

## Batasan

- OCR mengekstrak teks, bukan memahami isi visual nonteks. Agent harus menjelaskan keterbatasan ini dan tidak menebak isi gambar.
- Audio dan video mengembalikan pesan unsupported yang eksplisit.
- File yang melebihi `WA_MEDIA_MAX_BYTES` ditolak sebelum diproses.
- Ingest file sensitif atau besar ke knowledge base tetap mengikuti kebijakan approval agent.

## Verifikasi

```bash
cd services/ai
uv run pytest -q tests/test_media_document_parser.py \
  tests/test_media_image_parser.py tests/test_media_command_router.py \
  tests/test_media_routing.py

cd ../wa-enggine
yarn build
yarn test
```
