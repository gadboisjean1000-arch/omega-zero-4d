---
name: vr-structura-supela
description: Gouvernance souveraine VR Structura Supela (VR-01..VR-20), continuité SUP-ICI-01, barrière Ω-ZERO, pont GRPO GF1-GF5 et bus réseau MCP. Utiliser avant toute revue d'architecture, validation d'invariants ou audit A12/OPA/WORM.
---
# Gouvernance Souveraine · `vr-structura-supela` (`VR-01..VR-20`)

Tu opères sous la discipline **Supela Ω-ZERO · Guard-Kernel · GDS = ⟨D, O, A, γ⟩**.

## Règles Fondamentales
1. **Honnêteté épistémique** : aucune propriété n'est vraie sans épreuve reproductible (`Score ≠ Preuve ≠ Vérité`, `RejetDuContenu ≠ EffacementDeLExistenceHistorique`).
2. **Projection fail-closed** : vérifier $\Pi_0(S_t) = \{I, P, M, A, H\} \neq \emptyset$ et aucun saut `OUVERT → RÉSOLU`.
3. **Continuité intercycle (`SUP-ICI-01`)** : utiliser `SupelaGuardKernel` pour garantir $K_n \subseteq \operatorname{Accessible}(G_{n+1})$ ; `C2` ne peut jamais prétendre à une copie complète (`reversible = false`).
4. **Bus réseau & MCP** :
   - Diagnostiquer l'intercommunication : `.venv/bin/omega-network doctor --online`
   - Exécuter le pipeline bout-en-bout (`GRPO → Π₀ → Guard-Kernel → 4D → OPA → WORM → Ed25519`) : `.venv/bin/omega-network pipeline`
   - Passerelle MCP stdio : `.venv/bin/python -m omega_zero.mcp_server` (`.agents/mcp_config.json`)
5. **Contrôles obligatoires avant tout commit / PR** :
   - `.venv/bin/python scripts/verify_a12.py` (`orphans: []`, `broken_links: []`, `drift: []`)
   - `.venv/bin/python scripts/vr_compliance_check.py` (`20/20`, `all_passed: true`)
   - `make all && make clean`
