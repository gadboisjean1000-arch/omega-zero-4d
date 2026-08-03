Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-HashHex {
    param([Parameter(Mandatory = $true)][string]$Path)
    return (Get-FileHash -Path $Path -Algorithm SHA256).Hash.ToLowerInvariant()
}

function Get-SignatureStatus {
    param([Parameter(Mandatory = $true)][string]$ArtifactPath)
    $sigCandidates = @("$ArtifactPath.sig", "$ArtifactPath.asc")
    $sig = $sigCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $sig) {
        return @{
            state = "DRAFT"
            file = $null
            verified = $false
            note = "Aucune signature associee detectee"
        }
    }
    $sigHash = Get-HashHex -Path $sig
    return @{
        state = "SIGNED"
        file = (Split-Path -Leaf $sig)
        verified = $false
        note = "Signature detectee; verification cryptographique externe requise"
        signature_sha256 = $sigHash
    }
}

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$institutionalDir = Join-Path $repoRoot "institutional"

if (-not (Test-Path $institutionalDir)) {
    throw "Dossier institutional introuvable: $institutionalDir"
}

$dependencyLocks = @(
    "requirements.txt",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "poetry.lock",
    "go.sum",
    "Cargo.lock"
) | ForEach-Object { Join-Path $repoRoot $_ } | Where-Object { Test-Path $_ }

$dependencyState = @()
foreach ($dep in $dependencyLocks) {
    $dependencyState += [ordered]@{
        file = (Resolve-Path $dep).Path.Substring($repoRoot.Length + 1).Replace("\", "/")
        sha256 = Get-HashHex -Path $dep
    }
}

$artifactFiles = Get-ChildItem -Path $institutionalDir -File |
    Where-Object {
        $_.Name -ne "REGISTRE-CHAINE-CONFIANCE.json" -and
        $_.Extension -in ".md", ".json", ".ps1"
    } |
    Sort-Object Name

$entries = @()
$chainInput = ""
foreach ($file in $artifactFiles) {
    $path = $file.FullName
    $hash = Get-HashHex -Path $path
    $sigInfo = Get-SignatureStatus -ArtifactPath $path
    $entry = [ordered]@{
        artifact = $file.Name
        sha256 = $hash
        status = $sigInfo.state
        signature = $sigInfo
    }
    $entries += $entry
    $chainInput += "$($file.Name):$hash`n"
}

$chainHash = [System.BitConverter]::ToString(
    [System.Security.Cryptography.SHA256]::Create().ComputeHash([System.Text.Encoding]::UTF8.GetBytes($chainInput))
).Replace("-", "").ToLowerInvariant()

$signedCount = @($entries | Where-Object { $_.status -eq "SIGNED" }).Count
$verifiedCount = @($entries | Where-Object { $_.status -eq "VERIFIED" }).Count

$overallStatus = "PROVISIONAL"
if ($verifiedCount -ge 2) {
    $overallStatus = "VERIFIED_TIER2"
} elseif ($signedCount -ge 2) {
    $overallStatus = "SIGNED"
}

$registry = [ordered]@{
    generated_at_utc = (Get-Date).ToUniversalTime().ToString("o")
    policy = [ordered]@{
        draft = "Aucune signature detectee"
        signed = "Signature detectee"
        verified = "Signature verifiee cryptographiquement"
    }
    overall_status = $overallStatus
    chain_sha256 = $chainHash
    dependency_locks = $dependencyState
    artifacts = $entries
}

$registryPath = Join-Path $institutionalDir "REGISTRE-CHAINE-CONFIANCE.json"
$registry | ConvertTo-Json -Depth 8 | Set-Content -Path $registryPath -Encoding UTF8

Write-Host "Registry updated: $registryPath"
Write-Host "Artifacts: $($entries.Count) | Signed: $signedCount | Verified: $verifiedCount | Overall: $overallStatus"
