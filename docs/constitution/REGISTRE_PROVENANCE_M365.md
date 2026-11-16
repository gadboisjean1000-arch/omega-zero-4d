# Registre de Provenance M365, Anonymisation Locale & Réduction de Manque · Supela Ω-ZERO

> **Schéma :** `supela-provenance-m365/1` · **Version :** `1.0.0` · **Date :** `2026-11-16` · **PR :** `PR-M365-01` · **Statut :** `PR_ACCEPTED_PARTIAL`

## 1. Principes Directeurs & Relations Interdites (`retrouver ≠ canoniser`)

- retrouver ≠ canoniser : toute source identifiée ou extraite passe par la chaîne complète avant tout statut
- source ≠ autorité : la provenance atteste l'existence documentaire, jamais une preuve formelle ni une exécution
- collecté ≠ publiable : l'inventaire brut C:\, D:\ et profils IA reste LOCAL_UNIQUEMENT_PAR_DEFAUT
- inventorié ≠ autorisé à diffuser : un passage en PR publique requiert un filtre d'anonymisation explicite
- K_t ⊆ K_{t+1} : l'ajout d'une source extraite n'efface ni le manque antérieur ni les tensions historiques

**Relations interdites (Draft 2020-12) :** `SOURCE_IDENTIFIED ⇏ PROUVÉ` · `EXTRACTED ⇏ VALIDATED` · `CODE_RECOVERED ⇏ CODE_EXECUTED` · `NEW_VERSION ⇏ ERASE(OLD_VERSION)` · `COLLECTE ⇏ PUBLIABLE` · `INVENTORIE ⇏ AUTORISE_A_DIFFUSER`

## 2. Contrôle d'Accès Réseau depuis la VM (`acces_reseau_vm`)

- **Plugin M365 connecté :** `False`
- **Réponse sonde VM `onedrive.live.com` :** `HTTP/2 403` (`2026-11-16T03:35:00Z`)
- **Mode d'acquisition :** `PASSAGES_ET_CORPUS_FOURNIS_PAR_UTILISATEUR`
- **Note d'honnêteté :** La sonde directe curl -sI depuis la VM Linux sur onedrive.live.com retourne HTTP/2 403 sans authentification Microsoft 365 ; les extraits primaires (TZI PDF, vr22.py dans Texte collé (3).txt, Hi Ace LOL.docx et texte complet Corpus Unifié v3.0) proviennent exclusivement des transmissions explicites de l'utilisateur, sans téléchargement binaire indépendant depuis la VM.

## 3. Chaîne Normative de Provenance (8 Étapes)

| Ordre | Étape | Rôle | Sorties autorisées |
|---|---|---|---|
| `1` | **`ORIGINE`** | Identifier l'auteur, le titre, le système source (OneDrive/M365, C:\, D:\) et la référence unique sans préjuger du contenu. | `auteur`, `titre`, `source_system`, `reference_id`, `emplacement` |
| `2` | **`SOURCE_BRUTE`** | Consigner le statut d'accessibilité technique (HTTP 403 VM vs extrait fourni par l'utilisateur) sans fabrication. | `M365_RECOVERED`, `SOURCE_IDENTIFIED`, `METADATA_AND_SNIPPET_ONLY` |
| `3` | **`EXTRACTION`** | Enregistrer textuellement le passage exact, la section ou ligne et le contexte avec les caveats de la source (ex. semi-formel). | `EXTRACTED`, `passage_exact`, `formules_exactes`, `elements_manquants` |
| `4` | **`NORMALISATION`** | Uniformiser la notation dans le squelette YAML à 29 clés sans ajouter aucune autorité épistémique (EXTRACTED ⇏ VALIDATED). | `NORMALIZED`, `notation_uniformisee`, `aucune_autorite_ajoutee` |
| `5` | **`OBJET_ENCYCLOPEDIQUE`** | Qualifier la nature exacte de l'entrée et la comparer aux entrées existantes (COMPATIBLE \| DIVERGENT \| CONTRADICTORY \| DUPLICATE). | `COMPARED_TO_CURRENT`, `Théorème`, `Axiome`, `Invariant`, `Opérateur`, `Règle`, `Architecture`, `Contre-exemple` |
| `6` | **`PREUVE_TEST`** | Séparer strictement un test simplement décrit/récupéré (RAPPORTÉ) d'une exécution vérifiée (EXÉCUTÉ/REPRODUIT). | `NON_EXÉCUTÉ`, `RAPPORTÉ`, `EXÉCUTÉ`, `REPRODUIT` |
| `7` | **`STATUT_EPISTEMIQUE`** | Borner le statut final selon Autorité ≤ Preuve après HUMAN_REVIEW (tout item non exécuté/non validé reste strictement sous PROUVÉ). | `HUMAN_REVIEW`, `STATUT_EPISTEMIQUE` |
| `8` | **`HISTORIQUE_4D`** | Conserver toutes les versions, manques antérieurs et contradictions (K_t ⊆ K_{t+1}) avec conditions explicites de réouverture. | `ACTIF`, `LATENT`, `RÉOUVERT` |

## 4. Politique de Confidentialité Locale (`collecté ≠ publiable`)

- **Mode par défaut :** `LOCAL_UNIQUEMENT_PAR_DEFAUT`
- **Architecture du flux :** `INVENTAIRE LOCAL COMPLET → FILTRE D'ANONYMISATION → EXPORT ADMISSIBLE`
- **Motifs interdits dans tout export public :** `Chemins complets contenant C:\Users\ ou D:\Users\`; `Chemins AppData / User Data / %LOCALAPPDATA% / %APPDATA% / %USERPROFILE%`; `Noms d'hôtes Windows privés (machine_name non anonymisé)`; `Cookies, Login Data, Local State, .env, .ssh, .kdbx, jetons et requêtes URL`

| Catégorie | Résumé anonyme | Admissible PR publique |
|---|---|---|
| `SOURCES_M365_ID_URLS` | Identifiants documentaires OneDrive/M365 publics de référence (cid=172bcdc878ead1c9) et extraits textuels théoriques explicitement autorisés par l'auteur. | `True` |
| `AGREGATS_COLLECTEUR_WINDOWS` | Statistiques agrégées sans chemin nominatif ni profil navigateur après passage par build_encyclopedie.anonymize_local_inventory(). | `False` |

## 5. Sources OneDrive / M365 Inventoriées (`16` entrées)

| ID | Titre | Type | Stade extraction | Accès VM | Cibles liées | Résumé / Extrait |
|---|---|---|---|---|---|---|
| `M365-SRC-01` | [Copilot 34.txt](https://onedrive.live.com/?id=deb055c0-7a2c-45d1-9514-ce40a56d0e34&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Identifié dans la recherche M365 ; contenu textuel complet non extrait dans ce tour. |
| `M365-SRC-02` | [Copilot.txt](https://onedrive.live.com/?id=06c75e68-0391-42f8-bdbd-0fa6d101e30c&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Archive conversationnelle Copilot brute ; distincte de M365-SRC-05 ; contenu complet à extraire. |
| `M365-SRC-03` | [Document OneDrive (doc.aspx · resid 1979c578)](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=1979c578-0335-4514-b1b9-0e0bd63c4141&cid=172bcdc878ead1c9) | `.docx / doc.aspx` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Document OneDrive doc.aspx signalé par la recherche M365 ; titre et contenu complets à extraire. |
| `M365-SRC-04` | [Théorème du Zéro-Intégration — Pierre Conceptuelle du Corpus Supela.pdf](https://onedrive.live.com/?id=3d411db4-56fc-4d4f-aa62-3a69da2899a3&cid=172bcdc878ead1c9&web=1&EntityRepresentationId=97423cb3-1a76-47cd-ac37-23b31da3f698) | `.pdf` | `PASSAGES_EXTRAITS_UTILISATEUR` | HTTP/2 403 VM ; extraits officiels section 2.1 et 6 écritures fournis par l'utilisateur | `MAT-00-ZERO-INT`, `PROV-TZI-001`, `CONTR-Z0-TENSION` | Section 2.1 : I(C,Z_0), ΔS = S_n - Z_0, R(S_n) → Z_0, ∀C intégrable ∃R(C)→Z_0, ¬∃R(C)→Z_0 ⇒ C ∉ Corpus, D(S_n,Z_0) = \|\|ΔS\|\| = \|\|S_n - Z_0\|\|. Mise en garde source : notation explicitement semi-formelle en attente de formalisation en logique du 1er ordre ou théorie des catégories. Relie également le théorème antérieur : « Chaque cycle doit se décharger à zéro, car toute excitation est définie par rapport au Vide. » |
| `M365-SRC-05` | [Copilot.txt](https://onedrive.live.com/?id=06257786-4302-46b0-966b-301a48e16d91&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Archive conversationnelle Copilot brute ; distincte de M365-SRC-02 ; contenu complet à extraire. |
| `M365-SRC-06` | [Document OneDrive (doc.aspx · resid 94cb52ff)](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=94cb52ff-8579-49dd-8935-782e6418bb6b&cid=172bcdc878ead1c9) | `.docx / doc.aspx` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Document OneDrive doc.aspx signalé par la recherche M365 ; contenu complet à extraire. |
| `M365-SRC-07` | [Théorème du Zéro-Intégration — Pierre Conceptuelle du Corpus Supela.pdf (copie 2)](https://onedrive.live.com/?id=c7985990-f0e1-4d26-9896-f805d201d491&cid=172bcdc878ead1c9&web=1) | `.pdf` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `MAT-00-ZERO-INT`, `PROV-TZI-001` | Second exemplaire OneDrive du PDF TZI ; vérification d'équivalence binaire SHA-256 par rapport à M365-SRC-04 encore ouverte. |
| `M365-SRC-08` | [Livre Supela — Version Académique Officielle v2.0.docx (exemplaire 1)](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=b3beaf49-796a-4e84-8007-cb0d5f22ed5b&cid=172bcdc878ead1c9) | `.docx` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `MAT-00-ZERO-INT`, `PROV-TZI-001`, `PROV-CORPUS-004` | Déclare intégrer TZI, Corpus Xero+Vide, SCDH Tricouche et PRZ v3.0.0 ; comparaison différentielle vs Corpus Unifié v3.0 à extraire. |
| `M365-SRC-09` | [Livre Supela — Corpus Unifié v3.0.docx](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=12e8eb37-4f68-49b6-9814-33328cf8c3ac&cid=172bcdc878ead1c9&EntityRepresentationId=89069acb-8231-48e7-bc8c-42576200fb0a) | `.docx` | `TEXTE_INTEGRAL_FOURNI_UTILISATEUR` | HTTP/2 403 VM ; texte intégral complet (Avant-propos, Prologue, Parties I–XI, Annexes A–I, Glossaire, Index, Bibliographie [1]–[25]) fourni directement par l'utilisateur | `MAT-00-ZERO-INT`, `MAT-00-XERO-VIDE`, `MAT-01-PRINCIPES-P1-P12`, `MAT-03-PRZ-V3`, `MAT-05-SCDH-TRICOUCHE`, `MAT-08-PATTERNS-LAS`, `CONTR-Z0-TENSION` | Édition Unifiée v3.0 (30 juillet 2026, Beauharnois, QC) : D1.1–D1.5, A0–A4, N0–N4, Xero (𝕏)/Z₀, Vide (𝕍), cycle Z₀→Sₙ→R→Z₀, TZI (4 arguments, C1–C5, T2–T5, P1–P8), SCDH Tricouche (Fond/Surface/Cible, I1–I4, 5 noyaux, IPC, Module Zéro, BootConfig/ModuleZero TypeScript), P1–P12, PA-01..10/PC-01..05/MP-01..03, PRZ v3.0.0 (6 phases), Reset N1–N3, RFC K3, MOG-E (IDI, IIB, SGG_v2), Pipeline Cuba CB-1..6, LAS BNF et AP-01..AP-15. |
| `M365-SRC-10` | [Corpus Doctrinal Supela · Géométrie Conversation.txt](https://onedrive.live.com/?id=797c3699-fffc-4561-b88e-b75263cd50ac&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `PROV-GEOM-005` | Mentionne Polygone Supela et Polygramme Supela ; corps complet non encore extrait. |
| `M365-SRC-11` | [PowerShell review.4 1.txt](https://onedrive.live.com/?id=715e37a2-47fd-4f28-9278-ded9975ac835&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `CANDIDAT_EXPLORATOIRE` | Revue PowerShell identifiée par la recherche M365 ; contenu complet à extraire. |
| `M365-SRC-12` | [Livre Supela — Version Académique Officielle v2.0.docx (exemplaire 2)](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=f8a0a71c-feb9-416d-bc11-73417665bf52&cid=172bcdc878ead1c9) | `.docx` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `PROV-CORPUS-004` | Seconde copie/variante de la v2.0 académique ; contenu complet à extraire pour diff éventuel. |
| `M365-SRC-13` | [Parfait Je ... que tu ve.txt](https://onedrive.live.com/?id=ccf18c17-5b80-4032-a83d-a6b8aa6681fd&cid=172bcdc878ead1c9&web=1) | `.txt` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `MAT-06-CHAINE-TRANSFO`, `PROV-TRANSFO-003` | Archive conversationnelle brute signalée par la recherche M365 ; reste candidate à l'extraction. |
| `M365-SRC-14` | [Livre Supela — Version Académique Officielle v2.0.docx (exemplaire 3)](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=309030d5-e3d3-4645-8fd3-d227b2040073&cid=172bcdc878ead1c9) | `.docx` | `METADATA_AND_SNIPPET_ONLY` | HTTP/2 403 (VM non authentifiée M365) | `PROV-CORPUS-004` | Troisième copie/variante de la v2.0 académique ; contenu complet à extraire. |
| `M365-SRC-15` | [Texte collé (3).txt](https://onedrive.live.com/?id=3f105653-da39-4a1a-ac40-25b8e4d1667a&cid=172bcdc878ead1c9&web=1&EntityRepresentationId=4786da25-fd0a-4d12-a358-d897230d22ed) | `.txt` | `PASSAGES_EXTRAITS_UTILISATEUR` | HTTP/2 403 VM ; spécification vr22.py et suite de tests extraites fournies par l'utilisateur | `MAT-03-RESET-STAR`, `PROV-RESET-002`, `CONTR-Z0-TENSION` | Moteur VR-22 (vr22.py) : P (invariants racines protégés), E (lemmes intermédiaires), C (conjectures/branches actives), K (mémoire cumulative). Niveaux R0_NOMINAL, R1_PARAMETRIQUE, R2_EPHEMERE, R3_LOCAL, R4_STRUCTUREL, R5_ABSOLU. Rétraction : Cible∈P⇒Refus, Cible∈E⇒R4, Cible∈C⇒R3, Cible∉(P∪E∪C)⇒Erreur, R5⇒Purge de E et C. Monotonie stricte \|K_{t+1}\| > \|K_t\| et règle de vitalité V_e = Valeur / Complexité ≥ 1.0 (CODE_RECOVERED ⇏ CODE_EXECUTED ; interdiction RUN_PASS). |
| `M365-SRC-16` | [Hi Ace LOL.docx](https://onedrive.live.com/personal/172bcdc878ead1c9/_layouts/15/doc.aspx?resid=e8728a71-b867-4ffe-a1ae-c33ec590a267&cid=172bcdc878ead1c9&EntityRepresentationId=d6aec6f6-c200-451a-ba84-4a13545b77da) | `.docx` | `PASSAGES_EXTRAITS_UTILISATEUR` | HTTP/2 403 VM ; inspection des lignes ouvertes rapportée par l'utilisateur | `MAT-06-CHAINE-TRANSFO`, `PROV-TRANSFO-003`, `CONTR-TRANSFO-UNDEF` | Contient une formulation générale sur les preuves, limites, inconnues, provenance et réévaluation ; NE contient PAS dans les lignes ouvertes les définitions exactes H / L / P ni la source exacte de la chaîne brute de Section H (exact_source_status: NOT_ESTABLISHED). |

## 6. Candidats M365 & Suivi de Provenance (`5` entrées)

### PROV-TZI-001 — Théorème du Zéro-Intégration (TZI) & État Zéro Z₀

- **Cible :** `MAT-00-ZERO-INT` · **Objet :** `Théorème` · **Stade :** `COMPARED_TO_CURRENT` · **Preuve/Test :** `RAPPORTÉ`
- **Comparaison :** `DIVERGENT` · **Revue humaine :** `REQUIS_AVANT_CANONISATION` · **Statut :** `SUPPORTÉ` · **État 4D :** `RÉOUVERT`
- **Origine :** Jean-François Gadbois (Jef) — *Théorème du Zéro-Intégration — Pierre Conceptuelle du Corpus Supela.pdf & Livre Supela — Corpus Unifié v3.0.docx* (`3d411db4-56fc-4d4f-aa62-3a69da2899a3 | 12e8eb37-4f68-49b6-9814-33328cf8c3ac`)
- **Caveat provenance :** Notation déclarée semi-formelle par la source (formalisation LPO / Catégories différée) ; tension Branche A (R(S_n)→Z₀) vs Branche B (v3.0 cycle_def: undefined / non_resolu) conservée dans CONTR-Z0-TENSION.
- **Éléments encore manquants :** Formalisation LPO ou Théorie des Catégories explicitement différée par la source PDF; Contrôle d'équivalence binaire SHA-256 avec copie 2 (M365-SRC-07 c7985990...)

### PROV-RESET-002 — Moteur VR-22 (vr22.py), niveaux R0–R5, vitalité Ve et lignée RESET*

- **Cible :** `MAT-03-RESET-STAR` · **Objet :** `Opérateur` · **Stade :** `COMPARED_TO_CURRENT` · **Preuve/Test :** `RAPPORTÉ`
- **Comparaison :** `DIVERGENT` · **Revue humaine :** `REQUIS_AVANT_CANONISATION` · **Statut :** `SUPPORTÉ` · **État 4D :** `RÉOUVERT`
- **Origine :** Jean-François Gadbois — *Texte collé (3).txt (vr22.py) + Théorème du Zéro-Intégration.pdf + Corpus Unifié v3.0.docx* (`3f105653-da39-4a1a-ac40-25b8e4d1667a | 3d411db4-56fc-4d4f-aa62-3a69da2899a3 | 12e8eb37-4f68-49b6-9814-33328cf8c3ac`)
- **Caveat provenance :** CODE_RECOVERED ⇏ CODE_EXECUTED : statut d'exécution RAPPORTÉ (tests vr22.py non exécutés sur banc local ; interdiction d'étiquetage RUN_PASS et de promotion PROUVÉ).
- **Éléments encore manquants :** Copie exécutable et exécution locale vérifiée de vr22.py dans omega-zero-4d (pas de RUN_PASS à ce stade); Cartographie unifiée R0..R5 (vr22.py) ↔ Reset Niveau 1..3 (Corpus Unifié v3.0 §8.5) ↔ E6/C09

### PROV-TRANSFO-003 — Chaîne de Transformation Section H (H / L / P brute manquante)

- **Cible :** `MAT-06-CHAINE-TRANSFO` · **Objet :** `Formule` · **Stade :** `SOURCE_IDENTIFIED` · **Preuve/Test :** `NON_EXÉCUTÉ`
- **Comparaison :** `NON_EVALUE` · **Revue humaine :** `REQUIS_AVANT_CANONISATION` · **Statut :** `INCONNU` · **État 4D :** `RÉOUVERT`
- **Origine :** Inconnu dans la source brute (chaîne originelle non localisée) — *Le Livre Supela — Corpus Unifié v3.0.docx & Hi Ace LOL.docx (M365) & Parfait Je ... que tu ve.txt* (`e8728a71-b867-4ffe-a1ae-c33ec590a267 | 12e8eb37-4f68-49b6-9814-33328cf8c3ac | ccf18c17-5b80-4032-a83d-a6b8aa6681fd`)
- **Caveat provenance :** m365_search_status=PARTIAL, exact_source_status=NOT_ESTABLISHED, PROMOTION_FORBIDDEN, MANQUE MAINTENU OUVERT.
- **Éléments encore manquants :** exact_H_definition : NON RETROUVÉ; exact_L_definition : NON RETROUVÉ; exact_P_definition : NON RETROUVÉ; exact_chain_source : NON ÉTABLIE

### PROV-CORPUS-004 — Corpus Unifié v3.0 : Xero+Vide, SCDH Tricouche, PRZ v3.0.0, P1–P12, Patterns & MOG-E

- **Cible :** `MAT-05-SCDH-TRICOUCHE` · **Objet :** `Corpus` · **Stade :** `NORMALIZED` · **Preuve/Test :** `NON_EXÉCUTÉ`
- **Comparaison :** `COMPATIBLE` · **Revue humaine :** `REQUIS_AVANT_CANONISATION` · **Statut :** `SUPPORTÉ` · **État 4D :** `ACTIF`
- **Origine :** Jean-François Gadbois (Jef) — Institut Supela — *Livre Supela — Corpus Unifié v3.0.docx (30 juillet 2026, Beauharnois, QC)* (`12e8eb37-4f68-49b6-9814-33328cf8c3ac`)
- **Caveat provenance :** EXTRACTED ⇏ VALIDATED : corpus normatif v3.0 authentifié textuellement, mais ses interfaces TypeScript (ModuleZero, SupelaModule), MOG-E et SGG_v2 (somme des poids 1.20) ne sont pas encore exécutés dans src/omega_zero/.
- **Éléments encore manquants :** Diff textuel avec Livre Supela v2.0.docx (b3beaf49, f8a0a71c, 309030d5); Implémentation/test exécutable de ModuleZero et MOG-E dans omega-zero-4d

### PROV-GEOM-005 — Polygone Supela & Polygramme Supela (Géométrie Conversation)

- **Cible :** `AUCUNE_FICHE_CIBLE` · **Objet :** `Corpus` · **Stade :** `SOURCE_IDENTIFIED` · **Preuve/Test :** `NON_EXÉCUTÉ`
- **Comparaison :** `NON_EVALUE` · **Revue humaine :** `EN_ATTENTE` · **Statut :** `INCONNU` · **État 4D :** `LATENT`
- **Origine :** Jean-François Gadbois (attribué) — *Corpus Doctrinal Supela · Géométrie Conversation.txt* (`797c3699-fffc-4561-b88e-b75263cd50ac`)
- **Caveat provenance :** SOURCE_IDENTIFIED ⇏ PROUVÉ : seuls le titre et la présence des notions Polygone Supela / Polygramme Supela sont attestés.
- **Éléments encore manquants :** Extraction du fichier Corpus Doctrinal Supela · Géométrie Conversation.txt; Définitions formelles de Polygone Supela et Polygramme Supela

## 7. Réduction de Manque M3 (`K_t ⊆ K_{t+1}`)

| ID Manque | Recherche M365 | Statut Source | Verdict | Promotion | Avant → Après | Manquants restants |
|---|---|---|---|---|---|---|
| `MAT-00-ZERO-INT` | `COMPLETE` | `ESTABLISHED_EXTRACTED` | `MANQUE_FORTEMENT_REDUIT` | `CAPPED_BELOW_PROUVE` | INCONNU / LATENT (recherche M365 vide) → SUPPORTÉ / RÉOUVERT — MANQUE ↓ (7 primitives, 6 écritures Section 2.1 PDF + Partie IV v3.0, clause semi-formelle) | Formalisation LPO / Théorie des Catégories explicitement différée par la source PDF; Audit comparatif SHA-256 du doublon M365-SRC-07 |
| `MAT-03-RESET-STAR` | `PARTIAL` | `PARTIAL_ESTABLISHED` | `MANQUE_FORTEMENT_REDUIT` | `CAPPED_BELOW_PROUVE` | INCONNU / LATENT (sigles sans corps) → SUPPORTÉ / RÉOUVERT — MANQUE ↓ (vr22.py P/E/C/K, R0..R5, V_e=Valeur/Complexité≥1.0, exécution RAPPORTÉ sans RUN_PASS) | Exécution vérifiée de vr22.py sur banc local (CODE_RECOVERED ⇏ CODE_EXECUTED ; pas de RUN_PASS); Preuve que l'ensemble des variantes RESET* dérive exclusivement d'une source unique |
| `MAT-06-CHAINE-TRANSFO` | `PARTIAL` | `NOT_ESTABLISHED` | `MANQUE_ENCORE_OUVERT` | `PROMOTION_FORBIDDEN` | INCONNU / RÉOUVERT (formulation_brute='undefined') → INCONNU / RÉOUVERT — MANQUE MAINTENU OUVERT (Corpus Unifié v3.0 et Hi Ace LOL.docx sans triplet H/L/P) | exact_H_definition : NON RETROUVÉ; exact_L_definition : NON RETROUVÉ; exact_P_definition : NON RETROUVÉ; exact_chain_source : NON ÉTABLIE |

---
Voir aussi : [ENCYCLOPEDIE_DICTIONNAIRE.md](ENCYCLOPEDIE_DICTIONNAIRE.md) · [REGISTRE_FORMULES_SUPELA.md](REGISTRE_FORMULES_SUPELA.md) · [REGISTRE_CONTRADICTIONS.md](REGISTRE_CONTRADICTIONS.md) · [INDEX_CONSTITUTION.md](INDEX_CONSTITUTION.md).
