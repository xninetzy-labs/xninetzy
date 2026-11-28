# Kaggle biodiversity extraction

All source PDF acquisition, document parsing, Hugging Face inference, OCR,
keyword matching and workbook generation execute in Kaggle. The worker exits
before importing extraction libraries when `/kaggle/working` is absent.
The native Xninetzy Kaggle tools upload source and read execution metadata.
PDFs, extracted text and workbooks remain in Kaggle.

The 59 source folders are in `seeds.json`. Inventory recursively discovers
public descendants and deduplicates Drive IDs. Downloads retain original
filenames and SHA-256 in private Kaggle notebook outputs. Each source folder
has its own acquisition and extraction job, followed by sector merges and a
final Excel merge. Authentication uses the existing Kaggle CLI configuration;
no credential is embedded in notebook source.

## Scoring contract

One row per PDF. Match the user's English terms as whole words without regard
to case, with the stated singular/plural variants. `ecology/ecological` and
`forest/rainforest` are grouped. Count every occurrence, including repeats of
the same keyword. Two or more occurrences give 1; fewer give 0. Partial/failed
extractions have a blank score and an explicit diagnostic. No overlapping
chunks are counted. The workbook starts with the four requested columns;
separate sheets retain document identity, coverage, per-keyword counts and
method notes. Page evidence and extracted page text remain in Kaggle outputs.

Docling uses local Hugging Face layout/table models with RapidOCR, integrated
through LangChain's DoclingLoader. Difficult image pages use the local
`ibm-granite/granite-docling-258M` fallback. No hosted inference API is used.
Company names come from the PDF cover when recognized; otherwise the filename
identifier is retained and explicitly marked for review. Years come from the
filename, with a single-year source-folder fallback.

Plain pages with valid embedded text, no bitmap (including inline images),
and no vector drawings use Docling's native pipeline through the same LangChain
loader. Pages with images, vectors, or poor text retain the full layout/table/OCR
path. Each page records its method. The spatial scoring is unchanged, so verified
version-4 checkpoints remain compatible with the version-5 routing optimization.

## Recovered native queue

The legacy `control.py` supervisor is retired. Do not start it alongside the
recovered native pipeline `biodiversity-recovered-20261116`. Its authoritative
state is `~/.local/share/xninetzy/kaggle/pipelines/biodiversity-recovered-20261116.json`.
The recovered worker, original checkpoint copy and tool plans are under
`~/.local/share/xninetzy/kaggle/biodiversity-recovery/`.

The owner explicitly enabled `kaggle_pipeline_tick=auto` in the repository
`.env`. A user systemd timer invokes the existing native Xninetzy tool harness
every two minutes, loading current settings on each invocation. The harness
honors approval mode, revocation and the policy kill switch. It does not run
PDF parsing, OCR or models locally. Pipeline concurrency is four CPU jobs and
two GPU jobs, subject to Kaggle's live quotas and provider limits. Paid scaling
is never enabled.

```bash
systemctl --user status xninetzy-kaggle-biodiversity-recovery.timer
systemctl --user status xninetzy-kaggle-biodiversity-recovery.service
```

Ordinary pipeline ticks reconcile remote state, reuse completed outputs and
schedule continuations. They do not replay uncertain pushes or restart cancelled jobs.
For an explicitly authorized repair, the existing `kaggle_pipeline_tick` accepts
`reconcile_jobs` and `restart_cancelled`, each containing canonical job slugs.
Reconciliation adopts an existing run, or queues a fresh attempt only after a
complete authenticated owned-notebook listing confirms absence and an unused
new slug. The listing must contain a known completed pipeline notebook as a
witness. Network failures and incomplete listings leave delivery unresolved.
An explicitly requested cancelled continuation preserves published checkpoint
outputs; it never cancels a run. Recovery requests have persistent idempotency
records and retain the original uncertain-push ledger for audit.
The timer skips further calls after the pipeline writes its terminal marker
on completion or when blocked. Partial/failed jobs still need diagnosis and
a verified continuation. The final workbook is complete only when every
inventoried file is accounted for.

Transfers use Drive's regular public download URL and verify the response size.
Only the ordinary large-file virus-scan confirmation falls back to gdown.
HTTP 403/429, quota and human-verification responses defer the job for at least
30 minutes without trying another route. Successful files are copied from the
previous immutable Kaggle output in continuation runs, rather than fetched
from Drive again. Text checkpoints are atomic, keyed by PDF hash and pipeline
version, and reused at page boundaries. GPU reservations use the live free
quota; CPU continuations remain inside Kaggle. Paid scaling is never enabled.

The two readings of a physical page (native PDF text and Docling/OCR) are not
concatenated. Embedded-text occurrences form the baseline. Model/OCR region
coordinates are matched to embedded words in the same region, and only the
additional occurrences are added. Identical words in duplicate text layers
at the same coordinates are removed. The Kaggle smoke tests cover identical
layers and two physical mentions split between embedded text and an image.
Original readings and selected evidence remain available for audit.
Metadata inferred only from filenames is marked.
