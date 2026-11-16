# Supela Ω-ZERO · Local–Cloud–4D

Implémentation exécutable, schémas JSON Draft 2020-12, politiques OPA Rego v1 et suite de réfutation pour :
- l'opérateur de projection $\Pi_0(S_t) = \{I, P, M, A, H\}$ ;
- la machine à états des 7 statuts du Manque et règles M1–M5 ;
- le protocole d'escalade 4D `PLAN-4D-ΩZERO-ESC-01` (`E0..E7`, `C01..C10`, `Load(C)`, revidage transactionnel) ;
- le second exemple inter-domaines (Hydrologie × Droit administratif × Secours × Éthique territoriale) ;
- le pont méthodologique Supela-GRPO (`Exploration ≠ Autorité`, `Score ≠ Preuve ≠ Vérité`).

## Exécution rapide

```bash
python -m pip install -e ".[dev]"
python docs/constitution/HARNAIS_TEST_ESCALADE_4D.py
pytest -v
opa fmt --diff policies/ tests/rego/
opa check --strict policies/ tests/rego/
opa test policies/ tests/rego/ -v --explain=fails
```
