# Unification Multi-Dépôts & Multi-Branches · `gadboisjean1000-arch` (*Wheeppp*) & `groupnatupro/multi-branches`

> **Horodatage de vérification :** `2026-11-17T17:33:06Z`  
> **Règle appliquée :** `M3` (`OPEN ∧ ¬FABRICATE`) & Règle A12 (zéro orphelin, zéro lien cassé, zéro dérive).

---

## 1. Périmètre Vérifié : `gadboisjean1000-arch` (*Wheeppp*)

Relevé direct via `gh repo list gadboisjean1000-arch --limit 30` : **`15` dépôts accessibles** (`4` originaux + `11` forks).

### Dépôts originaux (architecture unifiée Supela)
| Dépôt | Branche par défaut | Rôle dans l'architecture unifiée | Statut d'intégration |
|---|---|---|---|
| `gadboisjean1000-arch/omega-zero-4d` | `main` (PR active : `feat/multi-engine-bench`) | Moteur formel $\Pi_0$, barrière 4D, Guard-Kernel Python/Rust, Banc multi-moteurs, OPA Rego v1, WORM, MCP stdio (`10` outils) | `ACTIF` (`PR #5`) |
| `gadboisjean1000-arch/Supela-K3-Omega` | `main` | Monolithe de cohérence $\mathrm{GDS} = \langle D, O, A, \gamma \rangle$, `policies/gds_invariants.rego` | `CONNECTED_GITHUB_API` (pont [`network_bus.py`](../../src/omega_zero/network_bus.py)) |
| `gadboisjean1000-arch/sevengate-store` | `main` | Dépôt original suivi dans l'encyclopédie | `INDEXÉ_DICTIONNAIRE` |
| `gadboisjean1000-arch/utilise` | `main` | Dépôt original suivi dans l'encyclopédie | `INDEXÉ_DICTIONNAIRE` |

### Forks suivis (`11` dépôts)
`cli-1` (`latest`), `kilocode` (`main`), `gk-cli` (`main`), `git` (`master` — monté localement), `sourcery` (`main`), `cline` (`main`), `pytest` (`main`), `vscode-github-actions` (`main`), `cloudflare-docs` (`production`), `LibreHardwareMonitor` (`master`), `PSReadLine` (`master`).

---

## 2. Manque Ouvert (`INACCESSIBLE_DANS_LE_PÉRIMÈTRE`) : `groupnatupro/multi-branches`

- **URL cible :** `https://github.com/groupnatupro/multi-branches`
- **Constat brut (`TRACE-05 → TRACE-06`) :**
  - `gh repo view groupnatupro/multi-branches` → `GraphQL: Could not resolve to a Repository with the name 'groupnatupro/multi-branches'. (repository)`
  - `gh repo list groupnatupro` → `[]`
- **Statut Supela (`M3`) :** `INACCESSIBLE_DANS_LE_PÉRIMÈTRE` (dépôt privé hors portée du jeton GitHub actuel, ou inexistant sous ce nom exact). Aucun contenu ni branche de `groupnatupro/multi-branches` n'est inventé ou présumé.
- **Conditions de réouverture :**
  1. Ajouter `groupnatupro/multi-branches` aux ressources GitHub du projet (ou autoriser l'accès OAuth à l'organisation `groupnatupro`), puis
  2. Réexécuter `gh repo view groupnatupro/multi-branches` et `gh api repos/groupnatupro/multi-branches/branches` pour fusionner ses branches dans ce registre.
