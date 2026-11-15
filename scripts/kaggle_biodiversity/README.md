# Kaggle biodiversity extraction

All source PDF acquisition, document parsing, Hugging Face inference, OCR,
keyword matching and workbook generation execute in Kaggle. The worker exits
before importing extraction libraries when `/kaggle/working` is absent.
The local controller uploads source and reads bounded execution metadata/logs;
it refuses to download reports, extracted text or workbooks.

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

## Control commands

Run with the Python environment containing the official Kaggle CLI (`/usr/bin/python3`
on this host). These commands control remote execution; they do not process PDFs locally.

```bash
python3 scripts/kaggle_biodiversity/control.py smoke biodiversity-pipeline-smoke
python3 scripts/kaggle_biodiversity/control.py inventory biodiversity-drive-inventory
python3 scripts/kaggle_biodiversity/control.py inspect biodiversity-pipeline-smoke
python3 scripts/kaggle_biodiversity/control.py inspect biodiversity-drive-inventory
# Only after the smoke test and inventory are verified:
python3 scripts/kaggle_biodiversity/control.py campaign-init biodiversity-drive-inventory
python3 scripts/kaggle_biodiversity/control.py tick campaign
python3 scripts/kaggle_biodiversity/control.py supervise campaign
```

Repeated `tick` calls (or `supervise`) reconcile current remote state and submit ready jobs,
with at most four CPU jobs and two GPU jobs owned by this campaign at once.
They do not replay uncertain submissions. Partial/failed runs require diagnosis
and a verified continuation before dependent jobs proceed. Kaggle resource
limits or Drive access restrictions may require subsequent runs; the final
workbook is complete only when every inventoried file is accounted for.

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
