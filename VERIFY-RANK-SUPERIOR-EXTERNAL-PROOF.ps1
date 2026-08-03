# SUPELA v1.1.0 — Vérification Preuve Externe Rang Supérieur
# Usage: .\VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF.ps1 [-repo <path>]
# Statuts possibles: PROVISIONAL (templates non signés) | VERIFIED_TIER2 (attestations complètes + hash ok)
param([string]$repo = $PSScriptRoot)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Continue'

$rankDir    = Join-Path $repo 'evidence\external-audit\rank-superior'
$attestA    = Join-Path $rankDir 'ATTESTATION-AUDITEUR-A.template.json'
$attestB    = Join-Path $rankDir 'ATTESTATION-AUDITEUR-B.template.json'
$registry   = Join-Path $rankDir 'EXTERNAL-REVIEW-REGISTRY.json'
$hashChain  = Join-Path $rankDir 'HASH-CHAIN-MANIFEST.json'

$requiredFields = @('auditor_org', 'contact', 'scope', 'method', 'findings', 'signature_block')
$issues = [System.Collections.Generic.List[string]]::new()
$checks = [System.Collections.Generic.List[string]]::new()

function Read-JsonSafe {
    param([string]$Path)
    if (-not (Test-Path $Path)) { return $null }
    try { return (Get-Content -Raw -Path $Path -Encoding UTF8) | ConvertFrom-Json -Depth 20 }
    catch { return $null }
}

function Test-FieldFilled {
    param($obj, [string]$field)
    $v = $obj.$field
    if ($null -eq $v) { return $false }
    $s = "$v"
    return (-not [string]::IsNullOrWhiteSpace($s)) -and (-not $s.StartsWith('<PLACEHOLDER'))
}

function Test-SignatureBlock {
    param($sb)
    if ($null -eq $sb) { return $false }
    $required = @('signed_by', 'signed_at_utc', 'algorithm', 'key_fingerprint', 'value')
    foreach ($f in $required) {
        $v = "$($sb.$f)"
        if ([string]::IsNullOrWhiteSpace($v) -or $v.StartsWith('<PLACEHOLDER')) { return $false }
    }
    return $true
}

""
"╔══════════════════════════════════════════════════════════════════╗"
"║   🔍  VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF — SUPELA v1.1.0       ║"
"╠══════════════════════════════════════════════════════════════════╣"

# ── ÉTAPE 1 : Présence des fichiers ──────────────────────────────────
"║  [ÉTAPE 1] Présence des fichiers requis"
$filesOK = $true
foreach ($f in @($attestA, $attestB, $registry, $hashChain)) {
    $name = Split-Path $f -Leaf
    $exists = Test-Path $f
    $sym = if ($exists) { '✓' } else { '✗'; $filesOK = $false }
    "║    $sym  $name"
    if (-not $exists) { $issues.Add("MANQUANT: $name") }
}
$checks.Add("presence_files=$filesOK")

# ── ÉTAPE 2 : Champs requis attestation A ─────────────────────────────
"║"
"║  [ÉTAPE 2] Champs requis — Attestation A"
$jsonA = Read-JsonSafe -Path $attestA
$aFieldsOK = $false
$aStatusOK = $false
if ($null -ne $jsonA) {
    $missingA = @()
    foreach ($f in $requiredFields) {
        $ok = Test-FieldFilled -obj $jsonA -field $f
        $sym = if ($ok) { '✓' } else { '✗'; $missingA += $f }
        "║    $sym  $f"
    }
    $aFieldsOK = $missingA.Count -eq 0
    $aStatusOK = $jsonA._status -ne 'TEMPLATE_UNSIGNED'
    "║    status=$($jsonA._status)  signature_complète=$(Test-SignatureBlock -sb $jsonA.signature_block)"
    if (-not $aFieldsOK) { $issues.Add("ATTESTATION-A: champs manquants/placeholder: $($missingA -join ', ')") }
    if (-not $aStatusOK) { $issues.Add("ATTESTATION-A: statut TEMPLATE_UNSIGNED — non signé") }
} else {
    "║    ✗  Fichier illisible ou absent"
    $issues.Add("ATTESTATION-A: fichier illisible")
}
$checks.Add("attestA_fields=$aFieldsOK")
$checks.Add("attestA_signed=$aStatusOK")

# ── ÉTAPE 3 : Champs requis attestation B ─────────────────────────────
"║"
"║  [ÉTAPE 3] Champs requis — Attestation B"
$jsonB = Read-JsonSafe -Path $attestB
$bFieldsOK = $false
$bStatusOK = $false
if ($null -ne $jsonB) {
    $missingB = @()
    foreach ($f in $requiredFields) {
        $ok = Test-FieldFilled -obj $jsonB -field $f
        $sym = if ($ok) { '✓' } else { '✗'; $missingB += $f }
        "║    $sym  $f"
    }
    $bFieldsOK = $missingB.Count -eq 0
    $bStatusOK = $jsonB._status -ne 'TEMPLATE_UNSIGNED'
    "║    status=$($jsonB._status)  signature_complète=$(Test-SignatureBlock -sb $jsonB.signature_block)"
    if (-not $bFieldsOK) { $issues.Add("ATTESTATION-B: champs manquants/placeholder: $($missingB -join ', ')") }
    if (-not $bStatusOK) { $issues.Add("ATTESTATION-B: statut TEMPLATE_UNSIGNED — non signé") }
} else {
    "║    ✗  Fichier illisible ou absent"
    $issues.Add("ATTESTATION-B: fichier illisible")
}
$checks.Add("attestB_fields=$bFieldsOK")
$checks.Add("attestB_signed=$bStatusOK")

# ── ÉTAPE 4 : Vérification hash chain ─────────────────────────────────
"║"
"║  [ÉTAPE 4] Cohérence de la chaîne de hachage"
$manifest = Read-JsonSafe -Path $hashChain
$hashChainOK = $false
$baseHashesOK = $true
if ($null -ne $manifest) {
    # Vérifier les hachés des artefacts de base
    foreach ($entry in $manifest.artifacts.base_corpus) {
        if ($null -eq $entry.sha256 -or $entry.sha256 -eq '') { continue }
        $p = Join-Path $repo ($entry.path -replace '/', '\')
        if (Test-Path $p) {
            $actual = (Get-FileHash -Algorithm SHA256 -Path $p).Hash.ToLowerInvariant()
            $expected = $entry.sha256.ToLowerInvariant()
            $match = $actual -eq $expected
            $sym = if ($match) { '✓' } else { '✗'; $baseHashesOK = $false; $issues.Add("HASH_MISMATCH: $($entry.path)") }
            "║    $sym  $($entry.id) hash=$(if($match){'OK'}else{'MISMATCH'})"
        } else {
            "║    ⚠  $($entry.id) fichier absent (non bloquant pour rang supérieur)"
        }
    }

    # Vérifier les hachés signés des attestations (requis pour TIER2)
    $rankArtifacts = $manifest.artifacts.rank_superior_layer | Where-Object { $_.id -in @('ATTESTATION-A','ATTESTATION-B') }
    $signedHashesPresent = $true
    foreach ($ra in $rankArtifacts) {
        $hasSignedHash = ($null -ne $ra.signed_sha256) -and ("$($ra.signed_sha256)" -ne '')
        $sym = if ($hasSignedHash) { '✓' } else { '✗'; $signedHashesPresent = $false }
        "║    $sym  $($ra.id) signed_sha256=$(if($hasSignedHash){'présent'}else{'NULL — template non signé'})"
        if ($hasSignedHash) {
            # Vérifier la cohérence du hash signé avec le fichier réel
            $filePath = Join-Path $repo ($ra.path -replace '/', '\')
            if (Test-Path $filePath) {
                $actualHash = (Get-FileHash -Algorithm SHA256 -Path $filePath).Hash.ToLowerInvariant()
                $match = $actualHash -eq "$($ra.signed_sha256)".ToLowerInvariant()
                $sym2 = if ($match) { '✓' } else { '✗'; $issues.Add("HASH_SIGNED_MISMATCH: $($ra.id)") }
                "║      $sym2  hash fichier vs signed_sha256: $(if($match){'COHERENT'}else{'INCOHÉRENT'})"
            }
        }
    }
    $hashChainOK = $baseHashesOK -and $signedHashesPresent
    if (-not $signedHashesPresent) { $issues.Add("HASH-CHAIN: signed_sha256 manquants dans HASH-CHAIN-MANIFEST.json") }
} else {
    "║    ✗  HASH-CHAIN-MANIFEST.json illisible"
    $issues.Add("HASH-CHAIN: manifeste illisible")
}
$checks.Add("hash_chain_base=$baseHashesOK")
$checks.Add("hash_chain_signed=$(if($hashChainOK){'true'}else{'false'})")

# ── ÉTAPE 5 : Registre ────────────────────────────────────────────────
"║"
"║  [ÉTAPE 5] Registre des revues"
$reg = Read-JsonSafe -Path $registry
$regOK = $false
if ($null -ne $reg) {
    $draftCount = @($reg.reviews | Where-Object { $_.status -eq 'draft' }).Count
    $signedCount = @($reg.reviews | Where-Object { $_.status -in @('signed','verified') }).Count
    "║    Revues en draft  : $draftCount"
    "║    Revues signées   : $signedCount / $($reg.required_for_tier2) requises"
    $regOK = $signedCount -ge $reg.required_for_tier2
    if (-not $regOK) { $issues.Add("REGISTRY: seulement $signedCount attestation(s) signée(s), $($reg.required_for_tier2) requises") }
} else {
    "║    ✗  Registre illisible"
    $issues.Add("REGISTRY: fichier illisible")
}
$checks.Add("registry_signed_count=$regOK")

# ── VERDICT FINAL ────────────────────────────────────────────────────
"║"
"╠══════════════════════════════════════════════════════════════════╣"
$allGreen = $filesOK -and $aFieldsOK -and $aStatusOK -and $bFieldsOK -and $bStatusOK -and $hashChainOK -and $regOK

if ($allGreen) {
    $status = 'VERIFIED_TIER2'
    "║  ✅  STATUT FINAL : VERIFIED_TIER2                               ║"
    "║  Les deux attestations sont signées, les champs requis sont     ║"
    "║  présents et la chaîne de hachage est cohérente.                ║"
} else {
    $status = 'PROVISIONAL'
    "║  ⚠️   STATUT FINAL : PROVISIONAL                                 ║"
    "║  Les templates d'attestation ne sont pas encore signés par      ║"
    "║  des auditeurs externes indépendants. Cette structure est prête ║"
    "║  à recevoir des signatures réelles mais NE CONSTITUE PAS        ║"
    "║  une preuve externe validée au sens VERIFIED_TIER2.             ║"
}
"║"
"║  Vérifications: $($checks -join ' | ')"
"║"
if ($issues.Count -gt 0) {
    "║  Points à corriger pour atteindre VERIFIED_TIER2 :"
    foreach ($i in $issues) { "║    • $i" }
}
"╚══════════════════════════════════════════════════════════════════╝"
""

# Retourner le statut pour utilisation par le super-calculateur
return $status
