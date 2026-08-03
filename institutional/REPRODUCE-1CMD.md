# Reproductibilité institutionnelle — 1 commande

## Commande unique
```powershell
powershell -ExecutionPolicy Bypass -File .\institutional\REPRODUCE.ps1
```

## Ce que fait le script
1. Capture les verrous de dépendances (`requirements.txt`, `package-lock.json`, etc.).
2. Recalcule les hashes SHA-256 des artefacts institutionnels.
3. Reconstruit `institutional/REGISTRE-CHAINE-CONFIANCE.json`.
4. Vérifie les signatures `.sig`/`.asc` quand présentes (couplage `fichier` + `fichier.sig`/`fichier.asc`).

## Vérification manuelle minimale
```powershell
Get-Content .\institutional\REGISTRE-CHAINE-CONFIANCE.json
Get-FileHash .\institutional\MANDAT-AUDIT-EXTERNE-v1.0.md -Algorithm SHA256
```

## Règle de statut
- `DRAFT`: artefact non signé.
- `SIGNED`: signature détectée.
- `VERIFIED`: signature vérifiée et chaîne de confiance cohérente.

## Sortie attendue
- Fichier mis à jour: `institutional/REGISTRE-CHAINE-CONFIANCE.json`
- Résumé terminal: nombre d'artefacts, nombre signés, nombre vérifiés.
