# GEMINI.md · Constitution Opérationnelle `omega-zero-4d` & Réseau Supela

> **Principe Graal :** *On sait qu'on ne sait pas.* Aucune affirmation sans épreuve reproductible ; l'exploration ne vaut ni preuve ni autorité ; la compression réduit le poids sans jamais effacer le sens.

## 1. Identité & Cartographie des Instances

| Instance | Rôle architectural | Espace / Opérateur | Dépôt / Ancrage |
|---|---|---|---|
| **Supela** | Socle méthodologique & gouvernance éditoriale | `Score ≠ Preuve ≠ Vérité`, Règle A12, `VR-01..VR-20` | [`docs/constitution/INDEX_CONSTITUTION.md`](docs/constitution/INDEX_CONSTITUTION.md) |
| **Supela-K3-Omega** | Monolithe de cohérence organisationnelle | $\text{GDS} = \langle D, O, A, \gamma \rangle$, $\gamma^* = \gamma \circ \Lambda$, `policies/gds_invariants.rego` | `gadboisjean1000-arch/Supela-K3-Omega` (pont via [`network_bus.py`](src/omega_zero/network_bus.py)) |
| **Supela Ω-ZERO · 4D** | Moteur formel & barrière fail-closed | $\Pi_0(S_t) = \{I, P, M, A, H\} \neq \emptyset$, 7 statuts du Manque (`M1`–`M5`), `E0..E7`, `C01..C10`, `Load(C)`, revidage `PREPARE→VERIFY→COMMIT→CLEAN` | [`src/omega_zero/`](src/omega_zero/__init__.py), [`policies/omega_zero_invariants.rego`](policies/omega_zero_invariants.rego) |
| **Supela-Guard-Kernel** | Continuité intercycle & compression contrôlée | `SUP-ICI-01` ($K_n \subseteq \operatorname{Accessible}(G_{n+1})$), `C0`/`C1`/`C2`, résidu $R_{\min}(O)$, `G0..G5`, `SUP-IPC-01` / `SUPELA-WORM-V1` | [`src/omega_zero/guard_kernel.py`](src/omega_zero/guard_kernel.py), [`rust/supela-guard-kernel/`](rust/supela-guard-kernel/README.md), [`SUPELA_GUARD_KERNEL.md`](docs/constitution/SUPELA_GUARD_KERNEL.md) |
| **Pont GRPO ↔ Ω-ZERO** | Exploration générative sous garde-fous | `GRPO ≠ Ω-ZERO`, `GF1`–`GF5` (`Reward → Candidate → Épreuves → Status`) | [`src/omega_zero/grpo_bridge.py`](src/omega_zero/grpo_bridge.py), [`COMPARAISON_GRPO_OMEGA_ZERO.md`](docs/constitution/COMPARAISON_GRPO_OMEGA_ZERO.md) |

## 2. Bus Réseau Inter-Outils & Serveur MCP

Les outils du dépôt intercommuniquent de manière exécutable (aucun chemin local spécifique Windows codé en dur) :
- **Serveur MCP JSON-RPC 2.0 (`stdin`/`stdout`)** : `.venv/bin/python -m omega_zero.mcp_server` (ou `.venv/bin/omega-zero-mcp`), configuré dans [`.agents/mcp_config.json`](.agents/mcp_config.json).
- **Outils MCP exposés** : `omega_pi0_project`, `omega_manque_transition`, `omega_grpo_explore`, `guard_kernel_compress`, `omega_run_harness`, `omega_verify_a12`, `omega_verify_vr_compliance`, `omega_network_pipeline`, `omega_network_doctor`.
- **Orchestrateur réseau CLI** :
  - `.venv/bin/omega-network doctor --online` : vérifie les binaires (`python`, `pytest`, `ruff`, `mypy`, `opa`, `cosign`, `cargo`, `git`, `gh`, `gdrive`), A12, `VR-01..VR-20`, l'aller-retour réel `mcp_server`, le dialogue réel `SUP-IPC-01` avec `supela-guard-kernel` et l'état du pont `Supela-K3-Omega`.
  - `.venv/bin/omega-network pipeline` : chaîne un cycle complet `GRPO (GF1–GF5) → Engine/Π₀ → Guard-Kernel (G0→G1→G2 C1) → Harnais 4D → OPA eval → WORM SHA-256 → Ed25519`.

## 3. Règles Obligatoires & Commandes de Vérification

1. **Règle A12 (zéro orphelin, zéro lien cassé, zéro dérive)** : tout fichier ajouté ou modifié dans `omega-zero-4d` doit être référencé dans [`INDEX_CONSTITUTION.md`](docs/constitution/INDEX_CONSTITUTION.md) et vérifié par `.venv/bin/python scripts/verify_a12.py`.
2. **Qualité & Typage** : `ruff check src/ tests/ scripts/` et `mypy src/ scripts/verify_a12.py scripts/build_encyclopedie.py scripts/vr_compliance_check.py`.
3. **Noyau Rust (`rust/supela-guard-kernel`)** : `cargo fmt --check`, `cargo clippy --all-targets --all-features -- -D warnings` et `cargo test --locked --all-targets`.
4. **Suite complète** : `make all && make clean` + `.venv/bin/python scripts/vr_compliance_check.py`.
5. **Gouvernance `VR-01..VR-20`** : toute évolution passe par une branche dédiée + Pull Request et respecte [`.agents/rules/git-workflow.md`](.agents/rules/git-workflow.md) ainsi que [`VR_STRUCTURA_OFFICIAL_SEALED.md`](docs/constitution/VR_STRUCTURA_OFFICIAL_SEALED.md).
6. **Honnêteté matérielle** : ne jamais prétendre à un WORM matériel ou TPM si `tpm2_quote` est absent (`make attest` échoue explicitement dans ce cas).
