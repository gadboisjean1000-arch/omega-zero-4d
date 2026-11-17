---
name: devops-cicd
description: Pipelines GitHub Actions, vérification SHA-256 d'outils, environnements cloud reproductibles et gouvernance CI/CD fail-closed.
---
# Skill `devops-cicd`

1. Toujours travailler sur branche dédiée + Pull Request (`direct_commit_to_main == false` vérifié par OPA Rego).
2. Vérifier l'empreinte SHA-256 de tout binaire téléchargé (`opa`, `cosign`, etc.) avant exécution.
3. Rendre `.agents/environment.json` non-interactif et idempotent (testé par double exécution consécutive `bash -e -c`).
4. Aligner `Makefile`, `.github/workflows/omega-zero-ci.yml` et `.github/workflows/vr-governance-triage.yml` avec `ruff`, `mypy`, `A12`, `vr_compliance_check`, `pytest` et `opa`.
