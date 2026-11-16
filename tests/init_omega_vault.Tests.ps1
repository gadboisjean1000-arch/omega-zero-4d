BeforeAll {
    $script:VaultTestDir = Join-Path ([System.IO.Path]::GetTempPath()) ("omega_vault_pester_" + [guid]::NewGuid().ToString("N"))
    $script:InitScript = Join-Path $PSScriptRoot "..\runtime\init_omega_vault.ps1"
}

AfterAll {
    if (Test-Path -LiteralPath $script:VaultTestDir) {
        Get-ChildItem -LiteralPath $script:VaultTestDir -Recurse -Force | ForEach-Object {
            if ($_.Attributes -band [System.IO.FileAttributes]::ReadOnly) {
                $_.IsReadOnly = $false
            }
        }
        Remove-Item -LiteralPath $script:VaultTestDir -Recurse -Force
    }
}

Describe "init_omega_vault.ps1 idempotence & WORM logique" {
    It "cree les 4 poles, verrouille le manifeste IsReadOnly et reste idempotent" {
        & $script:InitScript -VaultPath $script:VaultTestDir | Out-Null
        $manifest = Join-Path $script:VaultTestDir "omega_vault_manifest.json"
        $ledger   = Join-Path $script:VaultTestDir "ledger_append_only.log"

        Test-Path (Join-Path $script:VaultTestDir "Local_L") | Should -BeTrue
        Test-Path (Join-Path $script:VaultTestDir "Cloud_C") | Should -BeTrue
        Test-Path (Join-Path $script:VaultTestDir "Vide_Pi0") | Should -BeTrue
        Test-Path (Join-Path $script:VaultTestDir "Manque_M") | Should -BeTrue

        (Get-Item $manifest).IsReadOnly | Should -BeTrue
        $h1 = (Get-FileHash $manifest -Algorithm SHA256).Hash
        $l1 = @(Get-Content $ledger).Count

        & $script:InitScript -VaultPath $script:VaultTestDir | Out-Null
        $h2 = (Get-FileHash $manifest -Algorithm SHA256).Hash
        $l2 = @(Get-Content $ledger).Count

        $h2 | Should -BeExactly $h1
        $l2 | Should -BeGreaterThan $l1
    }
}
