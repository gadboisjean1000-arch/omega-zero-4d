# Protocole benchmark comparatif officiel (N5)

## Objectif
Comparer de manière traçable la couche institutionnelle N5 à trois référentiels cibles:
- **ISO/IEC 42001**
- **NIST AI RMF**
- **EU AI Act**

## Périmètre
- Gouvernance institutionnelle, audit externe, reproductibilité, red team, publication contrôlée.
- Évaluation par exigences, preuves, et niveau de maturité.

## Métriques
1. **Coverage**: % exigences couvertes avec preuve.
2. **Proof Quality**: complétude hash/signature/horodatage.
3. **Decision Traceability**: % décisions avec registre complet.
4. **Remediation Latency**: délai moyen correction après audit.
5. **Public Transparency Score**: cohérence version publique vs interne (avec redaction contrôlée).

## Jeux de données d'évaluation
- Artefacts institutionnels versionnés (`institutional/*.md`, `institutional/*.json`, `institutional/*.ps1`).
- Registres d'audit externe et PV comité.
- Rapports red team trimestriels.

## Méthode de comparaison
1. Mapper les exigences de chaque référentiel vers une matrice commune.
2. Noter chaque exigence: `0=non couvert`, `1=couvert partiel`, `2=couvert vérifié`.
3. Exiger preuve documentaire + hash + provenance.
4. Publier score global et écarts par référentiel.

## Format de rapport public
- Résumé exécutif (1 page).
- Tableau comparatif ISO/NIST/EU (par exigence).
- Forces / Écarts / Plan de convergence.
- Annexe technique: hash-chain, signatures, date de génération.
