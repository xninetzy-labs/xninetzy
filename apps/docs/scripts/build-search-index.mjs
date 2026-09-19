#!/usr/bin/env node
import { readFileSync, writeFileSync, readdirSync, statSync, mkdirSync } from 'node:fs';
import { join, dirname, relative } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const root = join(here, '..');
const docsDir = join(root, 'src', 'pages', 'docs');
const outDir = join(root, 'public');
const outPath = join(outDir, 'search-index.json');

const stripFrontmatter = (text) => text.replace(/^---\r?\n[\s\S]*?\r?\n---\r?\n/, '');

const walk = (dir) => {
  const out = [];
  for (const name of readdirSync(dir)) {
    const p = join(dir, name);
    if (statSync(p).isDirectory()) out.push(...walk(p));
    else if (name.endsWith('.md') && name !== 'index.md') out.push(p);
  }
  return out;
};

const extract = (text, key) => {
  const m = text.match(new RegExp(`^${key}:\\s*(.+)$`, 'm'));
  return m ? m[1].trim() : '';
};

const plain = (md) =>
  md
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`([^`]+)`/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1')
    .replace(/[#>*_~|-]+/g, ' ')
    .replace(/\s+/g, ' ')
    .trim();

const hrefFor = (absPath) => {
  const rel = relative(docsDir, absPath).replace(/\\/g, '/');
  const noExt = rel.replace(/\.md$/, '');
  return `/docs/${noExt}/`;
};

const files = walk(docsDir);
const index = files.map((p) => {
  const raw = readFileSync(p, 'utf8');
  const fm = raw.match(/^---\r?\n([\s\S]*?)\r?\n---/);
  const title = fm ? extract(fm[1], 'title') : '';
  const description = fm ? extract(fm[1], 'description') : '';
  const body = plain(stripFrontmatter(raw));
  return {
    title: title || 'Untitled',
    description: description || body.slice(0, 160),
    href: hrefFor(p),
    body
  };
});

mkdirSync(outDir, { recursive: true });
writeFileSync(outPath, JSON.stringify(index));
console.log(`[search] indexed ${index.length} pages -> ${relative(root, outPath)}`);
