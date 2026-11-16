# Règles Qualité de Code & Discipline Épistémique (`VR-02`)

1. **Formatage & Linting (`ruff`)** :
   - Longueur maximale de ligne : `110` caractères (`pyproject.toml`).
   - Exécuter `.venv/bin/ruff check src/ tests/ scripts/` avant tout commit : zéro erreur tolérée.
   - Interdiction des `except Exception:` aveugles (`BLE001`) : capturer uniquement des classes d'exceptions explicites (`ValueError`, `OSError`, `json.JSONDecodeError`, etc.).
   - Tout script muni d'un shebang `#!/usr/bin/env python3` dans `scripts/` doit être exécutable (`chmod +x`).

2. **Typage Strict (`mypy`)** :
   - `disallow_untyped_defs = true` et `warn_return_any = true` sur `src/` et `scripts/`.
   - Exécuter `.venv/bin/mypy src/ scripts/verify_a12.py scripts/vr_compliance_check.py`.

3. **Politiques & Schémas** :
   - Tout schéma dans `schemas/` doit être valide selon `Draft202012Validator.check_schema`.
   - Tout fichier `.rego` dans `policies/` et `tests/rego/` doit passer `opa fmt --diff`, `opa check --strict` et `opa test -v`.

4. **Invariants Métiers Non Négociables** :
   - **Ω-ZERO** : $\Pi_0(\Pi_0(S_t)) = \Pi_0(S_t)$, $\Pi_0(S_t) \neq \emptyset$, aucun saut direct `OUVERT → RÉSOLU`, `Autorité ≤ Preuve`.
   - **GRPO (`GF1`–`GF5`)** : aucun score heuristique ne confère `ETABLI` ou autorité ; le filtre `GF2` ($A_i \ge \tau$) s'applique uniquement côté admission afin de préserver $\sum \hat{A}_i = 0$.
   - **Guard-Kernel (`SUP-ICI-01`)** : aucune promotion `HYPOTHESE → FAIT` sans preuve nouvelle, aucune perte de provenance/contradiction, `C2` jamais déclaré comme copie complète (`reversible: false`).
