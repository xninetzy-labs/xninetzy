# Xninetzy WA + AI Second Brain Audit

_Audited 2026-06-02 against the actual working tree (not the master prompt's wishlist)._

Legend: ✅ implemented · 🟡 partial · ❌ missing · ⚠️ risky/needs care

## 1. Summary

The **WhatsApp capture side (wa-enggine) is much further along than the AI
consumption side.** wa-enggine can already download media, resolve group admins,
and ships quoted text + media metadata + mention/admin context in the AI payload.
The **AI service cannot yet act on any of it**: there is no media module, no
multimodal tools, no context builder, and the agent only receives media as
*metadata strings* — it never fetches or reads the bytes.

The "Second Brain" storage layers are split:
- **Knowledge/FAISS**: real and working (FAISS + FTS5 fallback, chunking, ingestion).
- **Memory**: only `chat_store` (raw chat history). No semantic memory system.
- **Graph RAG**: SQLite-only MVP (`graph_nodes`/`graph_edges`). No Neo4j, no hybrid.
- **Context builder**: does not exist as a unit; `ecosystem/context_builder.py`
  builds a *personal context* (goals/tasks/deadlines) but does not merge
  quoted/media/memory/knowledge/graph.

Net: the fastest high-value win is **wiring the AI side to consume media that
wa-enggine already downloads** (document → text → answer), because the capture
half is done.

## 2. WhatsApp Input Capabilities

| Capability | Status | Where |
|---|---|---|
| Receive text | ✅ | `message-listener.ts`, `message-parser.ts:extractMessageText` |
| Caption (image/video/doc) | ✅ | `extractMessageText` candidates |
| Quoted/reply detection | ✅ | `trigger.ts:detectReplyToBot`, `getMessageContextInfo` |
| Quoted **text** in payload | ✅ | `ai-payload.ts` → `metadata.quotedMessageText` |
| Quoted **media** in payload | ❌ | only quoted text/id/participant are forwarded |
| Mention detection (incoming) | ✅ | `trigger.ts:detectBotMention`, `textMentionsBot` |
| Mentions **array** in payload | 🟡 | mention *flags* (`isMentioned`) present; no structured `mentions[]` with names |
| Media metadata in payload | ✅ | `ai-payload.ts` → `metadata.media{hasMedia,mediaType,filename,mimetype,fileLength,messageId,caption}` |
| Media **download** | ✅ | `mcp/tools/media.ts:download_media_message` (Baileys `downloadMediaMessage` → disk + sha256) |
| Media metadata probe (no download) | ✅ | `mcp/tools/media.ts:get_message_metadata` |
| Group admin context | ✅ | `message-listener.ts:resolveGroupAdminMetadata` → `isGroupAdmin`, `groupAdmins[]` |
| Message cache for later download | ✅ | `socket-state.ts:cacheMessage` (last 500) |

**Gap:** wa-enggine downloads media on request, but **nothing on the AI side ever
calls `download_media_message`**, so `media.localPath` is never produced. The AI
sees `hasMedia: true` + filename and nothing else.

## 3. WhatsApp Output Capabilities

| Capability | Status | Where |
|---|---|---|
| Send text | ✅ | `messages.ts:send_text_message`, `wa_send_text` tool |
| Quoted reply to the user's msg | ✅ | `reply-context.ts` always replies quoting the incoming msg |
| `wa_send_reply` (reply to arbitrary msg id) | ❌ | not exposed as an AI tool |
| Send with **mentions array** | ❌ | no `send_text_with_mentions`; `messages.ts` send has no mentions support |
| Pin / announce | ✅ | `wa_pin_message`, `wa_set_announce` |
| Reaction / poll / location / contact | ✅ | `messages.ts` (MCP-level, not all surfaced as AI tools) |
| Admin WA healthcheck command | ❌ | no `/test-*` commands |

## 4. AI Payload Current Shape

From `ai-payload.ts:buildAIChatPayload` (top-level + `metadata`):

```
chat_id, sender_id, sender_name, message, chat_type, group_name,
metadata: {
  traceId, messageId, isGroup, groupJid, participantJid, senderJid, senderName,
  isGroupAdmin, senderIsGroupAdmin, groupAdmins[],
  quotedMessageId, quotedParticipantJid, quotedMessageText,
  triggerReason, isMentioned, hasPrefix, isReplyToBot,
  media: { hasMedia, mediaType, filename, mimetype, fileLength, messageId, caption } | null
}
```

vs. the master prompt's target payload:
- ❌ no structured `mentions[] {jid,name}` (only the `isMentioned` boolean)
- ❌ no `quotedMessage.mediaPath` / quoted media block
- ❌ no `media.localPath` (download not triggered)
- ✅ everything else is effectively present under `metadata`

The AI `ChatRequest` schema (`schemas/chat.py`) only declares
`metadata: dict`, so all of this flows through untyped — usable but unvalidated.

## 5. Tool Registry Current State

`tools/registry.py` registers ~70 tools across: general, obsidian, reminders,
planning(legacy), whatsapp(pin/announce/text), HEBAT (15), Life OS
(goals/tasks/money/workout/habit/daily), Knowledge (6), Research (13),
Skills (3), Learning roadmap (7), Graph RAG (7), HITL (5), admin notify, helper.

Missing categories from the Second-Brain spec:
- ❌ Media tools (`media_*`)
- ❌ Memory tools (`memory_*`)
- ❌ Context tools (`context_*`)
- ❌ WA reply/mention tools (`wa_send_reply`, `wa_send_text_with_mentions`, `wa_resolve_mentions`, `wa_get_message_context`)
- ❌ `graph_link_media`, `graph_sync_to_neo4j`, `graph_healthcheck`
- ❌ `system_*_healthcheck` admin tools

## 6. Command Router Current State

`ecosystem/command_router.py` handles: `/helper`, `/today`, `/goals`, `/tasks`,
`/money`, `/workout`, `/hebat`, `/review`, `/knowledge`, `/skills`, `/research`,
`/deep-research [mode]`, `/roadmaps`, `/roadmap`, `/study-today`, `/study-review`,
`/approvals`, `/approve N`, `/reject N`, `/skill X`, `/hebat-debug`.

Routing is deterministic (parsed in `chat.py` before LangGraph) and tools are
invoked directly with `chat_id/sender_id/sender_name/chat_type/metadata` injected.

Missing: all `/test-*`, `/media-*`, `/remember`, `/memory*`, `/forget-memory`,
`/knowledge-search`, `/knowledge-sources`, `/knowledge-rebuild`, `/graph-*`,
`/context-debug`. ⚠️ Note `/knowledge` already maps to `knowledge_search` but
expects no arg — `/knowledge-search <q>` would be a cleaner explicit form.

## 7. Media Handling Current State

- wa-enggine: ✅ download + metadata probe + shared `media_data` volume
  (`docker-compose.yml` mounts `wa-media` into both `ai` and `wa-enggine`).
- AI service: ❌ **no `app/media/` package at all.** No OCR, no audio
  transcription, no document parser wired to WA media. (PDF text extraction
  *does* exist but only for HEBAT downloads: `tools/hebat/pdf_reader.py`, and
  `knowledge/ingestion.py:ingest_pdf` reuses it.)
- Agent prompt *claims* multimodal handling but has no tools to back it ⚠️
  (prompt says "gunakan OCR/image analysis" — there is none).

## 8. Memory / Knowledge / Graph Current State

**Memory** 🟡→❌
- `memory/chat_store.py`: SQLite `chat_messages` raw history (works, used by chat).
- No `memories` / `conversation_summaries` tables, no semantic memory, no
  `memory_*` tools, no commands.

**Knowledge / FAISS** ✅
- `knowledge/`: `chunking.py`, `embeddings.py` (sentence-transformers with numpy
  TF-IDF fallback), `vector_store.py` (FAISS IndexFlatIP + FTS5 fallback + rebuild),
  `ingestion.py` (text/pdf, dedup by sha256), `rag.py`.
- Tables created in `db/sqlite.py`: `knowledge_sources`, `knowledge_chunks`,
  `knowledge_fts`. Tools: `knowledge_ingest_text/file`, `knowledge_search`,
  `knowledge_answer`, `knowledge_list_sources`, `knowledge_rebuild_index`.
- ⚠️ Schema differs from the master prompt (`content_hash` vs `sha256`,
  `faiss_id` vs `embedding_id`) — fine, just don't blindly re-create tables.
- ⚠️ FAISS dir env is `VECTOR_DATA_DIR=/app/data/vector`, not `FAISS_INDEX_DIR=/data/faiss`.

**Graph RAG** 🟡
- `graph_rag/`: SQLite `graph_nodes`/`graph_edges` (created in `db/migrations.py`),
  `graph_store.py` (add/search/edges), `graph_context.py`, tools
  (`graph_add_node/edge`, `graph_search`, `graph_get_context`, link helpers).
- ❌ No Neo4j store, no hybrid backend, no `graph_sync_to_neo4j`, no
  `graph_healthcheck`, no media/whatsapp node types.

## 9. Missing Capabilities (consolidated)

❌ AI-side media download + processing (OCR / audio transcript / doc parse)
❌ `app/media/` package, `media_items` table, media tools
❌ Semantic memory system (`memories`, `conversation_summaries`, `memory_*` tools)
❌ `app/context/` unified context builder (text+quoted+media+memory+knowledge+graph)
❌ Neo4j service + `neo4j_graph_store` + hybrid backend + graph healthcheck
❌ WA reply/mention output tools (`wa_send_reply`, `wa_send_text_with_mentions`)
❌ Structured `mentions[]` + quoted-media in WA payload
❌ Free research providers package (`research/providers/`: searxng/ddg/arxiv/crossref)
❌ `/test-*`, `/media-*`, `/memory*`, `/graph-*`, `/context-debug` commands
❌ `core/security.py` secret/path masking
❌ Docker volumes: `faiss_data`, `knowledge_data`, `media_data` (only ad-hoc `wa-media` exists), `neo4j_*`

⚠️ Risky / inconsistent:
- Agent prompt promises multimodal it cannot do (will hallucinate "I read your image").
- HEBAT browser session file is root-owned (Docker) → local runs fail to persist (see HEBAT_DEBUG_GUIDE).
- Knowledge env/table names diverge from the master prompt; reconcile before adding new code.

## 10. Priority Fix Order (recommended, WA-first, dependency-light first)

1. **Media → text → answer (documents first)** — highest value, lightest deps.
   wa-enggine already downloads; add a thin AI `media` module that calls
   `download_media_message` via MCP, parses pdf/docx/txt/md, and lets the agent
   answer from the content. (pypdf already a dep; add python-docx/openpyxl as
   optional.) No new infra.
2. **`core/security.py` masking** — tiny, unblocks safe `/test-*` + debug output.
3. **`/test-*` WA healthcheck commands** — pure-python, admin-only, no new deps;
   gives you the WA-first feedback loop the prompt wants.
4. **Image OCR** (pytesseract — needs `tesseract-ocr` system pkg) — medium.
5. **Audio transcription** (faster-whisper — needs model download) — heavier.
6. **Semantic memory system** (`memories` table + tools) — medium, no infra.
7. **Context builder** (`app/context/`) — depends on 1/5/6 + existing knowledge/graph.
8. **Neo4j service + hybrid graph backend** — heaviest infra; SQLite graph already works, so do last.
9. **Free research providers** (ddg/arxiv/crossref + optional SearxNG) — independent, can slot anytime.

Each step is independently shippable and testable; do **not** scaffold all
modules at once (violates "MVP jalan dulu / jangan rusak fitur lama").
```

