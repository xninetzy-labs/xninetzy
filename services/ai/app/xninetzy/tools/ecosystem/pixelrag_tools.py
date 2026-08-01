from __future__ import annotations

import asyncio
import ipaddress
import json
import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool

PIXELRAG_PUBLIC_API = os.environ.get(
    "PIXELRAG_PUBLIC_API", "https://api.pixelrag.ai"
).rstrip("/")
PIXELRAG_LOCAL_API = os.environ.get(
    "PIXELRAG_LOCAL_API", "http://127.0.0.1:30001"
).rstrip("/")
ALLOWED_DOCUMENT_ROOT = Path(
    os.environ.get("PIXELRAG_ALLOWED_DOCUMENT_ROOT", "data/documents")
).resolve()
PIXELRAG_OUTPUT_ROOT = Path(
    os.environ.get("PIXELRAG_OUTPUT_ROOT", "data/pixelrag")
).resolve()

REQUEST_TIMEOUT = 30.0
CAPTURE_TIMEOUT = 600


def _is_private_host(host: str) -> bool:
    if host in {"localhost", "0.0.0.0", "::1"}:
        return True
    try:
        addr = ipaddress.ip_address(host)
    except ValueError:
        return False
    return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved


def _validate_source(source: str, *, public: bool = True) -> None:
    parsed = urlparse(source)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError("source harus berupa URL http(s)")
    host = parsed.hostname.lower()
    if public:
        if _is_private_host(host):
            raise ValueError("source publik tidak boleh menunjuk host internal")
    elif host not in {"localhost", "127.0.0.1", "::1"}:
        raise ValueError("source lokal hanya boleh localhost/127.0.0.1")


def _validate_document_path(path: str) -> Path:
    candidate = Path(path).resolve()
    if not candidate.is_relative_to(ALLOWED_DOCUMENT_ROOT):
        raise ValueError(
            f"file di luar {ALLOWED_DOCUMENT_ROOT} tidak diizinkan: {candidate}"
        )
    if not candidate.exists():
        raise ValueError(f"file tidak ditemukan: {candidate}")
    return candidate


def _format_hits(payload: dict, api_base: str, n_docs: int) -> str:
    hits = payload.get("hits") if isinstance(payload, dict) else None
    flat: list[dict] = []
    if isinstance(hits, list):
        for item in hits:
            if isinstance(item, list):
                flat.extend(x for x in item if isinstance(x, dict))
            elif isinstance(item, dict):
                flat.append(item)
    if not flat:
        return json.dumps(payload, ensure_ascii=False)[:3000]
    lines = []
    for i, hit in enumerate(flat[:n_docs], start=1):
        article = hit.get("article_id", "")
        tile = hit.get("tile_index", "")
        chunk = hit.get("chunk_index", "")
        score = hit.get("score")
        parts = [f"[{i}] article={article} tile={tile} chunk={chunk}"]
        if score is not None:
            parts.append(f"score={score}")
        parts.append(f"{api_base}/tile/{article}/{tile}/{chunk}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)


async def _run_pixelshot(args: list[str]) -> str:
    proc = await asyncio.create_subprocess_exec(
        "pixelshot",
        *args,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.STDOUT,
    )
    try:
        out, _ = await asyncio.wait_for(proc.communicate(), timeout=CAPTURE_TIMEOUT)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.wait()
        raise RuntimeError(f"pixelshot timeout setelah {CAPTURE_TIMEOUT}s")
    return out.decode(errors="replace").strip()


async def _post_search(api_base: str, query: str, n_docs: int) -> str:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.post(
            f"{api_base}/search",
            json={"queries": [{"text": query}], "n_docs": n_docs},
        )
        response.raise_for_status()
        payload = response.json()
    return _format_hits(payload, api_base, n_docs)


@tool
async def pixelrag_capture(
    source: str, output_subdir: str = "", backend: str = "cdp"
) -> str:
    """Render URL atau dokumen lokal menjadi tile screenshot PixelRAG via CLI pixelshot.

    Args:
        source: URL http(s) publik atau path file di dalam data/documents
        output_subdir: nama subfolder output (default: diturunkan dari source)
        backend: backend browser, "cdp" (default) atau "playwright"
    """
    if not shutil.which("pixelshot"):
        return "CLI pixelshot belum terinstall. Jalankan: uv tool install pixelrag"
    if source.startswith("http://") or source.startswith("https://"):
        try:
            _validate_source(source, public=True)
        except ValueError as exc:
            return f"source tidak valid: {exc}"
        stem = re.sub(r"[^a-zA-Z0-9_-]", "_", urlparse(source).netloc)[:64]
    else:
        try:
            local_path = _validate_document_path(source)
        except ValueError as exc:
            return f"file tidak valid: {exc}"
        stem = local_path.stem[:64]
    out_dir = PIXELRAG_OUTPUT_ROOT / (output_subdir or stem)
    try:
        output = await _run_pixelshot([source, "--output", str(out_dir), "--backend", backend])
    except (RuntimeError, FileNotFoundError) as exc:
        return f"capture gagal: {exc}"
    return f"capture selesai -> {out_dir}\n{output}"


@tool
async def pixelrag_search_public(query: str, n_docs: int = 5) -> str:
    """Cari di indeks publik PixelRAG (8.28M artikel Wikipedia, visual retrieval).

    Args:
        query: pertanyaan natural language
        n_docs: jumlah hasil (default 5)
    """
    try:
        return await _post_search(PIXELRAG_PUBLIC_API, query, n_docs)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return f"search publik gagal: {exc}"


@tool
async def pixelrag_search_local(query: str, n_docs: int = 5) -> str:
    """Cari di server lokal pixelrag serve (127.0.0.1:30001).

    Args:
        query: pertanyaan natural language
        n_docs: jumlah hasil (default 5)
    """
    try:
        return await _post_search(PIXELRAG_LOCAL_API, query, n_docs)
    except (httpx.HTTPError, ValueError, KeyError) as exc:
        return f"search lokal gagal: {exc}"


@tool
def pixelrag_health() -> str:
    """Cek ketersediaan CLI pixelshot, server lokal, dan API publik PixelRAG."""
    cli = "ada" if shutil.which("pixelshot") else "tidak ada"
    lines = [f"CLI pixelshot: {cli}"]
    for label, base in (("Lokal", PIXELRAG_LOCAL_API), ("Publik", PIXELRAG_PUBLIC_API)):
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{base}/health")
            lines.append(f"{label} ({base}): HTTP {response.status_code}")
        except httpx.HTTPError:
            lines.append(f"{label} ({base}): tidak terjangkau")
    return "\n".join(lines)
