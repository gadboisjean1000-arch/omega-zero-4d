# Registre des Contradictions & Échecs Conservés · Supela Ω-ZERO

> **Schéma :** `supela-contradictions/1` · **Version :** `1.0.0` · **Effacement interdit :** `True`

> Une contradiction ou un échec antérieur (ex. essai adversarial T11) n'est jamais supprimé parce qu'un run ultérieur devient PASS ; l'état passe de FAIL à historique conservé avec conditions explicites de réouverture.

| ID | Titre | Objet | Statut Contradiction | État 4D | Invariants impactés | Conditions de réouverture |
|---|---|---|---|---|---|---|
| `CONTR-T11` | **Essai adversarial T11 : FAIL antérieur conservé malgré un run ultérieur PASS** | `MAT-02-CONSERVATION-ECHEC / T11` | `HISTORIQUE_CORRIGEE_CONSERVEE` | `LATENT` | `I5`, `I_M`, `K_t ⊆ K_{t+1}`, `ACTIF → LATENT → RÉOUVERT → ACTIF` | Réexécution complète des suites adversariales sur T11 lors de toute évolution du moteur de transition 4D ou du journal WORM, ou apparition d'une nouvelle régression. |
| `CONTR-C001` | **Conflit interdisciplinaire C-001 (Psychologie × Droit × Gestion)** | `DICT-025 / C-001 (TEST_P0_EXEMPLE)` | `CONSERVEE_NON_ACQUISE` | `ACTIF` | `I4`, `C04`, `C05`, `C10` | Apport d'une preuve interdisciplinaire nouvelle satisfaisant Required(G) sans écraser l'une des trois disciplines. |
| `CONTR-GRPO-001` | **Paradoxe apparent GRPO : perte nulle L(θ_old) = 0 avec gradient non nul ∇_θ L ≠ 0** | `MAT-07-REWARD-NOT-TRUTH / DICT-038` | `HISTORIQUE_CORRIGEE_CONSERVEE` | `ACTIF` | `Score ≠ Preuve ≠ Vérité`, `Reward(x) ⇏ Vérité(x)` | Modification des paramètres GRPO (μ, β, ε), ajout d'une nouvelle fonction de perte ou échec du test numérique dans tests/test_second_domain_example.py. |
| `CONTR-TRANSFO-UNDEF` | **Chaîne de transformation H retournée comme 'undefined' (Hi Ace LOL.docx insuffisant)** | `MAT-06-CHAINE-TRANSFO` | `INCONNUE_SOURCE_INCOMPLETE` | `RÉOUVERT` | `M3`, `I_M`, `H ≠ L ≠ P`, `amélioration ≠ autorisation`, `EXTRACTED ⇏ VALIDATED` | Réouverture directe du fil Copilot source 19:b__mSUKb... ou d'un fichier M365/local contenant explicitement H/L/P et la source de la chaîne brute. |
| `CONTR-PR1-PS1-AUDIT` | **Défauts initiaux du collecteur PR #1 (normalisation C:, StrictMode, fuites URL, faux COMPLET)** | `scripts/collect_local_encyclopedie.ps1 et scripts/build_encyclopedie.py` | `HISTORIQUE_CORRIGEE_CONSERVEE` | `ACTIF` | `Authority(G) ≤ Proof(G)`, `G(G) ≤ P`, `I5` | Exécution réelle de collect_local_encyclopedie.ps1 sur le poste Windows cible et inspection du local_pc_inventory.json résultant. |
| `CONTR-ZERO-INT-MANQUANT` | **Réduction progressive M365 : TZI et VR-22 extraits mais non encore formalisés/exécutés** | `MAT-00-ZERO-INT / MAT-03-RESET-STAR / PROV-TZI-001 / PROV-RESET-002` | `CONSERVEE_OUVERTE` | `RÉOUVERT` | `I_M`, `M3`, `K_t ⊆ K_{t+1}`, `explorable ≠ actif`, `CODE_RECOVERED ⇏ CODE_EXECUTED` | Exécution vérifiée de vr22.py en suite de tests reproductible et formalisation logique complète du TZI + comparaison différentielle Livre v2.0 / v3.0. |
| `CONTR-Z0-TENSION` | **Tension Z₀ / Cycle & divergences multi-sources : Branche A (TZI R(S_n)→Z₀) vs Branche B (v3.0 cycle_def: undefined / non_resolu) & Vide ≠ Z₀** | `MAT-00-ZERO-INT / MAT-00-XERO-VIDE / MAT-03-RESET-STAR / MAT-00-PI0` | `CONSERVEE_OUVERTE` | `ACTIF` | `I4`, `K_t ⊆ K_{t+1}`, `H ≠ L ≠ P`, `SOURCE_IDENTIFIED ⇏ PROUVÉ`, `NEW_VERSION ⇏ ERASE(OLD_VERSION)` | Formalisation LPO / Théorie des Catégories reliant sans perte Branche A (TZI R(S_n)→Z₀), Branche B (Corpus v3.0 cycle_def / Vide ≠ Z₀), les niveaux R0..R5 (vr22.py) et Π₀(S_t). |

## CONTR-T11 — Essai adversarial T11 : FAIL antérieur conservé malgré un run ultérieur PASS

- **Objet concerné :** `MAT-02-CONSERVATION-ECHEC / T11`
- **Statut contradiction :** `HISTORIQUE_CORRIGEE_CONSERVEE` · **État 4D :** `LATENT`
- **Constat / FAIL historique :** Lors des tests adversariaux initiaux sur les transitions temporelles ACTIF / LATENT / RÉOUVERT et l'invariant de non-effacement, l'essai T11 a produit un état FAIL qui devait demeurer visible dans la chronologie même après correction.
- **État ultérieur :** Un run ultérieur documenté dans le fil conversationnel Copilot M365 est passé PASS, sans effacer le FAIL d'origine ni autoriser la réécriture du passé.
- **Justification du non-effacement :** Règle I5 (Conservation de la preuve) et chronologie XII : NOUVEAU RÉSULTAT ne produit jamais EFFACEMENT DU PASSÉ ; la vulnérabilité antérieure reste une trace d'apprentissage et de régression.
- **Conditions de réouverture :** Réexécution complète des suites adversariales sur T11 lors de toute évolution du moteur de transition 4D ou du journal WORM, ou apparition d'une nouvelle régression.
- **Source / Provenance :** Extrait Copilot M365 fourni par l'utilisateur (19:b__mSUKbgyV6KrsLScOwey2Ti8-Fa0EFmEGYVZlbgrM1@thread.v2)

## CONTR-C001 — Conflit interdisciplinaire C-001 (Psychologie × Droit × Gestion)

- **Objet concerné :** `DICT-025 / C-001 (TEST_P0_EXEMPLE)`
- **Statut contradiction :** `CONSERVEE_NON_ACQUISE` · **État 4D :** `ACTIF`
- **Constat / FAIL historique :** Désaccord normatif et empirique entre les évaluations disciplinaires (Psychologie, Droit du travail, Gestion) dans le scénario TEST-4D-ESC-01 : aucune convergence silencieuse autorisée (C04/C05).
- **État ultérieur :** Représenté comme Conflict4D explicitement CONSERVÉ et NON_ACQUISE dans reports/TEST-4D-ESC-01.report.json ; bloque toute promotion automatique sans revue humaine.
- **Justification du non-effacement :** Invariant I4 (Cohérence sans écrasement) et conditions C04/C05 de PLAN-4D-ΩZERO-ESC-01 : l'unanimité artificielle viole la fidélité probatoire.
- **Conditions de réouverture :** Apport d'une preuve interdisciplinaire nouvelle satisfaisant Required(G) sans écraser l'une des trois disciplines.
- **Source / Provenance :** docs/constitution/TEST_P0_EXEMPLE.json et reports/TEST-4D-ESC-01.report.json

## CONTR-GRPO-001 — Paradoxe apparent GRPO : perte nulle L(θ_old) = 0 avec gradient non nul ∇_θ L ≠ 0

- **Objet concerné :** `MAT-07-REWARD-NOT-TRUTH / DICT-038`
- **Statut contradiction :** `HISTORIQUE_CORRIGEE_CONSERVEE` · **État 4D :** `ACTIF`
- **Constat / FAIL historique :** Une lecture naïve de L_GRPO(θ) = -min(r·A, clip(r)·A) conduirait à conclure à tort que L(θ_old)=0 implique un gradient nul ou une preuve de vérité du modèle.
- **État ultérieur :** Contre-exemple analytique et numérique vérifié dans src/omega_zero/grpo_bridge.py (à μ=1, β=0, θ_old=0.25 : loss=0.0 mais grad_theta=-0.273837), tout en maintenant Reward(x) ⇏ Vérité(x).
- **Justification du non-effacement :** Empêche la confusion récurrente entre optimisation locale (avantage relatif), convergence scalaire et preuve épistémique indépendante.
- **Conditions de réouverture :** Modification des paramètres GRPO (μ, β, ε), ajout d'une nouvelle fonction de perte ou échec du test numérique dans tests/test_second_domain_example.py.
- **Source / Provenance :** docs/constitution/SCHEMA_GRPO_SUPELA.md, src/omega_zero/grpo_bridge.py et Copilot M365 (19:aaBvPORfeBzfC2j9RnsFuEP3hSvhHqVwd9jyhWyGn241@thread.v2)

## CONTR-TRANSFO-UNDEF — Chaîne de transformation H retournée comme 'undefined' (Hi Ace LOL.docx insuffisant)

- **Objet concerné :** `MAT-06-CHAINE-TRANSFO`
- **Statut contradiction :** `INCONNUE_SOURCE_INCOMPLETE` · **État 4D :** `RÉOUVERT`
- **Constat / FAIL historique :** Lors de l'extraction de la section H (« Transformation et responsabilité »), la formule brute originale est ressortie littéralement comme 'undefined' dans le rendu source.
- **État ultérieur :** La recherche M365 partielle dans Hi Ace LOL.docx (e8728a71...) et Corpus Unifié v3.0 (12e8eb37...) montre bien des énoncés généraux (preuves, limites, inconnues, Pipeline Cuba CB-1..6), mais pas la chaîne H/L/P brute exacte (missing: exact_H_definition, exact_L_definition, exact_P_definition, exact_chain_source). La proposition dérivée reste marquée INCONNU / promotion: FORBIDDEN.
- **Justification du non-effacement :** Règle M3 (Manque ≠ permission d'inventer) et séparation Source ≠ Autorité : interdiction d'attribuer rétrospectivement une reconstruction à une archive absente.
- **Conditions de réouverture :** Réouverture directe du fil Copilot source 19:b__mSUKb... ou d'un fichier M365/local contenant explicitement H/L/P et la source de la chaîne brute.
- **Source / Provenance :** Copilot M365 (19:b__mSUKbgyV6KrsLScOwey2Ti8-Fa0EFmEGYVZlbgrM1@thread.v2) & Hi Ace LOL.docx (e8728a71-b867-4ffe-a1ae-c33ec590a267)

## CONTR-PR1-PS1-AUDIT — Défauts initiaux du collecteur PR #1 (normalisation C:, StrictMode, fuites URL, faux COMPLET)

- **Objet concerné :** `scripts/collect_local_encyclopedie.ps1 et scripts/build_encyclopedie.py`
- **Statut contradiction :** `HISTORIQUE_CORRIGEE_CONSERVEE` · **État 4D :** `ACTIF`
- **Constat / FAIL historique :** Bien que les 4 vérifications CI de PR #1 aient été vertes, la revue automatisée (Devin, Sourcery, Copilot) a relevé que -Drives C,D produisait C\, que StrictMode échouait sur .children, que des URL/remotes pouvaient contenir des jetons et que local_pc_scan='PARTIELLE' ou ai_platforms vides pouvaient faussement afficher COMPLET.
- **État ultérieur :** Correctifs appliqués dans collect_local_encyclopedie.ps1, build_encyclopedie.py et supela_encyclopedie_1.schema.json tout en conservant la trace historique que CI vert initial ≠ absence de défaut.
- **Justification du non-effacement :** Illustre concrètement « PR candidate ≠ certitude » et « Ce qui est vert dans une suite n'exclut pas un angle mort non couvert ».
- **Conditions de réouverture :** Exécution réelle de collect_local_encyclopedie.ps1 sur le poste Windows cible et inspection du local_pc_inventory.json résultant.
- **Source / Provenance :** Revues PR #1 GitHub (Devin Review, Sourcery, Copilot) observées le 2026-11-16

## CONTR-ZERO-INT-MANQUANT — Réduction progressive M365 : TZI et VR-22 extraits mais non encore formalisés/exécutés

- **Objet concerné :** `MAT-00-ZERO-INT / MAT-03-RESET-STAR / PROV-TZI-001 / PROV-RESET-002`
- **Statut contradiction :** `CONSERVEE_OUVERTE` · **État 4D :** `RÉOUVERT`
- **Constat / FAIL historique :** État initial (2026-11-16) : la recherche M365 fichiers n'avait rien retourné et les fils 19:Fcb7Bbl... / 19:nWs3b4mo... ne livraient que les titres Théorème du Zéro-Intégration, RESET*, R* et VR-22 sans contenu source.
- **État ultérieur :** Réduction majeure de Manque sans effacer le constat initial : 16 sources OneDrive/M365 identifiées ; passages PDF TZI (3d411db4..., 6 écritures semi-formelles), Corpus Unifié v3.0 complet (12e8eb37..., Parties I–XI), et spécification vr22.py (Texte collé (3).txt 3f105653...) extraits. Restent ouverts : formalisation 1er ordre/catégories annoncée par le PDF, exécution locale de vr22.py (CODE_RECOVERED ⇏ CODE_EXECUTED) et dérivation complète de tous les variants RESET*.
- **Justification du non-effacement :** Monotonie K_t ⊆ K_{t+1} et règles « SOURCE_IDENTIFIED ⇏ PROUVÉ », « EXTRACTED ⇏ VALIDATED », « CODE_RECOVERED ⇏ CODE_EXECUTED ».
- **Conditions de réouverture :** Exécution vérifiée de vr22.py en suite de tests reproductible et formalisation logique complète du TZI + comparaison différentielle Livre v2.0 / v3.0.
- **Source / Provenance :** Fils M365 (19:Fcb7Bbl..., 19:nWs3b4mo...), PDF TZI (3d411db4...), Texte collé (3).txt (3f105653...) et Corpus Unifié v3.0 (12e8eb37...)

## CONTR-Z0-TENSION — Tension Z₀ / Cycle & divergences multi-sources : Branche A (TZI R(S_n)→Z₀) vs Branche B (v3.0 cycle_def: undefined / non_resolu) & Vide ≠ Z₀

- **Objet concerné :** `MAT-00-ZERO-INT / MAT-00-XERO-VIDE / MAT-03-RESET-STAR / MAT-00-PI0`
- **Statut contradiction :** `CONSERVEE_OUVERTE` · **État 4D :** `ACTIF`
- **Constat / FAIL historique :** Branche A (Théorème du Zéro-Intégration — PDF Pierre Conceptuelle, Section 2.1) exige une clôture stricte du cycle par retour au zéro d'ancrage R(S_n) → Z₀ (¬∃R(C)→Z₀ ⇒ C ∉ Corpus) avec notations déclarées semi-formelles (LPO / Catégories différées) et filiation « Reset fusionné au Vide ». Branche B (Livre Supela — Corpus Unifié v3.0.docx et Hi Ace LOL.docx) comporte des définitions du cycle sans retour strict uniforme au point d'origine (cycle_def: undefined / non_resolu), sépare strictement Vide (𝕍) ≠ Zéro (Z₀) (§3.2) tout en écrivant §4.1 « depuis l'état Zéro — le Vide intact » et SGG_v2 (somme des poids = 1.20), tandis que vr22.py définit R0..R5 avec purge R5(E,C) sur ⟨P,E,C,K⟩ face au PRZ v3.0.0 (N1..N3) et Π₀(S_t) = {I,P,M,A,H}.
- **État ultérieur :** Traitement 4D (PR-M365-01 / PR_ACCEPTED_PARTIAL) : divergence enregistrée explicitement comme tension historique conservée ; toute harmonisation artificielle ou écrasement de la Branche A ou B est interdit.
- **Justification du non-effacement :** Règle « NEW_VERSION ⇏ ERASE(OLD_VERSION) », invariant I4 (Cohérence sans écrasement) et séparation H ≠ L ≠ P : la divergence Z₀ / Cycle et l'état semi-formel du PDF TZI doivent rester auditables.
- **Conditions de réouverture :** Formalisation LPO / Théorie des Catégories reliant sans perte Branche A (TZI R(S_n)→Z₀), Branche B (Corpus v3.0 cycle_def / Vide ≠ Z₀), les niveaux R0..R5 (vr22.py) et Π₀(S_t).
- **Source / Provenance :** PDF TZI (3d411db4...), Livre Supela Corpus Unifié v3.0 (12e8eb37...), Texte collé (3).txt vr22.py (3f105653...), Hi Ace LOL.docx (e8728a71...) et src/omega_zero/projection.py
