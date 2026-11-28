from __future__ import annotations

import json
import re
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing_extensions import TypedDict

from langchain_core.tools import tool

from xninetzy.core.security import redact_chat_ids_in_text, redact_secrets
from xninetzy.db.sqlite import connect


_SLUG = re.compile(r"[a-z0-9][a-z0-9_.-]{0,79}")
_LATEST = """
    SELECT revision, payload_json, saved_at
      FROM memory_session_checkpoints
     WHERE owner=? AND workspace=? AND task=?
     ORDER BY revision DESC LIMIT 1
"""


class GraphAnchor(TypedDict):
    node_type: str
    title: str


def _scope(workspace: str, sender_id: str) -> tuple[str, str]:
    path = Path(workspace)
    if not sender_id or not path.is_absolute() or len(workspace) > 1024 or "\x00" in workspace:
        raise ValueError("workspace must be an absolute path and requires a trusted owner")
    return sender_id, str(path.resolve())


def _task(value: str) -> str:
    slug = value.strip().lower()
    if not _SLUG.fullmatch(slug):
        raise ValueError("task must be a stable slug of up to 80 characters")
    return slug


def _text(value: str, max_bytes: int) -> str:
    clean = redact_chat_ids_in_text(redact_secrets(value)).strip()
    return clean.encode()[:max_bytes].decode(errors="ignore")


def _fit_text(value: str, max_bytes: int) -> str:
    low, high = 0, min(len(value), max_bytes)
    while low < high:
        middle = (low + high + 1) // 2
        if len(json.dumps(value[:middle], ensure_ascii=False).encode()) <= max_bytes:
            low = middle
        else:
            high = middle - 1
    return value[:low]


def _snapshot(summary, next_action, references, graph_anchors) -> dict:
    from xninetzy.os.graph.v3.identity import node_key

    action = _fit_text(_text(next_action, 512), 512)
    if not action:
        raise ValueError("next_action is required")
    return {
        "summary": _text(summary, 1800),
        "next_action": action,
        "references": list(dict.fromkeys(_text(item, 240) for item in (references or [])[:5] if item.strip())),
        "graph_node_keys": list(dict.fromkeys(
            node_key(anchor["node_type"], anchor["title"]) for anchor in (graph_anchors or [])[:3]
            if anchor["node_type"].strip() and anchor["title"].strip()
        )),
    }


@tool(description=(
    "Save a compact checkpoint for an absolute workspace and task slug. "
    "Use revision 0 for a new task or the latest revision to update. Provide evidence references "
    "and optional GraphRAG anchors by node type and title. Use a unique idempotency key "
    "and omit secrets and transcripts."
))
def memory_session_checkpoint(
    workspace: str,
    task: str,
    expected_revision: int,
    summary: str,
    next_action: str,
    idempotency_key: str,
    references: list[str] | None = None,
    graph_anchors: list[GraphAnchor] | None = None,
    sender_id: str = "",
) -> dict:
    scope = (*_scope(workspace, sender_id), _task(task))
    key = idempotency_key.strip()
    if not key or len(key) > 200 or expected_revision < 0:
        raise ValueError("invalid checkpoint revision or idempotency key")
    payload = json.dumps(_snapshot(summary, next_action, references, graph_anchors), ensure_ascii=False)
    with closing(connect()) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        previous = conn.execute(
            "SELECT revision, payload_json, saved_at FROM memory_session_checkpoints "
            "WHERE owner=? AND workspace=? AND task=? AND request_key=?",
            (*scope, key),
        ).fetchone()
        if previous:
            if previous["payload_json"] != payload or previous["revision"] != expected_revision + 1:
                raise ValueError("idempotency_payload_mismatch")
            return {"status": "saved", "task": scope[-1], "revision": previous["revision"],
                    "saved_at": previous["saved_at"]}
        latest = conn.execute(_LATEST, scope).fetchone()
        revision = latest["revision"] if latest else 0
        if expected_revision != revision:
            return {"status": "revision_conflict", "task": scope[-1], "revision": revision}
        saved_at = datetime.now(UTC).isoformat()
        conn.execute(
            "INSERT INTO memory_session_checkpoints "
            "(owner, workspace, task, revision, request_key, payload_json, saved_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (*scope, revision + 1, key, payload, saved_at),
        )
    return {"status": "saved", "task": scope[-1], "revision": revision + 1, "saved_at": saved_at}


def _graph_context(keys: list[str]) -> tuple[str, list[dict]]:
    from xninetzy.os.graph.v3 import graph_service

    if not graph_service.enabled():
        return "disabled", []
    links = [{
        "source": _text(edge["source_title"], 100),
        "relation": _text(edge["edge_type"], 64),
        "target": _text(edge["target_title"], 100),
        "edge_key": edge["canonical_key"],
    } for edge in graph_service.active_links(keys)]
    return ("included" if links else "no_active_links"), links


def _size(value: dict) -> int:
    return len(json.dumps(value, ensure_ascii=False).encode())


@tool(description=(
    "Resume from the latest checkpoint when switching tabs or after compaction. "
    "Pass the same absolute workspace and task slug, or omit task to discover candidates. "
    "Returns bounded context, the revision and the next action. Revalidate evidence before acting."
))
def memory_session_resume(
    workspace: str,
    task: str | None = None,
    max_context_bytes: int = 4096,
    include_graph: bool = True,
    sender_id: str = "",
) -> dict:
    limit = min(8192, max(1024, max_context_bytes))
    scope = _scope(workspace, sender_id)
    with closing(connect()) as conn:
        if task is None:
            candidates = conn.execute(
                "SELECT task FROM memory_session_checkpoints WHERE owner=? AND workspace=? "
                "GROUP BY task ORDER BY MAX(saved_at) DESC, task LIMIT 6",
                scope,
            ).fetchall()
            if len(candidates) > 1:
                return {"status": "choose_task", "tasks": [row["task"] for row in candidates[:5]],
                        "has_more": len(candidates) > 5}
            if not candidates:
                return {"status": "not_found"}
            task = candidates[0]["task"]
        task = _task(task)
        row = conn.execute(_LATEST, (*scope, task)).fetchone()
    if row is None:
        return {"status": "not_found"}
    saved = json.loads(row["payload_json"])
    checkpoint = {"task": task, "revision": row["revision"], "saved_at": row["saved_at"],
                  "next_action": saved["next_action"]}
    result = {"status": "resumed", "checkpoint": checkpoint, "truncated": True}
    keys = saved["graph_node_keys"]
    result["graph_status"] = "deferred" if include_graph and keys else "not_requested"
    result["context_bytes"] = 9999
    checkpoint["summary"] = ""
    if include_graph and keys:
        graph_reserve = min(768, max(0, (limit - _size(result)) // 3)) if limit >= 2048 else 0
    else:
        graph_reserve = 0
    checkpoint["summary"] = _fit_text(saved["summary"], limit - _size(result) - graph_reserve)
    truncated = checkpoint["summary"] != saved["summary"]
    if saved["references"]:
        checkpoint["references"] = []
        for ref in saved["references"]:
            checkpoint["references"].append(ref)
            if _size(result) <= limit - graph_reserve - 1:
                continue
            checkpoint["references"].pop()
            truncated = True
        if not checkpoint["references"]:
            checkpoint.pop("references")
    if include_graph and keys and limit - _size(result) >= 384:
        try:
            status, links = _graph_context(keys)
            result["graph_status"] = status
            if links:
                result["graph"] = []
                for link in links:
                    result["graph"].append(link)
                    if _size(result) > limit - 1:
                        result["graph"].pop()
                        truncated = True
                if not result["graph"]:
                    result.pop("graph")
                    result["graph_status"] = "deferred"
        except Exception:
            result["graph_status"] = "unavailable"
    result["truncated"] = truncated or result["graph_status"] == "deferred"
    result["context_bytes"] = _size(result)
    result["context_bytes"] = _size(result)
    return result
