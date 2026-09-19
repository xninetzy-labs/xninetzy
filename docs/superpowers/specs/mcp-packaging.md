# MCP packaging and distribution

How Xninetzy is built, distributed, and installed.

## Build a wheel + sdist

`pyproject.toml` declares `hatchling` as the build backend and
`xninetzy` as the wheel target:

```toml
[build-system]
requires = ["hatchling>=1.26"]
build-backend = "hatchling.build"

[project]
name = "xninetzy-mcp"
version = "1.0.0"
license = "LicenseRef-Xninetzy-Source-Available-2.2.0"

[project.scripts]
xninetzy     = "xninetzy.cli.supervisor:main"
xninetzy-cli = "xninetzy.cli.orchestrator:main"

[tool.hatch.build.targets.wheel]
packages = ["xninetzy"]

[tool.hatch.build.targets.sdist]
include = ["xninetzy", "README.md", "LICENSE", "scripts", "tests", "docs"]

[tool.uv]
package = true
```

`MANIFEST.in` ships LICENSE + README + recursive tests / docs /
skills / installers so the sdist is self-contained.

Build locally:

```bash
uv build
# dist/xninetzy_mcp-1.0.0-py3-none-any.whl
# dist/xninetzy_mcp-1.0.0.tar.gz
```

## Verify a built wheel in a fresh venv

```bash
rm -rf /tmp/xninetzy-wheel-test
uv venv /tmp/xninetzy-wheel-test --python python3.14
VIRTUAL_ENV=/tmp/xninetzy-wheel-test uv pip install dist/xninetzy_mcp-1.0.0-py3-none-any.whl
/tmp/xninetzy-wheel-test/bin/xninetzy release-check
/tmp/xninetzy-wheel-test/bin/python -m xninetzy.cli.supervisor release-check
```

Both invocations should print:

```text
  [PASS   ] tool_registry            343 tools classified
  [PASS   ] secret_redaction         3/3 sample secrets redacted
  [PASS   ] safe_fetch               3/3 SSRF guard scenarios blocked
  [PASS   ] transport_config         transport=stdio host=127.0.0.1
  [PASS   ] sdk_pin                  mcp resolved=1.x
  [PASS   ] canonical_final_tools    3 FINAL tools match canonical set
overall: PASS
```

## Install paths

Three install paths exist; each clones the source repo. Direct
`pip install xninetzy-mcp` from PyPI is not yet published — the wheel
is built but the source-available license plus `Private :: Do Not
Upload` classifier block auto-upload.

| Path | Script | OS |
|---|---|---|
| One-line | `curl ... \| bash` | Linux, macOS |
| One-line | `iwr ... \| iex` | Windows |
| Manual | `git clone` + `uv sync --all-extras` | any |

### Bash one-liner (Linux + macOS)

```bash
curl -fsSL https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.sh | bash
```

What it does:

1. detects OS via `uname -s` (refuses to run on Windows / unsupported)
2. ensures `git`, `openssl`, and `uv` (auto-install via brew on macOS,
   `astral.sh` on Linux)
3. clones the repo at `XNINETZY_BRANCH` (default `main`) into
   `XNINETZY_INSTALL_DIR` (default `~/xninetzy`)
4. installs OS deps via the system package manager:
   - Debian/Ubuntu: `tesseract-ocr`, `tesseract-ocr-eng`, `sqlite3`,
     `libatlas3-base`, `liblapack3`, `libgomp1`, `libxml2`, `libxslt1.1`
   - Fedora/RHEL: `tesseract`, `tesseract-langpack-eng`, `sqlite`,
     `atlas`, `lapack`, `libgomp`, `libxml2`, `libxslt`, `openssl-devel`
   - Arch: `tesseract`, `tesseract-data-eng`, `sqlite`, `atlas`,
     `lapack`, `libxml2`, `libxslt`, `openssl`
   - macOS (brew): `tesseract`, `sqlite`
5. installs Playwright Chromium (`python -m playwright install chromium
   --with-deps`)
6. opt-in Neo4j: set `XNINETZY_INSTALL_NEO4J=true` to install via apt
   repo (Linux) or brew (macOS) and write `NEO4J_ENABLED=true` to
   `.env`
7. delegates the rest to `scripts/setup-mcp.sh` (env, dirs, sync,
   release-check)
8. prints an install summary table (paths, versions, masked key)

### PowerShell one-liner (Windows)

```powershell
iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
```

Mirror image of the bash installer:

- forces TLS 1.2 (`[Net.ServicePointManager]::SecurityProtocol`)
- ensures `git`; auto-installs `uv` to `%USERPROFILE%\.local\bin`
- clones, copies `.env`, sets hidden attribute on `.env`
- skips OS package step (SQLite ships with Python; Tesseract is optional
  via the official Windows installer)
- delegates to `scripts/setup-mcp.ps1`

### Manual install

```bash
git clone https://github.com/xninetzy-labs/xninetzy
cd xninetzy
bash scripts/setup-mcp.sh
```

## Setup (post-install verification)

`scripts/setup-mcp.sh` (Linux/macOS) and `scripts/setup-mcp.ps1`
(Windows) are idempotent and run after the installer:

1. create `.env` from `.env.example` if missing
2. write a random `AI_API_KEY` via `openssl rand -hex 32` (or
   `secrets.token_hex(32)` if `openssl` is unavailable)
3. write `OBSIDIAN_VAULT_HOST_PATH`, `DATA_DIR`, `OUTPUT_DIR`
4. create the vault, data, and output directories
5. run `uv sync --all-extras`
6. run the release gate (`xninetzy.cli.supervisor release-check`)
7. print the connection summary (path, dirs, stdio + Streamable HTTP
   start commands, `claude mcp add` snippet)

Re-running the setup script is safe — it only writes empty keys.

Flags:

```bash
bash scripts/setup-mcp.sh --no-validate   # skip release-check
bash scripts/setup-mcp.sh --help         # print top-of-file docstring
```

## Release gate

```bash
uv run python -m xninetzy.cli.supervisor release-check
```

Six checks must pass:

| Check | Verifies |
|---|---|
| `tool_registry` | 343 tools classified, no unknown risk, no missing idempotency |
| `secret_redaction` | `redact_secrets` strips sample OpenAI / GitHub / Google keys |
| `safe_fetch` | SSRF guard rejects non-http(s), private/loopback, oversize |
| `transport_config` | transport ∈ stdio\|streamable-http; default loopback |
| `sdk_pin` | resolved `mcp` version on v1.x |
| `canonical_final_tools` | the 3 FINAL tools match the canonical set |

## Env vars set by setup

| Var | Value |
|---|---|
| `AI_API_KEY` | 64-hex (256-bit) random, mode `600` |
| `OBSIDIAN_VAULT_HOST_PATH` | `~/Documents/xninetzy-vault` (created) |
| `DATA_DIR` | `~/.local/share/xninetzy` (+ `hebat`, `external-mcp.d` subdirs) |
| `OUTPUT_DIR` | `~/Documents/xninetzy/output` (+ `generated/research`) |
| `NEO4J_ENABLED` | `true` only when `XNINETZY_INSTALL_NEO4J=true` |

Everything else stays at `.env.example` defaults.

## Why we don't auto-publish to PyPI

`pyproject.toml` declares `Private :: Do Not Upload` as a classifier
and the license as `LicenseRef-Xninetzy-Source-Available-2.2.0` (a
non-OSI SPDX expression). These are deliberate:

- `Private :: Do Not Upload` blocks `twine upload` and `uv publish`
  classifiers-based upload filters when configured; the maintainer
  intentionally ships the wheel through installers and direct sdist
  download, not the public PyPI index.
- The custom license requires a written agreement for Commercial
  Use, so making the wheel trivially `pip install`-able from PyPI
  would invite redistribution that the license does not permit.

To redistribute inside an organization that has a commercial
agreement with the Licensee, install from the wheel:

```bash
uv pip install xninetzy_mcp-1.0.0-py3-none-any.whl
```

## See also

- [MCP system reference](mcp-system.md) — transports, registry, FINAL tools
- [Quick start](../../apps/docs/src/pages/docs/getting-started.md) — install + connect an MCP host
- [Configuration](../../apps/docs/src/pages/docs/configuration.md) — every env var explained
