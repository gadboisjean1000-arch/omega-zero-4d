# CADRE DIRECTEUR D'INGÉNIERIE ET DE VALORISATION LOGICIELLE

**Entité titulaire :** Personne morale sans but lucratif (*Loi sur les compagnies du Québec*, Partie III)  
**Paradigme directeur :** Architecture déterministe, souveraineté numérique et doctrine d'autosuffisance logicielle (0 $ de dépendance captive).  
**Ancrage écosystème :** [`omega-zero-4d`](https://github.com/gadboisjean1000-arch/omega-zero-4d) · [`Supela-K3-Omega`](https://github.com/gadboisjean1000-arch/Supela-K3-Omega) · [ORCID 0009-0001-5361-6795](https://orcid.org/0009-0001-5361-6795)

> **Note de conformité épistémique (`MATRICE_CONFORMITE_INSTITUTIONNELLE.md`) :** Ce cadre directeur formalise la gouvernance corporative, contractuelle et architecturale de l'OSBL. Les obligations fiscales (TPS/TVQ, Revenu Québec) et juridiques (Partie III, *Loi sur les compagnies du Québec*) relèvent du droit applicable et de la validation par un conseiller juridique/comptable agréé, distinctes des preuves automatisées en CI.

---

### I. GOUVERNANCE ÉCONOMIQUE ET CONFORMITÉ CORPORATIVE

1. **Capacité d'exercice commercial accessoire :**  
   Conformément aux prérogatives conférées aux personnes morales sans but lucratif constituées en vertu du droit québécois, l'entité dispose de la pleine capacité juridique pour déployer des activités d'ingénierie logicielle marchande. Les revenus d'honoraires, d'octroi de licences d'exploitation ou de prestations de services constituent des **activités commerciales accessoires légitimes**, pourvu que l'intégralité des flux excédentaires (surplus nets d'exploitation) soit obligatoirement consolidée et réaffectée à la poursuite exclusive des fins non lucratives statutaires de l'OSBL (principe de non-distribution des dividendes).

2. **Étanchement fiscal et traçabilité :**  
   * **Assujettissement TPS/TVQ :** Dépassement du seuil de « petit fournisseur » (30 000 $ CAD de fournitures taxables brutes sur quatre trimestres civils consécutifs) déclenchant la perception et la remise réglementaires auprès de Revenu Québec.
   * **Ségrégation des avoirs :** Imperméabilité absolue entre le patrimoine corporatif de l'OSBL, ses contrats-cadres de développement, ses actifs incorporels (code source, dépôts canoniques) et les mandataires ou administrateurs personnes physiques.

---

### II. SOUVERAINETÉ TECHNOLOGIQUE ET SOCLE ARCHITECTURAL (TCB Minimal)

L'architecture logicielle de l'organisation est érigée sous la discipline d'un **Trusted Computing Base (TCB) restreint**, éliminant tout assujettissement à des plateformes propriétaires opaques :

```text
               TOPOLOGIE DU SOCLE D'INGÉNIERIE SOUVERAIN
┌────────────────────────────────────────────────────────────────────────┐
│ COUCHE APPLICATIVE & PRÉSENTATION                                      │
│ React / Next.js (SSG/SSR) • TypeScript strict • Web API standard       │
├────────────────────────────────────────────────────────────────────────┤
│ MOTEUR DE TRAITEMENT & CONFINEMENT                                     │
│ Node.js (Runtime V8) / Python (FastAPI / Core) / Rust Guard-Kernel     │
│ Validation structurelle par schémas stricts (JSON Schema / Zod / OPA)  │
├────────────────────────────────────────────────────────────────────────┤
│ PERSISTANCE RELATIONNELLE ACID & JOURNAL WORM                          │
│ PostgreSQL / SQLite • Contraintes d'intégrité • SUPELA-WORM-V1         │
├────────────────────────────────────────────────────────────────────────┤
│ INFRASTRUCTURE HORS-CLOUD CAPTIF                                       │
│ Nœuds conteneurisés Linux • Déploiement reproductible • Git canonique  │
└────────────────────────────────────────────────────────────────────────┘
```

1. **Typage et invariance :** Proscription de la programmation non contrainte. Adoption d'interfaces déclaratives fortement typées (TypeScript en mode strict, Python typé `mypy`, Rust `#![forbid(unsafe_code)]`, schémas JSON Draft 2020-12 et relationnels normalisés).
2. **Déterminisme d'exécution :** Chaque transaction de persistance garantit les propriétés ACID (et journalisation durable `File::lock()` + `sync_all()` côté `supela-guard-kernel`). Zéro accumulation d'état fantôme (*ghost state*).
3. **Immutabilité du code et auditabilité :** Versionnement continu par graphes acycliques orientés (DAG Git), chaque révision étant authentifiée par signature cryptographique de commit / attestation Ed25519 / Cosign v3.

---

### III. TAXONOMIE DES ACTIFS LOGICIELS EXPLOITABLES

L'entité valorise quatre catégories d'artefacts logiciels standardisés :

1. **Interfaces institutionnelles et portails réactifs :**  
   Systèmes de diffusion de contenu à haute performance, optimisés pour la conformité WCAG (accessibilité), le balisage sémantique rigoureux et l'isolation des données côté client.
2. **Moteurs d'évaluation transactionnelle et devis algorithmiques :**  
   Composants de logique métier pure traduisant une matrice de paramètres complexes en une estimation déterministe (tarification dynamique, arborescence de décision, validation d'intrants).
3. **Systèmes de gestion opérationnelle (ERP/CRM légers) :**  
   Architectures centrées sur la donnée relationnelle, assurant la ségrégation des privilèges (RBAC), la gestion d'inventaire, le suivi de membres et la tenue de registres opérationnels.
4. **Pipelines d'orchestration et d'automatisation d'effets de bord :**  
   Flux asynchrones reliant les points d'entrée numériques à des micro-services internes (conversion dynamique de documents PDF normalisés, transmission cryptée de courriels transactionnels, synchronisation bidirectionnelle).

---

### IV. CONTRAT-CADRE DE PRESTATION LOGICIELLE (STRICTUM JUS)

Tout engagement liant l'OSBL à un tiers bénéficiaire est subordonné aux clauses d'ingénierie formelle suivantes :

1. **Délimitation formelle du périmètre d'exécution (*Scope of Work*) :**  
   L'énoncé des travaux détaille exhaustivement l'arbre des routes, les endpoints d'API, les modèles de données et les règles d'acceptation. Tout écart structurel requiert un avenant contractuel bilatéral (*Change Request*) tarifé à l'acte.
2. **Protocole de transfert de droits sous condition résolutoire :**  
   L'organisme conserve la propriété intellectuelle originaire de l'architecture et du code source jusqu'au paiement libératoire intégral de la créance. Le défaut de paiement maintient le code sous la seule autorité de l'OSBL.
3. **Période de garantie et recette technique :**  
   La recette formelle s'opère selon des critères d'acceptation objectifs (tests unitaires, d'intégration et de charge validés). La couverture des anomalies critiques est circonscrite à un horizon de garantie fixe de 30 jours civils post-déploiement, excluant toute maintenance évolutive tacite.

Ce modèle positionne l'organisme comme un laboratoire d'ingénierie logicielle de haut niveau, alliant rigueur mathématique, indépendance d'infrastructure et conformité statutaire rigoureuse.

---

### V. PYRAMIDE NORMATIVE INTERNATIONALE (CONTRATS TRANSFRONTALIERS & PI)

Pour les engagements, licences et coopérations internationales (universités, administrations, défense, partenaires étrangers), l'architecture contractuelle *Strictum Jus* s'articule en deux plans juridiques distincts et complémentaires :

1. **Statut corporatif interne (*lex societatis*) :** l'entité demeure constituée et régie par la *Loi sur les compagnies du Québec* (Partie III) ainsi que par le régime fiscal applicable (TPS/TVQ, Revenu Québec).
2. **Socle normatif international de référence :**
   - **Convention de Berne (OMPI / WIPO)** : protection internationale automatique du droit d'auteur sur le code source, les spécifications formelles, les schémas et les thèses scientifiques dans les États signataires, sans formalité préalable de dépôt ;
   - **Convention de Vienne de 1980 (CVIM / CISG, CNUDCI)** : référentiel uniforme des contrats internationaux de vente, dont l'applicabilité ou l'exclusion expresse (art. 6) est précisée au contrat selon la qualification juridique de la fourniture logicielle ou de la prestation de services ;
   - **Convention de New York de 1958 (CNUDCI)** : reconnaissance et exécution transfrontalière des sentences arbitrales dans plus de 170 États pour le règlement des différends contractuels internationaux ;
   - **Droit matériel suisse (Code des obligations — CO)** : *lex contractus* neutre de référence (à l'exclusion de ses règles de conflit de lois) lorsque les parties stipulent un ancrage contractuel international neutre.

> **Clause de rigueur juridique :** l'invocation de ces instruments internationaux dans un contrat effectif requiert l'insertion de clauses écrites explicites (droit applicable, clause compromissoire d'arbitrage, qualification PI/licence) ratifiées par les parties et revues par un conseiller juridique qualifié dans les juridictions concernées.

