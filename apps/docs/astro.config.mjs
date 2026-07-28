import { defineConfig } from 'astro/config';

export default defineConfig({
  output: 'static',
  trailingSlash: 'always',
  build: {
    format: 'directory'
  },
  compressHTML: true
});
