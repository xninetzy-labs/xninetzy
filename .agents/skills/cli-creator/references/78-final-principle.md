# cli-creator — §78

## 78. Final Principle

The resulting CLI should feel like:

```text
a stable API for agents
```

rather than:

```text
a collection of shell commands
```

The ideal architecture is:

```text
SOURCE
  ↓
API/WORKFLOW MODEL
  ↓
COMMAND CONTRACT
  ↓
DOMAIN CLIENT
  ↓
AUTH + CONFIG
  ↓
STABLE JSON
  ↓
INSTALLABLE BINARY
  ↓
COMPANION SKILL
```

The final quality bar is:

```text
portable
composable
deterministic
machine-readable
safe by default
explicit about writes
easy to diagnose
easy to install
easy for future agents to reuse
```

And the governing rule is:

> **Build high-level commands for real workflows; keep the raw API escape hatch as an escape hatch, not as the entire CLI.**

---

Struktur ini juga sengaja membuat **`doctor` + `resolve` + stable JSON + verification** menjadi bagian inti, bukan fitur tambahan. Jadi future Codex thread bisa mengikuti pola:

```text
tool --json doctor
        ↓
resource list
        ↓
resource resolve
        ↓
resource get
        ↓
narrow action
        ↓
status/verify
```
