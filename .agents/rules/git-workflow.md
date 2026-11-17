# Workflow Git & Gouvernance VR (`VR-03`, `VR-19`, `VR-20`)

## 1. Flux de Développement & Protection de `main`
- **Commit direct sur `main` interdit** : toute modification passe par une branche (`feat/...`, `fix/...`, `docs/...`) et une Pull Request soumise aux workflows CI ([`.github/workflows/omega-zero-ci.yml`](../../.github/workflows/omega-zero-ci.yml)).
- Avant chaque commit :
  1. `.venv/bin/ruff check src/ tests/ scripts/`
  2. `.venv/bin/mypy src/ scripts/verify_a12.py scripts/vr_compliance_check.py`
  3. `.venv/bin/python scripts/verify_a12.py` (`orphans == []`, `broken_links == []`, `drift == []`)
  4. `.venv/bin/python scripts/vr_compliance_check.py` (`all_passed == true`)
  5. `make all && make clean`

## 2. Labels Obligatoires & Triage Issues (`VR-19` / `VR-20`)
Tout ticket / issue gouverné par `VR Structura Supela` reçoit au moins l'un des 5 labels canoniques :
- `VR-BUG` — Anomalie de code, régression, échec de test ou violation d'invariant détectée.
- `VR-FEATURE` — Évolution fonctionnelle du moteur 4D, GRPO, Guard-Kernel ou bus MCP.
- `VR-DOCS` — Mise à jour documentaire, constitutionnelle ou schémas indexés.
- `VR-STRUCTURE` — Architecture dépôt, A12, environnement cloud, CI/CD ou pont inter-dépôts.
- `VR-GOVERNANCE` — Règles CTO/CTA/TI, seuils d'escalade humaine, conformité VR-01..VR-20.

## 3. Engagements Organisationnels d'Escalade (CTO / CTA / TI)
> **Note d'honnêteté :** les délais ci-dessous constituent des **engagements de gouvernance humaine** appliqués lors de la revue CTO/CTA/TI (non vérifiables automatiquement par un commit CI) ; le workflow [`.github/workflows/vr-governance-triage.yml`](../../.github/workflows/vr-governance-triage.yml) automatise uniquement le triage des labels et l'audit statique VR.

| Sévérité | Délai cible de prise en charge | Responsable d'escalade |
|---|---|---|
| **Critique** (faille sécurité / rupture WORM / autorité non bornée) | **2 h** | CTO + CTA + TI |
| **Élevée** (échec CI bloquant / dérive A12 / OPA) | **8 h** | CTA / Mainteneur |
| **Normale** (`VR-FEATURE`, `VR-STRUCTURE`) | **48 h** | Équipe d'ingénierie |
| **Faible** (`VR-DOCS`, améliorations mineures) | **7 jours** | Contributeur / Revue PR |
