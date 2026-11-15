# context-engineering — §80

## 80. Final Principle

The Xninetzy context engine should behave like:

```text
INTENT ROUTER
+
EVIDENCE FILTER
+
CONTEXT COMPRESSOR
+
STATE TRACKER
+
CAPABILITY SELECTOR
+
CACHE / RECOMPUTE CONTROLLER
```

not:

```text
PROMPT DUMPER
```

The target architecture is:

```text
USER INTENT
    ↓
TASK MODEL
    ↓
SKILL ROUTING
    ↓
TOOL ROUTING
    ↓
EVIDENCE RETRIEVAL
    ↓
RELEVANCE / FRESHNESS RANKING
    ↓
CONTRADICTION CHECK
    ↓
BUDGET ENFORCEMENT
    ↓
MINIMUM SUFFICIENT CONTEXT
    ↓
EXECUTION
    ↓
RESULT COMPRESSION
    ↓
STATE UPDATE
    ↓
TARGETED RECOMPUTATION
```

The key optimization objective is:

> **Maximum decision quality per token, with no loss of critical constraints, evidence, provenance, authorization, or unresolved uncertainty.**

And the governing invariant is:

> **Never confuse a smaller context with a better context; the correct context is the smallest one that remains sufficient, fresh, trustworthy, and safe.**

---
