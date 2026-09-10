---
# New Tool Plan — Scanned PDF Extraction v2 (OCR-first pipeline)

Status: planned  
Owner: Xninetzy OS knowledge pipeline  
Related: `services/ai/app/xninetzy/os/knowledge/extraction/`, `services/ai/app/xninetzy/os/knowledge/ingestion.py`, `services/ai/app/xninetzy/interfaces/media/image_parser.py`

## Problem statement

Scanned (image-only) PDFs cannot be extracted by the current pipeline. Real case:
`REV 4 Roster S1 Sistem Informasi Gasal 2026-2027.pdf` (22 pages, pure scan,
text-ratio 0) failed through every ingestion path:

- `document_ingest` → router marks `scanned` → `pdf_structured` + OCR attempt,
  but any exception falls back to `ingest_pdf` (pypdf only) which returns
  `"Could not extract text from PDF"`.
- `knowledge_ingest_file` → `ingest_pdf` → `hebat/pdf_reader.read_pdf_text`
  (pypdf only) → empty text → same error.
- `hebat_read_pdf` → pypdf only → same error.
- `document_tables` → pdfplumber only → 0 tables on a scan.

Result: the roster had to be transcribed manually by the owner (22 pages of
class schedules, rooms, and codes). This must not happen again.

## Root-cause analysis (from current code)

1. `router._pdf_probe` correctly detects `text_ratio < 1.0` as scanned and
   routes to `pdf_structured` with `use_ocr=True` when `OCR_ENABLED` and
   `DOC_IMAGE_OCR_ENABLED` are both true (defaults are true).
2. `images.ocr_pdf_pages` renders each page at fixed `scale=2` via pypdfium2
   and runs pytesseract with `OCR_LANGUAGES="eng+ind"`. Weak points:
   - No preprocessing (no deskew, no binarization, no contrast normalization)
     before OCR; low quality scans degrade sharply.
   - Fixed scale=2 is often too low for dense tables (roster grids).
   - Tesseract layout analysis is not used; table structure is lost, so the
     output is a flat text blob instead of rows/columns.
   - No per-page OCR confidence or word-level bounding boxes captured.
3. `extract_document` raising anywhere → `ingest_document` silently falls back
   to pypdf-only `ingest_pdf` → guaranteed empty for scans. The error message
   hides the real OCR failure.
4. `hebat/pdf_reader.py` and the `hebat_read_pdf` tool have no OCR path at all.
5. No diagnostics: no "OCR attempted / engine available / confidence" surfaced
   in tool responses, so failures look like "the PDF has no text".

## Goal

Make scanned PDF extraction actually work, deterministically and open-source:

- Scanned PDFs get OCR'd into page-tagged text AND table-structured blocks.
- Tables inside scans are reconstructed as Markdown tables (roster use case).
- Ingestion never silently degrades to a pypdf-only empty result when OCR is
  enabled: either OCR output is ingested or a truthful error is returned.
- The pipeline stays offline, deterministic, and free (no vision LLM as a hard
  dependency; tesseract / OCR engines remain the default).

## Design decisions

- Keep the router (simple vs complex) as the entry point; only upgrade the
  scanned branch and the OCR engine layer.
- Add a new extractor stage `ocr_tables` that combines:
  - render at adaptive scale (based on page DPI/size, minimum ~3x for dense
    tables);
  - optional preprocessing: grayscale, binarize (Otsu), deskew when detected;
  - tesseract TSV/`image_to_data` output with word boxes;
  - deterministic line/column clustering (projection profiles) to rebuild
    table rows/columns;
  - fallback to plain OCR text when structure recovery fails.
- Engine strategy: tesseract (installed via Dockerfile, already present) as
  the default; add an optional PaddleOCR/PaddleOCR-table or `ocr_translate`
  off switch behind a feature flag for better table recovery, still local.
- New tool surface (registry + MCP), versioned names, backward compatible:
  - `document_ocr_status` — engine availability, language packs, last OCR
    diagnostics (read-only).
  - `document_extract_ocr` — one-off OCR of a local PDF/image with structure
    recovery and a preview of recovered tables (no knowledge ingestion).
  - `document_ingest` gains `force_ocr` and `ocr_engine` parameters; it never
    returns `"Could not extract text from PDF"` when OCR produced non-empty
    text — instead it ingests the OCR output and records
    `manifest.ocr = {engine, pages, chars, tables}`.
- Keep the deterministic contract: no vision model required; provider-based
  vision remains an explicit opt-in, never a silent fallback.

## Scope

1. Preprocessing + adaptive render pipeline in `extraction/extractors/images.py`
   (deskew, binarize, adaptive scale, optional upscale for dense grids).
2. Word-box OCR (`pytesseract.image_to_data`) with a deterministic table
   reconstructor in a new module
   `extraction/extractors/ocr_tables.py`.
3. Router: scanned PDFs route to `pdf_structured` with `use_ocr=True` and
   `recover_tables=True`; propagate OCR metadata into the plan.
4. `ingest_document`/`ingest_pdf` error contract: no silent pypdf fallback when
   OCR is enabled; truthful status (`ocr_failed`, `ocr_empty`) with engine
   diagnostics; ingest OCR text when available.
5. `hebat/pdf_reader.py` + `hebat_read_pdf`: add OCR fallback for scanned PDFs
   using the same engine.
6. New tools `document_ocr_status`, `document_extract_ocr` registered in the
   shared tool registry (`tools/registry.py`) and exposed through MCP + agent.
7. Diagnostics surfaced in tool responses: pages OCR'd, chars/page, recovered
   tables, engine + language used, per-page confidence when available.
8. Regression tests with a real scanned roster fixture and a
   text-based PDF fixture (both paths must still pass).

## Acceptance gate

- `REV 4 Roster S1 SI Gasal 2026-2027.pdf` (or an equivalent scanned roster
  fixture) extracts with ≥ 90% of class codes/room numbers recoverable and
  tables reconstructed, verified against the manually transcribed truth.
- `document_ingest` on the scanned roster returns `status: ingested` with
  `manifest.ocr` populated; no `"Could not extract text from PDF"` path taken
  when OCR succeeded.
- `document_extract_ocr` returns page-tagged text + recovered Markdown tables
  without touching the knowledge base.
- Clean text-based PDFs still take the fast `pdf_text` path (no OCR slowdown).
- Full AI suite passes: `uv run ruff check app tests && uv run pytest`.

## Implementation steps

1. Add fixtures + failing tests for scanned roster extraction.
2. Upgrade render/preprocessing in `images.py`; keep `ocr_pil_image` API.
3. Add `ocr_tables.py` (word boxes + projection-profile table recovery).
4. Wire router plan fields (`recover_tables`, OCR metadata).
5. Fix ingestion fallback contract + manifest.ocr.
6. Add OCR fallback to `hebat/pdf_reader.py`.
7. Register new tools in registry + MCP adapter; add CLI parity test.
8. Add `document_ocr_status` diagnostics.
9. Run full test suite + verify against the real roster file.

## Risks / notes

- Tesseract is present in `services/ai/Dockerfile` (tesseract-ocr-eng + ind);
  local `uv run` hosts must install it too — `document_ocr_status` must report
  missing binaries clearly.
- Dense tables may still lose column alignment; the reconstructor must degrade
  to plain OCR text instead of failing the whole page.
- OCR of 22 pages is slower than the fast path; keep `OCR_MAX_PDF_PAGES` and
  surface page budget in diagnostics.
- Do not silently ingest OCR output that is mostly garbage: a minimum
  chars/page sanity gate is required.

## Related files

- `services/ai/app/xninetzy/os/knowledge/extraction/router.py`
- `services/ai/app/xninetzy/os/knowledge/extraction/extractors/pdf_structured.py`
- `services/ai/app/xninetzy/os/knowledge/extraction/extractors/images.py`
- `services/ai/app/xninetzy/os/knowledge/ingestion.py`
- `services/ai/app/xninetzy/os/academic/hebat/pdf_reader.py`
- `services/ai/app/xninetzy/interfaces/media/image_parser.py`
- `services/ai/app/xninetzy/tools/registry.py`
- `services/ai/Dockerfile`
