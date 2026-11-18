# Système Nerveux Exécutable Supela · Local Bridge v0.1 (`L0`) & Runtime v0.2 (`L1`–`L7`)

> **Schéma d'état :** [`schemas/supela-state.schema.json`](../../schemas/supela-state.schema.json) (`supela-state/0.2`) · **Implémentation :** [`src/omega_zero/supela_runtime.py`](../../src/omega_zero/supela_runtime.py) · **Serveur MCP :** [`src/omega_zero/mcp_server.py`](../../src/omega_zero/mcp_server.py) · **Autorité normative exclusive :** `Jean-François Gadbois`

## 1. Provenance & Honnêteté Épistémique (M365 Copilot ↔ `omega-zero-4d`)

| Artefact M365 Copilot | Empreinte SHA-256 rapportée | Couche | Statut d'acquisition VM | Statut local `omega-zero-4d` |
|---|---|---|---|---|
| `supela-local-bridge-v0.1.zip` | `650337274c316f1cf76f47be5489eec592fa6bcfbdb5fbc614809cf8c2085710` | `L0 Transport` | URL éphémère Skype ASM (`HTTP/2 404` hors session M365) — `RAPPORTÉ` | Réimplémenté et vérifié localement dans [`SupelaLocalBridge`](../../src/omega_zero/supela_runtime.py) (`EXÉCUTÉ`) |
| `supela-runtime-v0.2.zip` | `b5fab177db18288ed78a60a9cd8e84dd866034e0557c0f1c95ed9c06cdebab83` | `L0`–`L7` Système nerveux | URL éphémère Skype ASM (`HTTP/2 404` hors session M365) — `RAPPORTÉ` | Réimplémenté et vérifié localement dans [`SupelaRuntime`](../../src/omega_zero/supela_runtime.py) + [`schemas/supela-state.schema.json`](../../schemas/supela-state.schema.json) (`EXÉCUTÉ`) |

## 2. Architecture des Couches `L0` à `L7`

```text
CONCEPT (L1)
  ↓
CODE (L2)
  ↓
EXÉCUTION (L3)
  ↓
PREUVE (L4)
  ↓
CONTRADICTION (L5)
  ├── ouverte ──→ RÉVISION (L6 : generation + 1, sans effacer l'ancienne trace) ──→ CODE (L2)
  └── absente ──→ CANDIDAT À RATIFICATION (L7)
                    ↓
              Jean-François Gadbois
              ├── ACCEPT   (RATIFIED_ACCEPTED)
              ├── REFUSE   (RATIFIED_REFUSED)
              └── ADJOURN  (RATIFIED_ADJOURNED)
                    ↓
              RÉOUVERTURE POSSIBLE (REOPENED, raison inscrite dans l'historique)
```

| Couche | Classe / Méthode | Rôle mécanique & Garde-fous |
|---|---|---|
| **`L0 Transport`** | `SupelaLocalBridge` | Lecture/écriture bornée au dépôt (`PathBoundaryError`), commandes en liste blanche sans shell libre (`shell=False`, `UnauthorizedCommandError`), registre JSONL chaîné SHA-256 (`LedgerTamperError`). |
| **`L1 Concept`** | `create_concept` | Crée un dossier (`generation = 1`, statut `CONCEPT`) avec affirmation, périmètre (`scope`) et provenance. |
| **`L2 Build`** | `register_code` | Enregistre l'artefact dans le périmètre autorisé, calcule son SHA-256 et conserve le lien `concept → artefact` (`CODE_REGISTERED`). |
| **`L3 Execute`** | `execute` | Exécute une commande autorisée et conserve un échec (`returncode != 0`) comme résultat observé dans son périmètre (`OBSERVED_FAIL_IN_SCOPE`) sans en faire automatiquement une réfutation universelle. |
| **`L4 Evidence`** | `collect_evidence` | Scelle les empreintes d'artefacts, les exécutions et l'environnement dans le registre probatoire JSONL append-only (`EVIDENCE_COLLECTED`). |
| **`L5 Contradiction`** | `evaluate` | Si une contradiction est ouverte (`OPEN`), produit trois effets mécaniques : (1) statut `CONTRADICTOIRE`, (2) blocage mécanique de `submit_ratification`, (3) obligation de révision motivée. |
| **`L6 Revision`** | `request_revision` | Archive l'état de la génération $g$ dans `previous_generations` ($K_g \subseteq K_{g+1}$), marque les contradictions de génération $g$ comme `SUPERSEDED_BY_REVISION` et passe à `generation + 1` (`REVISION_REQUESTED`). |
| **`L7 Ratification`** | `submit_ratification`, `ratify`, `reopen` | Refuse toute auto-ratification par l'IA (`SupelaAuthorityError`) ; seul `"Jean-François Gadbois"` peut décider `ACCEPT`, `REFUSE` ou `ADJOURN`. Tout état ratifié/refusé/ajourné reste réouvrable (`RATIFICATION ≠ FIN`). |

## 3. Les 11 Outils MCP Exposés (`omega-zero-mcp`)

1. `supela_create_concept` — Initialise un dossier en génération 1 (`L1`).
2. `supela_register_code` — Enregistre un artefact de code et son SHA-256 (`L2`).
3. `supela_execute` — Exécute une commande de la liste blanche sans shell libre (`L3`).
4. `supela_collect_evidence` — Scelle les preuves dans le registre JSONL SHA-256 (`L4`).
5. `supela_evaluate` — Évalue les contradictions dans le périmètre (`L5`).
6. `supela_request_revision` — Ouvre une nouvelle génération `generation + 1` sans effacer l'ancienne trace (`L6`).
7. `supela_submit_ratification` — Soumet le dossier sans contradiction ouverte au seuil normatif (`L7`).
8. `supela_ratify` — Franchit la frontière normative (réservé à `Jean-François Gadbois` : `ACCEPT`, `REFUSE`, `ADJOURN`).
9. `supela_reopen` — Réouvre un dossier ratifié/refusé/ajourné avec motivation inscrite dans l'historique.
10. `supela_get_state` — Retourne l'état complet vérifié SHA-256 conforme à [`schemas/supela-state.schema.json`](../../schemas/supela-state.schema.json).
11. `supela_verify_ledger` — Vérifie l'intégrité de la chaîne SHA-256 du journal probatoire JSONL.

## 4. Commandes de Test & d'Exécution

```bash
# 1. Exécuter les tests unitaires et MCP du Runtime Supela v0.2
.venv/bin/pytest -v tests/test_supela_runtime_v02.py

# 2. Exécuter un cycle complet L0-L7 (G1 contradictoire -> Révision G2 -> Ratification -> Réouverture)
.venv/bin/omega-network runtime-cycle --out reports/SUPELA-RUNTIME-V02-CYCLE.json

# 3. Vérifier le diagnostic complet du bus réseau (24 outils MCP exposés)
.venv/bin/omega-network doctor
```
