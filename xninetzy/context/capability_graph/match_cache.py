from __future__ import annotations

from functools import lru_cache


_MAX_CACHE_SIZE: int = 1024


@lru_cache(maxsize=_MAX_CACHE_SIZE)
def tokenize_cached(value: str | None) -> frozenset[str]:
    if not value:
        return frozenset()
    out: set[str] = set()
    for token in value.lower().replace("/", " ").replace("-", " ").replace(".", " ").split():
        cleaned = "".join(ch for ch in token if ch.isalnum() or ch == "_")
        if cleaned and len(cleaned) >= 2:
            out.add(cleaned)
    return frozenset(out)


@lru_cache(maxsize=_MAX_CACHE_SIZE)
def jaccard_cached(left_id: int, right_id: int) -> float:
    from xninetzy.context.capability_graph.semantic_match import (
        _jaccard,
    )
    left = _CACHE_TOKENS[left_id]
    right = _CACHE_TOKENS[right_id]
    return _jaccard(set(left), set(right))


_CACHE_TOKENS: dict[int, frozenset[str]] = {}
_NEXT_TOKEN_ID: list[int] = [0]


def token_id(value: str | None) -> int:
    cached = tokenize_cached(value)
    for key, stored in _CACHE_TOKENS.items():
        if stored == cached:
            return key
    _NEXT_TOKEN_ID[0] += 1
    new_id = _NEXT_TOKEN_ID[0]
    _CACHE_TOKENS[new_id] = cached
    return new_id


def clear_cache() -> None:
    tokenize_cached.cache_clear()
    jaccard_cached.cache_clear()
    _CACHE_TOKENS.clear()
    _NEXT_TOKEN_ID[0] = 0


def cache_size() -> int:
    return len(_CACHE_TOKENS)
