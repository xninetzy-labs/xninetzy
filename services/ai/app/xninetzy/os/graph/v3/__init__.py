"""GraphRAG V3 — tri-store canonical layer.

SQLite is the source of truth. Neo4j (structural) and FAISS (semantic) are
rebuildable projections fed exclusively through ``graph_sync_outbox`` and the
projection worker. Nothing here dual-writes from business logic, and every
Neo4j/FAISS failure is swallowed so chat/knowledge/reminder/workflow never break.

The whole subsystem is gated behind ``GRAPHRAG_V3_ENABLED``; when disabled these
modules stay dormant and the legacy V1 ``graph_store`` keeps working untouched.
"""
