# Protocole institutionnel E/F — Transition N4→N5

## Objet

Ce protocole formalise l'extension de robustesse SUPELA vers un niveau N5 via deux blocs additionnels :

- **Bloc E : preuve externe indépendante**
- **Bloc F : validation psychométrique outillée**

## Bloc E — Preuve externe indépendante

### Entrées requises

- `evidence/external-audit/third-party-audit-artifact.txt`
- `evidence/external-audit/external-proof-manifest.json`

### Contrôles

1. **Présence des artefacts tiers**
2. **Intégrité cryptographique** : hash SHA-256 de l'artefact égal au hash attendu du manifeste
3. **Reproductibilité minimale** :
   - `run_reference`
   - `generated_at_utc` (ISO-8601)
   - `commit` (hash Git valide et résoluble)
   - `source` (origine de l'audit)

## Bloc F — Validation psychométrique outillée

### Entrées requises

- `evidence/psychometrics/psychometric-results.json`
- `evidence/psychometrics/psychometric-results.csv`
- `evidence/psychometrics/psychometric-thresholds.json`

### Seuils minimums (configurables)

- **Kappa** : κ ≥ 0.75
- **CFA** : CFI ≥ 0.95, TLI ≥ 0.95, RMSEA ≤ 0.06, SRMR ≤ 0.08
- **Rasch** : Infit/Outfit moyens dans [0.70, 1.30]

### Contrôles de traçabilité

- Paramètres de modélisation (Rasch/CFA/Kappa)
- Statistiques publiées (échantillons, indices, intervalles)
- Référence run/timestamp/commit/dataset/toolchain
- Export CSV concordant avec le JSON

## Exécution opérationnelle

1. Rafraîchir les preuves : `.\GENERATE-ADVANCED-PROOF.ps1`
2. Lancer le calculateur : `.\SUPER-CALCULATEUR-VERIFICATION.ps1`
3. Vérifier les scores de blocs E/F et le score global normalisé

## Résultat attendu

- Maintien des contrôles historiques A/B/C/D
- Ajout des contrôles E/F sans rupture
- Consolidation objective de la transition **N4→N5**
