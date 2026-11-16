<#
.SYNOPSIS
    Orchestrateur Windows pour Supela Ω-ZERO · Local–Cloud–4D.
    Vérifie honnêtement la présence des outils (aucun faux succès).
#>
[CmdletBinding()]
param(
    [ValidateSet("Test", "A12", "Vault", "Sign", "Verify", "Attest", "Clean", "All")]
    [string]$Task = "Test",
    [string]$Root = $PSScriptRoot,
    [string]$Vault = (Join-Path $env:TEMP "omega_zero_vault")
)

$ErrorActionPreference = "Stop"
$Report = Join-Path $Root "reports\TEST-4D-ESC-01.report.json"

function Assert-Tool([string]$name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host ("[!] outil absent du PATH : {0} - cible NON executee" -f $name) -ForegroundColor Red
        return $false
    }
    return $true
}

switch ($Task) {
    "Test" {
        python (Join-Path $Root "docs\constitution\HARNAIS_TEST_ESCALADE_4D.py") --out $Report
        pytest -v
        if (Assert-Tool "opa") {
            opa check --strict (Join-Path $Root "policies") (Join-Path $Root "tests\rego")
            opa test (Join-Path $Root "policies") (Join-Path $Root "tests\rego") -v --explain=fails
        }
    }
    "A12" {
        & (Join-Path $Root "scripts\verify_a12.ps1") -RootPath $Root
    }
    "Vault" {
        & (Join-Path $Root "runtime\init_omega_vault.ps1") -VaultPath $Vault
    }
    "Sign" {
        if (Assert-Tool "cosign") {
            cosign sign-blob --key cosign.key --yes --bundle "$Report.bundle" $Report
        }
    }
    "Verify" {
        if (Assert-Tool "cosign") {
            cosign verify-blob --key cosign.pub --bundle "$Report.bundle" $Report
        }
    }
    "Attest" {
        if (-not (Assert-Tool "tpm2_quote")) {
            Write-Host "[i] tpm2_quote absent : ancrage silicium DECLARATIF sur cette machine." -ForegroundColor Yellow
            return
        }
        tpm2_quote -c primary.ctx -l sha256:15,16,22 -m quote.msg -s quote.sig -p pcr.bin -g sha256
    }
    "Clean" {
        Remove-Item -Force -ErrorAction SilentlyContinue "$Report.bundle", "quote.msg", "quote.sig", "pcr.bin"
    }
    "All" {
        & $PSCommandPath -Task A12 -Root $Root -Vault $Vault
        & $PSCommandPath -Task Vault -Root $Root -Vault $Vault
        & $PSCommandPath -Task Test -Root $Root -Vault $Vault
    }
}
