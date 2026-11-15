# AGENTS.md — §17–21

Part of the AGENTS.md policy; binds equally.

Contents: 17. Security-Control Testing; 18. Scraping; 19. Recursive Crawling; 20. Dynamic Scraping; 21. Scraping Adaptation

## 17. Security-Control Testing

When testing security controls in an explicitly authorized environment, the agent may analyze whether controls can be circumvented.

Examples:

```text
authentication bypass testing
authorization bypass testing
session handling testing
CAPTCHA implementation analysis
rate-limit testing
input validation testing
access-control testing
```

The objective must remain:

```text
TEST THE SECURITY CONTROL
```

not:

```text
GAIN UNAUTHORIZED ACCESS
```

---

## 18. Scraping

Scraping is a first-class data-acquisition capability.

The agent may autonomously:

```text
DISCOVER
→ CRAWL
→ FETCH
→ PARSE
→ EXTRACT
→ NORMALIZE
→ DEDUPLICATE
→ VALIDATE
→ STORE
→ ANALYZE
```

when the data source and access are authorized/permitted.

---

## 19. Recursive Crawling

The crawler may recursively follow relevant links.

Controls:

```text
max_depth
max_pages
max_requests
max_bytes
max_runtime
domain_allowlist
path_allowlist
rate_limit
```

The crawler should automatically stop when:

```text
scope exhausted
budget exhausted
source exhausted
duplicate threshold reached
stop condition triggered
```

---

## 20. Dynamic Scraping

When static HTTP extraction is insufficient, the agent may switch:

```text
HTTP
→ Browser
→ Rendered DOM
→ Network-observable public data
→ Structured extraction
```

Do not repeatedly retry an extraction method that is structurally incapable of obtaining the required data.

---

## 21. Scraping Adaptation

If a parser fails because a webpage changed:

```text
DETECT
→ INSPECT NEW STRUCTURE
→ UPDATE EXTRACTION STRATEGY
→ VALIDATE SAMPLE
→ CONTINUE
```

The agent may adapt selectors and extraction logic.

It must preserve the source and provenance.

---
