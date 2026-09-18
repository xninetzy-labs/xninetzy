---
name: 2026-09-18-audit-research-expansion
description: Audit of Research MCP expansion across 30+ source categories. Cross-reference requested sources vs currently implemented adapters in xninetzy. From-scratch foundation per Q1=a decision.
metadata:
  type: audit
  date: 2026-09-18
  scope: project
  authority:
    - AGENTS.md
    - global opencode AGENTS.md
---

# Research Expansion Audit — 2026-09-18

## Scope

Audit of currently implemented source adapters vs the 30+ source categories
proposed in the Research MCP expansion request. Foundation decision
(from this turn): **Q1=a = all from-scratch, no external MCP gateway**.

## Currently implemented source adapters

Verified live via grep against `xninetzy/os/research/` + `xninetzy/os/web_analysis/`:

| Source | File | Free/Paid | Notes |
|---|---|---|---|
| arXiv | `os/research/academic_search.py:10-150` | Free | Atom XML, no key |
| Crossref | `os/research/academic_search.py:12-217` | Free | REST, no key |
| Tavily | `os/research/web_search.py:54-71` | Paid | `TAVILY_API_KEY` |
| Serper | `os/research/web_search.py:74-91` | Paid | `SERPER_API_KEY` |
| SearXNG | `os/research/web_search.py:121-131` | Free (self-host) | `SEARXNG_BASE_URL` |
| DuckDuckGo | `os/research/web_search.py:94-118` | Free | via `ddgs` lib |
| YouTube | `os/research/youtube_search.py` | Free quota | `YOUTUBE_API_KEY` |
| PixelRAG | `tools/ecosystem/pixelrag_tools.py` | Free | Self-hosted + public |
| Web Analysis sites | `os/web_analysis/sites.py` | N/A | Allowlist (hebat, mahasiswa, qa) |

**Total: 9 working adapters.** All others: NOT IMPLEMENTED.

## Source coverage matrix

Mark per category:

- ✅ EXISTING — working adapter
- ⚠ PARTIAL — stub or limited
- ❌ MISSING — no implementation
- 🚫 OUT-OF-SCOPE — legal/ToS/paid-only barrier

| # | Category | Status | Free priority | Notes |
|---|---|---|---|---|
| 1 | WEB / Search Engines | ✅ | DDGS + SearXNG | Tavily/Serper optional paid |
| 2 | GitHub | ❌ | gh CLI only, no API adapter | ToS: respect rate limits, no scraping |
| 3 | Reddit | ❌ | JSON API free | No auth for read |
| 4 | Hacker News | ❌ | Algolia free | hn.algolia.com |
| 5 | News | ⚠ | via web_search | No dedicated news adapter |
| 6 | RSS | ❌ | Free | No parser in tree |
| 7 | Academic Papers | ⚠ | arXiv+Crossref only | Missing: OpenAlex, Semantic Scholar, PubMed, OpenReview, DOAJ, DBLP, ORCID |
| 8 | Datasets | ❌ | Free | Missing: HF, Kaggle, UCI, OpenML, Zenodo, Figshare, World Bank, BPS |
| 9 | AI Models | ❌ | Free | Missing: HF Models, PapersWithCode, LMSYS |
| 10 | Startups/Companies | ❌ | Mostly paid | Crunchbase, PitchBook = paid only |
| 11 | Government (ID) | ❌ | Free | BPS Web API requires registration |
| 12 | Economics | ❌ | Mostly free | World Bank no key; FRED no key |
| 13 | Security | ❌ | Free | NVD, CVE, MITRE, CISA KEV, OSV |
| 14 | Patents | ❌ | Free | Google Patents, USPTO, WIPO |
| 15 | Jobs | 🚫 | ToS barrier | LinkedIn/Indeed block scraping |
| 16 | Social Media | ⚠ | YouTube only | X/IG/TikTok = ToS barrier |
| 17 | YouTube | ✅ | Free quota | Full coverage |
| 18 | Package ecosystems | ❌ | Free | NPM, PyPI, Crates, Maven, Docker |
| 19 | Docs/Standards | ❌ | Free | IETF, W3C, MDN, Python docs |
| 20 | Knowledge Graphs | ❌ | Free | Wikidata, DBpedia |
| 21 | Geospatial | ❌ | Free | OSM, Nominatim, Overpass |
| 22 | Health | ❌ | Free | PubMed E-utilities, WHO, ClinicalTrials.gov |
| 23 | Climate | ❌ | Free | NOAA, Open-Meteo, Copernicus |
| 24 | Finance | ⚠ | Free | SEC EDGAR, FRED, Yahoo Finance |
| 25 | Product Research | 🚫 | ToS barrier | Amazon/Shopee/Tokopedia anti-bot |
| 26 | Research Archive | ❌ | Free | Internet Archive Wayback, Common Crawl |
| 27 | Conferences | ❌ | Free | ACL Anthology, NeurIPS proceedings, OpenReview |
| 28 | Research Funding | ❌ | Free | NSF, NIH, CORDIS |
| 29 | People/Institutions | ❌ | Free | ORCID, ROR |
| 30 | Benchmark Intelligence | ❌ | Free | PapersWithCode, HF Leaderboards, LMSYS |
| 31 | MCP Ecosystem | ❌ | Free | Official Registry, Glama, Smithery |

## Gap counts

- ✅ Existing: 2 (Web/Search Engines, YouTube)
- ⚠ Partial: 3 (News, Academic Papers, Finance)
- ❌ Missing: 24
- 🚫 Out-of-scope: 2 (Jobs, Product Research)

## Foundation decision: from-scratch (Q1=a)

Per Q1=a, **no external MCP gateway** (no spawning GitHub MCP, Reddit MCP, etc.
as child processes). All adapters built in-tree.

Rationale:
- Avoid upstream dependency on third-party MCP server availability
- Avoid transitive security surface (child MCP = arbitrary code)
- Avoid ToS drift when upstream changes
- Reuse existing Xninetzy infra: idempotency, harness, tier gate, audit

Trade-off:
- More in-tree code to maintain
- Slower to reach breadth
- Mitigated by: per-adapter is small, free public APIs all follow similar patterns

## Recommended adapter implementation priority

Phase 1 (this turn + next, foundation):
1. Source registry schema + base adapter class (`xninetzy/os/research/sources/`)
2. OpenAlex adapter (largest free academic graph, no key)
3. arXiv adapter (already exists, wrap in registry)
4. Crossref adapter (already exists, wrap in registry)
5. Source router (intent → source list)

Phase 2 (deferred, next turn):
6. Semantic Scholar adapter (citations)
7. PubMed E-utilities (health/biomed)
8. Wikidata SPARQL (entity resolution)
9. World Bank API (econ/government)
10. BPS Web API (Indonesia stats, requires registration)
11. NVD/CVE (security)
12. Internet Archive Wayback (archive)
13. Hacker News Algolia (community)
14. RSS aggregator (news/catchall)

Phase 3 (deferred, later turn):
15-30. Remaining per user list, prioritizing free public APIs.

## Adapter pattern (proposed)

```python
class SourceAdapter:
    id: str
    category: str
    base_url: str
    requires_api_key: bool
    rate_limit: RateLimit
    retry: RetryPolicy
    circuit_breaker: CircuitBreaker

    async def search(self, query, limit, **kwargs) -> list[SourceRecord]: ...
    async def fetch(self, identifier) -> SourceRecord | None: ...
    async def health(self) -> HealthStatus: ...
```

Each adapter:
- Emits `harness_checkpoint_commit(plan_id, step_id, status)` on completion
- Honors `idempotency_key` if provided
- Returns `SourceRecord` with: title, url, source, source_type, published_at,
  author, snippet, content, language, license, retrieved_at, confidence,
  primary_source, citation
- Circuit breaker: 5 failures → open for 60s → half-open probe

## RiskClass mapping for new research tools

| Tool | RiskClass | Tier |
|---|---|---|
| `research_search` | READ | 0 |
| `research_fetch` | READ | 0 |
| `research_compare_sources` | READ | 0 |
| `research_grade_evidence` | READ | 0 |
| `research_cite` | WRITE | 1 (idempotency required) |
| `research_save_search` | WRITE | 1 |

All Tier 0/1. No FINAL. Research never mutates external academic sources
or graded records. Safe for auto-execution.

## Out-of-scope adapters (deferred)

- LinkedIn Jobs, Indeed: ToS violation per scraping
- Amazon, Shopee, Tokopedia: anti-bot + ToS
- X (Twitter), Instagram, TikTok: paywalled APIs, ToS
- Crunchbase, PitchBook: paid only, no free tier
- Any source requiring authentication scraping of gated content

## Skills gap

Existing skills: 36 built-in (per AGENTS.md §6). Audit of `.agents/skills/`:
- `cyber-campus`, `hebat-academic`, `hebat-assignment` — UNAIR specific
- `xninetzy-*` — orchestrator family
- `pdf`, `transcribe`, `screenshot` — media
- `playwright*`, `security-*` — engineering/security
- `regression-analysis`, `context-engineering`, `graph-rag`, `code-review` — meta

Proposed meta-skills (5 from this turn):
- `research-planner` — query → plan
- `source-selector` — plan → source list
- `evidence-grader` — result → grade
- `contradiction-hunter` — results → contradictions
- `research-critic` — synthesis → critique

Deferred (25):
- Discovery: topic, trend, paper, dataset, startup, competitor, open-source,
  mcp, benchmark
- AI: literature-review, paper-analysis, sota-analysis, benchmark-analysis,
  model-comparison, research-gap-analysis, experiment-design,
  hypothesis-generation
- Engineering: repository-analysis, architecture-analysis,
  dependency-analysis, implementation-discovery, technology-evaluation,
  documentation-research
- Business: market-research, competitor-analysis, startup-analysis,
  product-analysis, pricing-research, opportunity-discovery
- Security: security-research, vulnerability-research, cve-analysis,
  threat-intelligence, mcp-security-audit, supply-chain-analysis
- MCP: server-discovery, server-evaluation, server-monitoring,
  tool-routing, permission-audit

## Sources

- `xninetzy/os/research/academic_search.py`
- `xninetzy/os/research/web_search.py`
- `xninetzy/os/research/youtube_search.py`
- `xninetzy/os/research/deep_research.py`
- `xninetzy/os/web_analysis/sites.py`
- `xninetzy/tools/ecosystem/pixelrag_tools.py`
- `xninetzy/tools/ecosystem/research_tools.py`
- `xninetzy/tools/ecosystem/web_evidence_tools.py`
- `xninetzy/tools/ecosystem/web_analysis_tools.py`
- `xninetzy/core/config.py` — env vars
- Audit v1 doc: `2026-09-18-audit-tool-surface.md`
