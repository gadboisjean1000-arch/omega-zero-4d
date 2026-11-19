# Pack d'Audit Externe & Provenance Zenodo · Supela Ω-ZERO

> **Auteur souverain :** Jean-François Gadbois ([ORCID 0009-0001-5361-6795](https://orcid.org/0009-0001-5361-6795)) · Organisation *Supela K Omega*  
> **Dépôts couverts :** [`omega-zero-4d`](https://github.com/gadboisjean1000-arch/omega-zero-4d) · [`Supela-K3-Omega`](https://github.com/gadboisjean1000-arch/Supela-K3-Omega)  
> **Verrou DOI Zenodo :** `ZENODO_DOI_STATUS: DECLARE_EN_ATTENTE_DOI_REEL`  
> **Clause de bascule DOI :** tant que le DOI numérique réel (`10.5281/zenodo.<chiffres>`) attribué par Zenodo après publication de la GitHub Release n'est pas consigné dans `CITATION.cff` et vérifié en résolution publique, le statut DOI demeure strictement **⏳ DÉCLARÉ** (jamais `✅ RÉSOLU / VÉRIFIÉ`, aucun placeholder toléré dans `CITATION.cff`).

---

## Protocole Canonique d'Audit Externe en 10 Étapes

Chaque auditeur indépendant (institution, université, autorité publique ou défense) suit cette séquence stricte et réfutable sans confiance préalable :

### 1. Identifier
- Identifier exactement le dépôt, la branche ou le tag Release, le commit SHA complet, la licence (`Apache-2.0`), la notice (`NOTICE`) et les métadonnées bibliographiques (`CITATION.cff`, ORCID `0009-0001-5361-6795`).
- Vérifier que le périmètre couvre conjointement `omega-zero-4d` (moteur formel + noyau Rust) et `Supela-K3-Omega` (monolithe `GDS = ⟨D, O, A, γ⟩`).

### 2. Geler
- Geler une copie en lecture seule du commit ou de l'archive Release avant toute évaluation.
- Calculer ou vérifier les condensats cryptographiques (`SHA256SUMS.txt`) ainsi que le coffre-fort WORM logique (`0o444` / `IsReadOnly` + chaînage SHA-256).

### 3. Reconstruire
- Reconstruire les artefacts déterministes à partir des sources propres sans dépendance cachée :
  ```bash
  pip install -e ".[dev]"
  python scripts/build_proven_laws_web.py
  python scripts/build_encyclopedie.py
  cd rust/supela-guard-kernel && cargo build --locked
  ```
- Vérifier que `Cargo.lock` comporte **0 crate externe** et que `LOIS_PROUVEES_SUPELA.html` / `ENCYCLOPEDIE_DICTIONNAIRE.html` sont `0 CDN`.

### 4. Exécuter
- Exécuter l'intégralité des chaînes de preuve automatisées et confirmer zéro échec :
  ```bash
  ruff check src/ tests/ scripts/
  mypy src/ scripts/verify_a12.py scripts/build_encyclopedie.py scripts/vr_compliance_check.py
  python scripts/verify_a12.py
  python scripts/vr_compliance_check.py
  pytest -v
  opa fmt --diff policies/ tests/rego/
  opa check --strict policies/ tests/rego/
  opa test policies/ tests/rego/ -v --explain=fails
  cd rust/supela-guard-kernel && cargo fmt -- --check && cargo clippy --all-targets --all-features -- -D warnings && cargo test --locked --all-targets
  ```
- Exécuter deux fois `docs/constitution/HARNAIS_TEST_ESCALADE_4D.py` et vérifier l'identité stricte de `protocol_sha256` et `condition_results`.

### 5. Vérifier la provenance
- Vérifier la signature keyless **Sigstore Fulcio/OIDC + Rekor** du fichier `SHA256SUMS.txt` (produit en CI dans `omega-zero-ci.yml` ou attaché à la GitHub Release par `.github/workflows/release-provenance-zenodo.yml`) :
  ```bash
  cosign verify-blob SHA256SUMS.txt \
    --bundle SHA256SUMS.txt.sigstore.json \
    --certificate-identity-regexp "^https://github\.com/gadboisjean1000-arch/omega-zero-4d/\.github/workflows/" \
    --certificate-oidc-issuer "https://token.actions.githubusercontent.com"
  ```
- Inspecter en une requête typée **GitHub CLI (`cli/cli`, `gh`) + GitHub GraphQL API v4 (`github-api-v4`)** le dernier commit, sa signature, le bilan CI et la Release publiée (lecture seule, sans scraping HTML) :
  ```bash
  gh api graphql -F owner='gadboisjean1000-arch' -F name='omega-zero-4d' -f query='
    query($owner: String!, $name: String!) {
      repository(owner: $owner, name: $name) {
        defaultBranchRef {
          name
          target {
            ... on Commit {
              oid
              committedDate
              signature { isValid state }
              statusCheckRollup { state }
            }
          }
        }
        latestRelease { tagName publishedAt url }
      }
    }'
  ```
- Vérifier l'état du DOI Zenodo dans `CITATION.cff` :
  - Avant publication de la Release Zenodo : `doi` absent de `CITATION.cff`, statut `⏳ DÉCLARÉ`.
  - Après attribution Zenodo : `doi: "10.5281/zenodo.<chiffres>"` vérifié par regex stricte (`tests/test_citation_and_audit_package.py`) et résoluble sur `https://doi.org/`.

### 6. Vérifier l'attestation matérielle
- Exécuter la sonde d'attestation (`make attest` ou `.\omega.ps1 -Task Attest`).
- Vérifier que la sonde échoue honnêtement en l'absence d'un matériel TPM 2.0 (`tpm2_quote`) — **aucune simulation ni émulation silencieuse n'est admise** (`0_vide ≠ 0_vert`).
- Consigner l'état : `⏳ DÉCLARATIF (matériel TPM 2.0 / TEE requis)` tant que l'ancrage silicium réel n'est pas raccordé.

### 7. Chercher les contradictions
- Inspecter sans effacement les registres ouverts :
  - `docs/constitution/REGISTRE_CONTRADICTIONS.json` (`effacement_interdit = true`, 7 contradictions conservées dont `CONTR-T11` et `CONTR-Z0-TENSION`) ;
  - `docs/constitution/STATUT_MANQUE.json` et les conflits de lois `Conflict4D` conservés ;
  - vérifier qu'aucun échec historique n'a été réécrit ni dissimulé.

### 8. Vérifier la portée
- Contrôler le respect intégral des frontières épistémiques Supela :
  - `Score ≠ Preuve ≠ Vérité` ; `C ≠ P ≠ V ≠ A` ; `Authenticité ≠ Validité ≠ Vérité` ; `0_vide ≠ 0_vert` ;
  - 4 indécidables de Classe A isolés hors clôture binaire, 3 bornes discrètes de Classe B vérifiées ;
  - couverture locale Windows honnête (`local_pc_scan: NON_EXECUTEE` tant qu'aucun inventaire local `C:\`/`D:\` n'est importé) ;
  - **interdiction absolue du qualificatif « scellé en production »** sous `NOTICE-HDR-ISO-Monolithe-Probant.md` tant que les 3 prérequis complets (`Fulcio/OIDC` + `tpm2_quote` + `audit externe indépendant`) ne sont pas tous raccordés et publiés.

### 9. Produire le rapport
- Émettre un rapport d'audit horodaté UTC reprenant la séparation tripartite :
  - **✅ PROUVÉ MÉCANIQUEMENT** (tests, empreintes SHA-256, Run IDs CI, bundle Fulcio/OIDC + Rekor) ;
  - **🔷 ALIGNÉ PAR INGÉNIERIE** (architecture ISO/NIST/SLSA/NIS2/DORA/Loi 25/OSBL) ;
  - **⏳ DÉCLARATIF / HORS PÉRIMÈTRE CI** (`tpm2_quote`, HSM souverain hors cloud, audit externe tiers, DOI Zenodo tant que non attribué).

### 10. Soumettre à décision humaine
- Soumettre le rapport et toute proposition de modification exclusivement par Pull Request (`VR-03`) à la **ratification humaine souveraine de Jean-François Gadbois** (`C10 : amélioration ≠ autorisation`).
- Aucun agent, pipeline ou score automatisé ne peut prononcer un scellement final ni fusionner unilatéralement sur `main`.

---

## Procédure de Consignation du DOI Zenodo Réel (`docs/zenodo-doi-canonical`)

Une fois la GitHub Release publiée et le DOI numérique réel attribué par Zenodo :

1. Créer la branche dédiée depuis `main` : `git checkout -b docs/zenodo-doi-canonical`
2. Ajouter le champ exact `doi: "10.5281/zenodo.<CHIFFRES_REELS>"` dans `CITATION.cff` (jamais de placeholder).
3. Mettre à jour `ZENODO_DOI_STATUS` en `RESOLU_VERIFIE` dans ce document et consigner le lien `https://doi.org/10.5281/zenodo.<CHIFFRES_REELS>` dans `MATRICE_CONFORMITE_INSTITUTIONNELLE.md`.
4. Exécuter `pytest tests/test_citation_and_audit_package.py` + `python scripts/build_encyclopedie.py` + `python scripts/verify_a12.py`.
5. Ouvrir la PR `docs: add Zenodo provenance and external audit package` pour ratification humaine.
