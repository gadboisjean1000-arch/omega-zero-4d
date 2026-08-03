# PROTOCOLE — Preuve Externe de Rang Supérieur
## SUPELA v1.1.0 — Couche E2 — Attestations Auditeurs Indépendants

**Version:** 1.0  
**Date:** 2026-08-03  
**Statut:** ACTIF  
**Portée:** `evidence/external-audit/rank-superior/`

---

## 1. Objectif

Ce protocole définit les exigences, le processus et les critères d'acceptation pour l'obtention du statut **VERIFIED_TIER2** dans le cadre de la couche "preuve externe de rang supérieur" du système SUPELA v1.1.0.

> **Principe fondamental :** Aucune revendication de vérification tier-2 ne peut être effectuée sans la présence de deux attestations cryptographiquement signées par des auditeurs externes indépendants. Les templates non signés confèrent uniquement le statut **PROVISIONAL**, jamais **VERIFIED_TIER2**.

---

## 2. Statuts Possibles

| Statut | Condition | Points (E2) | Description |
|--------|-----------|-------------|-------------|
| `ABSENT` | Structure absente | 0/10 | Dossier `rank-superior/` manquant ou corrompu |
| `PROVISIONAL` | Structure présente, templates non signés | 4/10 | Templates en place, prêts à recevoir des signatures, mais aucun auditeur externe n'a encore signé |
| `VERIFIED_TIER2` | 2 attestations signées + hash chain cohérente | 10/10 | Preuve externe complète et vérifiable cryptographiquement |

---

## 3. Artefacts Requis

```
evidence/external-audit/rank-superior/
├── ATTESTATION-AUDITEUR-A.template.json   ← Attestation auditeur indépendant A
├── ATTESTATION-AUDITEUR-B.template.json   ← Attestation auditeur indépendant B
├── EXTERNAL-REVIEW-REGISTRY.json          ← Registre des revues (draft/signed/verified)
└── HASH-CHAIN-MANIFEST.json               ← Chaîne de hachage des artefacts clés
```

Scripts associés :
- `VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF.ps1` — vérification autonome
- `SUPER-CALCULATEUR-VERIFICATION.ps1` — intégration dans le score global (bloc E2)

---

## 4. Champs Requis par Attestation

Chaque fichier d'attestation doit contenir les champs suivants, sans valeur placeholder :

| Champ | Type | Description |
|-------|------|-------------|
| `auditor_org` | string | Organisation de l'auditeur (institution réelle) |
| `contact` | objet | Nom, email, institution, ORCID ou identifiant |
| `scope` | objet | Cible, type de revue, artefacts examinés, période |
| `method` | objet | Approche, normes appliquées, outils, déclaration d'indépendance |
| `findings` | objet | Résumé, points forts, préoccupations, évaluation globale |
| `signature_block` | objet | Signataire, date UTC, algorithme, empreinte clé, valeur signature |

Le champ `_status` doit être différent de `TEMPLATE_UNSIGNED` pour qu'une attestation soit considérée signée.

---

## 5. Processus de Signature

### 5.1 Rôle de l'Auditeur Externe

L'auditeur externe doit :

1. Prendre connaissance du système SUPELA v1.1.0 et des artefacts listés dans la section `scope.artifacts_reviewed` de son attestation
2. Mener une revue indépendante selon la méthodologie décrite dans `method.approach`
3. Compléter tous les champs du template (remplacer chaque `<PLACEHOLDER>` par les valeurs réelles)
4. Modifier `_status` de `TEMPLATE_UNSIGNED` vers `SIGNED`
5. Signer cryptographiquement le fichier et renseigner `signature_block.value`
6. Fournir l'empreinte de sa clé publique dans `signature_block.key_fingerprint`

### 5.2 Après Signature — Mise à Jour du Registre

Après réception d'une attestation signée :

1. Mettre à jour `EXTERNAL-REVIEW-REGISTRY.json` :
   - Changer `status` de `draft` vers `signed`
   - Remplir `signed_at_utc`, `auditor_org`, `overall_assessment`
2. Calculer le SHA-256 du fichier signé
3. Mettre à jour `HASH-CHAIN-MANIFEST.json` :
   - Remplir le champ `signed_sha256` de l'entrée correspondante dans `artifacts.rank_superior_layer`

### 5.3 Activation de VERIFIED_TIER2

Le statut VERIFIED_TIER2 est activé automatiquement par `VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF.ps1` lorsque :

- ✓ Les 2 attestations sont présentes et lisibles
- ✓ Tous les champs requis sont renseignés (aucun placeholder)
- ✓ `_status` ≠ `TEMPLATE_UNSIGNED` pour les deux attestations
- ✓ `signature_block.value` est non-vide pour les deux attestations
- ✓ `signed_sha256` est non-null dans `HASH-CHAIN-MANIFEST.json` pour A et B
- ✓ Le registre compte ≥ 2 attestations au statut `signed` ou `verified`

---

## 6. Exigences d'Indépendance

Les deux auditeurs **doivent** être :

- Affiliés à des organisations distinctes
- Sans conflit d'intérêt avec l'auteur (Jean Gadbois) ou l'organisation (groupnatupro)
- Compétents dans le domaine qu'ils évaluent (architecture logicielle, méthodes psychométriques, systèmes critiques, etc.)

Les deux auditeurs **peuvent** évaluer des aspects différents du système (l'un l'architecture, l'autre les preuves psychométriques, etc.) — la complémentarité est encouragée.

---

## 7. Algorithmes de Signature Acceptés

| Algorithme | Accepté |
|------------|---------|
| GPG-RSA-4096 | ✓ |
| GPG-RSA-2048 | ✓ |
| ed25519 | ✓ |
| ECDSA-P256 | ✓ |
| SHA1/MD5 seuls | ✗ (insuffisant) |

---

## 8. Vérification

### Vérification autonome
```powershell
.\VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF.ps1
```
Affiche le statut `PROVISIONAL` ou `VERIFIED_TIER2` avec détail de chaque vérification.

### Intégration dans le super-calculateur
```powershell
.\SUPER-CALCULATEUR-VERIFICATION.ps1
```
Le bloc E2 "Rang supérieur" apparaît dans le tableau avec scoring différencié.

---

## 9. Anti-Patterns à Éviter

| ❌ À ne jamais faire | ✅ Correct |
|---------------------|-----------|
| Modifier `_status` manuellement sans signature réelle | Obtenir une vraie signature d'un auditeur externe |
| Remplir `signature_block.value` avec une valeur fictive | Utiliser une clé cryptographique réelle et vérifiable |
| Revendiquer VERIFIED_TIER2 avec des templates placeholders | Accepter PROVISIONAL jusqu'à signature réelle |
| Utiliser le même auditeur pour A et B | Utiliser deux auditeurs d'organisations différentes |

---

## 10. Références

- `evidence/external-audit/rank-superior/ATTESTATION-AUDITEUR-A.template.json`
- `evidence/external-audit/rank-superior/ATTESTATION-AUDITEUR-B.template.json`
- `evidence/external-audit/rank-superior/EXTERNAL-REVIEW-REGISTRY.json`
- `evidence/external-audit/rank-superior/HASH-CHAIN-MANIFEST.json`
- `VERIFY-RANK-SUPERIOR-EXTERNAL-PROOF.ps1`
- `SUPER-CALCULATEUR-VERIFICATION.ps1` (bloc E2)
