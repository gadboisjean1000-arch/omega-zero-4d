# Politique de Sécurité & Divulgation Coordonnée (`SECURITY.md`)

> **Alignement d'ingénierie :** RFC 9116 (CVD), NIST SP 800-218 (SSDF), ISO/IEC 27001 / 42001.  
> **Discipline Supela (`Score ≠ Preuve ≠ Vérité`) :** Ce document distingue strictement les contrôles **vérifiés mécaniquement en CI** des mécanismes **hors périmètre ou déclaratifs**.

---

## 1. Versions & Périmètre Soutenus

| Composant | Version / Branche | Statut de support |
|---|---|---|
| `omega-zero-4d` (Python ≥ 3.11 + OPA Rego v1) | `main` (`v1.1.x`) | ✅ Maintenu (CI continue) |
| `rust/supela-guard-kernel` (`#![forbid(unsafe_code)]`) | `v0.1.0` (0 dépendance tierce) | ✅ Maintenu (CI Linux + Windows) |
| `Supela-K3-Omega` (Monolithe GDS & Rego v1) | `main` | ✅ Maintenu (dépôt compagnon) |

---

## 2. Signalement d'une Vulnérabilité (Coordinated Vulnerability Disclosure)

Pour signaler une faille de sécurité, une rupture d'invariant WORM, un contournement de politique OPA/Rego ou un défaut cryptographique :

1. **Ne pas ouvrir d'issue publique** contenant un exploit actif ou des secrets.
2. Utiliser **GitHub Private Vulnerability Reporting** (*Security → Advisories → Report a vulnerability*) sur `gadboisjean1000-arch/omega-zero-4d` (ou `gadboisjean1000-arch/Supela-K3-Omega`).
3. Joindre idéalement :
   - la version ou le commit SHA exact ;
   - un cas de réfutation minimal reproductible (test `pytest`, cas `opa test` ou trame `SUP-IPC-01`) ;
   - l'invariant constitutionnel impacté (`SUP-ICI-01`, `C01..C10`, `VR-01..VR-20`, `Authority(G) ≤ Proof(G)`).

### Engagements organisationnels de prise en charge (alignés `.agents/rules/git-workflow.md`)

> *Note d'honnêteté : ces délais constituent des engagements de gouvernance humaine (non vérifiables automatiquement par un commit CI).*

| Sévérité | Exemples | Délai cible de réponse | Escalade |
|---|---|---|---|
| **Critique** | Rupture WORM, contournement `allow_human_review`, élévation d'autorité non bornée, fuite de clé privée | **2 h** | CTO + CTA + TI |
| **Élevée** | Échec d'un contrôle OPA/Rust/A12, contournement de validation de schéma Draft 2020-12 | **8 h** | CTA / Mainteneur |
| **Modérée / Faible** | Durcissement CI, faux négatif non critique, documentation sécurité | **48 h – 7 j** | Mainteneur / Revue PR |

---

## 3. Modèle de Menaces & Frontière Honnête des Garanties

### 3.1 Contrôles vérifiés mécaniquement dans le pipeline CI
- **Mémoire & isolation Rust** : `rust/supela-guard-kernel` compile avec `#![forbid(unsafe_code)]`, **zéro crate externe** (`Cargo.lock` sans dépendance tierce), lecteur IPC à mémoire bornée $O(1)$, verrous OS (`File::lock()`) et `sync_all()` sur le journal `SUPELA-WORM-V1`.
- **Chaîne d'approvisionnement CI** : binaires `opa` (`v1.22.4`) et `cosign` (`v3.1.4`) vérifiés par empreinte **SHA-256** avant exécution.
- **Politiques fail-closed** : 31 tests de réfutation OPA Rego v1 (`opa fmt`, `opa check --strict`, `opa test`) interdisant commit direct sur `main`, auto-promotion GRPO, altération du ledger, rejeu temporel et autorité supérieure à la preuve.
- **Hygiène des secrets** : aucune clé privée Ed25519 ou `cosign.key` n'est versionnée ; les tests et le CI utilisent exclusivement des clés éphémères jetables.

### 3.2 Limites explicites & contrôles hors périmètre CI (non proclamés)
- **Ancrage silicium TPM / TEE** : `make attest` et `.\omega.ps1 -Task Attest` échouent volontairement si `tpm2_quote` est absent — aucun TPM/TEE n'est simulé.
- **Identité cryptographique de production** : le CI prouve le **mécanisme** `cosign v3 --bundle` avec clé jetable ; une identité de production requiert **Fulcio/OIDC keyless** ou un **HSM/KMS** dédié.
- **WORM matériel** : `WormVault` fournit un WORM **logique** (`0o444`/`IsReadOnly` + chaînage SHA-256), non un support physique WORM (ex. S3 Object Lock Compliance / bande optique).
- **Accréditation officielle** : ce dépôt applique une ingénierie alignée sur ISO/IEC 27001, ISO/IEC 42001 et NIST SSDF, mais **ne revendique aucune certification délivrée par un organisme accrédité** sans audit externe indépendant.

---

## 4. Architecture d'Audit Défensif Autorisé (Patterns Dual-Graph & Retest `T11`)

> **Cadre éthique & légal strict :** Supela est un écosystème **exclusivement défensif et d'audit autorisé**. Aucun exploit, aucune charge offensive ni aucun code sous licence copyleft incompatible (`AGPL-3.0` / `GPL-2.0`) n'est intégré dans ce dépôt `Apache-2.0`.

Les patrons architecturaux défensifs de référence (notamment la séparation *Dual-Graph* et boucle de contre-épreuve documentées dans des plateformes d'audit comme [ARTEX / BaaRai](https://github.com/BaaRai) ainsi que les taxonomies défensives structurées par classes de vulnérabilités et matrices identité/infrastructure type [Claude-BugHunter](https://github.com/elementalsouls/Claude-BugHunter)) sont traduits en invariants **purement défensifs** dans Supela :

1. **Séparation Dual-Graph (*Authorized Asset Graph* ≠ *Exploration Graph*)** : toute vérification ou sonde reste confinée au périmètre explicitement autorisé (`FourBoundaryGate` : `C ≠ P ≠ V ≠ A`), bloquant tout accès hors cible ou inter-tenant (`policies/gds_invariants.rego`, `policies/omega_zero_invariants.rego`).
2. **Boucle de contre-épreuve et non-régression (`Retest Loop` × `T11`)** : toute anomalie corrigée conserve sa trace historique `FAIL` (`REGISTRE_CONTRADICTIONS.json`) et exige un test négatif automatisé (ex. `test_generic_refutes_indefinite_m`, `test_law07_reversible_append_only_ledger`, `test_deny_*` OPA).
3. **Couverture défensive par classes de risques (identités & infrastructure)** :
   - *Élévation d'autorité / contournement d'approbation* → `Authority(G) ≤ Proof(G)`, `FourBoundaryGate`, `allow_human_review` ;
   - *Falsification & rejeu* → chaînage SHA-256 WORM, fenêtre 15 min anti-rejeu, triggers SQLite `BEFORE UPDATE`/`DELETE` ;
   - *Déni de service structurel & mémoire* → lecteur IPC Rust borné $O(1)$ (`#![forbid(unsafe_code)]`), garde `RecursionError`, bornes finies Classe B ;
   - *Chaîne d'approvisionnement CI* → binaires `opa` et `cosign` vérifiés SHA-256, `trivy-action@v0.28.0`, 0 crate tierce dans le noyau Rust.

