from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from xninetzy.db.sqlite import connect


@dataclass(frozen=True, slots=True)
class MatchResult:
    capability: str
    surface: str
    alias: str
    score: float
    method: str


_STOPWORDS: frozenset[str] = frozenset(
    {
        "a", "an", "the", "and", "or", "to", "for", "of", "in", "on",
        "with", "without", "please", "tolong", "saya", "aku", "kamu",
        "ingin", "bisa", "mau", "cara", "how", "what", "is", "do",
    }
)


def _tokenize(value: str) -> set[str]:
    if not value:
        return set()
    out: set[str] = set()
    for token in value.lower().replace("/", " ").replace("-", " ").replace(".", " ").split():
        cleaned = "".join(ch for ch in token if ch.isalnum() or ch == "_")
        if not cleaned or cleaned in _STOPWORDS or len(cleaned) < 2:
            continue
        out.add(cleaned)
    return out


def _jaccard(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = left & right
    union = left | right
    return len(intersection) / len(union)


def _alias_hash_rows(conn, alias_keys: Iterable[str]) -> list[dict]:
    keys = [key for key in alias_keys if key]
    if not keys:
        return []
    placeholders = ",".join("?" for _ in keys)
    return conn.execute(
        f"""
        SELECT capability, surface, alias, weight
        FROM capability_aliases
        WHERE alias IN ({placeholders})
        """,
        keys,
    ).fetchall()


def _candidate_pool(conn, alias_keys: Iterable[str], tokens: set[str]) -> list[dict]:
    rows = _alias_hash_rows(conn, alias_keys)
    if not rows and tokens:
        like_clauses = " OR ".join(["alias LIKE ?"] * len(tokens))
        params = [f"%{token}%" for token in tokens]
        return conn.execute(
            f"""
            SELECT capability, surface, alias, weight
            FROM capability_aliases
            WHERE {like_clauses}
            LIMIT 200
            """,
            params,
        ).fetchall()
    return rows


def match_capability(
    query: str,
    *,
    top_k: int = 5,
    min_score: float = 0.1,
) -> list[MatchResult]:
    tokens = _tokenize(query)
    if not tokens:
        return []
    alias_keys = sorted(tokens)
    with connect() as conn:
        candidates = _candidate_pool(conn, alias_keys, tokens)
    if not candidates:
        return []
    scored: list[MatchResult] = []
    for row in candidates:
        alias = str(row["alias"])
        alias_tokens = _tokenize(alias)
        jaccard = _jaccard(tokens, alias_tokens)
        contains_bonus = 0.25 if any(token in alias.lower() for token in tokens) else 0.0
        weight = float(row["weight"])
        score = (jaccard + contains_bonus) * weight
        method = "jaccard" if jaccard > 0 else "contains"
        if score < min_score:
            continue
        scored.append(
            MatchResult(
                capability=str(row["capability"]),
                surface=str(row["surface"]),
                alias=alias,
                score=round(score, 4),
                method=method,
            )
        )
    scored.sort(key=lambda match: match.score, reverse=True)
    return scored[:top_k]
