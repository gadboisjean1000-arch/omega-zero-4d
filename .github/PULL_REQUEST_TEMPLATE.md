## Description

<!-- Décrivez clairement les changements apportés et pourquoi -->

## Type de changement

- [ ] `feat` — Nouvelle fonctionnalité ou module
- [ ] `fix` — Correction de bug
- [ ] `docs` — Documentation uniquement
- [ ] `chore` — Maintenance, dépendances, outillage
- [ ] `ci` — Pipeline CI/CD
- [ ] `perf` — Optimisation de performance
- [ ] `refactor` — Refactorisation (pas de feature/fix)

## Checklist SUPELA

- [ ] Tous les workflows CI **passent** (supela-ci, test-raim, validate-formalization)
- [ ] `governance/test_governance_rules.py` — **17/17 PASS**
- [ ] Marqueur `19/19 PASS` préservé dans `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`
- [ ] Marqueur `Point Fixe Atteint` préservé dans `NORMALISATION-COMPLETE.md`
- [ ] Contrainte **IS ≤ 3** respectée dans tous les nouveaux modules
- [ ] Documentation mise à jour si le comportement change
- [ ] Aucune archive supprimée (`corpus-supela`, `norme-canu`, `document-maitre`, `supela-corpus-v1.0.0`)
- [ ] Aucun secret ou credential commis

## Références

<!-- Lien vers issue, RFC, ou document : closes #XX -->
