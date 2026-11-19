# Matrice de Conformité & Prêt-à-Auditer Institutionnel · Écosystème Supela

> **Public cible :** Auditeurs Défense / Souveraineté nationale, Administrations publiques, Universités & Jurys HDR, Organismes normatifs internationaux (ISO / NIST / IEEE).  
> **Auteur souverain :** Jean-François Gadbois ([ORCID 0009-0001-5361-6795](https://orcid.org/0009-0001-5361-6795)) · Organisation *Supela K Omega*  
> **Clause constitutionnelle d'honnêteté (`Score ≠ Preuve ≠ Vérité`) :** Aucune certification tierce non délivrée n'est revendiquée. Cette matrice sépare rigoureusement :
> - **✅ PROUVÉ MÉCANIQUEMENT** : exécuté et réfutable automatiquement dans le dépôt / pipeline CI ;
> - **🔷 ALIGNÉ PAR INGÉNIERIE** : architecture, documentation et contrôles structurés selon le référentiel cité ;
> - **⏳ DÉCLARATIF / HORS PÉRIMÈTRE CI** : exige un matériel dédié (TPM/TEE, HSM) ou une accréditation externe indépendante.

---

## 1. Cartographie Unifiée de l'Écosystème Supela

| Composant | Dépôt / Chemin | Rôle institutionnel | Licence |
|---|---|---|---|
| **Moteur formel Ω-ZERO · 4D** | [`gadboisjean1000-arch/omega-zero-4d`](https://github.com/gadboisjean1000-arch/omega-zero-4d) | Projection $\Pi_0$, 7 statuts du Manque, protocole `TEST-4D-ESC-01`, OPA Rego v1 (31 tests), Ed25519/Cosign, Runtime `L0–L7`, Bus MCP (24 outils) | Apache-2.0 |
| **Noyau durci Rust** | `omega-zero-4d/rust/supela-guard-kernel` | `#![forbid(unsafe_code)]`, **0 dépendance tierce**, `SUP-ICI-01`, `SUP-IPC-01`, journal WORM durable `File::lock()` + `sync_all()` (26 tests) | Apache-2.0 |
| **Monolithe formel K3-Ω** | [`gadboisjean1000-arch/Supela-K3-Omega`](https://github.com/gadboisjean1000-arch/Supela-K3-Omega) | Formalisme `GDS = ⟨D, O, A, γ⟩`, `VR-Fractal-Ω`, OPA 13/13, Pester WORM, Notice HDR/ISO, Docker + Trivy + Cosign | Apache-2.0 |
| **Corpus Académique (6 Thèses)** | `omega-zero-4d/reports/theses_orcid_0009/` | 6 PDF autonomes déterministes + métadonnées JSON + BibTeX + ORCID Work v3.0 + manifeste signé Ed25519 | Apache-2.0 |
| **Mathématiques Unifiées** | `docs/constitution/FORMALISATION_MATHEMATIQUE_UNIFIEE.md` | Preuves algébriques et vérificateurs exécutables (`MAT-00..MAT-08`, `VR-Fractal-Ω`, `GENERIC n-D` PSD, `SGG_v2`, `GRPO`) | Apache-2.0 |

---

## 2. Alignement Défense, Gouvernement, International & Université

### 2.1 Ingénierie Défense & Chaîne d'Approvisionnement Souveraine (NIST SSDF / SLSA / Zero-Trust)

| Exigence / Standard | Implémentation Supela | Preuve exécutable | Statut |
|---|---|---|---|
| **NIST SP 800-218 (SSDF) — PO / PS / PW / RV** | Politique `SECURITY.md`, revue PR obligatoire (`VR-03`), `ruff`, `mypy --disallow-untyped-defs`, `cargo clippy -D warnings`, suite de réfutation | `.github/workflows/omega-zero-ci.yml` | ✅ Prouvé (CI) |
| **Mémoire sûre & surface d'attaque minimale** | Noyau Rust `#![forbid(unsafe_code)]`, `Cargo.lock` avec **0 crate externe**, lecture IPC bornée $O(1)$ | `cargo test --locked --all-targets` (26/26) | ✅ Prouvé (CI) |
| **Intégrité supply-chain CI (SLSA aligné)** | Binaires CI `opa` (`v1.22.4`) et `cosign` (`v3.1.4`) vérifiés par empreinte **SHA-256** avant exécution ; signatures `--bundle` | `omega-zero-ci.yml` & `Supela-K3-Omega` CI | ✅ Mécanisme prouvé |
| **Cloisonnement Zero-Trust & Quorum recalculé** | Règles Rego v1 anti-cross-tenant, révocations d'agents exclues, déduplication de votes, anti-rejeu temporel (15 min) | `policies/gds_invariants.rego` (13/13) & `omega_zero_invariants.rego` (31/31) | ✅ Prouvé (OPA) |
| **Journalisation immuable (WORM)** | `WormVault` Python + PowerShell (`0o444`/`IsReadOnly` + chaînage SHA-256) + `DurableJournal` Rust (`File::lock`, `sync_all`) | `test_worm_and_crypto.py` + `concurrency_recovery_tests.rs` | ✅ WORM logique prouvé |
| **Ancrage matériel silicium (TPM 2.0 / TEE)** | Commande `make attest` / `.\omega.ps1 -Task Attest` échoue honnêtement sans `tpm2_quote` | Aucune simulation TPM | ⏳ Déclaratif (matériel requis) |
| **Identité cryptographique production (KMS / Fulcio)** | Clés éphémères utilisées en CI pour démontrer le mécanisme uniquement | À raccorder Fulcio/OIDC ou HSM souverain | ⏳ Hors périmètre CI |

### 2.2 Gouvernements, Souveraineté & Réglementation Internationale

| Référentiel | Principes couverts dans Supela | Ancrage vérifiable | Statut |
|---|---|---|---|
| **ISO/IEC 27001:2022** *(Sécurité de l'information)* | Traçabilité append-only SHA-256, contrôle de changement par PR, non-répudiation Ed25519/Cosign, divulgation `SECURITY.md` | `NOTICE-HDR-ISO-Monolithe-Probant.md`, `SECURITY.md` | 🔷 Aligné (non certifié) |
| **ISO/IEC 42001:2023 & NIST AI RMF 1.0** *(Gouvernance IA)* | Barrière `Reward(x) ⇏ Vérité(x)`, `GF1–GF5`, supervision humaine obligatoire (`allow_human_review`, `C10`), registre de contradictions sans effacement | `grpo_bridge.py`, `omega_zero_invariants.rego`, `REGISTRE_CONTRADICTIONS.json` | 🔷 Aligné + ✅ Garde-fous prouvés |
| **UE NIS2 (2022/2555) & DORA (2022/2554)** | Résilience transactionnelle (`PREPARE→VERIFY→COMMIT→CLEAN`), reprise après coupure du journal Rust, escalade CTO/CTA/TI | `protocol.py`, `journal.rs`, `.agents/rules/git-workflow.md` | 🔷 Aligné par ingénierie |
| **UE AI Act & Québec Loi 25** | Transparence des limites (`M1–M5`), anonymisation locale par défaut (`LOCAL_UNIQUEMENT_PAR_DEFAUT`, `anonymize_local_inventory`), traçabilité humaine | `build_encyclopedie.py`, `supela_provenance_m365_1.schema.json` | 🔷 Aligné + ✅ Tests anonymisation |
| **Standards ouverts IETF / NIST / JSON** | JSON Schema Draft 2020-12 (13 schémas), FIPS 180-4 SHA-256, RFC 3339, RFC 4648 Base64 strict, RFC 9116 (`SECURITY.md`) | `test_schemas.py`, `sha256.rs`, `clock.rs`, `base64.rs` | ✅ Vecteurs vérifiés |

### 2.3 Universités, Recherche & Reproductibilité Scientifique

| Standard académique | Implémentation Supela | Artefact vérifiable | Statut |
|---|---|---|---|
| **Identité chercheur persistante (ORCID)** | Liée aux 6 thèses, `CITATION.cff`, `NOTICE` et manifeste signé Ed25519 | [ORCID 0009-0001-5361-6795](https://orcid.org/0009-0001-5361-6795) | ✅ Intégré |
| **Citation logicielle normalisée (CFF 1.2.0 / BibTeX)** | Fichiers `CITATION.cff` à la racine des 2 dépôts + export `theses_orcid_0009.bib` + `orcid_works_v3.json` | `CITATION.cff`, `reports/theses_orcid_0009/` | ✅ Prêt (Zenodo DOI via Release) |
| **Reproductibilité mathématique** | Vérificateurs exécutables (`MAT-00..MAT-08`, Cholesky pivoté $M \succeq 0$, `VR-Fractal-Ω`, `SGG_v2` rationnel, `GRPO` analytique + DF, 24 permutations `E3`) | `supela_math_core.py`, `test_supela_math_core.py`, `test_properties_hypothesis.py` | ✅ Prouvé localement & CI |
| **Intégrité documentaire anti-orphelins (`Règle A12`)** | Bijection vérifiée entre arborescence du dépôt, `INDEX_CONSTITUTION.md`, schémas JSON, OPA Rego et encyclopédie HTML/MD | `scripts/verify_a12.py`, `scripts/vr_compliance_check.py` (20/20) | ✅ Prouvé (0 orphelin) |

---

## 3. Protocole de Reproductibilité pour Auditeur Indépendant

Un auditeur (université, administration ou défense) peut reproduire intégralement les preuves locales sans confiance préalable :

```bash
# 1. Vérifications statiques, bijection A12 et conformité VR-01..VR-20
ruff check src/ tests/ scripts/
mypy src/ scripts/verify_a12.py scripts/build_encyclopedie.py scripts/vr_compliance_check.py
python scripts/verify_a12.py
python scripts/vr_compliance_check.py

# 2. Suite complète Python + Mathématiques unifiées + 6 Thèses + OPA Rego v1
pytest -v
opa fmt --diff policies/ tests/rego/
opa check --strict policies/ tests/rego/
opa test policies/ tests/rego/ -v --explain=fails

# 3. Noyau Rust durci (0 dépendance externe, #![forbid(unsafe_code)])
cd rust/supela-guard-kernel
cargo fmt -- --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --locked --all-targets
```

> **Condition de scellement institutionnel :** conformément à `NOTICE-HDR-ISO-Monolithe-Probant.md`, le qualificatif **« scellé en production »** demeure interdit tant que l'ancrage matériel (`tpm2_quote`), l'identité keyless/HSM (Fulcio/OIDC ou KMS) et un audit externe indépendant ne sont pas raccordés et publiés dans le registre.
