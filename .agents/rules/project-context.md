# Contexte Projet Unifié (`VR-04`)

## 1. Périmètre & Artefacts Clés
- **Dépôt actif** : `gadboisjean1000-arch/omega-zero-4d` (Python ≥ 3.11, JSON Schema Draft 2020-12, OPA Rego v1, Ed25519, Cosign v3 `--bundle`, WORM logique).
- **Pont inter-dépôts** : `gadboisjean1000-arch/Supela-K3-Omega` (`GDS = ⟨D, O, A, γ⟩`, `policies/gds_invariants.rego`), interrogé à la demande par `omega-network doctor --online`.
- **Registre épistémique verrouillé (`VR-15`)** : [`docs/constitution/supela-article-registry-1.json`](../../docs/constitution/supela-article-registry-1.json) reste en statut `Hook: AnalysisCandidate`, `verdict_final: OUVERT`, `reproduction_exp: NON_EXECUTEE`, `validation_dep: NON_ACQUISE`, `ENTREE_NORMATIVE: NON`.

## 2. Portabilité Multi-Environnements
- Aucun chemin Windows local fixe (tel que `C:\Users\Group\...`) ne doit apparaître dans la configuration active `.agents/mcp_config.json`, `.agents/environment.json` ou le code `src/omega_zero/`.
- Les scripts PowerShell hérités (`omega.ps1`, `runtime/init_omega_vault.ps1`, `scripts/verify_a12.ps1`, `scripts/install_into_excited_meitner.ps1`) restent maintenus exclusivement pour la parité Windows / CI `windows-latest`.
- Sur Linux / VM Cloud, [`.agents/environment.json`](../environment.json) Provisionne `.venv`, `.[dev]`, `opa` v1.22.4 et `cosign` v3.1.4 de façon idempotente.
