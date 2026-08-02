# Phase 4 — Professional Bilingual Documentation

Status: planned  
Schedule: weeks 9-10

## Goal

Ship reviewed, navigable documentation that helps users install, operate,
extend, and safely maintain Xninetzy.

## Design decisions

- Documentation uses paired reviewed pages at `/docs/en/` and `/docs/id/`.
  English is canonical for technical contracts.
- Runtime text switching does not replace translated page content.
- Documentation is part of each feature slice, not release-only work.

## Scope

1. Replace partial language switching with paired English and Indonesian routes
   and a persistent language switcher.
2. Document installation, provider selection, feature packs, CLI, MCP setup,
   skills, security, backup, troubleshooting, and migrations.
3. Add architecture, tool-contract, evidence, approval, and lifecycle diagrams
   that match code.
4. Add portfolio and GitHub links for the project owner.

## Acceptance gate

- Every public page has a reviewed counterpart or explicit translation status.
- Documentation navigation has no broken internal links.
