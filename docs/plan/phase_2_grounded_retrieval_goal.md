# Phase 2 — Grounded Retrieval, Graph, and Academic Packs

Status: in progress  
Schedule: weeks 3-5

## Goal

Make information acquisition reliable, grounded, and non-blocking while
keeping HEBAT, Cyber Campus, and QA as optional UNAIR feature-pack adapters.

## Design decisions

- Retrieval is deterministic before generation: retrieve, fuse, deduplicate,
  cite, synthesize, and disclose insufficient evidence.
- Source content is untrusted data. It cannot provide instructions or change
  tool policy.
- SQLite is the canonical graph store. FAISS and Neo4j are derived indexes and
  must not block a request when unavailable.
- Free, CPU-friendly paths are primary. Tavily, Serper, YouTube API, hosted
  embeddings, and other paid providers are optional adapters.
- Academic sessions distinguish locally stored credentials from a verified live
  portal session.

## Scope

1. Enable DDGS search fallback and optional yt-dlp YouTube metadata/subtitle
   retrieval without requiring an API key.
2. Add bounded Obsidian FTS and observable index health.
3. Complete Graph V1 compatibility through a documented V3 migration or alias.
4. Move Neo4j startup and projection reconciliation out of synchronous request
   paths.
5. Add safe generic web discovery with HTTPS/public-host validation, read-only
   traversal, graph provenance, and evidence-aware ingestion.
6. Unify optional academic-pack enablement, session validation, safety policy,
   rate limiting, audit, and replay behavior.

## Acceptance gate

- Search has a free path when network access permits it.
- [x] The shared web-search tool reaches DDGS when Tavily and Serper are not
  configured; paid providers remain optional adapters.
- [x] Public HTTPS validation, bounded discovery, human-verification stop
  behavior, and web-page graph provenance remain shared-service behavior.
- [x] Add bounded SQLite FTS indexing for Obsidian notes, excluding vault
  backups, with content-hash updates and a configurable file cap.
- [x] Expose Obsidian index health through the shared registry and canonical MCP
  schema so every interface observes the same state.
- [ ] Complete the remaining explicit GraphRAG projection-health and migration
  work in the next Phase 2 slice.

Focused verification: 13 Obsidian and MCP registry tests pass; targeted Ruff
checks pass. Full AI verification remains the phase gate.

Earlier focused verification: 23 retrieval, manifest, MCP, and web-search tests pass.
