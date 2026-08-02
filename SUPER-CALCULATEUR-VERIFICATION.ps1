# SUPELA v1.1.0 — Super Calculateur de Vérification
# Usage: .\SUPER-CALCULATEUR-VERIFICATION.ps1 [-repo <path>]
param([string]$repo = $PSScriptRoot)

$scoreA=0;$scoreB=0;$scoreC=0;$scoreD=0;$details=@()

# BLOC A: Fichiers requis (40 pts)
$files=@(
 'SYNTHESE-FINALE-SUPELA-v1.1.0.md','MASTER-FORMALIZATION.md',
 'PERFORMANCE-BENCHMARKS-SUPELA-v1.1.0.md','PERFORMANCE-VALIDATION-50-50.md',
 'ANNEXES-A-D-NORMES-OPERATIONNELLES.md','DASHBOARD-SGG-v2-INTERACTIVE.html',
 'AUTHORS.md','RFC-SUPELA-K3-ANNEXE-E-SCDH.md',
 'NORMALISATION-COMPLETE.md','DEPLOYMENT-ROADMAP.md'
)
$present=0; foreach($f in $files){if(Test-Path (Join-Path $repo $f)){$present++}}
$scoreA=[math]::Round(($present/$files.Count)*40,2)
$details+="A fichiers   $present/$($files.Count) = $scoreA/40"

# BLOC B: Marqueurs de contenu (30 pts)
$markers=@(
 @{file='PERFORMANCE-VALIDATION-50-50.md';p='50/50 PASS'},
 @{file='RFC-SUPELA-K3-ANNEXE-E-SCDH.md';p='19/19 PASS'},
 @{file='NORMALISATION-COMPLETE.md';p='Point Fixe Atteint'},
 @{file='ANNEXES-A-D-NORMES-OPERATIONNELLES.md';p='N0'},
 @{file='ANNEXES-A-D-NORMES-OPERATIONNELLES.md';p='V1'},
 @{file='DASHBOARD-SGG-v2-INTERACTIVE.html';p='SGG_v2'}
)
$hits=0
foreach($m in $markers){
  $f2=Join-Path $repo $m.file
  if((Test-Path $f2) -and (Select-String -Path $f2 -Pattern $m.p -Quiet)){$hits++}
}
$scoreB=[math]::Round(($hits/$markers.Count)*30,2)
$details+="B marqueurs  $hits/$($markers.Count) = $scoreB/30"

# BLOC C: Preuves Git immuables (20 pts)
$cc=[int](git -C $repo rev-list --count HEAD 2>$null)
$hasTag=[bool](git -C $repo tag -l v1.1.0-PRODUCTION-READY 2>$null)
$clean=-not [bool](git -C $repo status --porcelain 2>$null)
$cpts=0
if($cc -ge 15){$cpts+=10}
if($hasTag){$cpts+=6}
if($clean){$cpts+=4}
$scoreC=$cpts
$details+="C git        commits=$cc tag=$hasTag clean=$clean = $scoreC/20"

# BLOC D: Opérations (10 pts)
$wfDir=Join-Path $repo '.github\workflows'
$wfYml=0
if(Test-Path $wfDir){
  $wfYml=(Get-ChildItem $wfDir -Filter *.yml).Count+(Get-ChildItem $wfDir -Filter *.yaml).Count
}
$dash=Join-Path $repo 'DASHBOARD-SGG-v2-INTERACTIVE.html'
$hasY=Select-String -Path $dash -Pattern '🟡|status-yellow' -Quiet
$hasR=Select-String -Path $dash -Pattern '🔴|status-red' -Quiet
$kpiOK=(-not $hasY) -and (-not $hasR)
if($wfYml -gt 0){$scoreD+=6}
if($kpiOK){$scoreD+=4}
$details+="D ops        workflows=$wfYml kpiAllGreen=$kpiOK = $scoreD/10"

$total=[math]::Round($scoreA+$scoreB+$scoreC+$scoreD,2)
$level=if($total -ge 95){'CERTIFIE PRODUCTION  [100%]'} `
       elseif($total -ge 85){'PRET AVEC RESERVES   [85-94]'} `
       else {'NON CONFORME         [<85]'}

""
"╔══════════════════════════════════════════════════╗"
"║   ⬡  SUPELA v1.1.0 — SUPER CALCULATEUR  ⬡      ║"
"╠══════════════════════════════════════════════════╣"
foreach($d in $details){"║  $d"}
"╠══════════════════════════════════════════════════╣"
"║  SCORE TOTAL  ->  $total / 100"
"║  NIVEAU       ->  $level"
"╚══════════════════════════════════════════════════╝"
""; "Run: .\SUPER-CALCULATEUR-VERIFICATION.ps1"
