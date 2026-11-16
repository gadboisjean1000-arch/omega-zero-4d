---
name: backend-api
description: Conception d'API, microservices, passerelles RPC/MCP, validation stricte des entrées et résilience transactionnelle.
---
# Skill `backend-api`

1. Valider toute charge entrante contre un schéma formel (Draft 2020-12 / Pydantic / TypeScript strict) et échouer de façon fail-closed (`HTTP 4xx` ou erreur JSON-RPC explicite).
2. Imposer l'idempotence sur les opérations critiques et des transactions ordonnées (`PREPARE → VERIFY → COMMIT → CLEAN`).
3. Proscrire les `except Exception:` génériques (`BLE001`) : capturer uniquement les exceptions attendues et journaliser sans fuite de jetons.
4. Tester en sous-processus et bout-en-bout (statuts nominaux, erreurs de parsing, limites de capacité `Load(C)`).
