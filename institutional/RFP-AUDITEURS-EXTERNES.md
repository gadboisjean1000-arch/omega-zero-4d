# RFP — Auditeurs externes indépendants (N5)

## Objet
Sélectionner un auditeur externe indépendant pour accompagner la montée du statut **PROVISIONAL** vers **VERIFIED_TIER2** sur la couche institutionnelle N5.

## Portée attendue
- Vérification de la chaîne de preuve externe et de la traçabilité décisionnelle.
- Contrôle de la reproductibilité documentaire et des artefacts publics.
- Validation de la conformité de gouvernance (comité externe, red team, registre).

## Critères de sélection (obligatoires)
1. **Indépendance**: absence de conflit d'intérêt, déclaration écrite, séparation contractuelle.
2. **Expérience démontrée**: audits ML, SSO, gouvernance des systèmes critiques.
3. **Signature cryptographique**: capacité opérationnelle à signer les livrables (GPG/eIDAS/X.509) et fournir les preuves de vérification.
4. **Qualité documentaire**: livrables structurés, versionnés, auditable trail.

## Références de candidats déjà identifiés
- **Nord Paradigm**: expertise GPG/eIDAS et procédures de signature forte.
- **Certisyn Inc.**: expérience VRO Anchor Event et vérification d'événements d'ancrage.

## Calendrier (18 jours)
- **J1–J3**: cadrage + données d'entrée + protocole de preuve.
- **J4–J10**: exécution audit + collecte des écarts + première revue.
- **J11–J14**: remédiations + contre-vérifications.
- **J15–J17**: consolidation du rapport final et signature.
- **J18**: remise officielle + séance de clôture.

## Format livrable attendu
- Rapport principal en Markdown/PDF signé.
- Annexes techniques (hashes, signatures, logs de vérification).
- Verdict explicite: `PROVISIONAL`, `SIGNED`, ou `VERIFIED`.
- Bloc "Non-conformités / Correctifs / Risques résiduels".
