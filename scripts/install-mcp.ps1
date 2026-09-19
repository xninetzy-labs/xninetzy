# Xninetzy MCP installer (Windows PowerShell 5.1+).
#
# One-line install:
#   iwr -useb https://raw.githubusercontent.com/xninetzy-labs/xninetzy/main/scripts/install-mcp.ps1 | iex
#
# Linux/macOS variant lives at scripts/install-mcp.sh.
#
# Environment overrides:
#   $env:XNINETZY_INSTALL_DIR     install path          (default: $HOME\xninetzy)
#   $env:XNINETZY_BRANCH          git ref               (default: main)
#   $env:XNINETZY_INSTALL_MODE    local | docker        (default: local)
#   $env:XNINETZY_AI_API_KEY      pre-set bearer key    (default: random)
#   $env:XNINETZY_OBSIDIAN_VAULT  vault path            (default: $HOME\Documents\xninetzy-vault)
#   $env:XNINETZY_INSTALL_NEO4J   install Neo4j         (default: false; opt-in)
#
# Steps performed (local mode):
#   1. ensure git, openssl (auto-install uv to %USERPROFILE%\.local\bin)
#   2. clone repo at requested branch
#   3. install Python deps via uv sync --all-extras (mcp, fastapi, faiss-cpu,
#      torch CPU, sentence-transformers, neo4j, opencv, langchain-core, etc.)
#   4. playwright install chromium (HEBAT browser)
#   5. opt-in: Neo4j via choco (if installed)
#   6. random AI_API_KEY, OBSIDIAN_VAULT_HOST_PATH
#   7. supervisor release-check

[CmdletBinding()]
param(
  [string]$InstallDir = $env:XNINETZY_INSTALL_DIR,
  [string]$Branch     = $env:XNINETZY_BRANCH,
  [string]$Mode       = $env:XNINETZY_INSTALL_MODE,
  [string]$AiKey      = $env:XNINETZY_AI_API_KEY,
  [string]$VaultPath  = $env:XNINETZY_OBSIDIAN_VAULT
)

$ErrorActionPreference = 'Stop'
[Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor 3072

if (-not $InstallDir) { $InstallDir = Join-Path $HOME 'xninetzy' }
if (-not $Branch)     { $Branch     = 'main' }
if (-not $Mode)       { $Mode       = 'local' }
if (-not $VaultPath)  { $VaultPath  = Join-Path $HOME 'Documents\xninetzy-vault' }

$RepoUrl = if ($env:XNINETZY_REPO_URL) { $env:XNINETZY_REPO_URL } else { 'https://github.com/xninetzy-labs/xninetzy.git' }

function Write-Section([string]$msg) { Write-Host '' ; Write-Host $msg ; Write-Host '' }

function Test-Command([string]$name) { return [bool](Get-Command -ErrorAction SilentlyContinue $name) }

function Install-Uv {
  if (Test-Command 'uv') { return }
  Write-Host 'uv not found; installing via official PowerShell bootstrap...'
  iwr -useb https://astral.sh/uv/install.ps1 | iex
  if (-not (Test-Command 'uv')) {
    $uvBin = Join-Path $env:USERPROFILE '.local\bin'
    if (Test-Path (Join-Path $uvBin 'uv.exe')) {
      $env:PATH = "$uvBin;$env:PATH"
      [Environment]::SetEnvironmentVariable('PATH', $env:PATH, 'User')
    }
  }
  if (-not (Test-Command 'uv')) { throw 'uv install failed; install manually: https://docs.astral.sh/uv/' }
}

function Require-Cmd([string]$name) {
  if (-not (Test-Command $name)) { throw "$name not found; install it first" }
}

function Set-EnvFileValue([string]$key, [string]$value) {
  $lines = Get-Content '.env'
  $found = $false
  $out = foreach ($line in $lines) {
    if ($line -match "^$([regex]::Escape($key))=") {
      "$key=$value"
      $found = $true
    } else {
      $line
    }
  }
  if (-not $found) { $out += "$key=$value" }
  $out | Set-Content '.env' -Encoding utf8
  (Get-Item '.env').Attributes = 'Hidden'
}

if ($Mode -eq 'docker') {
  Require-Cmd 'git'
  Require-Cmd 'docker'
  Require-Cmd 'openssl'
} else {
  Require-Cmd 'git'
  Install-Uv
}

if ((Test-Path 'pyproject.toml') -and (Test-Path 'xninetzy\interfaces\mcp_server.py')) {
  $InstallDir = (Get-Location).Path
} elseif (Test-Path (Join-Path $InstallDir '.git')) {
  Write-Host "Updating existing install at $InstallDir"
  git -C $InstallDir fetch --depth 1 origin $Branch
  git -C $InstallDir checkout $Branch
  git -C $InstallDir reset --hard "origin/$Branch"
} else {
  Write-Host "Cloning $RepoUrl ($Branch) into $InstallDir"
  git clone --depth 1 --branch $Branch $RepoUrl $InstallDir
}

Set-Location $InstallDir

if (-not (Test-Path '.env')) {
  Copy-Item '.env.example' '.env'
  (Get-Item '.env').Attributes = 'Hidden'
}

if (-not $AiKey) {
  $bytes = New-Object byte[] 32
  (New-Object Random).NextBytes($bytes)
  $AiKey = -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

$envContent = Get-Content '.env' -Raw
if ($envContent -match '(?m)^AI_API_KEY=$') { Set-EnvFileValue 'AI_API_KEY' $AiKey }

if (-not (Test-Path $VaultPath)) {
  New-Item -ItemType Directory -Path $VaultPath -Force | Out-Null
}
$envContent = Get-Content '.env' -Raw
if ($envContent -match '(?m)^OBSIDIAN_VAULT_HOST_PATH=$') {
  Set-EnvFileValue 'OBSIDIAN_VAULT_HOST_PATH' $VaultPath
}

if ($Mode -eq 'docker') {
  Write-Section 'Starting Docker stack...'
  docker compose up -d --build
  docker compose ps
  Write-Host ''
  Write-Host "Xninetzy MCP running in Docker at $InstallDir"
  Write-Host 'Connect via stdio or http://127.0.0.1:8765/mcp (set XNINETZY_MCP_TRANSPORT=streamable-http).'
  return
}

Write-Section 'Installing Python deps (uv sync --all-extras)...'
uv sync --all-extras

Write-Section 'Installing Playwright Chromium (HEBAT browser)...'
try {
  uv run --no-project python -m playwright install chromium
} catch { Write-Warning "playwright install failed: $_" }

if ($env:XNINETZY_INSTALL_NEO4J -eq 'true') {
  Write-Section 'Installing Neo4j (opt-in via XNINETZY_INSTALL_NEO4J=true)...'
  if (Test-Command 'choco') {
    choco install -y neo4j
  } else {
    Write-Warning 'choco not found; install Neo4j manually or install choco first'
  }
  Set-EnvFileValue 'NEO4J_ENABLED' 'true'
}

Write-Section 'Running release gate...'
try { uv run --no-project python -m xninetzy.cli.supervisor release-check } catch { Write-Warning "release-check failed: $_" }

Write-Section 'Running smoke test (mcp_audit.py)...'
try { uv run --no-project python scripts/mcp_audit.py } catch { Write-Warning "mcp_audit failed: $_" }

Write-Section 'Xninetzy MCP install summary'

$envContent = Get-Content '.env' -Raw
$aiKeyRaw   = if ($envContent -match '(?m)^AI_API_KEY=(.+)$') { $Matches[1] } else { '' }
$aiKeyMasked = if ($aiKeyRaw.Length -gt 20) { $aiKeyRaw.Substring(0, 16) + '...' + $aiKeyRaw.Substring($aiKeyRaw.Length - 5) } else { $aiKeyRaw }
$dataDir    = if ($envContent -match '(?m)^DATA_DIR=(.+)$') { $Matches[1] } else { '' }
$vault      = if ($envContent -match '(?m)^OBSIDIAN_VAULT_HOST_PATH=(.+)$') { $Matches[1] } else { '' }
$llmBlock   = if ($envContent -match '(?m)^(FLAZ_API_KEY|OPENAI_API_KEY)=.+$') { 'configured' } else { 'not configured (host supplies the model)' }
$sqliteVer  = if (Test-Command 'sqlite3') { (sqlite3 --version) } else { 'MISSING' }

Write-Host ('  Install path : {0}' -f $InstallDir)
Write-Host ('  sqlite3      : {0}' -f $sqliteVer)
Write-Host ('  tesseract    : ' -NoNewline)
if (Test-Command 'tesseract') { tesseract --version 2>&1 | Select-Object -First 1 } else { Write-Host 'MISSING' }
Write-Host ('  neo4j        : ' -NoNewline)
if ($env:XNINETZY_INSTALL_NEO4J -eq 'true') {
  if (Test-Command 'neo4j') { neo4j --version 2>&1 | Select-Object -First 1 } else { Write-Host 'requested but missing' }
} else { Write-Host 'skipped (opt-in via XNINETZY_INSTALL_NEO4J=true)' }
Write-Host ''
Write-Host ('  .env         : {0}\.env (mode hidden)' -f $InstallDir)
Write-Host ('  AI_API_KEY   : {0}' -f $aiKeyMasked)
Write-Host ('  DATA_DIR     : {0}' -f $dataDir)
Write-Host ('  OBSIDIAN_VAULT: {0}' -f $vault)
Write-Host ('  LLM block    : {0}' -f $llmBlock)
Write-Host ''
Write-Host '  Next:'
Write-Host ('    cd "{0}"' -f $InstallDir)
Write-Host '    uv run python -m xninetzy.cli.supervisor start      # stdio MCP'
Write-Host '    $env:XNINETZY_MCP_TRANSPORT = ''streamable-http'''
Write-Host '    uv run python -m xninetzy.interfaces.mcp_server     # http://127.0.0.1:8765/mcp'
Write-Host ''
Write-Host '  Optional:'
Write-Host '    $env:XNINETZY_INSTALL_NEO4J = ''true''; iwr -useb ...install-mcp.ps1 | iex  # add Neo4j'
Write-Host '    uv run --no-project python scripts/mcp_audit.py --strict                  # strict audit'

Write-Section 'Xninetzy MCP installed.'
Write-Host "Path : $InstallDir"
Write-Host ''
Write-Host 'Next steps:'
Write-Host "  cd `"$InstallDir`""
Write-Host '  uv run python -m xninetzy.cli.supervisor start      # stdio MCP'
Write-Host '  $env:XNINETZY_MCP_TRANSPORT = ''streamable-http'''
Write-Host '  uv run python -m xninetzy.interfaces.mcp_server     # http://127.0.0.1:8765/mcp'
