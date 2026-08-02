# Xninetzy Documentation

Static documentation site for Xninetzy, built with Astro 7. The UI follows the terminal client design system: a deep-space background, purple orbit, and orange event-horizon accent.

## Prerequisites

- Node.js 22.12 or newer.
- Yarn 1.22.

## Run locally

```bash
cd apps/docs
yarn install --frozen-lockfile
yarn dev
```

Open `http://127.0.0.1:4321`.

## Quality checks

```bash
yarn check
yarn build
```

Production output is written to `apps/docs/dist` and is not tracked by Git.

Preview that output:

```bash
yarn preview --host 127.0.0.1
```

## Structure

```text
apps/docs/
├── public/
│   ├── favicon.svg
│   └── og.svg
├── src/
│   ├── components/         # brand, header, search, sidebar, mobile drawer
│   ├── data/navigation.ts  # source of truth for navigation and the search index
│   ├── layouts/            # base HTML shell and Markdown documentation shell
│   ├── pages/
│   │   ├── docs/*.md       # all guides
│   │   └── index.astro     # landing page
│   └── styles/global.css   # design tokens and responsive styles
├── astro.config.mjs
├── package.json
├── tsconfig.json
└── yarn.lock
```

## Add a page

1. Create a Markdown file in `src/pages/docs`, for example `backup.md`.
2. Add frontmatter:

```yaml
---
layout: ../../layouts/DocsLayout.astro
title: Backup and restore
description: Vault and database backup strategy.
section: Operations
---
```

3. Write the Markdown content.
4. Add an item to `src/data/navigation.ts`:

```ts
{
  title: 'Backup and restore',
  description: 'Vault, database, and runtime state.',
  href: '/docs/backup/'
}
```

5. Run `yarn check && yarn build`.

Navigation data also provides the client-side search index. It does not require a search backend or API key.

## Design system

The primary tokens live in `src/styles/global.css`:

| Token | Value | Role |
|---|---|---|
| `--background-deep` | `#020008` | canvas |
| `--surface` | `#05010f` | cards and code |
| `--purple` | `#8b5cf6` | primary accent |
| `--purple-bright` | `#c084fc` | active state |
| `--orange` | `#f97316` | event/action accent |
| `--lavender` | `#ddd6fe` | reading text |

Preserve contrast, keyboard focus, the mobile layout, and `prefers-reduced-motion`. Use SVG or code-native visuals for lightweight diagrams; avoid adding a UI dependency for a single component.

## Content and security

- Use placeholders for API key, password, phone numbers, JIDs, and personal paths.
- Do not copy `.env`, cookie, session, log, or course material into documentation.
- Describe the current security boundary accurately; do not claim an endpoint is secure when its guard is not implemented.
- Update the root `README.md` when commands or the main structure change.

## Deployment

Site uses `output: 'static'` and produces portable HTML/CSS/JS. Upload the contents of `dist` to your preferred static host. When deploying to a subpath, set `base` in `astro.config.mjs` and use `import.meta.env.BASE_URL` for assets or links that require the prefix.

For the production canonical URL and social metadata, add a `site` value to `astro.config.mjs` after the final domain is known.
