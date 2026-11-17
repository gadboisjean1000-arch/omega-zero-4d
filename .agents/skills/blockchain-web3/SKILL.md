---
name: blockchain-web3
description: Conception et vérification de chaînes d'empreintes, preuves d'intégrité, séparation honnête entre chaîne cumulative et arbre de Merkle.
---
# Skill `blockchain-web3`

1. **Nommage cryptographique honnête** : ne jamais appeler « racine Merkle » une chaîne cumulative (`compute_chained_state_root`), ni « SHA-256 » un hachage non cryptographique.
2. Toujours employer un **séparateur de domaine explicite** (`SUPELA-WORM-RECORD-V1\0`, `SUPELA-CHAINED-STATE-V1\0`) pour éviter toute collision inter-protocoles.
3. Vérifier l'intégrité des transitions d'état et des signatures (`Ed25519` / `Cosign v3`) de bout en bout avant de confirmer un reçu.
4. Distinguer l'auditabilité tamper-evident locale de l'immutabilité distribuée ou matérielle.
