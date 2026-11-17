---
name: security-audit
description: Audit de sécurité fail-closed, zéro confiance, séparation crypto/politique/silicium et prévention des escalades silencieuses d'autorité.
---
# Skill `security-audit`

1. Appliquer la règle **Autorité ≤ Preuve** et séparer rigoureusement :
   - présence/fraîcheur/cohérence (OPA Rego v1),
   - validité cryptographique réelle (SHA-256 / Ed25519 / Cosign `--bundle`),
   - ancrage matériel réel (`tpm2_quote` — échec explicite si absent).
2. Rejeter toute lecture IPC non bornée, tout décodage Base64 permissif, toute horodatage futur et tout registre WORM altéré (`WormTamperError`).
3. Proscrire tout chemin personnel local ou secret dans le code, `.agents/mcp_config.json` et `.agents/environment.json`.
4. Documenter explicitement les limites réelles (WORM coopératif vs matériel, audit crypto externe requis).
