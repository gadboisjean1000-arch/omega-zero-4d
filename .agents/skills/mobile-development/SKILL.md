---
name: mobile-development
description: Conception d'applications mobiles résilientes offline-first, synchronisation locale-cloud bornée et gestion des états de manque.
---
# Skill `mobile-development`

1. Traiter les clients mobiles comme des nœuds `LocalNode` : état minimal local synchronisé sans perte vers `CloudOmega` via `Merge*` et `Load(C)`.
2. Préserver les objets non résolus sous statut `Manque` explicite (`OUVERT`, `SOUS_EXPLORATION`, `INACCESSIBLE_DANS_LE_PÉRIMÈTRE`) hors ligne plutôt que d'inventer une synchronisation réussie.
3. Protéger les requêtes réseau par idempotence (`request_id`) en cas de perte de connectivité ou de réponse perdue.
4. Ne jamais stocker de secrets en clair dans le bundle applicatif mobile.
