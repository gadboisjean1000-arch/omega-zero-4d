# `supela-guard-kernel` (Crate Rust · `SUP-ICI-01` / `SUP-IPC-01` / `SUPELA-WORM-V1`)

Implémentation Rust sans dépendance externe (`[dependencies]` vide, `#![forbid(unsafe_code)]`) du noyau fail-closed **Supela-Guard-Kernel**.

## Garanties réelles et limites explicites
- **Sécurité mémoire & typage :** `#![forbid(unsafe_code)]`, lecture IPC bornée en mémoire $O(1)$ (`read_bounded_line`), parser JSON à profondeur bornée (`MAX_JSON_DEPTH = 64`), décodage RFC 4648 Base64 strict (rejet des bits de remplissage non nuls).
- **WORM coopératif durable :** journal append-only JSON-Lines chaîné par SHA-256 séparé par domaine (`SUPELA-WORM-V1`), verrou OS exclusif via `std::fs::File::lock()`, synchronisation disque `sync_all()`, reprise après coupure sur queue partielle (`RecoveryPolicy::TruncatePartialTail`) sans masquer les altérations historiques, et idempotence/conflit sur `request_id`.
- **Limites explicites (honnêteté épistémique) :**
  - Verrouillage fichier coopératif OS (`File::lock()` + `sync_all()`) — **ne constitue pas** un stockage WORM matériel ni une attestation silicium TPM/TEE.
  - `0` dépendance externe signifie l'absence de CVE tierce importée dans `Cargo.toml`, **sans** remplacer un audit cryptographique externe indépendant (`CRYPTO-AUDITED` reste en attente).

## Commandes locales
```bash
cargo fmt --check
cargo clippy --all-targets --all-features -- -D warnings
cargo test --all-targets
```
