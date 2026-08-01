"""Deterministic identity + content hashing for GraphRAG V3.

Idempotency is the whole game: the same fact upserted twice must land on the
same canonical row, and the projection layer must be able to tell "changed"
from "unchanged" without a diff. We get that from two pure functions:

* ``node_key`` / ``edge_key`` — a stable UUID5 derived from the *identity* of
  the thing (node_type + normalized title, or the edge triple). Same identity
  always yields the same key, across processes and rebuilds.
* ``content_hash`` — a sha256 over the *mutable content*. Same content ⇒ same
  hash ⇒ the upsert is a no-op and no outbox row is emitted.
"""

from __future__ import annotations

import hashlib
import json
import uuid

# Fixed namespace so canonical keys are stable forever. Do not change — doing so
# would orphan every previously-projected node/edge in Neo4j and FAISS.
_NAMESPACE = uuid.UUID("6f3d1c2a-9b4e-5d7f-8a1b-2c3d4e5f6a7b")


def normalize_text(value: str | None) -> str:
    """Case-fold + collapse whitespace so trivially-different titles collide."""
    return " ".join((value or "").split()).casefold()


def node_key(node_type: str, title: str, *, identity: str | None = None) -> str:
    """Canonical key for a node.

    ``identity`` overrides the title-derived identity when the caller has a
    stronger natural key (e.g. an entity id). Falls back to normalized title.
    """
    ident = normalize_text(identity if identity is not None else title)
    raw = f"node|{normalize_text(node_type)}|{ident}"
    return str(uuid.uuid5(_NAMESPACE, raw))


def edge_key(source_key: str, edge_type: str, target_key: str) -> str:
    """Canonical key for an edge — the (source, type, target) triple identity."""
    raw = f"edge|{source_key}|{normalize_text(edge_type)}|{target_key}"
    return str(uuid.uuid5(_NAMESPACE, raw))


def _canonical_json(data: dict | None) -> str:
    return json.dumps(data or {}, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def node_content_hash(
    *, node_type: str, title: str, content: str | None, properties: dict | None
) -> str:
    material = "␟".join(
        [
            normalize_text(node_type),
            normalize_text(title),
            (content or "").strip(),
            _canonical_json(properties),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def edge_content_hash(
    *, edge_type: str, weight: float, properties: dict | None
) -> str:
    material = "␟".join(
        [
            normalize_text(edge_type),
            format(float(weight), ".6f"),
            _canonical_json(properties),
        ]
    )
    return hashlib.sha256(material.encode("utf-8")).hexdigest()
