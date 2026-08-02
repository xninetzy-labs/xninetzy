# V1 Release Readiness

## Quality gates

- Run AI Ruff and the full pytest suite.
- Run WhatsApp lint, test, and build.
- Run CLI and Astro docs check/build.
- Run `xninetzy doctor --docker` with a clean local `.env`.

## Security and data

- Do not track `.env`, sessions, browser state, SQLite, vault files, downloads, or generated documents.
- Verify the Apache-2.0 `LICENSE` is present and release notes state supported platforms.
- Keep services on loopback unless an owner deliberately configures a private network boundary.

## Support baseline

Linux, macOS, Windows with WSL2/Docker Desktop, CPU-only execution, and Ollama or an enabled compatible provider are supported. No V1 capability requires a GPU, cloud account, or paid API.
