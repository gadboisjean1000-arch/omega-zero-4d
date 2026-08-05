<#
.SYNOPSIS
    Supela – Push complet + création de PR vers gadboisjean1000-arch
    Exécuter APRÈS avoir placé le fichier DOCX dans docs/academic/

.PREREQUIS
    - Git installé et configuré
    - GitHub CLI (gh) installé : winget install GitHub.cli
    - Authentifié : gh auth login
    - Remote origin configuré vers gadboisjean1000-arch/supela

.NOTES
    Auteur : Jean-François Gadbois (gadboisjean1000-arch)
    Date   : Août 2026
#>

$ErrorActionPreference = "Stop"

$Remote     = "https://github.com/gadboisjean1000-arch/supela.git"
$AuthorName = "Jean-François Gadbois"
$AuthorMail = "GroupeNatuPro@outlook.com"

Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  SUPELA – Push multi-branches + Pull Request GitHub" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# ── Étape 1 : Init si pas déjà fait ──────────────────────────────
if (-not (Test-Path ".git")) {
    Write-Host "[1] Initialisation du dépôt Git..." -ForegroundColor Yellow
    git init
    git config user.name  $AuthorName
    git config user.email $AuthorMail
} else {
    Write-Host "[1] Dépôt Git déjà initialisé." -ForegroundColor Green
    git config user.name  $AuthorName
    git config user.email $AuthorMail
}

# ── Étape 2 : Remote ─────────────────────────────────────────────
$remotes = git remote 2>$null
if ($remotes -notcontains "origin") {
    Write-Host "[2] Ajout du remote origin..." -ForegroundColor Yellow
    git remote add origin $Remote
} else {
    Write-Host "[2] Remote origin déjà configuré." -ForegroundColor Green
}

# ── Étape 3 : Commit initial sur main ───────────────────────────
Write-Host "[3] Commit initial (main)..." -ForegroundColor Yellow
git add .
git commit -m "chore(init): initialisation Supela Framework v1.0

- README.md : architecture tripartite Fond-Surface-Cible
- CONTRIBUTING.md : workflow de PR Conventional Commits
- Template PR GitHub
- Boucle d'exécution PowerShell (src/powershell/Supela-Loop.ps1)
- Tests unitaires (tests/Test-Supela-Loop.ps1)
- Scripts d'initialisation Git"

# ── Étape 4 : Push main ─────────────────────────────────────────
Write-Host "[4] Push branche main..." -ForegroundColor Yellow
git push -u origin main

# ── Étape 5 : Branche dev/supela-core ───────────────────────────
Write-Host "[5] Création et push de dev/supela-core..." -ForegroundColor Yellow
git checkout -b dev/supela-core
git commit --allow-empty -m "chore(branch): création branche dev/supela-core

Branche principale de développement du moteur entropique Supela.
Reçoit les PR des branches feature/* et docs/*."
git push -u origin dev/supela-core

# ── Étape 6 : Branche feature/powershell-loop ───────────────────
Write-Host "[6] Création et push de feature/powershell-loop..." -ForegroundColor Yellow
git checkout -b feature/powershell-loop dev/supela-core
git commit --allow-empty -m "chore(branch): création branche feature/powershell-loop

Branche dédiée aux itérations sur la boucle d'exécution PS.
Fonction de transition T(H,v,σ) — seuils τ, λ, θ."
git push -u origin feature/powershell-loop

# ── Étape 7 : Branche docs/academic + DOCX ──────────────────────
Write-Host "[7] Création de docs/academic et ajout du document DOCX..." -ForegroundColor Yellow
git checkout main
git checkout -b docs/academic

# Vérifier si le DOCX est présent
$DocxPath = Join-Path $PSScriptRoot "docs\academic\Document-Maitre-Supela-Academique.docx"
if (Test-Path $DocxPath) {
    git add "docs/academic/Document-Maitre-Supela-Academique.docx"
    Write-Host "  ✔ Document DOCX ajouté au staging." -ForegroundColor Green
} else {
    Write-Host "  ⚠ DOCX non trouvé dans docs/academic/ — commit vide pour la branche." -ForegroundColor Yellow
}

git add PR-BODY.md
git commit -m "docs(academic): ajout Document Maître Supela version académique complète

Document Maître Supela – Version Académique Complète
Classification : Recteur / Docteur
Auteur : Jean-François Gadbois (gadboisjean1000-arch)
Date   : Août 2026

Sections :
  1. Résumé exécutif (Abstract)
  2. Introduction – Problématique et Positionnement
  3. Architecture Tripartite Fond – Surface – Cible
  4. Métriques Entropiques H(S), dH/dt, σ
  5. Seuils Décisionnels τ, λ, θ
  6. Fonction de Transition T(H, v, σ)
  7. Boucle d'Exécution PowerShell
  8. Intégration GitHub Multi-Branches
  9. Validation et Perspectives
 10. Conclusion + Références"

git push -u origin docs/academic

# ── Étape 8 : Création de la Pull Request ───────────────────────
Write-Host ""
Write-Host "[8] Création de la Pull Request via GitHub CLI..." -ForegroundColor Yellow

$GhAvailable = Get-Command gh -ErrorAction SilentlyContinue
if ($GhAvailable) {
    gh pr create `
        --base dev/supela-core `
        --head docs/academic `
        --title "feat(docs): Document Maître Supela – Version Académique Complète" `
        --body-file PR-BODY.md `
        --assignee "@me" `
        --label "documentation,academic"

    Write-Host ""
    Write-Host "  ✔ Pull Request créée avec succès !" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "  ⚠ GitHub CLI (gh) non trouvé. Créez la PR manuellement :" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "  URL de création de PR :"
    Write-Host "  https://github.com/gadboisjean1000-arch/supela/compare/dev/supela-core...docs/academic"
    Write-Host ""
    Write-Host "  Titre : feat(docs): Document Maître Supela – Version Académique Complète"
    Write-Host "  Corps : voir PR-BODY.md dans ce dossier"
    Write-Host ""
    Write-Host "  Installation GitHub CLI : winget install GitHub.cli"
    Write-Host "  Authentification        : gh auth login"
}

# ── Récapitulatif final ──────────────────────────────────────────
Write-Host ""
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  RÉCAPITULATIF" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""
git branch -v
Write-Host ""
Write-Host "  Remote : $(git remote get-url origin)"
Write-Host ""
Write-Host "  Branches poussées :" -ForegroundColor Green
Write-Host "    ✔ main"
Write-Host "    ✔ dev/supela-core"
Write-Host "    ✔ feature/powershell-loop"
Write-Host "    ✔ docs/academic"
Write-Host ""
Write-Host "  PR : docs/academic → dev/supela-core" -ForegroundColor Green
Write-Host ""
Write-Host "[Supela] Opération terminée." -ForegroundColor Cyan
