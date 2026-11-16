---
name: database-management
description: Modélisation de données, migrations sans perte, journaux WORM append-only et intégrité référentielle intercycle.
---
# Skill `database-management`

1. Garantir des migrations **sans perte** : toute compression ou réduction de schéma doit conserver le noyau de continuité `K_n` (`SUP-ICI-01`).
2. Protéger les journaux d'audit en mode **append-only** chaîné (`prev_hash` → `entry_hash` SHA-256) et détecter toute altération avant lecture.
3. Distinguer l'archivage (`NON-RÉCLAMÉ`) et le rejet documenté (`REJET_JUSTIFIE`) de la suppression silencieuse : `RejetDuContenu ≠ EffacementDeLExistenceHistorique`.
4. Valider l'idempotence d'initialisation (`init_idempotent`) avant toute mise en production.
