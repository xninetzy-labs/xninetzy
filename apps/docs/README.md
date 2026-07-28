# Xninetzy Documentation

Documentation site statis untuk Xninetzy, dibangun dengan Astro 7. UI mengikuti design system terminal client: deep-space background, purple orbit, dan orange event-horizon accent.

## Prasyarat

- Node.js 22.12 atau lebih baru.
- Yarn 1.22.

## Menjalankan lokal

```bash
cd apps/docs
yarn install --frozen-lockfile
yarn dev
```

Buka `http://127.0.0.1:4321`.

## Quality checks

```bash
yarn check
yarn build
```

Production output berada di `apps/docs/dist` dan tidak masuk Git.

Preview output tersebut:

```bash
yarn preview --host 127.0.0.1
```

## Struktur

```text
apps/docs/
├── public/
│   ├── favicon.svg
│   └── og.svg
├── src/
│   ├── components/         # brand, header, search, sidebar, mobile drawer
│   ├── data/navigation.ts  # source of truth navigasi dan search index
│   ├── layouts/            # base HTML shell dan Markdown docs shell
│   ├── pages/
│   │   ├── docs/*.md       # seluruh panduan
│   │   └── index.astro     # landing page
│   └── styles/global.css   # design tokens dan responsive styles
├── astro.config.mjs
├── package.json
├── tsconfig.json
└── yarn.lock
```

## Menambah halaman

1. Buat file Markdown di `src/pages/docs`, misalnya `backup.md`.
2. Tambahkan frontmatter:

```yaml
---
layout: ../../layouts/DocsLayout.astro
title: Backup dan restore
description: Strategi backup vault dan database.
section: Operasional
---
```

3. Tulis isi Markdown.
4. Tambahkan item pada `src/data/navigation.ts`:

```ts
{
  title: 'Backup dan restore',
  description: 'Vault, database, dan runtime state.',
  href: '/docs/backup/'
}
```

5. Jalankan `yarn check && yarn build`.

Navigation data juga menjadi indeks pencarian client-side. Tidak ada search backend atau API key.

## Design system

Token utama berada pada `src/styles/global.css`:

| Token | Nilai | Peran |
|---|---|---|
| `--background-deep` | `#020008` | canvas |
| `--surface` | `#05010f` | cards dan code |
| `--purple` | `#8b5cf6` | primary accent |
| `--purple-bright` | `#c084fc` | active state |
| `--orange` | `#f97316` | event/action accent |
| `--lavender` | `#ddd6fe` | reading text |

Pertahankan contrast, keyboard focus, mobile layout, dan `prefers-reduced-motion`. Gunakan SVG/code-native visual untuk diagram ringan; hindari dependency UI hanya untuk satu komponen.

## Konten dan keamanan

- Gunakan placeholder untuk API key, password, nomor, JID, dan path personal.
- Jangan menyalin `.env`, cookie, session, log, atau course material ke docs.
- Jelaskan current security boundary secara jujur; jangan mengklaim endpoint aman jika guard belum diterapkan.
- Perbarui root `README.md` ketika command atau struktur utama berubah.

## Deployment

Site menggunakan `output: 'static'` dan menghasilkan HTML/CSS/JS portabel. Upload isi `dist` ke static hosting pilihanmu. Jika memakai subpath, set `base` pada `astro.config.mjs` dan gunakan `import.meta.env.BASE_URL` untuk asset/link yang membutuhkan prefix.

Untuk canonical URL dan social metadata produksi, tambahkan nilai `site` pada `astro.config.mjs` setelah domain final diketahui.
