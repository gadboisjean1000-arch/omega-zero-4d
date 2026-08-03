param(
    [string]$Repo = $PSScriptRoot,
    [string]$ExternalRunReference = "EXT-AUDIT-$(Get-Date -Format 'yyyyMMdd-HHmmss')",
    [string]$PsychometricRunReference = "PSY-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$artifactPath = Join-Path $Repo "evidence\external-audit\third-party-audit-artifact.txt"
$manifestPath = Join-Path $Repo "evidence\external-audit\external-proof-manifest.json"
$psyPath = Join-Path $Repo "evidence\psychometrics\psychometric-results.json"

if (-not (Test-Path $artifactPath)) { throw "Missing artifact: $artifactPath" }
if (-not (Test-Path $manifestPath)) { throw "Missing manifest: $manifestPath" }
if (-not (Test-Path $psyPath)) { throw "Missing psychometric JSON: $psyPath" }

$commit = (& git -C $Repo rev-parse HEAD).Trim()
$utcNow = [datetime]::UtcNow.ToString("yyyy-MM-ddTHH:mm:ssZ")
$hash = (Get-FileHash -Path $artifactPath -Algorithm SHA256).Hash.ToLowerInvariant()

$manifest = Get-Content -Raw -Encoding UTF8 -Path $manifestPath | ConvertFrom-Json -Depth 20
$manifest.commit = $commit
$manifest.generated_at_utc = $utcNow
$manifest.expected_sha256 = $hash
$manifest.run_reference = $ExternalRunReference
$manifest | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $manifestPath

$psy = Get-Content -Raw -Encoding UTF8 -Path $psyPath | ConvertFrom-Json -Depth 20
$psy.metadata.commit = $commit
$psy.metadata.generated_at_utc = $utcNow
$psy.metadata.run_reference = $PsychometricRunReference
$psy.traceability.config_hash = (Get-FileHash -Path (Join-Path $Repo "evidence\psychometrics\psychometric-thresholds.json") -Algorithm SHA256).Hash.ToLowerInvariant()
$psy | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $psyPath

Write-Host "Advanced proofs refreshed."
Write-Host "commit=$commit"
Write-Host "external_sha256=$hash"
Write-Host "manifest=$manifestPath"
Write-Host "psychometric=$psyPath"
