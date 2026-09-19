---
name: "mcp-discovery"
description: "Discover MCP servers for a given capability need. Searches official registry, GitHub, and awesome-mcp lists. Outputs ranked list with health + security notes."
metadata:
  type: "workflow"
  layer: "mcp-ecosystem"
  consumes:
    - research_search (via web_search fallback)
    - research_fetch
    - evidence-grader
  produces:
    - mcp_shortlist
  tier: "0"
---

# mcp-discovery

Find MCP servers that match a capability need. Owner-curated shortlist with
health, security, and license signals.

## When to invoke

- User asks "find an MCP for X", "best MCP for research",
  "what MCP handles Y"
- A new capability is needed but no in-tree tool exists

## Workflow

```yaml
steps:
  - id: search_official
    tool: research_search (web fallback)
    args:
      query: "<capability> MCP server site:registry.modelcontextprotocol.io OR site:github.com"
      limit: 10
    tier: 0
  - id: search_awesome
    tool: research_search (web fallback)
    args:
      query: "<capability> MCP awesome list"
      limit: 10
    tier: 0
  - id: compare
    tool: research_compare_sources
    depends_on: [search_official, search_awesome]
    tier: 0
  - id: grade
    tool: research_grade_evidence
    depends_on: [compare]
    tier: 0
  - id: health_hint
    tool: web_analysis_status (if site_slug known)
    tier: 0
```

## Output structure

```yaml
mcp_shortlist:
  capability: "<echo>"
  candidates:
    - name
      repo_url
      description
      stars: <int | null>
      last_commit: <iso | null>
      license: <string | null>
      security_notes: "<child-process risk | stdio transport | env vars>"
      evidence_grade: strong | moderate | weak | uncertain
      health: healthy | degraded | unreachable | unknown
  recommendation: "<name + 1-line rationale>"
```

## Constraints

- Only recommend servers with `evidence_grade >= moderate`.
- Always surface security_notes (child process, env vars, transport).
- Note `last_commit` age; > 12 months = stale.

## Anti-patterns

- Do NOT recommend a server without a license check.
- Do NOT skip security_notes for "obvious" picks.
- Do NOT spawn or call any MCP server during the discovery phase —
  discovery is read-only. After owner approval, installation may proceed
  via `skill_install` or the external MCP registry workflow; that is a
  separate phase from this skill's scope.
