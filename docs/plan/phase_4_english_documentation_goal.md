# Phase 4 — Professional English Documentation

Status: complete  
Schedule: weeks 9–10

## Goal

Ship reviewed, navigable English documentation that helps users install,
operate, extend, and safely maintain Xninetzy.

## Design decisions

- English is the canonical and only public documentation language.
- Each guide has one Markdown source and one stable route under `/docs/`.
- The site has no runtime locale state, language localStorage, translated DOM
  attributes, or duplicate `/docs/en/` and `/docs/id/` routes.
- Documentation is part of every feature slice, not release-only work.

## Scope

1. Keep installation, provider selection, feature packs, CLI, MCP setup, skills,
   security, backup, troubleshooting, and migration guides in English.
2. Keep architecture, tool-contract, evidence, approval, and lifecycle diagrams
   synchronized with code.
3. Keep portfolio and GitHub links in the site header.
4. Validate frontmatter, navigation, internal routes, Astro check, and the static
   build whenever documentation changes.

## Acceptance gate

- Every public documentation page is English-only.
- No locale selector, localization state, or duplicate locale routes remain.
- Documentation navigation has no broken internal links.
- `yarn check` and `yarn build` pass.
