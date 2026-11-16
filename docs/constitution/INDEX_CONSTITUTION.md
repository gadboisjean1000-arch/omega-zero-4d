# Index Constitutionnel · Supela Ω-ZERO · Local–Cloud–4D

Ce répertoire rassemble les artefacts normatifs, schémas JSON Draft 2020-12, moteur Python, politiques OPA Rego v1, coffre-fort WORM, attestations cryptographiques et tests exécutés dans `omega-zero-4d`.

## 1. Constitution & Spécifications (`docs/constitution/`)
- [PLAN_4D_OMEGA_ZERO_ESC_01.md](PLAN_4D_OMEGA_ZERO_ESC_01.md) — Spécification complète corrigée ($\Pi_0$, 7 statuts du Manque, 8 paliers `E0..E7`, 10 conditions `C01..C10`, `Load(C)`, revidage transactionnel).
- [DEFINITION_P0_PROJECTION.json](DEFINITION_P0_PROJECTION.json) — Définition formelle et assertions exécutables de $\Pi_0$.
- [STATUT_MANQUE.json](STATUT_MANQUE.json) — Les 7 statuts canoniques, règles M1–M5 et machine à états complète (`TR-01`..`TR-16` + transitions interdites).
- [TEST_P0_EXEMPLE.json](TEST_P0_EXEMPLE.json) — Exemple 1 corrigé (Psychologie × Droit du travail × Gestion).
- [TEST_P0_EXEMPLE_SEC_DOMAINE.json](TEST_P0_EXEMPLE_SEC_DOMAINE.json) — Exemple 2 inter-domaines (Hydrologie × Droit administratif × Secours × Éthique territoriale).
- [PLAN-4D-ΩZERO-ESC-01.json](PLAN-4D-%CE%A9ZERO-ESC-01.json) — Manifeste JSON exécutable du protocole d'escalade 4D.
- [SCHEMA_GRPO_SUPELA.md](SCHEMA_GRPO_SUPELA.md) — Pont méthodologique GRPO → Supela (`Score ≠ Preuve ≠ Vérité` et démonstration `L=0, ∇L≠0`).
- [HARNAIS_TEST_ESCALADE_4D.py](HARNAIS_TEST_ESCALADE_4D.py) — Point d'entrée CLI du harnais exécutable.

## 2. Schémas JSON Draft 2020-12 (`schemas/`)
- `schemas/projection_pi0.schema.json`
- `schemas/manque_statut.schema.json`
- `schemas/exemple_cycle_p0.schema.json`
- `schemas/plan_4d_omega_zero_esc_01.schema.json`
- `schemas/execution_report.schema.json`

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

## 6. Runtime, Règle A12 & Export Windows (`runtime/`, `scripts/`)
- `runtime/init_omega_vault.ps1` — Initialisation idempotente et WORM logique du coffre-fort sous Windows.
- `scripts/verify_a12.py` — Vérificateur anti-orphelins et cohérence croisée JSON/Rego/Markdown (Règle A12).
- `scripts/verify_a12.ps1` — Enveloppe PowerShell pour la vérification A12.
- `scripts/install_into_excited_meitner.ps1` — Script PowerShell de déploiement et vérification SHA-256 vers `C:\Users\Group\Documents\antigravity\excited-meitner`.
