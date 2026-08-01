"""LangChain tools for GraphRAG V3.

Thin wrappers over ``graph_service``. They speak (node_type, title) pairs — the
model never handles canonical keys directly; identity is derived here so writes
stay idempotent and stable across rebuilds.

Rebuild is destructive to the projections and therefore routed through HITL: the
tool only files an approval request; execution happens in
``approval_service._execute_approved_action`` after an admin approves.
"""

from __future__ import annotations

from langchain_core.tools import tool

from app.xninetzy.os.graph.v3 import graph_service
from app.xninetzy.os.graph.v3.identity import node_key


def _disabled_msg() -> str:
    return "GraphRAG V3 belum aktif (set GRAPHRAG_V3_ENABLED=true)."


@tool
def graph_v3_upsert_node(
    node_type: str,
    title: str,
    content: str = "",
    properties: dict | None = None,
    provenance: dict | None = None,
) -> str:
    """Tambah/perbarui node di GraphRAG V3 (idempotent, canonical SQLite)."""
    if not graph_service.enabled():
        return _disabled_msg()
    res = graph_service.upsert_node(
        node_type=node_type,
        title=title,
        content=content or None,
        properties=properties,
        provenance=provenance,
        actor="tool",
    )
    verb = "dibuat" if res.created else ("diperbarui" if res.changed else "tidak berubah")
    return f"✅ Node [{node_type}] {title} {verb} (v{res.version})."


@tool
def graph_v3_link(
    source_type: str,
    source_title: str,
    target_type: str,
    target_title: str,
    edge_type: str,
    weight: float = 1.0,
    provenance: dict | None = None,
) -> str:
    """Hubungkan dua node GraphRAG V3 dengan edge berarah (idempotent)."""
    if not graph_service.enabled():
        return _disabled_msg()
    src = node_key(source_type, source_title)
    tgt = node_key(target_type, target_title)
    res = graph_service.upsert_edge(
        source_key=src,
        target_key=tgt,
        edge_type=edge_type,
        weight=weight,
        provenance=provenance,
        actor="tool",
    )
    verb = "dibuat" if res.created else ("diperbarui" if res.changed else "tidak berubah")
    return f"✅ Edge {source_title} —{edge_type}→ {target_title} {verb}."


@tool
def graph_v3_search(query: str, top_k: int = 8, expand_depth: int = 1) -> str:
    """Hybrid search GraphRAG V3 (FTS + semantic + struktur) → konteks graph."""
    if not graph_service.enabled():
        return _disabled_msg()
    pack = graph_service.search(query, top_k=top_k, expand_depth=expand_depth)
    return pack.to_markdown()


@tool
def graph_v3_neighborhood(node_type: str, title: str, depth: int = 1) -> str:
    """Tampilkan tetangga struktural sebuah node GraphRAG V3."""
    if not graph_service.enabled():
        return _disabled_msg()
    key = node_key(node_type, title)
    neighbors = graph_service.neighborhood([key], depth=depth)
    if not neighbors:
        return f"Tidak ada tetangga untuk [{node_type}] {title} (atau Neo4j offline)."
    lines = [f"*Tetangga [{node_type}] {title}:*"]
    for nb in neighbors:
        lines.append(f"• [{nb.get('node_type')}] {nb.get('title')} (+{nb.get('hops')} hop)")
    return "\n".join(lines)


@tool
def graph_v3_path(
    source_type: str, source_title: str, target_type: str, target_title: str
) -> str:
    """Cari jalur terpendek antar dua node GraphRAG V3."""
    if not graph_service.enabled():
        return _disabled_msg()
    src = node_key(source_type, source_title)
    tgt = node_key(target_type, target_title)
    path = graph_service.shortest_path(src, tgt)
    if not path:
        return f"Tidak ada jalur {source_title} ke {target_title} (atau Neo4j offline)."
    return " → ".join(f"[{n.get('node_type')}] {n.get('title')}" for n in path)


@tool
def graph_v3_stats() -> str:
    """Status GraphRAG V3: outbox pending, ketersediaan Neo4j, jumlah node/edge."""
    s = graph_service.stats()
    return (
        f"*GraphRAG V3*\n"
        f"Enabled: {s['enabled']}\n"
        f"Node aktif: {s['active_nodes']}, Edge aktif: {s['active_edges']}\n"
        f"Outbox pending: {s['outbox_pending']}\n"
        f"Neo4j online: {s['neo4j_available']}"
    )


@tool
async def graph_v3_rebuild(chat_id: str = "system", sender_id: str | None = None) -> str:
    """Rebuild projeksi GraphRAG V3 (Neo4j+FAISS) dari SQLite. DESTRUKTIF → HITL."""
    if not graph_service.enabled():
        return _disabled_msg()
    from app.xninetzy.os.hitl.approval_service import request_approval
    from app.xninetzy.os.notifications.admin_notifier import notify_admin_approval

    title = "Rebuild projeksi GraphRAG V3"
    summary = (
        "Menghapus seluruh projeksi Neo4j + index FAISS, lalu memutar ulang dari "
        "SQLite kanonis. Sumber kebenaran (SQLite) tidak tersentuh."
    )
    approval_id = request_approval(chat_id, sender_id, "graph_rebuild", title, summary, {})
    delivered = await notify_admin_approval(approval_id, "graph_rebuild", title, summary)
    delivery = (
        "Tombol approve/reject dikirim ke WhatsApp admin."
        if delivered
        else "Tombol gagal dikirim; cek ADMIN_JID dan WA Engine."
    )
    return (
        f"*Approval Required #{approval_id}*\n\n{summary}\n\n{delivery}\n\n"
        f"Fallback:\n`/approve {approval_id}`\natau\n`/reject {approval_id}`"
    )
