from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

from xninetzy.tools.ecosystem.web_evidence_tools import (
    web_compare,
    web_evidence,
    web_extract,
    web_source_ledger,
)


SAMPLE_HTML = """
<html>
  <head><title>Quantum supremacy explained</title></head>
  <body>
    <h1>Quantum supremacy and modern processors</h1>
    <p>Quantum supremacy is the point where quantum processors outperform classical computers
       for specific tasks such as random circuit sampling. Google demonstrated this in 2019 with
       the Sycamore processor.</p>
    <p>Classical supercomputers still dominate general workloads. The supremacy claim is
       contested for specific tasks like random number generation.</p>
  </body>
</html>
"""

CONTRADICTING_HTML = """
<html>
  <head><title>Quantum computers are slow</title></head>
  <body>
    <p>Quantum computers fail to outperform classical machines on most workloads.</p>
  </body>
</html>
"""


class _MockHandler(BaseHTTPRequestHandler):
    routes = {
        "/quantum.html": (SAMPLE_HTML, "text/html"),
        "/slow.html": (CONTRADICTING_HTML, "text/html"),
        "/robots.txt": ("User-agent: *\nAllow: /\n", "text/plain"),
    }

    def log_message(self, format, *args):
        return

    def do_GET(self):
        if self.path in self.routes:
            body, content_type = self.routes[self.path]
            encoded = body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        else:
            self.send_response(404)
            self.end_headers()


@pytest.fixture(scope="module")
def mock_server():
    server = ThreadingHTTPServer(("127.0.0.1", 0), _MockHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_address[1]}"
    finally:
        server.shutdown()
        thread.join(timeout=2)


def _invoke(tool, **kwargs) -> dict:
    return json.loads(tool.invoke(kwargs))


def test_web_extract_stores_to_ledger(tmp_path, monkeypatch, mock_server):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("PIXELRAG_LOCAL_SERVE_ENABLED", "false")
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    url = f"{mock_server}/quantum.html"
    out = _invoke(web_extract, url=url, max_chars=2000)
    assert "error" not in out
    assert out["http_status"] == 200
    assert out["title"] == "Quantum supremacy explained"
    assert out["excerpt_chars"] > 50
    assert out["ledger_id"] >= 1


def test_web_extract_rejects_non_http(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    out = _invoke(web_extract, url="file:///etc/passwd", max_chars=1000)
    assert "error" in out


def test_web_compare_returns_supporting_verdict(tmp_path, monkeypatch, mock_server):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    claim = "Quantum supremacy demonstrated by Google Sycamore"
    urls = [f"{mock_server}/quantum.html"]
    out = _invoke(web_compare, claim=claim, urls=urls, max_chars=3000)
    assert out["verdict"] in {"supported", "neutral", "insufficient"}
    assert out["terms"] >= 1
    assert out["supporting"] or out["neutral"]


def test_web_compare_rejects_empty(tmp_path, monkeypatch):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    out = _invoke(web_compare, claim="quantum supremacy", urls=[])
    assert "error" in out


def test_web_evidence_search_finds_recent_entries(tmp_path, monkeypatch, mock_server):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("PIXELRAG_LOCAL_SERVE_ENABLED", "false")
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()

    url = f"{mock_server}/quantum.html"
    _invoke(web_extract, url=url, max_chars=2000)
    out = _invoke(web_evidence, claim="quantum supremacy sycamore", limit=5)
    assert out["match_count"] >= 1
    assert out["results"][0]["score"] >= 0.4


def test_web_source_ledger_lists_recent(tmp_path, monkeypatch, mock_server):
    monkeypatch.setenv("SQLITE_PATH", str(tmp_path / "test.sqlite3"))
    monkeypatch.setenv("PIXELRAG_LOCAL_SERVE_ENABLED", "false")
    from xninetzy.core.config import get_settings

    get_settings.cache_clear()
    from xninetzy.db.sqlite import init_db

    init_db()
    _invoke(web_extract, url=f"{mock_server}/quantum.html", max_chars=1000)
    out = _invoke(web_source_ledger, limit=10)
    assert "summary" in out
    assert "items" in out
    assert len(out["items"]) >= 1
