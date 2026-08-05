#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════
#  SUPELA – Script d'initialisation Git multi-branches
#  À exécuter dans le dossier racine du dépôt local
#  Auteur : Jean-François Gadbois (gadboisjean1000-arch)
#  Date   : Août 2026
# ═══════════════════════════════════════════════════════════════
set -e

REPO_REMOTE="https://github.com/gadboisjean1000-arch/supela.git"
AUTHOR_NAME="Jean-François Gadbois"
AUTHOR_EMAIL="GroupeNatuPro@outlook.com"

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  SUPELA – Initialisation du dépôt multi-branches"
echo "══════════════════════════════════════════════════════════"
echo ""

# ── 1. Init & config ─────────────────────────────────────────
git init
git config user.name  "$AUTHOR_NAME"
git config user.email "$AUTHOR_EMAIL"

echo "[1/6] Dépôt initialisé."

# ── 2. Branche main – commit initial ─────────────────────────
git add .
git commit -m "chore(init): initialisation du dépôt Supela Framework

- Structure multi-branches : main / dev / feature / docs
- README.md avec architecture tripartite Fond-Surface-Cible
- CONTRIBUTING.md avec workflow de PR
- Template de Pull Request GitHub"

echo "[2/6] Commit initial sur 'main' effectué."

# ── 3. Branche dev/supela-core ───────────────────────────────
git checkout -b dev/supela-core
git commit --allow-empty -m "chore(branch): création branche dev/supela-core

Branche de développement principal du moteur entropique.
Base : main v1.0"

echo "[3/6] Branche 'dev/supela-core' créée."

# ── 4. Branche feature/powershell-loop ──────────────────────
git checkout -b feature/powershell-loop dev/supela-core
git commit --allow-empty -m "chore(branch): création branche feature/powershell-loop

Branche dédiée aux itérations sur la boucle d'exécution PS.
Base : dev/supela-core"

echo "[4/6] Branche 'feature/powershell-loop' créée."

# ── 5. Branche docs/academic ─────────────────────────────────
git checkout main
git checkout -b docs/academic
git commit --allow-empty -m "docs(academic): ajout Document Maître Supela version académique

Document Maître Supela – Version Académique Complète
- Architecture tripartite Fond/Surface/Cible
- Métriques entropiques H(S), dH/dt, σ
- Seuils τ, λ, θ
- Fonction de transition T(H,v,σ)
- Boucle d'exécution PowerShell complète commentée
- Intégration GitHub multi-branches"

echo "[5/6] Branche 'docs/academic' créée avec commit documentaire."

# ── 6. Retour sur main & récapitulatif ──────────────────────
git checkout main
echo ""
echo "══════════════════════════════════════════════════════════"
echo "  BRANCHES CRÉÉES :"
git branch -v
echo ""
echo "══════════════════════════════════════════════════════════"
echo ""

# ── 7. Instructions pour pousser vers GitHub ─────────────────
echo "  ÉTAPES SUIVANTES pour pousser vers GitHub :"
echo ""
echo "  Option A – Remote déjà configuré :"
echo "    git remote add origin $REPO_REMOTE"
echo "    git push -u origin main"
echo "    git push origin dev/supela-core"
echo "    git push origin feature/powershell-loop"
echo "    git push origin docs/academic"
echo ""
echo "  Option B – GitHub CLI (recommandé) :"
echo "    gh repo create gadboisjean1000-arch/supela --public --source=. --remote=origin --push"
echo "    git push origin --all"
echo ""
echo "[6/6] Script terminé."
