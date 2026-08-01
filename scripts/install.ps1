$ErrorActionPreference = "Stop"

$RepositoryUrl = "https://github.com/misbahul45/xninetzy.git"
$InstallDir = if ($env:XNINETZY_INSTALL_DIR) { $env:XNINETZY_INSTALL_DIR } else { Join-Path $HOME "xninetzy" }

if (-not (Get-Command git -ErrorAction SilentlyContinue)) { throw "Git belum terpasang." }
if (-not (Get-Command docker -ErrorAction SilentlyContinue)) { throw "Docker Desktop belum terpasang." }
docker compose version | Out-Null

if ((Test-Path ".\docker-compose.yml") -and (Test-Path ".\.env.example")) {
    $InstallDir = (Get-Location).Path
} elseif (Test-Path (Join-Path $InstallDir ".git")) {
    git -C $InstallDir pull --ff-only
} else {
    git clone $RepositoryUrl $InstallDir
}

Set-Location $InstallDir
if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }

function Set-EnvValue([string]$Key, [string]$Value) {
    $lines = [System.Collections.Generic.List[string]](Get-Content ".env")
    $found = $false
    for ($index = 0; $index -lt $lines.Count; $index++) {
        if ($lines[$index].StartsWith("$Key=")) {
            $lines[$index] = "$Key=$Value"
            $found = $true
        }
    }
    if (-not $found) { $lines.Add("$Key=$Value") }
    [System.IO.File]::WriteAllLines((Join-Path $InstallDir ".env"), $lines)
}

function New-UrlSafeKey([int]$Length) {
    $bytes = New-Object byte[] $Length
    [System.Security.Cryptography.RandomNumberGenerator]::Fill($bytes)
    return [Convert]::ToBase64String($bytes).Replace("+", "-").Replace("/", "_")
}

$defaultVault = Join-Path $HOME "Documents\Xninetzy Vault"
$vaultPath = Read-Host "Lokasi Obsidian vault [$defaultVault]"
if ([string]::IsNullOrWhiteSpace($vaultPath)) { $vaultPath = $defaultVault }
New-Item -ItemType Directory -Force -Path $vaultPath | Out-Null

$adminNumber = (Read-Host "Nomor WhatsApp admin (contoh 62812...)").Split("@")[0]
$secureFlaz = Read-Host "Masukkan FLAZ API Key" -AsSecureString
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secureFlaz)
try { $flazKey = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer) }
finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer) }
if ([string]::IsNullOrWhiteSpace($flazKey)) { throw "FLAZ API Key wajib diisi." }

Set-EnvValue "HOST_UID" "1000"
Set-EnvValue "HOST_GID" "1000"
Set-EnvValue "OBSIDIAN_VAULT_HOST_PATH" $vaultPath
Set-EnvValue "ADMIN_JID" "$adminNumber@s.whatsapp.net"
Set-EnvValue "FLAZ_API_KEY" $flazKey
Set-EnvValue "AI_API_KEY" (New-UrlSafeKey 48)
$mcpKey = New-UrlSafeKey 48
Set-EnvValue "MCP_API_KEY" $mcpKey
Set-EnvValue "WA_MCP_API_KEY" $mcpKey
Set-EnvValue "WEB_ANALYSIS_ENCRYPTION_KEY" (New-UrlSafeKey 32)
Set-EnvValue "CODING_AGENT_HOST_BRIDGE_TOKEN" (New-UrlSafeKey 32)
Set-EnvValue "CODING_AGENT_ENABLED" "true"
Set-EnvValue "CODING_AGENT_EXECUTION_MODE" "host_bridge"
Set-EnvValue "WA_LOGIN_MODE" "qr"

$flazKey = $null
$mcpKey = $null
$secureFlaz.Dispose()

docker compose config -q
docker compose up --build -d ai wa-enggine
docker compose ps

Write-Host "Host coding-agent bridge: jalankan uv run --directory services/ai --no-dev python -m app.xninetzy.interfaces.host_agent_bridge pada startup Windows."

Write-Host ""
Write-Host "Xninetzy terpasang di $InstallDir"
Write-Host "Jalankan: cd `"$InstallDir`"; docker compose logs -f wa-enggine"
