# Index Constitutionnel · Supela Ω-ZERO · Local–Cloud–4D

Ce répertoire rassemble les artefacts normatifs, schémas JSON Draft 2020-12, moteur Python, politiques OPA Rego v1, coffre-fort WORM, attestations cryptographiques et tests exécutés dans `omega-zero-4d`.

## 1. Constitution & Spécifications (`docs/constitution/`)
- [PLAN_4D_OMEGA_ZERO_ESC_01.md](PLAN_4D_OMEGA_ZERO_ESC_01.md) — Spécification complète corrigée ($\Pi_0$, 7 statuts du Manque, 8 paliers `E0..E7`, 10 conditions `C01..C10`, `Load(C)`, revidage transactionnel).
- [DEFINITION_P0_PROJECTION.json](DEFINITION_P0_PROJECTION.json) — Définition formelle et assertions exécutables de $\Pi_0$.
- [STATUT_MANQUE.json](STATUT_MANQUE.json) — Les 7 statuts canoniques, règles M1–M5 et machine à états complète (`TR-01`..`TR-16` + transitions interdites).
- [TEST_P0_EXEMPLE.json](TEST_P0_EXEMPLE.json) — Exemple 1 corrigé (Psychologie × Droit du travail × Gestion).
- [TEST_P0_EXEMPLE_SEC_DOMAINE.json](TEST_P0_EXEMPLE_SEC_DOMAINE.json) — Exemple 2 inter-domaines (Hydrologie × Droit administratif × Secours × Éthique territoriale).
- [PLAN-4D-ΩZERO-ESC-01.json](PLAN-4D-%CE%A9ZERO-ESC-01.json) — Manifeste JSON exécutable du protocole d'escalade 4D.
- [supela-article-registry-1.json](supela-article-registry-1.json) — Registre candidat des 6 articles IA en 5 branches indépendantes (`Hook: AnalysisCandidate`, `verdict_final: OUVERT`).
- [SCHEMA_GRPO_SUPELA.md](SCHEMA_GRPO_SUPELA.md) — Pont méthodologique GRPO → Supela (`Score ≠ Preuve ≠ Vérité` et démonstration `L=0, ∇L≠0`).
- [HARNAIS_TEST_ESCALADE_4D.py](HARNAIS_TEST_ESCALADE_4D.py) — Point d'entrée CLI du harnais exécutable.

## 2. Schémas JSON Draft 2020-12 (`schemas/`)
- `schemas/projection_pi0.schema.json`
- `schemas/manque_statut.schema.json`
- `schemas/exemple_cycle_p0.schema.json`
- `schemas/plan_4d_omega_zero_esc_01.schema.json`
- `schemas/execution_report.schema.json`
- `schemas/supela_article_registry_1.schema.json`
- `schemas/supela_encyclopedie_1.schema.json`
- `schemas/supela_contradictions_1.schema.json`

## 3. Moteur Python & Verrous (`src/omega_zero/`)
- `src/omega_zero/__init__.py` — Exports publics du package `omega_zero`.
- `src/omega_zero/models.py` — Objets 4D (`Manque`, `Raccord`, `DisciplineAssessment`, `Conflict4D`, `LocalNode`, `Delta4D`, `Container`, `ZeroState`, `CloudOmega`).
- `src/omega_zero/projection.py` — Opérateur $\Pi_0$ et machine à états `ManqueStateMachine`.
- `src/omega_zero/protocol.py` — Moteur Local–Cloud–4D, `Merge*`, `Load(C)`, migration sans perte, revidage transactionnel `PREPARE→VERIFY→COMMIT→CLEAN`, réouverture de cône et émergence candidate.
- `src/omega_zero/grpo_bridge.py` — Pont GRPO → Supela (`Score ≠ Preuve ≠ Vérité`) et analyse numérique `L=0, ∇L≠0`.
- `src/omega_zero/worm_ledger.py` — Coffre-fort WORM logique (manifeste lecture seule + ledger append-only chaîné SHA-256).
- `src/omega_zero/attestation.py` — Signatures et vérifications cryptographiques Ed25519 non-répudiables.
- `src/omega_zero/scenarios.py` — Scénario `TEST-4D-ESC-01` et second exemple inter-domaines hydrologie/droit/secours/éthique.
- `src/omega_zero/harness.py` — Exécuteur complet produisant le rapport JSON validé (`reports/TEST-4D-ESC-01.report.json`).

## 4. Suite de tests (`tests/`) & Rapports (`reports/`)
- `tests/test_schemas.py` — Validation Draft 2020-12 positive et négative.
- `tests/test_supela_article_registry.py` — Chaîne `JSON → Schema 2020-12 → Validation → A12 → pytest → Trace` pour le registre 6 articles (`Hook: AnalysisCandidate`, `verdict_final: OUVERT`).
- `tests/test_pi0_and_manque.py` — Idempotence $\Pi_0$, bornage d'autorité, transitions autorisées/interdites des 7 statuts.
- `tests/test_escalation_4d.py` — Exécution positive de `TEST-4D-ESC-01` + 10 tests négatifs (échecs critiques `C01`..`C10`).
- `tests/test_second_domain_example.py` — Exécution end-to-end du second exemple inter-domaines et de l'architecture Supela-GRPO.
- `tests/test_opa_rego.py` — Pont `pytest` vérifiant `opa fmt`, `opa check --strict`, les 16 tests Rego et l'évaluation directe du rapport `TEST-4D-ESC-01`.
- `tests/test_worm_and_crypto.py` — Coffre-fort WORM, Ed25519, Cosign v3 `--bundle` et vérification A12.
- `tests/test_properties_hypothesis.py` — Invariance exhaustive des 24 permutations (`E3`) et tests par propriétés `Hypothesis`.
- `tests/init_omega_vault.Tests.ps1` — Tests Pester PowerShell d'idempotence WORM Windows.
- `reports/TEST-4D-ESC-01.report.json` — Rapport d'exécution vérifié contre `schemas/execution_report.schema.json`.

## 5. Politiques OPA Rego v1 & CI (`policies/`, `tests/rego/`, `.github/workflows/`)
- `policies/omega_zero_invariants.rego` — Contrôle de cohérence `coherence_satisfied` et barrière `allow_human_review`.
- `tests/rego/omega_zero_invariants_test.rego` — Suite de réfutation OPA (2 cas positifs + 14 cas négatifs).
- `.github/workflows/omega-zero-ci.yml` — Pipeline GitHub Actions Python 3.11 + Draft 2020-12 + OPA Rego v1 + Cosign v3 + PowerShell Pester.
- `.github/workflows/pages-encyclopedie.yml` — Workflow GitHub Pages manuel (`workflow_dispatch`) séparant trace versionnée et publication après validation parité/JS.

## 6. Runtime, Règle A12 & Export Windows (`runtime/`, `scripts/`)
- `runtime/init_omega_vault.ps1` — Initialisation idempotente et WORM logique du coffre-fort sous Windows.
- `scripts/verify_a12.py` — Vérificateur anti-orphelins et cohérence croisée JSON/Rego/Markdown (Règle A12).
- `scripts/verify_a12.ps1` — Enveloppe PowerShell pour la vérification A12.
- `scripts/install_into_excited_meitner.ps1` — Script PowerShell de déploiement et vérification SHA-256 vers `C:\Users\Group\Documents\antigravity\excited-meitner`.

## 7. Dictionnaire, Encyclopédie Universelle, Formules & Contradictions
- [supela-dictionnaire-encyclopedie-1.json](supela-dictionnaire-encyclopedie-1.json) — Catalogue canonique JSON unifié (Dictionnaire 52 termes, 15 dépôts GitHub, 54 discussions/docs/notebooks Drive, 9 plateformes IA/navigateurs, taxonomie `MATH/00_FONDEMENTS/`..`MATH/08_TESTS/`, architecture XIII domaines, 20 formules normalisées, lien contradictions et suivi `C:\`/`D:\`).
- [ENCYCLOPEDIE_DICTIONNAIRE.md](ENCYCLOPEDIE_DICTIONNAIRE.md) — Vue Markdown lisible générée depuis le catalogue JSON canonique.
- [ENCYCLOPEDIE_DICTIONNAIRE.html](ENCYCLOPEDIE_DICTIONNAIRE.html) — Explorateur HTML statique autonome (zéro CDN) exporté dans le dépôt avec contrôle de parité SHA-256 et syntaxe JS vérifiée.
- [REGISTRE_FORMULES_SUPELA.md](REGISTRE_FORMULES_SUPELA.md) — Registre normalisé des 20 formules retrouvées, taxonomie `MATH/00..08` et architecture XIII sections (`Source ≠ Autorité`, `M3`).
- [REGISTRE_CONTRADICTIONS.json](REGISTRE_CONTRADICTIONS.json) — Registre canonique JSON des contradictions et échecs conservés sans effacement (`CONTR-T11`, `CONTR-C001`, `CONTR-GRPO-001`, `CONTR-TRANSFO-UNDEF`, `CONTR-PR1-PS1-AUDIT`, `CONTR-ZERO-INT-MANQUANT`).
- [REGISTRE_CONTRADICTIONS.md](REGISTRE_CONTRADICTIONS.md) — Vue Markdown générée du registre des contradictions (`effacement_interdit = true`).
- `schemas/supela_encyclopedie_1.schema.json` — Schéma JSON Draft 2020-12 avec verrou épistémique M3 interdisant toute clôture sans preuve locale (`NON_EXECUTEE` / `PARTIELLE`).
- `schemas/supela_contradictions_1.schema.json` — Schéma JSON Draft 2020-12 imposant `effacement_interdit: true` sur le registre des contradictions.
- `scripts/build_encyclopedie.py` — Constructeur, normalisateur YAML/Formules, vérificateur HTML/JS et fusionneur Python (`--sources-dir`, `--local-inventory`).
- `scripts/collect_local_encyclopedie.ps1` — Collecteur PowerShell lecture-seule pour `C:\`, `D:\`, Edge/Copilot, Chrome/Gemini, Arc, Brave, Opera, Antigravity, Cursor et VS Code (`local_pc_inventory.json` produit au runtime et ignoré par Git/A12).
- `tests/test_encyclopedie_dictionnaire.py` — Suite `pytest` vérifiant schémas 2020-12, barrière M3, exhaustivité, parité HTML/JS, fiches YAML 29 clés, non-effacement des contradictions, exclusions de secrets et Règle A12.

### 7.1 Fiches Encyclopédiques YAML Initiales (`docs/constitution/fiches/`)
- [INDEX_FICHES.md](fiches/INDEX_FICHES.md) — Index des 20 fiches initiales conformes au squelette universel à 29 clés.
- [MAT-00-ETAT-FOND.yaml](fiches/MAT-00-ETAT-FOND.yaml) — État fondamental Supela $S_i = \langle P_i, E_i, C_i, K_i \rangle$.
- [MAT-00-MONOTONIE-K.yaml](fiches/MAT-00-MONOTONIE-K.yaml) — Monotonie du registre $K_t \subseteq K_{t+1}$ et reset $C \to \emptyset$.
- [MAT-00-PI0.yaml](fiches/MAT-00-PI0.yaml) — Opérateur de projection zéro $\Pi_0$ et idempotence.
- [MAT-00-ZERO-INT.yaml](fiches/MAT-00-ZERO-INT.yaml) — Théorème du Zéro-Intégration (`INCONNU` / `LATENT` sous M3).
- [MAT-01-TREILLIS.yaml](fiches/MAT-01-TREILLIS.yaml) — Treillis probatoire $G_0 \prec G_1 \prec G_2 \prec G_3 \prec G_4$.
- [MAT-01-AUTORITE-BORNEE.yaml](fiches/MAT-01-AUTORITE-BORNEE.yaml) — Loi d'autorité bornée par la preuve $\mathrm{Authority}(G) \le \mathrm{Proof}(G)$.
- [MAT-01-RECURSIVITE-G.yaml](fiches/MAT-01-RECURSIVITE-G.yaml) — Récursivité de la garantie $G(G) \le P$ et $G \Rightarrow P(G)$.
- [MAT-01-REFLPROB.yaml](fiches/MAT-01-REFLPROB.yaml) — Principe de réflexivité probatoire (`HYPOTHÉTIQUE`).
- [MAT-02-ETATS-4D.yaml](fiches/MAT-02-ETATS-4D.yaml) — Cycle temporel 4D `ACTIF → LATENT → RÉOUVERT → ACTIF` (`explorable ≠ actif`).
- [MAT-02-CONSERVATION-ECHEC.yaml](fiches/MAT-02-CONSERVATION-ECHEC.yaml) — Conservation des échecs adversariaux (`T11`).
- [MAT-02-MANQUE-M.yaml](fiches/MAT-02-MANQUE-M.yaml) — Objet Manque $M(S_t, G)$ et règles M1–M5.
- [MAT-03-RESET-STAR.yaml](fiches/MAT-03-RESET-STAR.yaml) — Famille `RESET*`, `R*`, `VR-22` (`INCONNU` / `LATENT` sous M3).
- [MAT-03-REVIDAGE-LOAD.yaml](fiches/MAT-03-REVIDAGE-LOAD.yaml) — Saturation `Load(C)` et revidage transactionnel `E6` / `C09`.
- [MAT-04-HLP.yaml](fiches/MAT-04-HLP.yaml) — Distinction tridimensionnelle $H \neq L \neq P$ sans effacement.
- [MAT-05-MERGE-STAR.yaml](fiches/MAT-05-MERGE-STAR.yaml) — Opérateur `Merge*` et invariance aux 24 permutations (`E3`).
- [MAT-05-CONFLIT-C001.yaml](fiches/MAT-05-CONFLIT-C001.yaml) — Conflit interdisciplinaire conservé `C-001`.
- [MAT-06-AMELIORATION-AUTO.yaml](fiches/MAT-06-AMELIORATION-AUTO.yaml) — Séparation `amélioration ≠ autorisation` (`C10`).
- [MAT-06-CHAINE-TRANSFO.yaml](fiches/MAT-06-CHAINE-TRANSFO.yaml) — Chaîne de transformation H (`formulation_brute: undefined`, `INCONNU` / `RÉOUVERT`).
- [MAT-07-REWARD-NOT-TRUTH.yaml](fiches/MAT-07-REWARD-NOT-TRUTH.yaml) — Découplage $\mathrm{Reward}(x) \nRightarrow \text{Vérité}(x)$ et contre-exemple GRPO ($L=0, \nabla L \neq 0$).
- [MAT-08-TESTS-PARITE.yaml](fiches/MAT-08-TESTS-PARITE.yaml) — Chaîne de vérification A12, `GDS`, `SCT` et parité HTML/JS.
