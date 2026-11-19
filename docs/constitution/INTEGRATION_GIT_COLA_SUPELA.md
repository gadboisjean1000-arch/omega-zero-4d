# Intégration Souveraine `git-cola` × Supela (`0 $ PMU` · DAG Git · Revue Humaine)

> **Référence amont :** [`https://github.com/git-cola/git-cola`](https://github.com/git-cola/git-cola) (*The highly caffeinated Git GUI*, Python/Qt, licence `GPL-2.0`)  
> **Séparation de licence propre (`Apache-2.0` ↔ `GPL-2.0`) :** `git-cola` est intégré exclusivement comme **outil externe optionnel invoqué hors processus** (configuration locale `git config --local guitool.*`). Aucun code source `GPL-2.0` de `git-cola` n'est copié ni lié dans le paquet `omega-zero-4d` (`Apache-2.0`), garantissant une conformité juridique internationale irréprochable.

---

## 1. Apports de `git-cola` alignés sur la doctrine Supela

| Capacité `git-cola` | Alignement Supela (`VR-01..20` · `0 $ PMU`) |
|---|---|
| **Visualiseur DAG (`git cola dag`)** | Inspection graphique directe du graphe acyclique orienté Git (`K_t ⊆ K_{t+1}`, branches, rétractions, tags) sans service cloud propriétaire. |
| **Indexation chirurgicale par bloc/ligne (*hunk/line staging*)** | Permet une revue humaine granulaire (`C10 : amélioration ≠ autorisation`) avant chaque commit sur branche de PR (`VR-03`). |
| **Signature cryptographique GPG / SSH intégrée** | Authentification de l'auteur souverain (`QUI`) directement depuis l'interface locale, en complément des preuves automatisées (`QUOI`). |
| **Actions personnalisées (`guitool.*`)** | Déclenche en un clic les sondes locales Supela (`verify_a12.py`, `vr_compliance_check.py`, `build_proven_laws_web.py`, `opa test`, `pytest`). |
| **0 $ PMU & Multi-OS (Windows / Linux / macOS)** | Zéro abonnement, zéro télémétrie, fonctionne 100 % hors ligne dans le socle TCB minimal (`CADRE_DIRECTEUR_OSBL_VALORISATION.md`) aux côtés de [VSCodium](https://github.com/VSCodium/vscodium) (`MIT`, 0 télémétrie) et `.editorconfig`. |

---

## 2. Installation locale (`0 $ PMU`) & Activation des Actions Supela

### Installation (dans un environnement isolé dédié — recommandé : `pipx`)
```bash
pipx install git-cola
# ou sous Linux (Debian/Ubuntu) : sudo apt install git-cola
# ou sous Windows (winget)     : winget install git-cola.git-cola
```

### Enregistrement des commandes Supela dans `git-cola` (local au dépôt uniquement)
Sous Windows (PowerShell) :
```powershell
.\scripts\setup_git_cola_supela.ps1
```

Ou manuellement sur tout OS (Windows / Linux / macOS) :
```bash
git config --local guitool."Supela: Verify Rule A12".cmd "python scripts/verify_a12.py"
git config --local guitool."Supela: Verify VR-01..20".cmd "python scripts/vr_compliance_check.py"
git config --local guitool."Supela: Build Proven Laws Web".cmd "python scripts/build_proven_laws_web.py"
git config --local guitool."Supela: OPA Rego Tests (31/31)".cmd "opa test policies/ tests/rego/ -v"
git config --local guitool."Supela: Pytest Laws & Math".cmd "pytest tests/test_supela_laws.py tests/test_supela_math_core.py -v"
```

### Lancement
```bash
git cola        # Interface principale (staging granulaire, commit signé, actions guitool Supela)
git cola dag    # Visualiseur DAG complet de l'historique immuable
```

> **Rappel `VR-03` & `C10` :** `git-cola` facilite l'audit visuel et la préparation de commits signés sur une branche dédiée ; le commit direct sur `main` reste interdit et toute promotion demeure soumise aux workflows CI + ratification humaine souveraine.

---

## 3. Poste de Travail Souverain sans Télémétrie (Apports `VSCodium` / `@daiyam` / `zokugun`)

Dans la continuité de la doctrine **0 $ PMU / zéro télémétrie** portée par [VSCodium](https://github.com/VSCodium/vscodium), son mainteneur principal [Baptiste Augrain (`@daiyam`)](https://github.com/daiyam) et l'organisation MIT [`zokugun`](https://github.com/zokugun) :

- **IDE souverain sans télémétrie (`VSCodium` / `zokugun/MrCode`) :** privilégier **VSCodium** (ou sa variante durcie [`zokugun/MrCode`](https://github.com/zokugun/MrCode), licence `MIT`) couplé au registre ouvert **Open VSX** et au fichier `.editorconfig` partagé entre `omega-zero-4d` et `Supela-K3-Omega`.
- **Synchronisation souveraine hors cloud propriétaire (`zokugun/vscode-sync-settings`) :** exporter et versionner la configuration IDE, les profils et la liste d'extensions dans un dépôt Git privé ou un répertoire local chiffré — aucune dépendance à un compte cloud propriétaire (`0 $ PMU`).
- **Audit lisible des spécifications longues (`zokugun/vscode-explicit-folding`) :** utiliser le pliage explicite par régions nommées pour naviguer proprement les registres canoniques (`ENCYCLOPEDIE_DICTIONNAIRE`, `LOIS_PROUVEES_SUPELA`, politiques Rego v1, noyau Rust).
- **Discipline *Result-type* & transactions Git typées (`zokugun/node-fs-extra-plus`, `zokugun/node-git-toolkit`) :** adopter le principe des retours explicites (`ok / err` sans avaler les erreurs silencieusement), aligné directement sur la **Loi 3 (`0_vide != 0_vert`)** et le contrôle déterministe des opérations Git locales.
- **Changelogs & synchronisation multi-dépôts déterministes (`zokugun/extract-changelog`, `zokugun/repo-starter-kit`) :** maintenir une parité traçable (`K_t ⊆ K_{t+1}`) entre `omega-zero-4d` et `Supela-K3-Omega` (`.editorconfig`, `.gitattributes`, `SECURITY.md`, politiques SHA-256).
- **Builds reproductibles & séries de correctifs auditables :** chaque outil de la chaîne locale (`git-cola`, `VSCodium`/`MrCode`, `opa v1.22.4`, `cosign v3.1.4`, `cargo --locked`) reste vérifiable par empreinte SHA-256 et remplaçable sans perte du canon Supela.

> **Séparation de licence :** tous les projets `zokugun` et `VSCodium` référencés ici sont sous licence `MIT` et intégrés uniquement comme **outillage de poste de travail / références d'architecture** — aucun binaire ni code tiers n'est vendu ni copié dans le cœur `omega-zero-4d` (`Apache-2.0`).

