---
name: automation-scripting
description: Scripts d'automatisation Python/PowerShell/Bash déterministes, idempotents, encodés UTF-8 et conformes à la Règle A12.
---
# Skill `automation-scripting`

1. Garantir l'**idempotence** : exécuter le script deux fois consécutives ne doit ni dupliquer des ressources ni détruire des preuves (`init_idempotent`).
2. Forcer l'encodage `UTF-8` explicitement (`PYTHONUTF8=1`, `sys.stdout.reconfigure(encoding="utf-8")`) pour la parité Linux/Windows.
3. Vérifier l'empreinte SHA-256 de tout artefact généré ou téléchargé.
4. Rendre exécutables (`chmod +x`) les scripts Python POSIX dans `scripts/` et les indexer dans `INDEX_CONSTITUTION.md` (`A12`).
