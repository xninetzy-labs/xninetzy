from __future__ import annotations

import pytest

from app.xninetzy.tools.ecosystem.pixelrag_tools import _validate_source
from app.xninetzy.tools.registry import get_all_tools

PIXELRAG_TOOLS = {
    "pixelrag_capture",
    "pixelrag_search_public",
    "pixelrag_search_local",
    "pixelrag_health",
}


def test_pixelrag_tools_registered() -> None:
    names = {t.name for t in get_all_tools()}
    assert PIXELRAG_TOOLS <= names


def test_validate_source_rejects_internal_hosts_for_public() -> None:
    for bad in ("http://localhost:8000/x", "http://127.0.0.1:30001", "http://192.168.1.5/x"):
        with pytest.raises(ValueError):
            _validate_source(bad, public=True)


def test_validate_source_accepts_public_https() -> None:
    _validate_source("https://en.wikipedia.org/wiki/Python", public=True)


def test_validate_source_local_restricted_to_loopback() -> None:
    _validate_source("http://127.0.0.1:30001/search", public=False)
    with pytest.raises(ValueError):
        _validate_source("http://10.0.0.5:30001/search", public=False)
