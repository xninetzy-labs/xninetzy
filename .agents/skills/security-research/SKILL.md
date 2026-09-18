---
name: security-research
description: Research a CVE, advisory, or vulnerability topic. Pulls from NVD (when available) + web sources. Surfaces affected packages, severity, exploits.
metadata:
  type: workflow
  layer: research-security
  consumes:
    - research_search
    - research_fetch
    - evidence-grader
    - contradiction-hunter
  produces:
    - security_brief
  tier: 0
---

# security-research

Structured brief on a CVE, advisory, or vulnerability topic.

## When to invoke

- User asks "CVE-XXXX-XXXXX", "is X vulnerable", "what's the impact of Y"
- A new vulnerability disclosure needs triage

## Workflow

```yaml
steps:
  - id: search_papers_and_advisories
    tool: research_search
    args:
      intent: security
      query: "<CVE-id or topic>"
      limit: 10
    tier: 0
  - id: cross_check
    tool: research_compare_sources
    depends_on: [search_papers_and_advisories]
    tier: 0
  - id: grade
    tool: research_grade_evidence
    depends_on: [cross_check]
    tier: 0
  - id: hunt_contradictions
    tool: contradiction-hunter
    depends_on: [grade]
    tier: 0
```

## Output structure

```yaml
security_brief:
  identifier: "<CVE or topic>"
  aliases: ["GHSA-...", "..."]
  affected_packages:
    - name: "<pkg>"
      ecosystem: pypi | npm | crates | maven | ...
      vulnerable_versions: "<range>"
      patched_versions: "<version>"
  severity: low | medium | high | critical | unknown
  cvss: <number | null>
  exploit_status: theoretical | poc-public | in-the-wild | unknown
  mitigations:
    - "<step>"
  contradictions:
    - topic: "<where sources disagree>"
      verdict: requires_investigation | likely_different_setup | likely_error
  references:
    - title, url, citation, evidence_grade
```

## Constraints

- Always cite primary source (NVD or vendor advisory) when available.
- NVD is the only direct CVE adapter currently wired. OSV.dev and
  GitHub Advisory Database adapters are deferred; web search is the
  fallback for non-NVD sources.
- Surface exploit_status explicitly; do not default to "unknown" without
  searching at least 2 sources.
- Do NOT propose code patches in the brief; surface affected versions only.

## Anti-patterns

- Do NOT grade a CVE severity yourself; defer to CVSS / NVD when available.
- Do NOT recommend disabling a security control without owner approval.
- Do NOT include unverified exploit code or PoC URLs.
