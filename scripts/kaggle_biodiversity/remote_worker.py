"""Kaggle-only worker. JOB is injected by the control script before upload."""

from pathlib import Path

if not Path("/kaggle/working").is_dir():
    raise SystemExit("This worker only runs inside Kaggle; local PDF processing is disabled.")

import collections
import gzip
import hashlib
import importlib.metadata
import json
import os
import re
import shutil
import subprocess
import sys
import time
import unicodedata
from datetime import datetime, timezone

JOB = globals().get("JOB", {})
OUT = Path("/kaggle/working")
TEMP = Path("/kaggle/temp/biodiversity")
TEMP.mkdir(parents=True, exist_ok=True)
os.environ["HF_HOME"] = str(TEMP / "hf")
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
STARTED = time.monotonic()
DEADLINE = STARTED + JOB.get("time_budget_seconds", 25_200)
PIPELINE_VERSION = "2026-11-15.4"


def stamp():
    return datetime.now(timezone.utc).isoformat()


def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(json.dumps(value, ensure_ascii=False, default=str), encoding="utf-8")
    temp.replace(path)


def emit(**value):
    print(json.dumps({"at": stamp(), **value}, ensure_ascii=False), flush=True)


def install(extraction=False):
    packages = ["beautifulsoup4", "requests", "gdown==6.5.1", "pymupdf", "pandas", "openpyxl"]
    if extraction:
        packages += ["docling==2.150.1", "langchain-docling[local]==3.0.0", "rapidocr==3.10.0", "onnxruntime"]
    subprocess.run([sys.executable, "-m", "pip", "install", "-q", *packages], check=True)


KEYWORDS = {
    "biodiversity": r"biodiversity",
    "ecosystem": r"ecosystems?",
    "ecology/ecological": r"ecology|ecological",
    "habitat": r"habitats?",
    "species": r"species",
    "forest/rainforest": r"(?:rain[\s-]?)?forests?",
    "deforestation": r"deforestation",
    "fauna": r"fauna",
    "flora": r"flora",
    "marine": r"marine",
    "tropical": r"tropical",
    "freshwater": r"fresh[\s-]?water",
    "wetland": r"wetland",
    "wildlife": r"wildlife",
    "coral": r"coral",
    "aquatic": r"aquatic",
    "desertification": r"desertification",
    "carbon sink": r"carbon[\s-]+sinks?",
    "ecosphere": r"ecosphere",
    "biosphere": r"biosphere",
}
PATTERNS = {key: re.compile(r"(?<!\w)(?:" + value + r")(?!\w)", re.I) for key, value in KEYWORDS.items()}


def normalize(text):
    text = unicodedata.normalize("NFKC", text).replace("\u00ad", "")
    text = re.sub(r"(?<=\w)-\s*\n\s*(?=\w)", "", text)
    return re.sub(r"\s+", " ", text).strip()


def keyword_matches(text):
    text = normalize(text)
    counts, evidence = {}, []
    for keyword, pattern in PATTERNS.items():
        found = list(pattern.finditer(text))
        counts[keyword] = len(found)
        for match in found:
            evidence.append({"keyword": keyword, "matched": match.group(), "context": text[max(0, match.start()-80):match.end()+80]})
    return counts, evidence


def scoring_contract_tests():
    cases = [
        ("species species", 2, 1), ("species habitat", 2, 1),
        ("species", 1, 0), ("habits habitual specialists", 0, 0),
        ("biodiversity-free", 1, 0), ("rainforest deforestation", 2, 1),
        ("forests rain forests rain-forest", 3, 1),
        ("ECOSYSTEMS ecological habitats carbon sinks", 4, 1),
        ("bio-\ndiversity carbon\n sinks", 2, 1),
        ("unrelated report", 0, 0),
    ]
    for text, expected_count, expected_score in cases:
        counts, _ = keyword_matches(text)
        total = sum(counts.values())
        assert total == expected_count, (text, counts)
        assert int(total >= 2) == expected_score
    # Distinct terms are not required; no overlapping LangChain chunks are counted.
    assert sum(keyword_matches("deforestation")[0].values()) == 1
    word = [10, 10, 65, 25, "species", 0, 0, 0]
    same = {"text": "species", "bbox": [8, 8, 70, 28]}
    distinct = {"text": "species", "bbox": [8, 90, 70, 110]}
    assert page_counts([word], [same])[0]["species"] == 1
    assert page_counts([word], [same, distinct])[0]["species"] == 2
    assert page_counts([word, word], [same])[0]["species"] == 1
    assert page_counts([], [same, same])[0]["species"] == 1
    emit(event="scoring_tests_passed", cases=len(cases))


def get_html(url):
    import requests
    from bs4 import BeautifulSoup
    for attempt in range(4):
        response = requests.get(url, timeout=(15, 90))
        if response.status_code == 429:
            delay = min(300, max(60, int(response.headers.get("Retry-After", "60"))))
            emit(event="rate_limited", retry_after=delay)
            time.sleep(delay)
            continue
        if response.status_code >= 500:
            time.sleep(15 * (attempt + 1))
            continue
        response.raise_for_status()
        if "text/html" not in response.headers.get("content-type", ""):
            raise RuntimeError("Expected public folder HTML")
        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(" ", strip=True)
        if any(marker in text.lower() for marker in ("unusual traffic", "verify you are human", "recaptcha")):
            raise RuntimeError("human_verification_required")
        return soup
    raise RuntimeError("rate_or_service_limit; resume later without bypassing it")


def inventory():
    queue = [dict(seed) for seed in JOB["seeds"]]
    known_roots = {x["id"] for x in queue}
    visited, files, folders, errors = set(), {}, [], []
    while queue:
        current = queue.pop(0)
        fid = current["id"]
        if fid in visited:
            continue
        try:
            soup = get_html("https://drive.google.com/embeddedfolderview?id=" + fid + "&hl=en")
            entries = soup.select(".flip-entry")
            if not entries and not soup.select(".flip-entries"):
                raise RuntimeError("Folder listing not recognized; cannot classify as empty")
            children, count = [], 0
            for entry in entries:
                link = entry.select_one("a[href]")
                name = entry.select_one(".flip-entry-title")
                if not link or not name:
                    raise RuntimeError("Unrecognized folder entry")
                item_id = entry.get("id", "").removeprefix("entry-")
                url = link["href"]
                if not re.fullmatch(r"[A-Za-z0-9_-]{15,}", item_id):
                    raise RuntimeError("Missing Drive item identifier")
                if "/folders/" in url or "/folderview" in url:
                    children.append(item_id)
                    if item_id not in visited and item_id not in known_roots:
                        queue.append({**current, "id": item_id, "name": name.get_text(), "root": current.get("root", fid)})
                else:
                    count += 1
                    files[item_id] = {"id": item_id, "name": name.get_text(), "url": url, "parent": fid, "sector": current["sector"], "folder_year": current["year"], "root": current.get("root", fid), "discovered_at": stamp()}
            folders.append({**current, "status": "accessible", "direct_files": count, "children": children})
            visited.add(fid)
        except Exception as exc:
            errors.append({**current, "error": str(exc)[:300]})
        atomic_json(OUT / "inventory.json", {"files": list(files.values()), "folders": folders, "errors": errors, "complete": not queue and not errors})
        time.sleep(1.5)
    summary = {"mode": "inventory", "complete": not errors, "files": len(files), "folders": len(folders), "errors": errors, "sectors": dict(collections.Counter(f["sector"] for f in files.values())), "roots": {root: sum(f["root"] == root for f in files.values()) for root in known_roots}}
    atomic_json(OUT / "summary.json", summary)
    emit(**summary)


def attached_file(name):
    matches = list(Path("/kaggle/input").rglob(name))
    if not matches:
        raise RuntimeError("Missing attached Kaggle output: " + name)
    return matches


def safe_name(name):
    return re.sub(r"[^\w. -]+", "_", Path(name).name)[:180]


class DriveDeferred(RuntimeError):
    def __init__(self, reason, retry_after=1800):
        super().__init__(reason)
        self.retry_after = max(1800, retry_after)


def public_download(item, partial):
    import requests
    import gdown
    # This is Drive's normal public download URL. The server's access decision
    # is authoritative: a denial/rate limit never triggers an alternate route.
    url = "https://drive.usercontent.google.com/uc"
    with requests.get(url, params={"id": item["id"], "export": "download"}, stream=True, timeout=(15, 90)) as response:
        if response.status_code in (403, 429):
            wait = response.headers.get("Retry-After", "1800")
            raise DriveDeferred("Drive HTTP " + str(response.status_code) + "; deferred without bypass", int(wait) if wait.isdigit() else 1800)
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            html = response.raw.read(100000).decode("utf-8", "replace")
            lower = html.lower()
            if any(marker in lower for marker in ("captcha", "unusual traffic", "too many users", "quota exceeded")):
                raise DriveDeferred("Drive verification/rate/quota page; deferred without bypass")
            if "virus" not in lower or not any(marker in lower for marker in ("scan", "large")):
                raise DriveDeferred("Drive returned an access page instead of a report")
        else:
            expected = response.headers.get("Content-Length")
            written = 0
            with partial.open("wb") as handle:
                for block in response.iter_content(1024 * 1024):
                    handle.write(block)
                    written += len(block)
            if expected and int(expected) != written:
                raise RuntimeError("Incomplete HTTP transfer")
            return
    # Only Google's ordinary large-file virus-scan confirmation uses gdown.
    result = gdown.download(id=item["id"], output=str(partial), quiet=True, use_cookies=False)
    if not result:
        raise DriveDeferred("Drive large-file confirmation could not complete")


def download_one(item):
    import signal
    import fitz
    target = OUT / "pdfs" / (item["id"] + "__" + safe_name(item["name"]))
    target.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(OUT).free < 1_000_000_000:
        raise RuntimeError("Disk reserve reached; split this shard and resume")
    if not target.exists():
        partial = target.with_suffix(target.suffix + ".part")

        def download_timeout(*args):
            raise TimeoutError("Drive transfer exceeded 180 seconds; retry with backoff")

        previous_handler = signal.signal(signal.SIGALRM, download_timeout)
        signal.alarm(180)
        try:
            public_download(item, partial)
        finally:
            signal.alarm(0)
            signal.signal(signal.SIGALRM, previous_handler)
        partial.replace(target)
    digest = hashlib.sha256()
    with target.open("rb") as handle:
        signature = handle.read(5)
        handle.seek(0)
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    record = {**item, "path": str(target.relative_to(OUT)), "bytes": target.stat().st_size, "sha256": digest.hexdigest(), "download_status": "complete", "is_pdf": signature == b"%PDF-"}
    if item["name"].lower().endswith(".pdf") and not record["is_pdf"]:
        raise RuntimeError("Drive returned a non-PDF response for a PDF filename")
    if record["is_pdf"]:
        with fitz.open(target) as pdf:
            if pdf.needs_pass:
                raise RuntimeError("password_required")
            record["pages"] = len(pdf)
            if len(pdf) == 0:
                raise RuntimeError("zero_page_pdf")
    return record


def previous_downloads():
    successful = {}
    for manifest in Path("/kaggle/input").rglob("downloads.json"):
        for record in json.loads(manifest.read_text())["records"]:
            if record.get("download_status") == "complete":
                source = manifest.parent / record["path"]
                if source.exists():
                    successful[record["id"]] = (record, source)
    return successful


def download_shard():
    data = json.loads(attached_file("inventory.json")[0].read_text())
    if not data["complete"]:
        raise RuntimeError("Inventory incomplete; do not start bulk acquisition")
    selected = [f for f in data["files"] if f["root"] == JOB["root"]]
    selected = selected[JOB.get("offset", 0): JOB.get("end", len(selected))]
    previous = previous_downloads()
    records = []
    deferred = None
    for index, item in enumerate(selected):
        if time.monotonic() > DEADLINE - 180:
            break
        try:
            if item["id"] in previous:
                record, source = previous[item["id"]]
                target = OUT / record["path"]
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)
            else:
                for attempt in range(3):
                    try:
                        record = download_one(item)
                        break
                    except Exception as exc:
                        emit(event="download_retry", file_id=item["id"], attempt=attempt+1, error=str(exc)[:180])
                        if isinstance(exc, DriveDeferred) or attempt == 2 or "password_required" in str(exc):
                            raise
                        time.sleep(30 * (2 ** attempt))
        except Exception as exc:
            record = {**item, "download_status": "failed", "error": str(exc)[:300]}
            if isinstance(exc, DriveDeferred):
                deferred = {"reason": str(exc), "retry_after_seconds": exc.retry_after}
        records.append(record)
        atomic_json(OUT / "downloads.json", {"records": records, "expected": len(selected)})
        emit(event="download_progress", processed=len(records), expected=len(selected), successful=sum(x["download_status"] == "complete" for x in records))
        if deferred:
            break
        time.sleep(2)
    completed = sum(r["download_status"] == "complete" for r in records)
    summary = {"mode": "download", "root": JOB["root"], "expected": len(selected), "processed": len(records), "downloaded": completed, "bytes": sum(r.get("bytes", 0) for r in records), "complete": completed == len(selected), "failures": [{"id": r["id"], "error": r.get("error")} for r in records if r["download_status"] != "complete"][:20]}
    if deferred:
        summary["deferred"] = deferred
    atomic_json(OUT / "summary.json", summary)
    emit(**summary)


def make_converter(vlm=False):
    import torch
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, RapidOcrOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption
    accelerator = AcceleratorOptions(num_threads=2, device=AcceleratorDevice.CUDA if torch.cuda.is_available() else AcceleratorDevice.CPU)
    if vlm:
        from docling.datamodel import vlm_model_specs
        from docling.datamodel.pipeline_options import VlmPipelineOptions
        from docling.pipeline.vlm_pipeline import VlmPipeline
        model = vlm_model_specs.GRANITEDOCLING_TRANSFORMERS.model_copy(deep=True, update={"torch_dtype": "float32"})
        options = VlmPipelineOptions(vlm_options=model, accelerator_options=accelerator)
        return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_cls=VlmPipeline, pipeline_options=options)})
    options = PdfPipelineOptions(do_ocr=True, do_table_structure=True, accelerator_options=accelerator)
    options.ocr_options = RapidOcrOptions(backend="onnxruntime", lang=["iso:en"])
    options.enable_remote_services = False
    return DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=options)})


class CheckedConverter:
    def __init__(self, converter):
        self.converter = converter
        self.result = None

    def convert(self, source, **kwargs):
        self.result = self.converter.convert(source, **kwargs)
        if str(self.result.status.value) != "success":
            raise RuntimeError("Partial/failed document conversion: " + str(self.result.status))
        start, end = kwargs["page_range"]
        if len(self.result.pages) != end - start + 1:
            raise RuntimeError("Converter page coverage mismatch")
        return self.result


def convert_pages(pdf, start, end, converter):
    import itertools
    from docling_core.types.doc.document import ContentLayer
    from langchain_docling import DoclingLoader
    from langchain_docling.loader import ExportType
    checked = CheckedConverter(converter)
    loader = DoclingLoader(file_path=str(pdf), converter=checked, export_type=ExportType.MARKDOWN, convert_kwargs={"page_range": (start, end), "raises_on_error": True}, md_export_kwargs={"image_placeholder": ""})
    documents = loader.load()
    if not documents or checked.result is None:
        raise RuntimeError("LangChain loader returned no converted document")
    document = checked.result.document
    pages = {p: {"text": document.export_to_markdown(page_no=p, image_placeholder=""), "regions": []} for p in range(start, end+1)}
    roots = [document.body, document.furniture]
    items = itertools.chain.from_iterable(document.iterate_items(root=root, traverse_pictures=True, included_content_layers=set(ContentLayer)) for root in roots)
    for item, _ in items:
        provenance = getattr(item, "prov", [])
        is_table = hasattr(getattr(item, "data", None), "table_cells")
        if is_table:
            if len({prov.page_no for prov in provenance}) != 1:
                continue
            value = "\n".join(cell.text for cell in item.data.table_cells if getattr(cell, "text", None))
        else:
            value = getattr(item, "text", "")
        if not value:
            continue
        for prov in provenance:
            if prov.page_no not in pages:
                continue
            size = document.pages[prov.page_no].size
            bbox = prov.bbox
            if "BOTTOMLEFT" in str(getattr(bbox.coord_origin, "value", bbox.coord_origin)).upper():
                box = [bbox.l, size.height - bbox.t, bbox.r, size.height - bbox.b]
            else:
                box = [bbox.l, bbox.t, bbox.r, bbox.b]
            text = value
            if not is_table and len(provenance) > 1:
                text = value[prov.charspan[0]:prov.charspan[1]]
            pages[prov.page_no]["regions"].append({"text": text, "bbox": box, "size": [size.width, size.height]})
    return pages


def metadata(item, cover):
    years = sorted(set(re.findall(r"(?<!\d)20(?:20|21|22|23|24|25)(?!\d)", item["name"])))
    year = int(years[0]) if len(years) == 1 else None
    year_source = "filename" if year else "unresolved"
    if year is None and re.fullmatch(r"20\d{2}", item.get("folder_year", "")):
        year, year_source = int(item["folder_year"]), "folder"
    candidates = re.findall(r"(?im)\bPT\.?[ \t]+[^\n|#]{3,150}?\bTbk\.?", cover)
    company = normalize(candidates[0]) if candidates else re.split(r"[ _.-]+(?:AR|SR|LK|20\d{2})\b", item["name"], flags=re.I)[0]
    return {"nama_perusahaan": company or item["name"], "tahun": year, "company_source": "pdf_cover" if candidates else "filename_identifier", "year_source": year_source}


def words_text(words):
    lines = []
    previous = None
    for word in words:
        line = (word[5], word[6])
        if line != previous:
            lines.append([])
        lines[-1].append(word[4])
        previous = line
    return "\n".join(" ".join(line) for line in lines)


def page_counts(native_words, regions):
    # Start with embedded text, then add only OCR/model occurrences in spatial
    # regions where the embedded text does not already contain those words.
    # This handles both duplicate OCR layers and disjoint native/image mentions.
    unique, words = set(), []
    for word in native_words:
        key = (normalize(word[4]).casefold(), *(round(v, 1) for v in word[:4]))
        if key not in unique:
            unique.add(key)
            words.append(word)
    counts, matches = keyword_matches(words_text(words))
    matches = [{**m, "reading": "native_pdf_text"} for m in matches]
    seen_regions = set()
    for region in regions:
        x0, y0, x1, y1 = region["bbox"]
        key = (normalize(region["text"]).casefold(), *(round(v, 1) for v in region["bbox"]))
        if key in seen_regions:
            continue
        seen_regions.add(key)
        covered = [w for w in words if x0-1.5 <= (w[0]+w[2])/2 <= x1+1.5 and y0-1.5 <= (w[1]+w[3])/2 <= y1+1.5]
        embedded_counts, _ = keyword_matches(words_text(covered))
        region_counts, region_matches = keyword_matches(region["text"])
        for keyword, count in region_counts.items():
            extra = max(0, count - embedded_counts[keyword])
            counts[keyword] += extra
            matches += [{**m, "reading": "docling_ocr_region", "bbox": region["bbox"]} for m in region_matches if m["keyword"] == keyword][:extra]
    return counts, matches


def resume_pages(item):
    best = []
    for source in Path("/kaggle/input").rglob(item["id"] + ".json.gz"):
        if source.parent.name != "texts":
            continue
        try:
            with gzip.open(source, "rt", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, dict) or data.get("pipeline_version") != PIPELINE_VERSION or data.get("sha256") != item.get("sha256"):
                continue
            pages = data["pages"]
            if [p["page"] for p in pages] == list(range(1, len(pages)+1)) and len(pages) > len(best):
                best = pages
        except (OSError, ValueError, KeyError):
            continue
    return best


def save_pages(item, page_records):
    target = OUT / "texts" / (item["id"] + ".json.gz")
    temporary = target.with_suffix(target.suffix + ".tmp")
    with gzip.open(temporary, "wt", encoding="utf-8") as handle:
        json.dump({"pipeline_version": PIPELINE_VERSION, "sha256": item.get("sha256"), "pages": page_records}, handle, ensure_ascii=False)
    temporary.replace(target)


def extract_one(item, pdf_path, converter, page_limit=None):
    import fitz
    record = {**item, "status": "failed", "score": None, "counts": {k: 0 for k in KEYWORDS}, "pages_processed": 0}
    cover, evidence, page_records = [], [], resume_pages(item)
    for page in page_records:
        counts, matches = page["counts"], page["matches"]
        for keyword, count in counts.items():
            record["counts"][keyword] += count
        evidence += [{"file_id": item["id"], "page": page["page"], "method": page["method"], **match} for match in matches]
        if page["page"] <= 2:
            cover.append(page["text"])
    record["pages_processed"] = len(page_records)
    with fitz.open(pdf_path) as pdf:
        total_pages = len(pdf)
        end_page = min(total_pages, page_limit or total_pages)
        record["pages"] = total_pages
        for start in range(len(page_records) + 1, end_page + 1, 8):
            if time.monotonic() > DEADLINE - 240:
                record["error"] = "Time budget reached; resume from saved pages"
                break
            end = min(end_page, start + 7)
            pages = convert_pages(pdf_path, start, end, converter)
            for page_no, conversion in pages.items():
                text = conversion["text"]
                regions = conversion["regions"]
                native = pdf[page_no - 1].get_text()
                method = "docling_native_layout_tables_ocr"
                if len(normalize(native)) >= 30 and len(normalize(text)) < min(30, len(normalize(native)) // 4):
                    if native.count("\ufffd") > max(5, len(native) * .02):
                        raise RuntimeError("Unresolved native and structured text quality at page " + str(page_no))
                    # Some covers are classified entirely as pictures. Preserve
                    # their valid embedded text instead of dropping those words.
                    text = native
                    method = "native_pdf_fallback_for_layout_omission"
                if len(normalize(text)) < 5 and pdf[page_no-1].get_images():
                    # VLM is local to Kaggle. Never let an OCR failure silently become score 0.
                    global VLM_CONVERTER
                    if VLM_CONVERTER is None:
                        VLM_CONVERTER = make_converter(vlm=True)
                    conversion = convert_pages(pdf_path, page_no, page_no, VLM_CONVERTER)[page_no]
                    text, regions = conversion["text"], conversion["regions"]
                    method = "granite_docling_258m_local_ocr"
                    if len(normalize(text)) < 5:
                        raise RuntimeError("Image page has unresolved OCR quality at page " + str(page_no))
                if text.count("\ufffd") > max(5, len(text) * .02):
                    raise RuntimeError("Unresolved character corruption at page " + str(page_no))
                native_words = pdf[page_no - 1].get_text("words", sort=True)
                # Docling's coordinates describe the displayed page orientation.
                if pdf[page_no - 1].rotation:
                    rotated = []
                    for word in native_words:
                        box = fitz.Rect(*word[:4]) * pdf[page_no - 1].rotation_matrix
                        rotated.append([box.x0, box.y0, box.x1, box.y1, *word[4:]])
                    native_words = rotated
                for region in regions:
                    width, height = region["size"]
                    sx, sy = pdf[page_no - 1].rect.width / width, pdf[page_no - 1].rect.height / height
                    b = region["bbox"]
                    region["bbox"] = [b[0]*sx, b[1]*sy, b[2]*sx, b[3]*sy]
                counts, matches = page_counts(native_words, regions)
                for keyword, count in counts.items():
                    record["counts"][keyword] += count
                evidence += [{"file_id": item["id"], "page": page_no, "method": method, **match} for match in matches]
                page_records.append({"page": page_no, "method": method, "text": text, "native_text": native, "counts": counts, "matches": matches})
                if page_no <= 2:
                    cover.append(text)
                record["pages_processed"] += 1
            save_pages(item, page_records)
            emit(event="extraction_progress", file_id=item["id"], processed=record["pages_processed"], pages=total_pages)
        record.update(metadata(item, "\n".join(cover)))
        record["total_hits"] = sum(record["counts"].values())
        record["status"] = "complete" if record["pages_processed"] == total_pages else "partial"
        if record["status"] == "complete":
            record["score"] = int(record["total_hits"] >= 2)
        save_pages(item, page_records)
    return record, evidence


def workbook(records, path):
    import pandas as pd
    from openpyxl.styles import Font, PatternFill
    rows, details = [], []
    for r in records:
        rows.append({"nama perusahaan": r.get("nama_perusahaan", r["name"]), "tahun": r.get("tahun"), "keyword": "; ".join(f"{k} ({v})" for k, v in r.get("counts", {}).items() if v), "value score": r.get("score")})
        details.append({"file_id": r["id"], "nama_file": r["name"], "nama_perusahaan": r.get("nama_perusahaan"), "tahun": r.get("tahun"), "sector": r.get("sector"), "status": r["status"], "score": r.get("score"), "total_hits": r.get("total_hits"), "pages": r.get("pages"), "pages_processed": r.get("pages_processed"), "company_source": r.get("company_source"), "year_source": r.get("year_source"), "source_url": r.get("url"), "sha256": r.get("sha256"), "error": r.get("error"), **r.get("counts", {})})
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame(rows, columns=["nama perusahaan", "tahun", "keyword", "value score"]).to_excel(writer, sheet_name="Skor PDF", index=False)
        pd.DataFrame(details).to_excel(writer, sheet_name="Detail PDF", index=False)
        pd.DataFrame([{"aturan": "Ambang", "nilai": "Total >= 2 kemunculan dari seluruh keyword: 1; total < 2: 0. Keyword yang sama boleh berulang."}, {"aturan": "Cakupan", "nilai": "Satu baris per PDF, AR dan SR terpisah; kata bahasa Inggris sesuai daftar pengguna."}, {"aturan": "Dua pembacaan", "nilai": "Teks native ditambah kemunculan OCR yang belum tercakup pada wilayah koordinat yang sama. Lapisan teks identik pada koordinat sama dihapus duplikasinya. Bukti menyimpan sumber dan koordinat OCR."}, {"aturan": "Kegagalan", "nilai": "Skor kosong untuk PDF gagal/parsial; lihat Detail PDF. Tidak pernah diubah menjadi 0."}, {"aturan": "Nama perusahaan", "nilai": "Diambil dari sampul jika ditemukan; jika tidak, pengenal nama file dan ditandai company_source."}, {"aturan": "Sumber", "nilai": "Folder Google Drive diberikan pengguna; pencocokan kata utuh, tanpa membedakan kapital."}, {"aturan": "Dibuat", "nilai": stamp()}]).to_excel(writer, sheet_name="Metode", index=False)
        for sheet in writer.book:
            sheet.freeze_panes = "A2"
            sheet.auto_filter.ref = sheet.dimensions
            for cell in sheet[1]:
                cell.font = Font(name="Arial", bold=True, color="FFFFFF")
                cell.fill = PatternFill("solid", fgColor="17365D")
            for row in sheet.iter_rows(min_row=2):
                for cell in row:
                    cell.font = Font(name="Arial", size=10)
                    if isinstance(cell.value, str) and cell.value.startswith(("=", "+", "-", "@")):
                        cell.data_type = "s"
            for column in sheet.columns:
                sheet.column_dimensions[column[0].column_letter].width = min(70, max(14, max(len(str(c.value or "")) for c in column[:100]) + 2))
    from openpyxl import load_workbook
    book = load_workbook(path, read_only=True, data_only=True)
    assert book["Skor PDF"].max_row == len(records) + 1
    for row, r in zip(book["Skor PDF"].iter_rows(min_row=2, values_only=True), records):
        assert row[3] == r.get("score"), (row, r["id"])
    book.close()


VLM_CONVERTER = None


def extraction(smoke=False, canary=False):
    scoring_contract_tests()
    (OUT / "texts").mkdir(exist_ok=True)
    if smoke:
        item = {"id": "1fIZ2C9nT4rs-Ztm9IkbAJYDXlFTC0Kgq", "name": "ABMM_AR_2020.pdf", "folder_year": "2020", "sector": "Energy", "url": "https://drive.google.com/file/d/1fIZ2C9nT4rs-Ztm9IkbAJYDXlFTC0Kgq/view"}
        cached = list(Path("/kaggle/input").rglob(item["id"] + "__" + item["name"]))
        if cached:
            target = OUT / "pdfs" / cached[0].name
            target.parent.mkdir(exist_ok=True)
            shutil.copy2(cached[0], target)
        items = [download_one(item)]
        base = OUT
    else:
        downloads = attached_file("downloads.json")[0]
        items = json.loads(downloads.read_text())["records"]
        base = downloads.parent
        if canary:
            items = sorted((r for r in items if r.get("download_status") == "complete" and r.get("is_pdf")), key=lambda r: r.get("pages", 999999))[:1]
            if not items:
                raise RuntimeError("No validated PDF is available for full-document canary")
    converter = make_converter()
    records = []
    with gzip.open(OUT / "keyword_evidence.jsonl.gz", "wt", encoding="utf-8") as evidence_file:
        for item in items:
            if time.monotonic() > DEADLINE - 300:
                break
            try:
                if item.get("download_status") != "complete":
                    raise RuntimeError("Source file was not downloaded successfully")
                if not item.get("is_pdf"):
                    records.append({**item, "status": "not_pdf", "score": None})
                    continue
                record, evidence = extract_one(item, base / item["path"], converter, page_limit=3 if smoke else None)
                for value in evidence:
                    evidence_file.write(json.dumps(value, ensure_ascii=False) + "\n")
            except Exception as exc:
                record = {**item, "status": "failed", "score": None, "error": str(exc)[:500]}
                emit(event="extraction_failed", file_id=item["id"], error_type=type(exc).__name__, error=str(exc)[:500])
            records.append(record)
            atomic_json(OUT / "results.json", {"records": records})
            workbook(records, OUT / "biodiversity_scores.xlsx")
    if smoke:
        if any(record["status"] == "failed" for record in records):
            raise RuntimeError("Sample extraction failed: " + records[0].get("error", "unknown"))
        # A raster-only fixture verifies the real OCR path in Kaggle, not a mocked extractor.
        from PIL import Image, ImageDraw, ImageFont
        image = Image.new("RGB", (1400, 1000), "white")
        ImageDraw.Draw(image).text((70, 100), "species species habitat", font=ImageFont.load_default(size=52), fill="black")
        fixture = OUT / "ocr_fixture.pdf"
        image.save(fixture, "PDF", resolution=150)
        result, _ = extract_one({"id": "ocr_fixture", "name": "OCR_AR_2020.pdf", "folder_year": "2020"}, fixture, converter)
        assert result["score"] == 1 and result["counts"]["species"] == 2, result
        import fitz
        mixed = OUT / "mixed_fixture.pdf"
        image = Image.new("RGB", (900, 250), "white")
        ImageDraw.Draw(image).text((20, 60), "species", font=ImageFont.load_default(size=50), fill="black")
        from io import BytesIO
        buffer = BytesIO()
        image.save(buffer, "PNG")
        with fitz.open() as pdf:
            page = pdf.new_page(width=600, height=800)
            page.insert_text((70, 90), "species", fontsize=30)
            page.insert_image(fitz.Rect(60, 400, 540, 550), stream=buffer.getvalue())
            pdf.save(mixed)
        mixed_result, _ = extract_one({"id": "mixed_fixture", "name": "MIXED_AR_2020.pdf", "folder_year": "2020"}, mixed, converter)
        assert mixed_result["counts"]["species"] == 2 and mixed_result["score"] == 1, mixed_result
        assert records and records[0]["status"] == "partial" and records[0]["score"] is None
    summary = {"mode": "smoke" if smoke else "canary" if canary else "extract", "pipeline_version": PIPELINE_VERSION, "expected": len(items), "processed": len(records), "complete_pdfs": sum(r["status"] == "complete" for r in records), "failed": sum(r["status"] == "failed" for r in records), "partial": sum(r["status"] == "partial" for r in records), "pages_processed": sum(r.get("pages_processed", 0) for r in records), "elapsed_seconds": round(time.monotonic()-STARTED), "complete": (smoke and bool(records) and records[0]["status"] == "partial") or len(records) == len(items) and all(r["status"] in ("complete", "not_pdf") for r in records), "failures": [{"id": r["id"], "error": r.get("error")} for r in records if r["status"] == "failed"][:20], "versions": {p: importlib.metadata.version(p) for p in ("docling", "langchain-docling", "gdown", "rapidocr")}}
    atomic_json(OUT / "summary.json", summary)
    emit(**summary)


def merge():
    scoring_contract_tests()
    files = attached_file("results.json")
    unique = {}
    for path in files:
        for record in json.loads(path.read_text())["records"]:
            if record["id"] not in unique or record["status"] == "complete":
                unique[record["id"]] = record
    records = sorted(unique.values(), key=lambda r: (r.get("sector", ""), r.get("nama_perusahaan", r["name"]), str(r.get("tahun", "")), r["name"]))
    workbook(records, OUT / "biodiversity_scores.xlsx")
    atomic_json(OUT / "results.json", {"records": records})
    summary = {"mode": "merge", "files": len(records), "complete_pdfs": sum(r["status"] == "complete" for r in records), "unresolved": sum(r["status"] not in ("complete", "not_pdf") for r in records), "score_1": sum(r.get("score") == 1 for r in records), "score_0": sum(r.get("score") == 0 for r in records), "expected_files": JOB.get("expected_files"), "complete": len(records) == JOB.get("expected_files") and all(r["status"] in ("complete", "not_pdf") for r in records)}
    atomic_json(OUT / "summary.json", summary)
    emit(**summary)


if __name__ == "__main__":
    try:
        mode = JOB["mode"]
        install(extraction=mode in ("extract", "smoke", "canary"))
        if mode == "inventory":
            inventory()
        elif mode == "download":
            download_shard()
        elif mode in ("extract", "smoke", "canary"):
            extraction(smoke=mode == "smoke", canary=mode == "canary")
        elif mode == "merge":
            merge()
        else:
            raise RuntimeError("Unknown job mode")
    except Exception as exc:
        atomic_json(OUT / "fatal.json", {"mode": JOB.get("mode"), "error_type": type(exc).__name__, "error": str(exc)[:800], "at": stamp()})
        raise
