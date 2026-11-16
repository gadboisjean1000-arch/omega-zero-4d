<#
.SYNOPSIS
    Instanciation idempotente du coffre-fort WORM logique Ω-ZERO (Local, Cloud, Vide Π₀, Manque).
.DESCRIPTION
    Transparence : produit un WORM LOGIQUE (manifeste IsReadOnly + ledger append-only SHA-256).
    Ne constitue pas un WORM matériel ni un ancrage TPM/TEE.
#>
[CmdletBinding()]
param(
    [string]$VaultPath = (Join-Path $env:TEMP "omega_zero_vault"),
    [string]$ProtocolPath = (Join-Path $PSScriptRoot ("..\docs\constitution\PLAN-4D-" + [char]0x03A9 + "ZERO-ESC-01.json"))
)

$ErrorActionPreference = "Stop"

$subdirs = @("Local_L", "Cloud_C", "Vide_Pi0", "Manque_M")
if (-not (Test-Path -LiteralPath $VaultPath)) {
    New-Item -ItemType Directory -Force -Path $VaultPath | Out-Null
}
foreach ($name in $subdirs) {
    $p = Join-Path $VaultPath $name
    if (-not (Test-Path -LiteralPath $p)) {
        New-Item -ItemType Directory -Force -Path $p | Out-Null
    }
}

$manifest = Join-Path $VaultPath "omega_vault_manifest.json"
$ledger   = Join-Path $VaultPath "ledger_append_only.log"
$seal     = Join-Path $VaultPath "omega_seal.txt"
$timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ss.ffffffZ")
$protocolHash = (Get-FileHash -LiteralPath $ProtocolPath -Algorithm SHA256).Hash.ToLowerInvariant()

if (-not (Test-Path -LiteralPath $manifest)) {
    $manifestContent = [ordered]@{
        system          = "Supela-Omega-ZERO-4D"
        poles           = $subdirs
        protocol_sha256 = $protocolHash
        created_utc     = $timestamp
    } | ConvertTo-Json -Depth 4
    Set-Content -LiteralPath $manifest -Value $manifestContent -Encoding utf8
    Set-ItemProperty -LiteralPath $manifest -Name IsReadOnly -Value $true
}

$hash = (Get-FileHash -LiteralPath $manifest -Algorithm SHA256).Hash.ToLowerInvariant()
$entry = ("{0} | VAULT_INIT_RUN | manifest_sha256={1} | protocol_sha256={2}" -f $timestamp, $hash, $protocolHash)
Add-Content -LiteralPath $ledger -Value $entry -Encoding utf8

$ledgerLines = (Get-Content -LiteralPath $ledger | Measure-Object -Line).Lines
$omegaSym = [char]0x03A9
$sealContent = @"
Sceau $omegaSym-ZERO (WORM logique)
timestamp_utc   : $timestamp
manifest_sha256 : $hash
protocol_sha256 : $protocolHash
ledger_lines    : $ledgerLines
"@
Set-Content -LiteralPath $seal -Value $sealContent -Encoding utf8
Write-Host "SHA-256 manifeste = $hash | ledger = $ledgerLines lignes"
