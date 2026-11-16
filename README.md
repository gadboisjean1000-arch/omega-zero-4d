# Supela Ω-ZERO · Local–Cloud–4D

Implémentation exécutable, schémas JSON Draft 2020-12, politiques OPA Rego v1 et suite de réfutation pour :
- l'opérateur de projection $\Pi_0(S_t) = \{I, P, M, A, H\}$ ;
- la machine à états des 7 statuts du Manque et règles M1–M5 ;
- le protocole d'escalade 4D `PLAN-4D-ΩZERO-ESC-01` (`E0..E7`, `C01..C10`, `Load(C)`, revidage transactionnel) ;
- le second exemple inter-domaines (Hydrologie × Droit administratif × Secours × Éthique territoriale) ;
- le pont méthodologique Supela-GRPO (`Exploration ≠ Autorité`, `Score ≠ Preuve ≠ Vérité`) ;
- les couches complémentaires de vérification :
  - `WormVault` ([src/omega_zero/worm_ledger.py](src/omega_zero/worm_ledger.py) et [runtime/init_omega_vault.ps1](runtime/init_omega_vault.ps1)) : WORM **logique** (manifeste lecture seule `0o444` / `IsReadOnly` + ledger append-only chaîné SHA-256 ; ne prétend pas à un WORM matériel ni TPM/TEE) ;
  - `AttestationSigner` Ed25519 ([src/omega_zero/attestation.py](src/omega_zero/attestation.py)) + signature par `cosign v3` (`--bundle`) ;
  - vérificateur Règle A12 anti-orphelins & cohérence croisée JSON/Rego/Markdown ([scripts/verify_a12.py](scripts/verify_a12.py)) ;
  - tests de propriétés `Hypothesis` et invariance exhaustive sur les `4! = 24` permutations (`E3`).

## Exécution rapide

```bash
python -m pip install -e ".[dev]"
make all
```

Ou étape par étape :

```bash
ruff check src/ tests/ scripts/
mypy src/ scripts/verify_a12.py
python scripts/verify_a12.py
python docs/constitution/HARNAIS_TEST_ESCALADE_4D.py
pytest -v
opa fmt --diff policies/ tests/rego/
opa check --strict policies/ tests/rego/
opa test policies/ tests/rego/ -v --explain=fails
```

Sous Windows :

```powershell
.\omega.ps1 -Task All
```

> **Transparence :** `make attest` (ou `.\omega.ps1 -Task Attest`) échoue explicitement si `tpm2_quote` est absent : aucun ancrage silicium TPM/TEE n'est simulé.

