# Index Constitutionnel · Supela Ω-ZERO · Local–Cloud–4D

Ce répertoire rassemble les artefacts normatifs, schémas JSON Draft 2020-12, moteur Python, politiques OPA Rego v1, coffre-fort WORM, attestations cryptographiques, bus réseau MCP, gouvernance `VR-01..VR-20` et tests exécutés dans `omega-zero-4d`.

## 1. Constitution, Gouvernance & Spécifications (`GEMINI.md`, `docs/constitution/`)
- [GEMINI.md](../../GEMINI.md) — Constitution racine unifiant `Supela`, `Supela-K3-Omega`, `Ω-ZERO · 4D`, `Supela-Guard-Kernel`, `GRPO` et le bus réseau MCP.
- [LICENSE](../../LICENSE) — Licence open-source internationale SPDX `Apache-2.0` (clause brevet + attribution).
- [NOTICE](../../NOTICE) — Notice légale d'attribution souveraine (Jean-François Gadbois · ORCID `0009-0001-5361-6795` · Supela K Omega).
- [CITATION.cff](../../CITATION.cff) — Métadonnées de citation académique normalisées (CFF v1.2.0 / BibTeX / ORCID / Zenodo).
- [SECURITY.md](../../SECURITY.md) — Politique de sécurité, divulgation coordonnée (RFC 9116 / NIST SSDF) et frontière honnête des garanties CI vs silicium.
- [.gitattributes](../../.gitattributes) — Normalisation déterministe des fins de ligne (`LF` pour Rego/Python/Rust/Makefile, `CRLF` pour PowerShell).
- [FORMALISATION_MATHEMATIQUE_UNIFIEE.md](FORMALISATION_MATHEMATIQUE_UNIFIEE.md) — Monographie mathématique unifiée (`MAT-00..MAT-08`, treillis $G_0..G_4$, théorème d'agrégation `VR-Fractal-Ω`, `GENERIC n-D` $M \succeq 0$, simplexe exact `SGG_v2`, contraction `TZI`, `GRPO`).
- [MATRICE_CONFORMITE_INSTITUTIONNELLE.md](MATRICE_CONFORMITE_INSTITUTIONNELLE.md) — Matrice d'alignement et de vérification Défense / Gouvernement / International (ISO/NIST/SLSA/NIS2/DORA) / Université (ORCID), sous discipline `mesuré, non proclamé`.
- [PLAN_4D_OMEGA_ZERO_ESC_01.md](PLAN_4D_OMEGA_ZERO_ESC_01.md) — Spécification complète corrigée ($\Pi_0$, 7 statuts du Manque, 8 paliers `E0..E7`, 10 conditions `C01..C10`, `Load(C)`, revidage transactionnel).
- [DEFINITION_P0_PROJECTION.json](DEFINITION_P0_PROJECTION.json) — Définition formelle et assertions exécutables de $\Pi_0$.
- [STATUT_MANQUE.json](STATUT_MANQUE.json) — Les 7 statuts canoniques, règles M1–M5 et machine à états complète (`TR-01`..`TR-16` + transitions interdites).
- [TEST_P0_EXEMPLE.json](TEST_P0_EXEMPLE.json) — Exemple 1 corrigé (Psychologie × Droit du travail × Gestion).
- [TEST_P0_EXEMPLE_SEC_DOMAINE.json](TEST_P0_EXEMPLE_SEC_DOMAINE.json) — Exemple 2 inter-domaines (Hydrologie × Droit administratif × Secours × Éthique territoriale).
- [PLAN-4D-ΩZERO-ESC-01.json](PLAN-4D-%CE%A9ZERO-ESC-01.json) — Manifeste JSON exécutable du protocole d'escalade 4D.
- [supela-article-registry-1.json](supela-article-registry-1.json) — Registre candidat des 6 articles IA en 5 branches indépendantes (`Hook: AnalysisCandidate`, `verdict_final: OUVERT`).
- [SCHEMA_GRPO_SUPELA.md](SCHEMA_GRPO_SUPELA.md) — Pont méthodologique GRPO → Supela (`Score ≠ Preuve ≠ Vérité` et démonstration `L=0, ∇L≠0`).
- [COMPARAISON_GRPO_OMEGA_ZERO.md](COMPARAISON_GRPO_OMEGA_ZERO.md) — Formalisation mathématique corrigée de `GRPO ≠ Ω-ZERO` et des 5 garde-fous `GF1`–`GF5`.
- [SUPELA_GUARD_KERNEL.md](SUPELA_GUARD_KERNEL.md) — Spécification exécutable `Supela-Guard-Kernel` (`SUP-ICI-01`, `C0`/`C1`/`C2`, résidu $R_{\min}(O)$, `G0..G5`).
- [BANC_MULTI_MOTEURS_SUPELA.md](BANC_MULTI_MOTEURS_SUPELA.md) — Spécification du Banc multi-moteurs Supela (non-votant, 10 champs minimaux, symétrie `SUPELA_EN_DÉFAUT`).
- [MECANIQUE_IRREVERSIBLE_GENERIC_SUPELA.md](MECANIQUE_IRREVERSIBLE_GENERIC_SUPELA.md) — Application des mathématiques Supela (`MAT-00..MAT-08`) à la mécanique physique irréversible (GENERIC, $W_2$, Kružkov, GKSL) horodatée.
- [UNIFICATION_MULTI_BRANCHES.md](UNIFICATION_MULTI_BRANCHES.md) — Cartographie unifiée `gadboisjean1000-arch` (*Wheeppp*) et suivi honnête `M3` de `groupnatupro/multi-branches`.
- [VR_STRUCTURA_OFFICIAL_SEALED.md](VR_STRUCTURA_OFFICIAL_SEALED.md) — Référentiel officiel `VR Structura Supela (VR-01..VR-20)` et gouvernance CTO/CTA/TI.
- [PCEP_PROGRAMMATION_EVOLUTIVE_PREUVE.md](PCEP_PROGRAMMATION_EVOLUTIVE_PREUVE.md) — Formalisation réseau PCEP (9 familles de codage + points `A_PROUVER` + enveloppe `EN_ATTENTE_SIGNATURE`).
- [SUPELA_RUNTIME_V02_SYSTEME_NERVEUX.md](SUPELA_RUNTIME_V02_SYSTEME_NERVEUX.md) — Spécification du Système Nerveux Exécutable Supela (`SupelaLocalBridge` v0.1 `L0` + `SupelaRuntime` v0.2 `L1`–`L7`, 11 outils MCP `supela_*` et frontière normative `Jean-François Gadbois`).
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
- `schemas/supela_provenance_m365_1.schema.json`
- `schemas/supela_guard_kernel_1.schema.json`
- `schemas/supela_multi_engine_bench_1.schema.json`
- `schemas/supela_pcep_network_1.schema.json`
- `schemas/supela-state.schema.json`

## 3. Moteur Python, Guard-Kernel & Bus Réseau (`src/omega_zero/`)
- `src/omega_zero/__init__.py` — Exports publics du package `omega_zero`.
- `src/omega_zero/models.py` — Objets 4D (`Manque`, `Raccord`, `DisciplineAssessment`, `Conflict4D`, `LocalNode`, `Delta4D`, `Container`, `ZeroState`, `CloudOmega`).
- `src/omega_zero/projection.py` — Opérateur $\Pi_0$ et machine à états `ManqueStateMachine`.
- `src/omega_zero/protocol.py` — Moteur Local–Cloud–4D, `Merge*`, `Load(C)`, migration sans perte, revidage transactionnel `PREPARE→VERIFY→COMMIT→CLEAN`, réouverture de cône et émergence candidate.
- `src/omega_zero/grpo_bridge.py` — Pont GRPO ↔ Ω-ZERO (`GF1`–`GF5`, `explore_with_guardrails`) et analyse numérique `L=0, ∇L≠0`.
- `src/omega_zero/guard_kernel.py` — Noyau `SupelaGuardKernel` (`SUP-ICI-01`, `C0`/`C1`/`C2`, test de perte de sens à 8 questions, cycles `G0..G5` et registre des rejets).
- `src/omega_zero/multi_engine_bench.py` — Banc multi-moteurs non-votant (`SupelaMultiEngineBench`, 10 champs minimaux, détection `SUPELA_EN_DÉFAUT`).
- `src/omega_zero/pcep.py` — Moteur PCEP (9 familles de codage évolutif à preuve conservée, registre `A_PROUVER`, enveloppe `EN_ATTENTE_SIGNATURE`).
- `src/omega_zero/sovereign_net.py` — Noyau inhérent souverain (`ZERO-STATE-01`, `ZERO-AGENT-01`, `SUP-NORM-NET-01/1.0`, `SovereignSearchQuery` Ed25519, Anti-EaaS et topologies).
- `src/omega_zero/supela_math_core.py` — Noyau mathématique unifié (`MAT-00..MAT-08`, thermodynamique GENERIC $\dot{E}=0, \dot{S}\ge 0$ et séparation honnête `A_PROUVER`).
- `src/omega_zero/supela_runtime.py` — Système nerveux exécutable Supela v0.2 (`SupelaLocalBridge` v0.1 `L0` + `SupelaRuntime` v0.2 `L1`–`L7`, cycle contradiction-révision `generation + 1`, ratification `Jean-François Gadbois` et réouverture).
- `src/omega_zero/vr_compliance.py` — Auditeur déterministe `VR-01..VR-20` (`verify_vr_compliance`).
- `src/omega_zero/network_bus.py` — Bus réseau CLI `omega-network` (`doctor`, `pipeline`, `pcep-prepare`, `sovereign-verify`, `math-eval`, `runtime-cycle` + pont `Supela-K3-Omega`).
- `src/omega_zero/mcp_server.py` — Serveur MCP JSON-RPC 2.0 `stdin`/`stdout` exposant les 24 outils (`omega_*` + 11 `supela_*`) et 3 ressources constitutionnelles (`omega-zero-mcp`).
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
- `tests/test_guard_kernel.py` — Tests `Supela-Guard-Kernel` (`SUP-ICI-01`, `C0`/`C1`/`C2`, `G0..G5`, réclamation `G4→G1/G2`, `REJET_JUSTIFIE`, schéma Draft 2020-12).
- `tests/test_multi_engine_bench.py` — Tests du Banc multi-moteurs Supela (non-vote, divergence, `SUPELA_EN_DÉFAUT`, schéma Draft 2020-12 et MCP).
- `tests/test_pcep.py` — Tests PCEP (9 familles, auto-révocation, transport multi-référentiels, autorité calculée, schéma Draft 2020-12, MCP et CLI `pcep-prepare`).
- `tests/test_sovereign_net.py` — Tests `SupelaInherentCore` (`EMPTY_SHA`, `audit_trail` réel), `SovereignSearchQuery` (regex + Ed25519), topologies, MCP et CLI `sovereign-verify`.
- `tests/test_supela_math_core.py` — Tests du noyau mathématique unifié (`MAT-00..MAT-08`, GENERIC $\dot{E}=0, \dot{S}\ge 0$, validation humaine et CLI `math-eval`).
- `tests/test_supela_runtime_v02.py` — Tests du Système Nerveux Supela Runtime v0.2 (`L0`–`L7`, `schemas/supela-state.schema.json`, blocage hors dépôt et commandes non autorisées, falsification registre SHA-256, refus auto-ratification IA, contradiction/révision `G1→G2`, réouverture et 11 outils MCP `supela_*`).
- `tests/test_network_bus_and_mcp.py` — Tests bout-en-bout `GF1`–`GF5`, `VR-01..VR-20` (20/20), `omega-network doctor/pipeline` et sous-processus JSON-RPC 2.0 `mcp_server`.
- `tests/test_opa_rego.py` — Pont `pytest` vérifiant `opa fmt`, `opa check --strict`, les 31 tests Rego et l'évaluation directe du rapport `TEST-4D-ESC-01` avec traces Guard-Kernel & GRPO.
- `tests/test_worm_and_crypto.py` — Coffre-fort WORM, Ed25519, Cosign v3 `--bundle` et vérification A12.
- `tests/test_properties_hypothesis.py` — Invariance exhaustive des 24 permutations (`E3`) et tests par propriétés `Hypothesis`.
- `tests/init_omega_vault.Tests.ps1` — Tests Pester PowerShell d'idempotence WORM Windows.
- `reports/TEST-4D-ESC-01.report.json` — Rapport d'exécution vérifié contre `schemas/execution_report.schema.json`.
- `reports/PCEP-NETWORK-SIGN-READY.json` — Enveloppe réseau PCEP complète (9 familles + points `A_PROUVER`) prête à signer (`EN_ATTENTE_SIGNATURE`).
- `reports/SUPELA-RUNTIME-V02-CYCLE.json` — Rapport d'exécution complet du cycle `L0`–`L7` Supela Runtime v0.2 validé contre `schemas/supela-state.schema.json`.

## 5. Politiques OPA Rego v1 & CI (`policies/`, `tests/rego/`, `.github/workflows/`)
- `policies/omega_zero_invariants.rego` — Contrôle de cohérence `coherence_satisfied` (`sup_ici_01_satisfied`, `grpo_guardrails_satisfied`) et barrière `allow_human_review`.
- `tests/rego/omega_zero_invariants_test.rego` — Suite de réfutation OPA (22 tests : 3 cas positifs + 19 cas négatifs).
- `.github/workflows/omega-zero-ci.yml` — Pipeline GitHub Actions Python 3.11 + Draft 2020-12 + OPA Rego v1 + Cosign v3 + PowerShell Pester + `vr_compliance_check` + `omega-network`.
- `.github/workflows/pages-encyclopedie.yml` — Workflow GitHub Pages manuel (`workflow_dispatch`) séparant trace versionnée et publication après validation parité/JS.
- `.github/workflows/vr-governance-triage.yml` — Audit continu `VR-01..VR-20` et triage automatique des issues `VR-BUG..VR-GOVERNANCE`.

## 6. Règles, Environnement Cloud, Configuration MCP & Skills (`.agents/`)
- `.agents/environment.json` — Provisionnement cloud idempotent et non-interactif (`.venv`, `.[dev]`, `opa` v1.22.4 & `cosign` v3.1.4 vérifiés SHA-256).
- `.agents/mcp_config.json` — Configuration portable du serveur MCP `omega-zero-mcp` (`.venv/bin/python -m omega_zero.mcp_server`).
- `.agents/rules/code-quality.md` — Standards `ruff`, `mypy`, schémas Draft 2020-12, OPA Rego v1 et discipline épistémique (`VR-02`).
- `.agents/rules/git-workflow.md` — Workflow Git par Pull Request, protection `main`, labels `VR-BUG..VR-GOVERNANCE` et engagements d'escalade CTO/CTA/TI (`VR-03`).
- `.agents/rules/project-context.md` — Cartographie unifiée `omega-zero-4d` ↔ `Supela-K3-Omega` et portabilité multi-OS (`VR-04`).
- `.agents/skills/vr-structura-supela/SKILL.md` — Skill souverain de gouvernance `VR-01..VR-20` & `SUP-ICI-01`.
- `.agents/skills/web-fullstack/SKILL.md` — Skill architecture web full-stack typée & accessible.
- `.agents/skills/backend-api/SKILL.md` — Skill API, passerelles RPC/MCP et résilience transactionnelle.
- `.agents/skills/database-management/SKILL.md` — Skill migrations sans perte et journaux WORM append-only.
- `.agents/skills/devops-cicd/SKILL.md` — Skill pipelines GitHub Actions, SHA-256 et environnements cloud idempotents.
- `.agents/skills/ai-ml-engineering/SKILL.md` — Skill IA/RL (GRPO `GF1`–`GF5`, `Score ≠ Preuve ≠ Vérité`).
- `.agents/skills/automation-scripting/SKILL.md` — Skill scripts Python/PowerShell/Bash déterministes et conformes A12.
- `.agents/skills/security-audit/SKILL.md` — Skill audit fail-closed et séparation crypto/politique/silicium.
- `.agents/skills/blockchain-web3/SKILL.md` — Skill chaînes d'empreintes SHA-256 et distinction honnête chaîne cumulative vs Merkle.
- `.agents/skills/mobile-development/SKILL.md` — Skill synchronisation offline-first et préservation des statuts `Manque`.
- `.agents/skills/design-uiux/SKILL.md` — Skill interfaces fidèles aux statuts épistémiques (`CANDIDAT`, `OUVERT`, `REJET_JUSTIFIE`).

## 7. Runtime, Règle A12 & Export Windows (`runtime/`, `scripts/`)
- `runtime/init_omega_vault.ps1` — Initialisation idempotente et WORM logique du coffre-fort sous Windows.
- `scripts/__init__.py` — Déclaration de package Python pour un typage `mypy` univoque des scripts.
- `scripts/verify_a12.py` — Vérificateur anti-orphelins et cohérence croisée JSON/Rego/Markdown (Règle A12).
- `scripts/vr_compliance_check.py` — Point d'entrée CLI du vérificateur déterministe `VR-01..VR-20`.
- `scripts/verify_a12.ps1` — Enveloppe PowerShell pour la vérification A12.
- `scripts/install_into_excited_meitner.ps1` — Script PowerShell de déploiement et vérification SHA-256 vers `C:\Users\Group\Documents\antigravity\excited-meitner`.

## 8. Dictionnaire, Encyclopédie Universelle, Formules, Contradictions & Provenance M365
- [supela-dictionnaire-encyclopedie-1.json](supela-dictionnaire-encyclopedie-1.json) — Catalogue canonique JSON unifié (Dictionnaire 62 termes, 15 dépôts GitHub, 54 discussions/docs/notebooks Drive, 9 plateformes IA/navigateurs, 16 sources OneDrive/M365 via `PR-M365-01`, taxonomie `MATH/00_FONDEMENTS/`..`MATH/08_TESTS/`, architecture XIII domaines, 25 formules normalisées, lien contradictions et suivi `C:\`/`D:\`).
- [ENCYCLOPEDIE_DICTIONNAIRE.md](ENCYCLOPEDIE_DICTIONNAIRE.md) — Vue Markdown lisible générée depuis le catalogue JSON canonique.
- [ENCYCLOPEDIE_DICTIONNAIRE.html](ENCYCLOPEDIE_DICTIONNAIRE.html) — Explorateur HTML statique autonome (zéro CDN) exporté dans le dépôt avec contrôle de parité SHA-256 et syntaxe JS vérifiée.
- [REGISTRE_FORMULES_SUPELA.md](REGISTRE_FORMULES_SUPELA.md) — Registre normalisé des 25 formules retrouvées, taxonomie `MATH/00..08`, réduction M365 et architecture XIII sections (`Source ≠ Autorité`, `M3`).
- [REGISTRE_CONTRADICTIONS.json](REGISTRE_CONTRADICTIONS.json) — Registre canonique JSON des 7 contradictions et échecs conservés sans effacement (`CONTR-T11`, `CONTR-C001`, `CONTR-GRPO-001`, `CONTR-TRANSFO-UNDEF`, `CONTR-PR1-PS1-AUDIT`, `CONTR-ZERO-INT-MANQUANT`, `CONTR-Z0-TENSION`).
- [REGISTRE_CONTRADICTIONS.md](REGISTRE_CONTRADICTIONS.md) — Vue Markdown générée du registre des contradictions (`effacement_interdit = true`).
- [REGISTRE_PROVENANCE_M365.json](REGISTRE_PROVENANCE_M365.json) — Registre canonique de provenance M365 (`PR-M365-01`, 16 sources OneDrive/M365, 5 candidats suivis, anonymisation locale `LOCAL_UNIQUEMENT_PAR_DEFAUT`, sonde VM `HTTP/2 403`).
- [REGISTRE_PROVENANCE_M365.md](REGISTRE_PROVENANCE_M365.md) — Vue Markdown générée du registre de provenance M365, politique `collecté ≠ publiable` et réduction de manque M3.
- `schemas/supela_encyclopedie_1.schema.json` — Schéma JSON Draft 2020-12 avec verrou épistémique M3 interdisant toute clôture sans preuve locale (`NON_EXECUTEE` / `PARTIELLE`).
- `schemas/supela_contradictions_1.schema.json` — Schéma JSON Draft 2020-12 imposant `effacement_interdit: true` sur le registre des contradictions.
- `schemas/supela_provenance_m365_1.schema.json` — Schéma JSON Draft 2020-12 verrouillant `retrouver ≠ canoniser` (`SOURCE_IDENTIFIED ⇏ PROUVÉ`, `CODE_RECOVERED ⇏ CODE_EXECUTED`) et interdisant la fuite de chemins Windows privés.
- `scripts/build_encyclopedie.py` — Constructeur, normalisateur YAML/Formules, vérificateur HTML/JS, anonymiseur `--anonymize-local` et fusionneur Python (`--sources-dir`, `--local-inventory`).
- `scripts/collect_local_encyclopedie.ps1` — Collecteur PowerShell lecture-seule pour `C:\`, `D:\`, Edge/Copilot, Chrome/Gemini, Arc, Brave, Opera, Antigravity, Cursor et VS Code (`local_pc_inventory.json` produit au runtime et ignoré par Git/A12).
- `tests/test_encyclopedie_dictionnaire.py` — Suite `pytest` vérifiant schémas 2020-12, barrière M3, exhaustivité, parité HTML/JS, fiches YAML 29 clés, non-effacement des contradictions, provenance M365, anonymisation locale, exclusions de secrets et Règle A12.

### 8.1 Fiches Encyclopédiques YAML (`docs/constitution/fiches/`)
- [INDEX_FICHES.md](fiches/INDEX_FICHES.md) — Index des 25 fiches conformes au squelette universel à 29 clés.
- [MAT-00-ETAT-FOND.yaml](fiches/MAT-00-ETAT-FOND.yaml) — État fondamental Supela $S_i = \langle P_i, E_i, C_i, K_i \rangle$.
- [MAT-00-MONOTONIE-K.yaml](fiches/MAT-00-MONOTONIE-K.yaml) — Monotonie du registre $K_t \subseteq K_{t+1}$ et reset $C \to \emptyset$.
- [MAT-00-PI0.yaml](fiches/MAT-00-PI0.yaml) — Opérateur de projection zéro $\Pi_0$ et idempotence.
- [MAT-00-XERO-VIDE.yaml](fiches/MAT-00-XERO-VIDE.yaml) — Axiome ontologique dual Xero ($\mathbb{X} = Z_0$) et Vide ($\mathbb{V}$) (*Corpus Unifié v3.0*, `SUPPORTÉ`).
- [MAT-00-ZERO-INT.yaml](fiches/MAT-00-ZERO-INT.yaml) — Théorème du Zéro-Intégration (`SUPPORTÉ` / `RÉOUVERT` — `MANQUE ↓`, 7 primitives, 6 écritures Section 2.1 PDF + Partie IV v3.0, clause semi-formelle).
- [MAT-01-PRINCIPES-P1-P12.yaml](fiches/MAT-01-PRINCIPES-P1-P12.yaml) — Grille normative des Douze Principes Directeurs `P1..P12` et invariants `I1..I4` (*Corpus Unifié v3.0*, `SUPPORTÉ`).
- [MAT-01-TREILLIS.yaml](fiches/MAT-01-TREILLIS.yaml) — Treillis probatoire $G_0 \prec G_1 \prec G_2 \prec G_3 \prec G_4$.
- [MAT-01-AUTORITE-BORNEE.yaml](fiches/MAT-01-AUTORITE-BORNEE.yaml) — Loi d'autorité bornée par la preuve $\mathrm{Authority}(G) \le \mathrm{Proof}(G)$.
- [MAT-01-RECURSIVITE-G.yaml](fiches/MAT-01-RECURSIVITE-G.yaml) — Récursivité de la garantie $G(G) \le P$ et $G \Rightarrow P(G)$.
- [MAT-01-REFLPROB.yaml](fiches/MAT-01-REFLPROB.yaml) — Principe de réflexivité probatoire (`HYPOTHÉTIQUE`).
- [MAT-02-ETATS-4D.yaml](fiches/MAT-02-ETATS-4D.yaml) — Cycle temporel 4D `ACTIF → LATENT → RÉOUVERT → ACTIF` (`explorable ≠ actif`).
- [MAT-02-CONSERVATION-ECHEC.yaml](fiches/MAT-02-CONSERVATION-ECHEC.yaml) — Conservation des échecs adversariaux (`T11`).
- [MAT-02-MANQUE-M.yaml](fiches/MAT-02-MANQUE-M.yaml) — Objet Manque $M(S_t, G)$ et règles M1–M5.
- [MAT-03-PRZ-V3.yaml](fiches/MAT-03-PRZ-V3.yaml) — Protocole de Reset Zéro `PRZ v3.0.0`, Niveaux `N1..N3` et distance $D(S_n, Z_0)$ (*Corpus Unifié v3.0*, `SUPPORTÉ`).
- [MAT-03-RESET-STAR.yaml](fiches/MAT-03-RESET-STAR.yaml) — Famille `RESET*`, `R*`, `VR-22` (`vr22.py`, `SUPPORTÉ` / `RÉOUVERT`, exécution `RAPPORTÉ`).
- [MAT-03-REVIDAGE-LOAD.yaml](fiches/MAT-03-REVIDAGE-LOAD.yaml) — Saturation `Load(C)` et revidage transactionnel `E6` / `C09`.
- [MAT-04-HLP.yaml](fiches/MAT-04-HLP.yaml) — Distinction tridimensionnelle $H \neq L \neq P$ sans effacement.
- [MAT-05-MERGE-STAR.yaml](fiches/MAT-05-MERGE-STAR.yaml) — Opérateur `Merge*` et invariance aux 24 permutations (`E3`).
- [MAT-05-SCDH-TRICOUCHE.yaml](fiches/MAT-05-SCDH-TRICOUCHE.yaml) — Architecture `SCDH Tricouche` (`Fond`/`Surface`/`Cible`), 5 noyaux, 3 axiomes IPC et `Module Zéro` (*Corpus Unifié v3.0*, `SUPPORTÉ`).
- [MAT-05-CONFLIT-C001.yaml](fiches/MAT-05-CONFLIT-C001.yaml) — Conflit interdisciplinaire conservé `C-001`.
- [MAT-06-AMELIORATION-AUTO.yaml](fiches/MAT-06-AMELIORATION-AUTO.yaml) — Séparation `amélioration ≠ autorisation` (`C10`).
- [MAT-06-CHAINE-TRANSFO.yaml](fiches/MAT-06-CHAINE-TRANSFO.yaml) — Chaîne de transformation H (`formulation_brute: undefined`, `INCONNU` / `RÉOUVERT`, `PROMOTION_FORBIDDEN`).
- [MAT-07-REWARD-NOT-TRUTH.yaml](fiches/MAT-07-REWARD-NOT-TRUTH.yaml) — Découplage $\mathrm{Reward}(x) \nRightarrow \text{Vérité}(x)$ et contre-exemple GRPO ($L=0, \nabla L \neq 0$).
- [MAT-08-PATTERNS-LAS.yaml](fiches/MAT-08-PATTERNS-LAS.yaml) — Patterns `PA-01..10`/`PC-01..05`/`MP-01..03`, `AP-01..15`, métriques `MOG-E` (`SGG_v2`) et grammaire `LAS` (*Corpus Unifié v3.0*, `SUPPORTÉ`).
- [MAT-08-TESTS-PARITE.yaml](fiches/MAT-08-TESTS-PARITE.yaml) — Chaîne de vérification A12, `GDS`, `SCT` et parité HTML/JS.

## 9. Noyau Rust `supela-guard-kernel` (`rust/supela-guard-kernel/`)
- `rust/supela-guard-kernel/Cargo.toml` — Manifeste Cargo zéro dépendance externe (`#![forbid(unsafe_code)]`, Rust ≥ 1.89).
- `rust/supela-guard-kernel/Cargo.lock` — Verrouillage Cargo (`version = 4`, aucune dépendance tierce).
- `rust/supela-guard-kernel/README.md` — Documentation des garanties réelles (`SUP-ICI-01`, `SUP-IPC-01`, `SUPELA-WORM-V1`) et limites explicites.
- `rust/supela-guard-kernel/src/lib.rs` — Exports publics de la bibliothèque Rust `supela_guard_kernel`.
- `rust/supela-guard-kernel/src/main.rs` — Binaire CLI `supela-guard-kernel` (`serve`, `verify`, `status` sur `SUP-IPC-01`).
- `rust/supela-guard-kernel/src/clock.rs` — Abstraction d'horloge UTC (`Clock`, `SystemClock`, `FixedClock`) et parseur/formateur RFC 3339 strict.
- `rust/supela-guard-kernel/src/sha256.rs` — Hachage FIPS 180-4 SHA-256 et séparation de domaine `SUPELA-WORM-V1`.
- `rust/supela-guard-kernel/src/base64.rs` — Codec RFC 4648 Base64 strict (rejet des bits de remplissage non nuls).
- `rust/supela-guard-kernel/src/json.rs` — Parseur JSON à profondeur bornée et sérialisation canonique déterministe.
- `rust/supela-guard-kernel/src/kernel.rs` — Machine de transition `SUP-ICI-01` (`C0`/`C1`/`C2`, `G0..G5`) et barrière `Score ≠ Preuve ≠ Vérité`.
- `rust/supela-guard-kernel/src/journal.rs` — Journal `DurableJournal` coopératif verrouillé OS (`File::lock()`, `sync_all()`, reprise après coupure et idempotence `request_id`).
- `rust/supela-guard-kernel/src/ipc.rs` — Lecteur de trames à mémoire bornée $O(1)$ (`read_bounded_line`) et service `GuardService` (`SUP-IPC-01`).
- `rust/supela-guard-kernel/tests/acceptance_tests.rs` — Suite d'acceptation exécutable IPC, barrières `SUP-ICI-01`, Base64/horloge, altération WORM et binaire CLI.
- `rust/supela-guard-kernel/tests/concurrency_recovery_tests.rs` — Tests de concurrence multi-thread/multi-processus (`File::lock()`), idempotence/conflit et reprise après coupure.

## 10. Framework Autonome des 6 Thèses Supela (`ORCID 0009-0001-5361-6795`)
- `src/omega_zero/theses/__init__.py` — Exports du package autonome des 6 thèses Supela.
- `src/omega_zero/theses/common.py` — Socle commun (statuts `CONTROLE`/`INDETERMINE`/`ABSENT`, clause de souveraineté, générateur PDF 1.4 déterministe, BibTeX, ORCID Work v3.0, graphe de citations).
- `src/omega_zero/theses/thesis_invariant_axe01.py` — Thèse 1 (`INV-AXE-01`) : cadre à 5 questions.
- `src/omega_zero/theses/thesis_luc_promise.py` — Thèse 2 (`INV-LUC-PROPOSE`) : axiome de lucidité sans zone grise.
- `src/omega_zero/theses/thesis_fase_one.py` — Thèse 3 (`INV-FASE-01`) : non-indépendance `TOI/NOUS` avec trace écrite rang 10.
- `src/omega_zero/theses/thesis_verification_distrib.py` — Thèse 4 (`INV-04/INV-05`) : consensus ne peut pas élever le niveau de preuve.
- `src/omega_zero/theses/thesis_architecture_3niveaux.py` — Thèse 5 (`N1->N2->N3`) : hiérarchie Faits → Décisions → Omissions.
- `src/omega_zero/theses/thesis_dependance_souveraine.py` — Thèse 6 (`R-00`) : dépendance souveraine (7 invalidateurs, 25 transitions).
- `scripts/deposit_theses.py` — Orchestrateur complet de déposition horodatée UTC, export PDF/JSON/BibTeX/ORCID v3.0 et signature Ed25519.
- `tests/test_theses_framework.py` — Suite pytest des 6 thèses et du manifeste de déposition signé.
- `reports/theses_orcid_0009/THESIS-INV-001-ORCID0009.pdf` — PDF autonome Thèse 1 (`INV-AXE-01`).
- `reports/theses_orcid_0009/THESIS-INV-001-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 1.
- `reports/theses_orcid_0009/THESIS-LUC-002-ORCID0009.pdf` — PDF autonome Thèse 2 (`INV-LUC-PROPOSE`).
- `reports/theses_orcid_0009/THESIS-LUC-002-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 2.
- `reports/theses_orcid_0009/THESIS-FASE-003-ORCID0009.pdf` — PDF autonome Thèse 3 (`INV-FASE-01`).
- `reports/theses_orcid_0009/THESIS-FASE-003-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 3.
- `reports/theses_orcid_0009/THESIS-VERIF-004-ORCID0009.pdf` — PDF autonome Thèse 4 (`INV-04/INV-05`).
- `reports/theses_orcid_0009/THESIS-VERIF-004-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 4.
- `reports/theses_orcid_0009/THESIS-ARCHI-005-ORCID0009.pdf` — PDF autonome Thèse 5 (`N1->N2->N3`).
- `reports/theses_orcid_0009/THESIS-ARCHI-005-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 5.
- `reports/theses_orcid_0009/THESIS-DEP-006-ORCID0009.pdf` — PDF autonome Thèse 6 (`R-00`).
- `reports/theses_orcid_0009/THESIS-DEP-006-ORCID0009_metadata.json` — Métadonnées JSON horodatées Thèse 6.
- `reports/theses_orcid_0009/citation_network.json` — Graphe de références croisées entre les 6 thèses.
- `reports/theses_orcid_0009/theses_orcid_0009.bib` — Export BibTeX prêt pour import ORCID.
- `reports/theses_orcid_0009/orcid_works_v3.json` — Bundle JSON conforme au schéma ORCID Work v3.0.
- `reports/theses_orcid_0009/deposit_manifest.json` — Manifeste complet horodaté UTC et signé Ed25519.
