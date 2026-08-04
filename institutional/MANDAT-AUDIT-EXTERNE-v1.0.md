# Mandat d'audit externe — v1.0

## Objectif
Évaluer l'aptitude institutionnelle à passer de **PROVISIONAL** à **VERIFIED_TIER2** avec preuve externe indépendante et vérifiable.

## Scope complet (8 domaines)
1. **Gouvernance**: rôles, responsabilité, quorum, journalisation.
2. **Sécurité documentaire**: intégrité, anti-altération, contrôle de versions.
3. **Identité et signatures**: gestion des clés, signature, vérification.
4. **Traçabilité**: hash-chain, horodatage, registre de décisions.
5. **Reproductibilité**: exécution "1 commande", stabilité des résultats.
6. **Conformité externe**: alignement cadres ISO/NIST/EU AI Act.
7. **Red team institutionnelle**: sécurité, gouvernance, biais.
8. **Publication contrôlée**: confidentialité, redaction, diffusion publique.

## Format du rapport signé
- Rapport principal: Markdown + PDF exporté.
- Signature cryptographique: GPG/eIDAS/X.509 jointe.
- Fichiers de preuve: hash SHA-256, empreinte clé publique, date UTC, identifiant auditeur.

## SLA et continuité
- Délai initial: **18 jours calendaires**.
- Délai de reprise incident: **48h max**.
- Escalade: sponsor + comité externe sous 24h.

## Plan B (auditeur de réserve)
- Si indisponibilité auditeur principal >48h, transfert ordonné au réserve.
- Pré-condition: mandat miroir accepté et clés de signature pré-enregistrées.
- Objectif: zéro rupture de traçabilité.

## Confidentialité et redaction contrôlée
- NDA bilatéral obligatoire avant accès aux artefacts internes.
- Classification: Public / Restreint / Confidentiel.
- Toute publication publique passe par un cycle de redaction contrôlée:
  - justification du retrait,
  - version caviardée traçable,
  - conservation de l'original signé.
