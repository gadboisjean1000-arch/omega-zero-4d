# Charte Red Team institutionnelle

## Mission
Exécuter des évaluations adversariales sur trois axes:
1. **Sécurité** (intégrité, signatures, chaîne de confiance),
2. **Gouvernance** (processus, décisions, séparation des rôles),
3. **Biais** (risques méthodologiques et décisionnels).

## Cadence
- Exercice standard: **trimestriel**.
- Exercice exceptionnel: sous 15 jours en cas d'alerte majeure.

## Scope des tests
- Attaques sur preuve externe (falsification, substitution, rollback).
- Attaques procédurales (quorum non conforme, vote non traçable).
- Attaques sur crédibilité publique (redaction abusive, incohérences de rapports).

## Structure playbooks d'attaque
Chaque playbook suit le format:
- **ID scénario**,
- **Objectif de l'attaque**,
- **Préconditions**,
- **Étapes d'exécution**,
- **Signal de détection attendu**,
- **Critère de succès/échec**,
- **Contre-mesures**,
- **Évidence collectée**.

## Template rapport public (avec redaction)
1. Résumé exécutif.
2. Méthode et périmètre.
3. Constatations (classées critique/majeur/modéré).
4. Correctifs recommandés.
5. Risque résiduel.
6. Annexe redaction:
   - élément retiré,
   - justification,
   - référence interne non caviardée,
   - approbateur.
