# Xninetzy MCP setup (Windows PowerShell 5.1+).
#
# Idempotent. Runs after install-mcp.{sh,ps1} (or directly on an existing
# clone) to: copy .env.example -> .env, generate AI_API_KEY, set
# OBSIDIAN_VAULT_HOST_PATH, ensure DATA_DIR exists, validate the release
# gate, and print the connection summary.
#
# Usage:
#   powershell -File scripts/setup-mcp.ps1
#   powershell -File scripts/setup-mcp.ps1 -NoValidate

[CmdletBinding()]
param(
  [switch]$NoValidate
)

$ErrorActionPreference = 'Stop'

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $RepoRoot

if (-not (Test-Path 'pyproject.toml')) {
  throw "pyproject.toml not found at $RepoRoot"
}

if (-not (Get-Command 'uv' -ErrorAction SilentlyContinue)) {
  throw 'uv not found; run install-mcp.ps1 first or install from https://docs.astral.sh/uv/'
}

if (-not (Test-Path '.env')) {
  Write-Host 'creating .env from .env.example'
  Copy-Item '.env.example' '.env'
  (Get-Item '.env').Attributes = 'Hidden'
}

$AiKey = $env:AI_API_KEY
if ([string]::IsNullOrEmpty($AiKey)) {
  $bytes = New-Object byte[] 32
  (New-Object Random).NextBytes($bytes)
  $AiKey = -join ($bytes | ForEach-Object { $_.ToString('x2') })
}

function Set-EnvFileValue([string]$key, [string]$value) {
  $lines = Get-Content '.env'
  $found = $false
  $out = foreach ($line in $lines) {
    if ($line -match "^$([regex]::Escape($key))=") {
      "$key=$value"
      $found = $true
    } else { $line }
  }
  if (-not $found) { $out += "$key=$value" }
  $out | Set-Content '.env' -Encoding utf8
  (Get-Item '.env').Attributes = 'Hidden'
}

$envContent = Get-Content '.env' -Raw
if ($envContent -match '(?m)^AI_API_KEY=$') { Set-EnvFileValue 'AI_API_KEY' $AiKey }

$Vault = if ($env:XNINETZY_OBSIDIAN_VAULT) { $env:XNINETZY_OBSIDIAN_VAULT } `
  elseif ($env:OBSIDIAN_VAULT_HOST_PATH)  { $env:OBSIDIAN_VAULT_HOST_PATH } `
  else { Join-Path $HOME 'Documents\xninetzy-vault' }
if ($envContent -match '(?m)^OBSIDIAN_VAULT_HOST_PATH=$') { Set-EnvFileValue 'OBSIDIAN_VAULT_HOST_PATH' $Vault }
New-Item -ItemType Directory -Path $Vault -Force | Out-Null

$DataDir = if ($env:DATA_DIR) { $env:DATA_DIR } else { Join-Path $HOME '.local\share\xninetzy' }
New-Item -ItemType Directory -Path $DataDir, (Join-Path $DataDir 'hebat'), (Join-Path $DataDir 'external-mcp.d') -Force | Out-Null
if ($envContent -match '(?m)^DATA_DIR=$') { Set-EnvFileValue 'DATA_DIR' $DataDir }

$OutputDir = if ($env:OUTPUT_DIR) { $env:OUTPUT_DIR } else { Join-Path $HOME 'Documents\xninetzy\output' }
New-Item -ItemType Directory -Path $OutputDir, (Join-Path $HOME 'Documents\xninetzy\generated\research') -Force | Out-Null
if ($envContent -match '(?m)^OUTPUT_DIR=$') { Set-EnvFileValue 'OUTPUT_DIR' $OutputDir }

Write-Host 'syncing Python deps'
uv sync --all-extras

if (-not $NoValidate) {
  Write-Host 'running release gate'
  uv run --no-project python -m xninetzy.cli.supervisor release-check
}

Write-Host ''
Write-Host '=============================================================='
Write-Host '  Xninetzy MCP ready'
Write-Host '=============================================================='
Write-Host ('  Install path : {0}' -f $RepoRoot)
Write-Host ('  Data dir     : {0}' -f $DataDir)
Write-Host ('  Vault path   : {0}' -f $Vault)
Write-Host ('  Output dir   : {0}' -f $OutputDir)
Write-Host ''
Write-Host '  Start stdio MCP (primary):'
Write-Host '    uv run python -m xninetzy.cli.supervisor start'
Write-Host ''
Write-Host '  Start Streamable HTTP MCP (loopback):'
Write-Host '    $env:XNINETZY_MCP_TRANSPORT = ''streamable-http'''
Write-Host '    uv run python -m xninetzy.interfaces.mcp_server'
Write-Host ''
Write-Host '  Connect from Claude Code:'
Write-Host '    claude mcp add --scope user xninetzy -- '
Write-Host ('      {0} run --directory {1} python -m xninetzy.interfaces.mcp_server' -f (Get-Command uv).Source, $RepoRoot)
Write-Host '=============================================================='
