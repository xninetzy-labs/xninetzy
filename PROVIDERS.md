# Xninetzy Providers

Xninetzy ships a single default stack (SQLite + FAISS + local Obsidian
vault + stdio MCP) that works with zero optional dependencies. Heavier
backends are pluggable via the `ProviderAdapter`/`PluginAdapter`
shape — never a hard dependency of `xninetzy start`.

## Default stack (no opt-in required)

| Layer | Implementation | Required dependency |
|---|---|---|
| Persistence | SQLite | stdlib `sqlite3` |
| Vector index | FAISS | `faiss-cpu>=1.8` |
| Knowledge source | Obsidian vault (markdown) | None (filesystem) |
| MCP transport | stdio (primary) | `mcp>=1.28.1,<2` |
| MCP transport | Streamable HTTP (secondary, loopback) | `mcp>=1.28.1,<2` |
| OCR | Tesseract via `pytesseract` (opt-in via CAPTCHA config) | OS `tesseract` binary |
| External MCP intake | untrusted-by-default registry | None |

## Optional providers (adapter interface, not required)

Adapters follow this shape:

```
class ProviderAdapter(Protocol):
    id: str
    capabilities: list[str]
    async def health_check(self) -> bool: ...
    async def enable(self) -> None: ...
    async def disable(self) -> None: ...
```

Optional adapters currently referenced (not bundled):

| Provider | Capability | Status |
|---|---|---|
| Neo4j | GraphRAG V3 backend | `neo4j>=5.26` installed; autostart via docker-compose opt-in |
| Graphiti | Temporal knowledge graph (FalkorDB/Neo4j + Ollama) | Reference shape; consumed as external MCP via gateway if used at all |
| PageIndex | Document structure reasoning | Not bundled; pluggable |
| DSPy / GEPA / TextGrad | Prompt optimization | `xninetzy/tools/ecosystem/optimization_tools.py` graceful-degrades when libs missing |
| Mem0 / Letta | Long-term memory backends | Not bundled; pluggable |
| BGE / ColBERT / FlashRAG | Reranker / dense retriever | Not bundled; pluggable |
| DeepEval / Promptfoo / lm-eval-harness | Evaluation harnesses | Not bundled |
| Langfuse | Tracing export | Opt-in via env |

Adapters stay optional. `xninetzy release-check` does not require any
optional provider to be installed for a PASS verdict.

## Source adapters (Research + Career)

All sources use the `SourceAdapter` ABC + `SourceRecord` dataclass +
`RateLimiter` + `CircuitBreakerGuard` + `RetryPolicy` in
`xninetzy/os/research/sources/`. Each adapter declares its own
`rate_limit`, `retry`, and `circuit_breaker`; HTTP calls honor these.

Legal boundary: only sources with explicit free public API access.
LinkedIn / Indeed / JobStreet / Glints and similar walled-garden sites
are deliberately NOT integrated.
