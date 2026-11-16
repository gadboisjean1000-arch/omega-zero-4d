param(
    [string]$TargetRepoPath = "C:\Users\Group\Documents\antigravity\excited-meitner",
    [string]$ArchivePath = "$PSScriptRoot\..\dist\omega-zero-4d-bundle.zip"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (-not (Test-Path -LiteralPath $ArchivePath)) {
    throw "Archive introuvable : $ArchivePath"
}

if (-not (Test-Path -LiteralPath $TargetRepoPath)) {
    New-Item -ItemType Directory -Path $TargetRepoPath -Force | Out-Null
}

Write-Host "Extraction de $ArchivePath vers $TargetRepoPath ..."
Expand-Archive -LiteralPath $ArchivePath -DestinationPath $TargetRepoPath -Force

$manifestPath = Join-Path $TargetRepoPath "SHA256SUMS.txt"
if (Test-Path -LiteralPath $manifestPath) {
    Write-Host "Vérification des empreintes SHA-256..."
    Get-Content -LiteralPath $manifestPath | ForEach-Object {
        if ($_ -match "^([0-9a-fA-F]{64})\s+\*?(.+)$") {
            $expected = $Matches[1].ToLowerInvariant()
            $relPath = $Matches[2].Trim()
            $fullPath = Join-Path $TargetRepoPath $relPath
            if (-not (Test-Path -LiteralPath $fullPath)) {
                throw "Fichier manquant après extraction : $relPath"
            }
            $actual = (Get-FileHash -LiteralPath $fullPath -Algorithm SHA256).Hash.ToLowerInvariant()
            if ($actual -ne $expected) {
                throw "Divergence SHA-256 pour $relPath : attendu=$expected obtenu=$actual"
            }
        }
    }
    Write-Host "Empreintes SHA-256 validées avec succès."
}
