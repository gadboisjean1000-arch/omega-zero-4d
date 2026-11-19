<#
.SYNOPSIS
    Configure local Git custom actions (`guitool.*`) for git-cola inside omega-zero-4d.
.DESCRIPTION
    Zero external modification (writes exclusively to `.git/config` via `git config --local`).
    Preserves clean Apache-2.0 / GPL-2.0 separation by invoking git-cola out-of-process only.
#>
[CmdletBinding()]
param(
    [string]$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path (Join-Path $RepoRoot ".git"))) {
    Write-Error "Depot Git introuvable dans $RepoRoot"
    exit 1
}

$tools = [ordered]@{
    "Supela: Verify Rule A12"          = "python scripts/verify_a12.py"
    "Supela: Verify VR-01..20"         = "python scripts/vr_compliance_check.py"
    "Supela: Build Proven Laws Web"    = "python scripts/build_proven_laws_web.py"
    "Supela: OPA Rego Tests (31/31)"   = "opa test policies/ tests/rego/ -v"
    "Supela: Pytest Laws & Math"       = "pytest tests/test_supela_laws.py tests/test_supela_math_core.py -v"
}

foreach ($name in $tools.Keys) {
    git -C $RepoRoot config --local "guitool.$name.cmd" $tools[$name]
    git -C $RepoRoot config --local "guitool.$name.noconsole" "false"
    Write-Host "[OK] git-cola guitool configure : $name -> $($tools[$name])" -ForegroundColor Green
}

$cola = Get-Command git-cola -ErrorAction SilentlyContinue
if ($cola) {
    Write-Host "git-cola detecte : $($cola.Source)" -ForegroundColor Cyan
} else {
    Write-Host "Note: git-cola n'est pas encore dans le PATH (installer via 'pipx install git-cola' ou 'winget install git-cola.git-cola')." -ForegroundColor Yellow
}
