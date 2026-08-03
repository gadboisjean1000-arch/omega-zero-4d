# SUPELA v1.1.0 — Super Calculateur de Vérification
# Usage: .\SUPER-CALCULATEUR-VERIFICATION.ps1 [-repo <path>]
param([string]$repo = $PSScriptRoot)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Read-JsonFile {
    param([string]$Path)
    if (-not (Test-Path $Path)) {
        throw "Fichier JSON introuvable: $Path"
    }

    $raw = Get-Content -Raw -Path $Path -Encoding UTF8
    try {
        return $raw | ConvertFrom-Json -Depth 20
    } catch {
        throw "JSON invalide dans $Path :: $($_.Exception.Message)"
    }
}

function Invoke-Git {
    param(
        [string]$Repository,
        [string[]]$Arguments
    )

    return & git -C $Repository @Arguments 2>$null
}

function Test-IsoTimestamp {
    param([string]$Value)
    if ([string]::IsNullOrWhiteSpace($Value)) {
        return $false
    }

    try {
        [void][datetimeoffset]::Parse($Value)
        return $true
    } catch {
        return $false
    }
}

$scoreA = 0
$scoreB = 0
$scoreC = 0
$scoreD = 0
$scoreE = 0
$scoreF = 0
$details = @()

# BLOC A: Fichiers requis (40 pts)
$files = @(
    'SYNTHESE-FINALE-SUPELA-v1.1.0.md', 'MASTER-FORMALIZATION.md',
    'PERFORMANCE-BENCHMARKS-SUPELA-v1.1.0.md', 'PERFORMANCE-VALIDATION-50-50.md',
    'ANNEXES-A-D-NORMES-OPERATIONNELLES.md', 'DASHBOARD-SGG-v2-INTERACTIVE.html',
    'AUTHORS.md', 'RFC-SUPELA-K3-ANNEXE-E-SCDH.md',
    'NORMALISATION-COMPLETE.md', 'DEPLOYMENT-ROADMAP.md'
)
$present = 0
foreach ($f in $files) {
    if (Test-Path (Join-Path $repo $f)) {
        $present++
    }
}
$scoreA = [math]::Round(($present / $files.Count) * 40, 2)
$details += "A fichiers   $present/$($files.Count) = $scoreA/40"

# BLOC B: Marqueurs de contenu (30 pts)
$markers = @(
    @{ file = 'PERFORMANCE-VALIDATION-50-50.md'; p = '50/50 PASS' },
    @{ file = 'RFC-SUPELA-K3-ANNEXE-E-SCDH.md'; p = '19/19 PASS' },
    @{ file = 'NORMALISATION-COMPLETE.md'; p = 'Point Fixe Atteint' },
    @{ file = 'ANNEXES-A-D-NORMES-OPERATIONNELLES.md'; p = 'N0' },
    @{ file = 'ANNEXES-A-D-NORMES-OPERATIONNELLES.md'; p = 'V1' },
    @{ file = 'DASHBOARD-SGG-v2-INTERACTIVE.html'; p = 'SGG_v2' }
)
$hits = 0
foreach ($m in $markers) {
    $f2 = Join-Path $repo $m.file
    if ((Test-Path $f2) -and (Select-String -Path $f2 -Pattern $m.p -Quiet)) {
        $hits++
    }
}
$scoreB = [math]::Round(($hits / $markers.Count) * 30, 2)
$details += "B marqueurs  $hits/$($markers.Count) = $scoreB/30"

# BLOC C: Preuves Git immuables (20 pts)
$cc = [int](Invoke-Git -Repository $repo -Arguments @('rev-list', '--count', 'HEAD'))
$hasTag = [bool](Invoke-Git -Repository $repo -Arguments @('tag', '-l', 'v1.1.0-PRODUCTION-READY'))
$clean = -not [bool](Invoke-Git -Repository $repo -Arguments @('status', '--porcelain'))
$cpts = 0
if ($cc -ge 15) { $cpts += 10 }
if ($hasTag) { $cpts += 6 }
if ($clean) { $cpts += 4 }
$scoreC = $cpts
$details += "C git        commits=$cc tag=$hasTag clean=$clean = $scoreC/20"

# BLOC D: Opérations (10 pts)
$wfDir = Join-Path $repo '.github\workflows'
$wfYml = 0
if (Test-Path $wfDir) {
    $wfYml = @(Get-ChildItem $wfDir -Filter *.yml).Count + @(Get-ChildItem $wfDir -Filter *.yaml).Count
}
$dash = Join-Path $repo 'DASHBOARD-SGG-v2-INTERACTIVE.html'
$jsonExport = Join-Path $repo 'DASHBOARD-SGG-v2-KPI.json'
$csvExport = Join-Path $repo 'DASHBOARD-SGG-v2-KPI.csv'
$hasY = Select-String -Path $dash -Pattern '🟡|status-yellow' -Quiet
$hasR = Select-String -Path $dash -Pattern '🔴|status-red' -Quiet
$kpiOK = (-not $hasY) -and (-not $hasR)
if ($wfYml -gt 0) { $scoreD += 3 }
if ((Test-Path $jsonExport) -and (Test-Path $csvExport)) { $scoreD += 2 }
if ($kpiOK) { $scoreD += 5 }
$details += "D ops        workflows=$wfYml exports=$(Test-Path $jsonExport)/$(Test-Path $csvExport) kpiAllGreen=$kpiOK = $scoreD/10"

# BLOC E: Preuve externe (10 pts)
$externalArtifact = Join-Path $repo 'evidence\external-audit\third-party-audit-artifact.txt'
$externalManifestPath = Join-Path $repo 'evidence\external-audit\external-proof-manifest.json'
$externalPresenceScore = 0
$externalIntegrityScore = 0
$externalReproScore = 0

$artifactExists = Test-Path $externalArtifact
$manifestExists = Test-Path $externalManifestPath
if ($artifactExists) { $externalPresenceScore += 1.5 }
if ($manifestExists) { $externalPresenceScore += 1.5 }

$manifest = $null
if ($manifestExists) {
    $manifest = Read-JsonFile -Path $externalManifestPath
}

$hashMatches = $false
if ($artifactExists -and $manifestExists -and -not [string]::IsNullOrWhiteSpace($manifest.expected_sha256)) {
    $artifactHash = (Get-FileHash -Algorithm SHA256 -Path $externalArtifact).Hash.ToLowerInvariant()
    $hashMatches = $artifactHash -eq $manifest.expected_sha256.ToLowerInvariant()
    if ($hashMatches) {
        $externalIntegrityScore = 4
    }
}

$hasRunReference = $manifestExists -and -not [string]::IsNullOrWhiteSpace($manifest.run_reference)
$hasTimestamp = $manifestExists -and (Test-IsoTimestamp -Value $manifest.generated_at_utc)
$hasCommit = $manifestExists -and ($manifest.commit -match '^[0-9a-f]{7,40}$')
$hasSource = $manifestExists -and -not [string]::IsNullOrWhiteSpace($manifest.source)
$commitReachable = $false
if ($hasCommit) {
    & git -C $repo cat-file -e "$($manifest.commit)^{commit}" 2>$null
    $commitReachable = $LASTEXITCODE -eq 0
}
$reproChecks = @($hasRunReference, $hasTimestamp, $hasCommit, $hasSource, $commitReachable)
$externalReproScore = [math]::Round((($reproChecks | Where-Object { $_ }).Count / $reproChecks.Count) * 3, 2)

$scoreE = [math]::Round($externalPresenceScore + $externalIntegrityScore + $externalReproScore, 2)
$details += "E preuve ext presence=$([math]::Round($externalPresenceScore,2))/3 hash=$hashMatches runRef=$hasRunReference ts=$hasTimestamp commit=$hasCommit reachable=$commitReachable = $scoreE/10"

# BLOC F: Validation psychométrique outillée (10 pts)
$psyJsonPath = Join-Path $repo 'evidence\psychometrics\psychometric-results.json'
$psyCsvPath = Join-Path $repo 'evidence\psychometrics\psychometric-results.csv'
$thresholdsPath = Join-Path $repo 'evidence\psychometrics\psychometric-thresholds.json'

$psyPresenceScore = 0
$psyThresholdScore = 0
$psyTraceScore = 0
$psyJsonExists = Test-Path $psyJsonPath
$psyCsvExists = Test-Path $psyCsvPath
if ($psyJsonExists) { $psyPresenceScore += 1.5 }
if ($psyCsvExists) { $psyPresenceScore += 1.5 }

$thresholds = @{
    kappa_min = 0.75
    cfi_min = 0.95
    rmsea_max = 0.06
    tli_min = 0.95
    srmr_max = 0.08
    rasch_infit_min = 0.70
    rasch_infit_max = 1.30
    rasch_outfit_min = 0.70
    rasch_outfit_max = 1.30
}

if (Test-Path $thresholdsPath) {
    $thresholdOverrides = Read-JsonFile -Path $thresholdsPath
    foreach ($k in @($thresholds.Keys)) {
        if ($null -ne $thresholdOverrides.$k) {
            $thresholds[$k] = [double]$thresholdOverrides.$k
        }
    }
}

$psy = $null
if ($psyJsonExists) {
    $psy = Read-JsonFile -Path $psyJsonPath
}

$csvRows = @()
if ($psyCsvExists) {
    $csvRows = Import-Csv -Path $psyCsvPath
}

$kappaValue = if ($psy) { [double]$psy.kappa.value } else { 0 }
$cfi = if ($psy) { [double]$psy.cfa.cfi } else { 0 }
$rmsea = if ($psy) { [double]$psy.cfa.rmsea } else { 99 }
$tli = if ($psy) { [double]$psy.cfa.tli } else { 0 }
$srmr = if ($psy) { [double]$psy.cfa.srmr } else { 99 }
$infit = if ($psy) { [double]$psy.rasch.infit_mean } else { 0 }
$outfit = if ($psy) { [double]$psy.rasch.outfit_mean } else { 0 }

$kappaPass = $kappaValue -ge $thresholds['kappa_min']
$cfiPass = $cfi -ge $thresholds['cfi_min']
$rmseaPass = $rmsea -le $thresholds['rmsea_max']
$tliPass = $tli -ge $thresholds['tli_min']
$srmrPass = $srmr -le $thresholds['srmr_max']
$infitPass = ($infit -ge $thresholds['rasch_infit_min']) -and ($infit -le $thresholds['rasch_infit_max'])
$outfitPass = ($outfit -ge $thresholds['rasch_outfit_min']) -and ($outfit -le $thresholds['rasch_outfit_max'])

$thresholdChecks = @($kappaPass, $cfiPass, $rmseaPass, $tliPass, $srmrPass, $infitPass, $outfitPass)
$psyThresholdScore = [math]::Round((($thresholdChecks | Where-Object { $_ }).Count / $thresholdChecks.Count) * 4, 2)

$psyRunRef = $psy -and -not [string]::IsNullOrWhiteSpace($psy.metadata.run_reference)
$psyTimestamp = $psy -and (Test-IsoTimestamp -Value $psy.metadata.generated_at_utc)
$psyCommit = $psy -and ($psy.metadata.commit -match '^[0-9a-f]{7,40}$')
$psyDataset = $psy -and -not [string]::IsNullOrWhiteSpace($psy.metadata.dataset_id)
$psyTools = $psy -and $psy.metadata.toolchain.Count -ge 2
$psyParams = $psy -and $null -ne $psy.parameters.rasch_model -and $null -ne $psy.parameters.cfa_estimator
$psyStats = $psy -and $null -ne $psy.rasch.sample_size -and $null -ne $psy.cfa.sample_size -and $null -ne $psy.kappa.ci95_low
$psyCsvTrace = $csvRows.Count -ge 6

$traceChecks = @($psyRunRef, $psyTimestamp, $psyCommit, $psyDataset, $psyTools, $psyParams, $psyStats, $psyCsvTrace)
$psyTraceScore = [math]::Round((($traceChecks | Where-Object { $_ }).Count / $traceChecks.Count) * 3, 2)

$scoreF = [math]::Round($psyPresenceScore + $psyThresholdScore + $psyTraceScore, 2)
$details += "F psycho     files=$psyJsonExists/$psyCsvExists kappa=$kappaValue cfi=$cfi rmsea=$rmsea tli=$tli srmr=$srmr trace=$($psyTraceScore)/3 = $scoreF/10"

$rawTotal = [math]::Round($scoreA + $scoreB + $scoreC + $scoreD + $scoreE + $scoreF, 2)
$maxRaw = 120
$total = [math]::Round(($rawTotal / $maxRaw) * 100, 2)

$level = if ($total -ge 97) {
    'N5 ROBUSTESSE AVANCÉE [97-100]'
} elseif ($total -ge 95) {
    'N4+ RENFORCÉ          [95-96.99]'
} elseif ($total -ge 85) {
    'PRET AVEC RESERVES    [85-94.99]'
} else {
    'NON CONFORME          [<85]'
}

""
"╔════════════════════════════════════════════════════════════════╗"
"║   ⬡  SUPELA v1.1.0 — SUPER CALCULATEUR (A→F)   ⬡             ║"
"╠════════════════════════════════════════════════════════════════╣"
foreach ($d in $details) { "║  $d" }
"╠════════════════════════════════════════════════════════════════╣"
"║  SCORE BRUT   ->  $rawTotal / $maxRaw"
"║  SCORE GLOBAL ->  $total / 100"
"║  NIVEAU       ->  $level"
"╚════════════════════════════════════════════════════════════════╝"
""
"Run: .\SUPER-CALCULATEUR-VERIFICATION.ps1"
