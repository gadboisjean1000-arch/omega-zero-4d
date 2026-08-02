# Security Policy — SUPELA v1.1.0

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.1.x   | ✅ Yes    |
| 1.0.x   | ⚠️ Critical fixes only |
| < 1.0   | ❌ No     |

---

## Reporting a Vulnerability

**Ne pas ouvrir d'issue publique pour les vulnérabilités de sécurité.**

Signalez de façon privée via :
👉 [GitHub Security Advisories](https://github.com/groupnatupro/multi-branches/security/advisories/new)

Incluez dans votre rapport :
- Description claire de la vulnérabilité
- Étapes pour reproduire
- Impact potentiel (confidentialité, intégrité, disponibilité)
- Mitigation suggérée (optionnelle)

Nous répondrons dans les **72 heures** et coordonnerons un correctif et une divulgation responsable.

---

## Secret Management

- Ne jamais commiter de secrets, API keys, tokens ou mots de passe
- Utiliser GitHub Actions Secrets pour les pipelines CI/CD
- Les fichiers `.env` doivent être dans `.gitignore`
- Utiliser `.env.example` avec des valeurs placeholder

---

## Governance Security — SCDH V4

Le protocole **V4** (kill switch < 100ms) s'applique en cas de détection de dissonance critique (Δ ≥ 0.50). Ce mécanisme de sécurité est documenté dans `RFC-SUPELA-K3-ANNEXE-E-SCDH.md`.

---

## Dépendances

Les dépendances sont surveillées automatiquement via Dependabot (`.github/dependabot.yml`). Toute mise à jour de sécurité est traitée en priorité.
