<#
.SYNOPSIS
    Supela – Boucle d'exécution principale
    Modèle Entropique de Navigation Systémique

.DESCRIPTION
    Implémente la boucle de navigation entropique Supela.
    Calcule H(S), dH/dt, σ et applique la fonction de transition T(H,v,σ)
    pour piloter la navigation vers la Cible (C).

.PARAMETER Tau
    Seuil de transition τ — déclenche la navigation active (défaut: 0.75)

.PARAMETER Lambda
    Seuil de latence λ en secondes — délai minimal inter-décisions (défaut: 2.0)

.PARAMETER Theta
    Seuil de convergence θ — critère d'arrêt (défaut: 0.15)

.PARAMETER MaxIter
    Garde-fou : nombre maximal d'itérations (défaut: 1000)

.EXAMPLE
    .\Supela-Loop.ps1
    .\Supela-Loop.ps1 -Tau 0.8 -Lambda 1.5 -Theta 0.10 -MaxIter 500

.NOTES
    Auteur  : Jean-François Gadbois (gadboisjean1000-arch)
    Version : 1.0 Académique
    Date    : Août 2026
    Dépôt   : https://github.com/gadboisjean1000-arch/supela
#>

param(
    [double]$Tau     = 0.75,   # Seuil de transition τ
    [double]$Lambda  = 2.0,    # Seuil de latence λ (secondes)
    [double]$Theta   = 0.15,   # Seuil de convergence θ
    [int]   $MaxIter = 1000    # Garde-fou anti-boucle infinie
)

# ─────────────────────────────────────────────
# FONCTIONS UTILITAIRES
# ─────────────────────────────────────────────

function Get-Entropy {
    <#
    .SYNOPSIS Calcule l'entropie de Shannon H(S) = -∑ pᵢ·log₂(pᵢ)#>
    param([double[]]$Probs)
    $entropy = 0.0
    foreach ($p in $Probs) {
        if ($p -gt 0) {
            $entropy -= $p * [Math]::Log($p, 2)
        }
    }
    return $entropy
}

function Get-StdDev {
    <#
    .SYNOPSIS Calcule l'écart-type σ d'une distribution de probabilités#>
    param([double[]]$Probs)
    $mean = ($Probs | Measure-Object -Average).Average
    $variance = ($Probs | ForEach-Object { [Math]::Pow($_ - $mean, 2) } | Measure-Object -Sum).Sum / $Probs.Count
    return [Math]::Sqrt($variance)
}

function Get-Transition {
    <#
    .SYNOPSIS
        Fonction de transition T(H, v, σ)
        T : ℝ³ → {Navigation, Stabilisation, Convergence, Observation}
    #>
    param(
        [double]$H,
        [double]$V,      # v = dH/dt
        [double]$Sigma,
        [double]$Tau,
        [double]$Theta
    )
    if     ($H -lt $Theta)                   { return "Convergence"    }
    elseif ($H -gt $Tau -and $V -gt 0)       { return "Navigation"     }
    elseif ($H -gt $Tau -and $V -le 0)       { return "Stabilisation"  }
    else                                      { return "Observation"    }
}

function Get-NormalizedProbs {
    <#
    .SYNOPSIS Génère et normalise un vecteur de probabilités (simulation)#>
    $raw = 1..4 | ForEach-Object {
        [Math]::Max(0.01, (Get-Random -Minimum 5 -Maximum 45) / 100.0)
    }
    $sum = ($raw | Measure-Object -Sum).Sum
    return $raw | ForEach-Object { $_ / $sum }
}

# ─────────────────────────────────────────────
# INITIALISATION
# ─────────────────────────────────────────────

Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SUPELA — Boucle d'Exécution Entropique v1.0" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  τ=$Tau  |  λ=${Lambda}s  |  θ=$Theta  |  MaxIter=$MaxIter" -ForegroundColor Gray
Write-Host ""

$Iter       = 0
$H_prev     = 1.0      # Entropie initiale (état de haute incertitude)
$LastAction = [DateTime]::MinValue
$Action     = "Observation"
$Journal    = @()

# ─────────────────────────────────────────────
# BOUCLE PRINCIPALE
# ─────────────────────────────────────────────

do {
    $Iter++

    # 1. Vérifier le seuil de latence λ
    $Elapsed = (Get-Date) - $LastAction
    if ($Elapsed.TotalSeconds -lt $Lambda -and $Iter -gt 1) {
        Start-Sleep -Milliseconds 200
        continue
    }

    # 2. Collecter les probabilités de la Surface (S)
    $Probs = Get-NormalizedProbs

    # 3. Calculer les métriques entropiques
    $H     = Get-Entropy  -Probs $Probs
    $V     = $H - $H_prev                     # dH/dt (discrétisé)
    $Sigma = Get-StdDev   -Probs $Probs

    # 4. Appliquer la fonction de transition T(H, v, σ)
    $Action = Get-Transition -H $H -V $V -Sigma $Sigma -Tau $Tau -Theta $Theta

    # 5. Journaliser
    $Entry = [PSCustomObject]@{
        Iter   = $Iter
        H      = [Math]::Round($H, 4)
        V      = [Math]::Round($V, 4)
        Sigma  = [Math]::Round($Sigma, 4)
        Action = $Action
        Time   = (Get-Date).ToString("HH:mm:ss.fff")
    }
    $Journal += $Entry

    # 6. Afficher et exécuter l'action
    $color = switch ($Action) {
        "Navigation"    { "Yellow" }
        "Stabilisation" { "Blue"   }
        "Convergence"   { "Green"  }
        default         { "Gray"   }
    }
    Write-Host "[#$($Iter.ToString('D4'))]  H=$($Entry.H)  dH/dt=$($Entry.V)  σ=$($Entry.Sigma)  →  " -NoNewline
    Write-Host $Action -ForegroundColor $color

    switch ($Action) {
        "Navigation"     { Write-Host "  ↳ Exploration active — nouveaux états de la Surface..." -ForegroundColor DarkYellow }
        "Stabilisation"  { Write-Host "  ↳ Consolidation — réduction de la dérive entropique..." -ForegroundColor DarkBlue   }
        "Convergence"    { Write-Host "  ↳ Cible atteinte — H(S) < θ. Cycle terminé."           -ForegroundColor DarkGreen  }
        "Observation"    { Write-Host "  ↳ Surveillance passive — métriques sous τ et au-dessus θ..." -ForegroundColor DarkGray }
    }

    # 7. Mettre à jour l'état précédent
    $H_prev     = $H
    $LastAction = Get-Date

} while ($Action -ne "Convergence" -and $Iter -lt $MaxIter)

# ─────────────────────────────────────────────
# RAPPORT FINAL
# ─────────────────────────────────────────────

Write-Host ""
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RAPPORT FINAL SUPELA" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Itérations totales : $Iter"
Write-Host "  H final            : $([Math]::Round($H, 4))"
Write-Host "  État terminal      : $Action"
if ($Iter -ge $MaxIter) {
    Write-Host "  ⚠ Garde-fou MaxIter atteint — convergence non garantie" -ForegroundColor Red
}
Write-Host ""

# Exporter le journal en CSV
$JournalPath = Join-Path $PSScriptRoot "..\..\logs\supela-run-$(Get-Date -Format 'yyyyMMdd-HHmmss').csv"
$null = New-Item -ItemType Directory -Force -Path (Split-Path $JournalPath)
$Journal | Export-Csv -Path $JournalPath -NoTypeInformation -Encoding UTF8
Write-Host "  Journal exporté → $JournalPath" -ForegroundColor Gray
Write-Host ""
