# AGENTS.md — §38–40

Part of the AGENTS.md policy; binds equally.

## 38. Full Autonomous Optimization

The agent may autonomously optimize:

```text
latency
parallelism
cache usage
token usage
context size
request batching
source ordering
parser performance
database queries
memory retrieval
browser interaction count
scraping efficiency
retry strategy
```

Optimization must be validated empirically.

---

## 39. Browser Efficiency

For browser workflows:

```text
observe once
→ plan multiple compatible actions
→ execute batch
→ observe again
```

Avoid:

```text
observe
click
observe
click
observe
click
```

when the page state permits safe batching.

After significant navigation or DOM mutation, re-observe.

---

## 40. Intelligent Browser Navigation

The agent may automatically:

- follow links
- inspect menus
- traverse pagination
- detect redirects
- detect modals
- inspect forms
- discover API endpoints
- inspect structured metadata
- compare page states
- detect dynamic loading.

It should maintain a browser task state.

---
