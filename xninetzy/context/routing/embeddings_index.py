from __future__ import annotations

from typing import Any


_INDEX: dict[str, Any] = {"items": [], "vectors": []}


def _index_documents(items: list[str], vectors: list[Any] | None = None) -> None:
    _INDEX["items"] = list(items)
    if vectors is not None:
        _INDEX["vectors"] = list(vectors)
    else:
        _INDEX["vectors"] = [None] * len(items)


def get_indexed_items() -> list[str]:
    return list(_INDEX["items"])
