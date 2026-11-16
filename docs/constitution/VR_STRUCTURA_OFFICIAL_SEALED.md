# Document Officiel · Gouvernance `VR Structura Supela` (`VR-01..VR-20`)

> **Statut :** Référentiel exécutable et auditable dans `omega-zero-4d` via [`scripts/vr_compliance_check.py`](../../scripts/vr_compliance_check.py) (`vr-structura-compliance/1`).  
> **Discipline d'honnêteté :** ce document sépare strictement les **20 contrôles déterministes vérifiables sur disque** (exécutés par Python, Draft 2020-12, OPA Rego v1 et A12) des **engagements organisationnels humains CTO/CTA/TI** (non prouvables par un script local).

---

## 1. Matrice des 20 Exigences `VR-01..VR-20`

| ID | Exigence | Artefact(s) vérifié(s) automatiquement |
|---|---|---|
| **VR-01** | Constitution racine unifiée | [`GEMINI.md`](../../GEMINI.md) |
| **VR-02** | Règles qualité code & discipline épistémique | [`.agents/rules/code-quality.md`](../../.agents/rules/code-quality.md) |
| **VR-03** | Règles workflow Git & 5 labels canoniques (`VR-BUG`..`VR-GOVERNANCE`) | [`.agents/rules/git-workflow.md`](../../.agents/rules/git-workflow.md) |
| **VR-04** | Contexte projet multi-instances (`omega-zero-4d` ↔ `Supela-K3-Omega`) | [`.agents/rules/project-context.md`](../../.agents/rules/project-context.md) |
| **VR-05** | Opérateur $\Pi_0(S_t)$ et machine à états des 7 statuts du Manque (`M1`–`M5`) | [`projection.py`](../../src/omega_zero/projection.py), [`DEFINITION_P0_PROJECTION.json`](DEFINITION_P0_PROJECTION.json) |
| **VR-06** | Moteur Local–Cloud–4D et protocole d'escalade | [`protocol.py`](../../src/omega_zero/protocol.py), [`PLAN-4D-ΩZERO-ESC-01.json`](PLAN-4D-%CE%A9ZERO-ESC-01.json) |
| **VR-07** | Harnais exécutable 4D (`E0..E7`, `C01..C10`) | [`harness.py`](../../src/omega_zero/harness.py), [`HARNAIS_TEST_ESCALADE_4D.py`](HARNAIS_TEST_ESCALADE_4D.py) |
| **VR-08** | 9 schémas JSON Draft 2020-12 syntaxiquement valides | `schemas/*.schema.json` (incluant `supela_guard_kernel_1.schema.json`, `supela_encyclopedie_1.schema.json` et `supela_contradictions_1.schema.json`) |
| **VR-09** | Barrière OPA Rego v1 (`coherence_satisfied` & `sup_ici_01_satisfied`) | [`omega_zero_invariants.rego`](../../policies/omega_zero_invariants.rego) |
| **VR-10** | Coffre-fort WORM **logique** append-only SHA-256 | [`worm_ledger.py`](../../src/omega_zero/worm_ledger.py), [`init_omega_vault.ps1`](../../runtime/init_omega_vault.ps1) |
| **VR-11** | Attestation cryptographique Ed25519 (et pont Cosign `--bundle`) | [`attestation.py`](../../src/omega_zero/attestation.py) |
| **VR-12** | Environnement cloud reproductible et idempotent | [`.agents/environment.json`](../../.agents/environment.json) |
| **VR-13** | Pont GRPO ↔ Ω-ZERO corrigé (`GF1`–`GF5`) | [`grpo_bridge.py`](../../src/omega_zero/grpo_bridge.py), [`COMPARAISON_GRPO_OMEGA_ZERO.md`](COMPARAISON_GRPO_OMEGA_ZERO.md) |
| **VR-14** | `Supela-Guard-Kernel` (`SUP-ICI-01`, `C0`/`C1`/`C2`, `G0..G5`) | [`guard_kernel.py`](../../src/omega_zero/guard_kernel.py), [`SUPELA_GUARD_KERNEL.md`](SUPELA_GUARD_KERNEL.md) |
| **VR-15** | Registre candidat `supela-article-registry/1` verrouillé (`OUVERT`) | [`supela-article-registry-1.json`](supela-article-registry-1.json) |
| **VR-16** | Règle A12 anti-orphelins, liens intacts et zéro dérive | [`verify_a12.py`](../../scripts/verify_a12.py) |
| **VR-17** | Bus réseau inter-outils & passerelle MCP JSON-RPC 2.0 stdio | [`.agents/mcp_config.json`](../../.agents/mcp_config.json), [`network_bus.py`](../../src/omega_zero/network_bus.py), [`mcp_server.py`](../../src/omega_zero/mcp_server.py) |
| **VR-18** | Référentiel officiel VR Structura Supela indexé | [`VR_STRUCTURA_OFFICIAL_SEALED.md`](VR_STRUCTURA_OFFICIAL_SEALED.md) |
| **VR-19** | CI Python/OPA/Cosign/Pester & Triage gouvernance GitHub | [`.github/workflows/omega-zero-ci.yml`](../../.github/workflows/omega-zero-ci.yml), [`.github/workflows/vr-governance-triage.yml`](../../.github/workflows/vr-governance-triage.yml) |
| **VR-20** | Vérificateur continu exécutable `20/20` | [`vr_compliance.py`](../../src/omega_zero/vr_compliance.py), [`vr_compliance_check.py`](../../scripts/vr_compliance_check.py) |

---

## 2. Gouvernance CTO / CTA / TI (`VR-19` & `VR-20`)

- **Autorité normative** : aucune étape CI, heuristique GRPO ni compression `C2` ne peut auto-promouvoir une règle en vérité établie. Le seuil de promotion maximal automatisé reste `ADMISSIBLE_A_REVUE_HUMAINE`.
- **Séparation des couches** :
  - *Ce que la machine prouve* : intégrité SHA-256 du registre WORM logique, validité des schémas Draft 2020-12, passage `OPA`, signature `Ed25519` / `Cosign --bundle`, continuité `SUP-ICI-01`, absence d'orphelins `A12` et conformité `VR-01..VR-20` à `100 %`.
  - *Ce qui demeure organisationnel* : respect des délais humains (`2 h` critique, `8 h` élevée, `48 h` normale, `7 j` faible), revue des PR et ancrage matériel `TPM` (`make attest` échoue explicitement tant que `tpm2_quote` est absent).
