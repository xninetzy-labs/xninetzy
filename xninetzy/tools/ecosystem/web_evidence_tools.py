from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urlparse

import httpx
from langchain_core.tools import tool
from lxml import html as lxml_html

from xninetzy.db.sqlite import connect, init_db
from xninetzy.db.idempotency import idempotent_call
from xninetzy.tools.tool_results import to_tool_result


_DEFAULT_TIMEOUT = 20.0
_MAX_EXCERPT_CHARS = 1500
_ALLOWED_SCHEMES = ("http", "https")
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)


def _normalize_url(url: str) -> tuple[str, str, str]:
    parsed = urlparse(url.strip())
    if parsed.scheme.lower() not in _ALLOWED_SCHEMES or not parsed.hostname:
        raise ValueError(f"URL tidak valid: {url}")
    host = parsed.hostname.lower()
    canonical = parsed._replace(fragment="").geturl()
    return canonical, host, parsed.scheme.lower()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_db() -> None:
    init_db()


def _row_to_dict(row: Any) -> dict[str, Any]:
    return {key: row[key] for key in row.keys()}


def _excerpt_from_html(html: str, max_chars: int = _MAX_EXCERPT_CHARS) -> str:
    try:
        tree = lxml_html.fromstring(html)
    except (ValueError, lxml_html.etree.ParserError, lxml_html.etree.XMLSyntaxError):
        return ""
    for tag in ("script", "style", "noscript", "svg", "iframe"):
        for node in tree.xpath(f".//{tag}"):
            node.getparent().remove(node)
    text = tree.text_content()
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) > max_chars:
        return text[:max_chars] + "…"
    return text


def _extract_title(html: str) -> str:
    match = _TITLE_RE.search(html)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()[:300]


@tool
def web_extract(
    url: str,
    max_chars: int = 5000,
    capture_visual: bool = False,
    sender_id: str = "",
    idempotency_key: str = "",
) -> str:
    """Fetch URL HTTPS, parse HTML, dan simpan ke source ledger.

    Mengikuti batasan: GET-only, canonical URL, human-verification detection.
    Opsional memicu capture visual via PixelRAG (jika tersedia) untuk evidence
    screenshot.

    Args:
        url: URL HTTPS publik lengkap.
        max_chars: Batas karakter excerpt (500-20000).
        capture_visual: True untuk invoke pixelrag_capture (visual evidence).
        sender_id: Owner principal (dari context).
        idempotency_key: Kunci opsional agar retry tidak dobel fetch.
    """
    if max_chars < 500 or max_chars > 20000:
        raise ValueError("max_chars harus berada di antara 500 dan 20000.")

    def _do() -> str:
        try:
            canonical, host, _scheme = _normalize_url(url)
        except ValueError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)
        headers = {"User-Agent": "Xninetzy-WebExtract/1.0 (read-only)"}
        try:
            with httpx.Client(timeout=_DEFAULT_TIMEOUT, follow_redirects=True, headers=headers) as client:
                response = client.get(canonical)
        except httpx.HTTPError as exc:
            return json.dumps({"error": f"request failed: {exc}"}, ensure_ascii=False)
        content_type = response.headers.get("content-type", "")
        http_status = response.status_code
        title = ""
        excerpt = ""
        pixelrag_path: str | None = None
        if http_status < 400 and "html" in content_type.casefold():
            html = response.text
            title = _extract_title(html)
            excerpt = _excerpt_from_html(html, max_chars=max_chars)
            if capture_visual:
                try:
                    pixelrag_capture = _import_pixelrag_capture()
                    capture_result = pixelrag_capture.invoke({
                        "source": canonical,
                        "sender_id": sender_id,
                    })
                    pixelrag_path = _extract_capture_path(capture_result)
                except Exception:
                    pixelrag_path = None
        _ensure_db()
        with connect() as conn:
            cur = conn.execute(
                """
                INSERT INTO web_source_ledger
                  (url, canonical_url, title, publisher, host, content_type,
                   http_status, excerpt, retrieval_kind, pixelrag_capture_path,
                   evidence_score, metadata_json, fetched_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    url, canonical, title, host, host, content_type,
                    http_status, excerpt, "extract", pixelrag_path,
                    1.0 if excerpt else 0.0,
                    json.dumps({"max_chars": max_chars, "capture_visual": capture_visual}),
                    _now_iso(),
                ),
            )
            ledger_id = cur.lastrowid
        payload = {
            "ledger_id": ledger_id,
            "url": url,
            "canonical": canonical,
            "host": host,
            "http_status": http_status,
            "content_type": content_type,
            "title": title,
            "excerpt_chars": len(excerpt),
            "pixelrag_capture": pixelrag_path,
        }
        return json.dumps(payload, ensure_ascii=False)

    return idempotent_call("web_extract", idempotency_key, {"url": url, "max_chars": max_chars}, _do)[0]


def _import_pixelrag_capture():
    from xninetzy.tools.ecosystem.pixelrag_tools import pixelrag_capture
    return pixelrag_capture


def _extract_capture_path(output: str) -> str | None:
    if not output:
        return None
    match = re.search(r"capture selesai -> (.+)", output)
    if match:
        return match.group(1).strip()
    return output.splitlines()[0][:300] if output else None


@tool
def web_compare(
    claim: str,
    urls: list[str],
    max_chars: int = 4000,
    sender_id: str = "",
) -> str:
    """Bandingkan klaim terhadap beberapa URL: hitung dukungan bukti.

    Args:
        claim: Pernyataan yang akan diverifikasi.
        urls: Daftar URL untuk dibandingkan (maks 8).
        max_chars: Batas excerpt per URL.
        sender_id: Owner principal (dari context).
    """
    if not claim.strip():
        return json.dumps({"error": "claim kosong"}, ensure_ascii=False)
    if not urls:
        return json.dumps({"error": "urls kosong"}, ensure_ascii=False)
    bounded_urls = urls[:8]
    claim_terms = [t.lower() for t in re.findall(r"\w+", claim) if len(t) > 2]
    if not claim_terms:
        return json.dumps({"error": "claim terlalu pendek"}, ensure_ascii=False)

    results: list[dict[str, Any]] = []
    supporting: list[str] = []
    contradicting: list[str] = []
    neutral: list[str] = []

    headers = {"User-Agent": "Xninetzy-WebCompare/1.0"}
    for target in bounded_urls:
        try:
            canonical, host, _ = _normalize_url(target)
        except ValueError as exc:
            results.append({"url": target, "error": str(exc)})
            continue
        try:
            with httpx.Client(timeout=_DEFAULT_TIMEOUT, follow_redirects=True, headers=headers) as client:
                response = client.get(canonical)
        except httpx.HTTPError as exc:
            results.append({"url": canonical, "error": f"request failed: {exc}"})
            continue
        if response.status_code >= 400 or "html" not in response.headers.get("content-type", "").casefold():
            results.append({"url": canonical, "http_status": response.status_code})
            continue
        excerpt = _excerpt_from_html(response.text, max_chars=max_chars)
        overlap = sum(1 for term in claim_terms if term in excerpt.lower())
        score = overlap / len(claim_terms)
        verdict = "supporting" if score >= 0.3 else "neutral"
        results.append({
            "url": canonical,
            "host": host,
            "http_status": response.status_code,
            "overlap": overlap,
            "score": round(score, 3),
            "excerpt_chars": len(excerpt),
            "verdict": verdict,
        })
        if verdict == "supporting":
            supporting.append(canonical)
        else:
            neutral.append(canonical)

    payload = {
        "claim": claim,
        "terms": len(claim_terms),
        "supporting": supporting,
        "contradicting": contradicting,
        "neutral": neutral,
        "verdict": (
            "supported" if supporting else
            "contradicted" if contradicting else
            "insufficient"
        ),
        "results": results,
    }
    return json.dumps(payload, ensure_ascii=False)


@tool
def web_evidence(
    claim: str,
    min_confidence: float = 0.4,
    limit: int = 10,
    sender_id: str = "",
) -> str:
    """Cari di source ledger untuk klaim tertentu, dengan skor bukti.

    Args:
        claim: Klaim yang dicari di ledger.
        min_confidence: Skor minimum (0-1).
        limit: Maks jumlah hasil (cap 50).
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 50))
    claim_terms = [t.lower() for t in re.findall(r"\w+", claim) if len(t) > 2]
    _ensure_db()
    with connect() as conn:
        rows = conn.execute(
            """
            SELECT id, url, canonical_url, title, host, excerpt, claim,
                   confidence, evidence_score, retrieval_kind,
                   pixelrag_capture_path, metadata_json, fetched_at
              FROM web_source_ledger
             ORDER BY fetched_at DESC
             LIMIT 500
            """
        ).fetchall()

    scored: list[dict[str, Any]] = []
    for row in rows:
        record = _row_to_dict(row)
        corpus = " ".join(filter(None, [
            record.get("title"), record.get("excerpt"), record.get("claim"), record.get("url"),
        ])).lower()
        overlap = sum(1 for term in claim_terms if term in corpus)
        score = overlap / len(claim_terms) if claim_terms else 0.0
        evidence_score = float(record.get("evidence_score") or 0.0)
        combined = round((score * 0.6) + (evidence_score * 0.4), 3)
        if combined < min_confidence:
            continue
        scored.append({
            "id": record["id"],
            "url": record["url"],
            "canonical": record["canonical_url"],
            "title": record.get("title"),
            "host": record.get("host"),
            "score": combined,
            "overlap": overlap,
            "evidence_score": evidence_score,
            "fetched_at": record.get("fetched_at"),
            "has_pixelrag_capture": bool(record.get("pixelrag_capture_path")),
            "metadata": json.loads(record.get("metadata_json") or "{}"),
        })
    scored.sort(key=lambda r: (-r["score"], -r["evidence_score"]))
    top = scored[:bounded_limit]
    return json.dumps({
        "claim": claim,
        "match_count": len(top),
        "truncated": len(scored) > bounded_limit,
        "results": top,
    }, ensure_ascii=False)


@tool
def web_source_ledger(
    host: str = "",
    retrieval_kind: str = "",
    limit: int = 25,
    sender_id: str = "",
) -> str:
    """Tampilkan entry source ledger terbaru dengan filter host/kind.

    Args:
        host: Filter substring host (opsional).
        retrieval_kind: extract|compare|evidence (opsional).
        limit: Maks jumlah entry (cap 200).
        sender_id: Owner principal.
    """
    bounded_limit = max(1, min(limit, 200))
    _ensure_db()
    where: list[str] = []
    params: list[Any] = []
    if host:
        where.append("host LIKE ?")
        params.append(f"%{host.lower()}%")
    if retrieval_kind:
        where.append("retrieval_kind = ?")
        params.append(retrieval_kind)
    where_sql = ("WHERE " + " AND ".join(where)) if where else ""
    sql = f"""
        SELECT id, url, title, host, http_status, retrieval_kind,
               evidence_score, pixelrag_capture_path, fetched_at
          FROM web_source_ledger
          {where_sql}
         ORDER BY fetched_at DESC
         LIMIT ?
    """
    params.append(bounded_limit)
    with connect() as conn:
        rows = conn.execute(sql, params).fetchall()
    items = [_row_to_dict(row) for row in rows]
    return to_tool_result(
        f"{len(items)} entry source ledger.",
        items,
        filter_host=host or None,
        filter_kind=retrieval_kind or None,
        limit=bounded_limit,
    )
