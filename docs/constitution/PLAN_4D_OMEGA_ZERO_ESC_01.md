# Protocole Final Corrigé · Supela Ω-ZERO · Local–Cloud–4D (`PLAN-4D-ΩZERO-ESC-01`)

> **Statut documentaire :** `HARNAIS_DISPONIBLE_PRE_EXECUTION` (spécification corrigée, alignée avec les schémas JSON Draft 2020-12 ; le verdict expérimental provient exclusivement des rapports produits par l'exécution réelle du harnais Python).  
> **Principe fondamental :** `Exploration ≠ Autorité` · `Score ≠ Preuve ≠ Vérité` · `Synchronisation ≠ Validation` · `Revidage ≠ Amnésie`

---

## 1. Opérateur de projection $\Pi_0$

### 1.1 Distinction $\Pi_I$ vs $\Pi_0$
- $\Pi_I(\Omega_t) = 0_I$ projette l'état émergent global $\Omega_t$ sur ses invariants permanents en retirant les éléments variables.
- $\Pi_0(S_t) = 0_t = \{I, P, M, A, H\}$ projette un état de travail $S_t$ vers l'état zéro opérationnel prêt pour une reprise honnête :
  - $I$ : **Invariants** ($I_1$ vérité vérifiable, $I_2$ traçabilité, $I_3$ réfutabilité, $I_4$ cohérence, $I_5$ conservation de la preuve, $I_M$ conservation du manque ouvert) ;
  - $P$ : **Preuves et provenances indispensables** (incluant les traces de réfutation $\text{Ref}$ sans autorité concluante) ;
  - $M$ : **Manques encore ouverts** conservés comme potentiel orienté ;
  - $A$ : **Autorités applicables** bornées par les preuves ($A(c) \leq \text{Preuve}(c)$) ;
  - $H$ : **Histoire minimale** permettant la reconstruction causale et la réouverture ciblée des cônes de dépendance.

Au niveau d'un nœud local $L_i$, la projection produit :
$$\Pi_0^{\text{local}}(L_i) = L_i^0 = \{\text{identité}, \text{invariants}, \text{autorités}, \text{index\_minimal}, \text{preuve\_transfert}, \text{mécanisme\_récupération}, \text{manques\_locaux}\}$$
avec $L_i^0 \neq L_i^{\text{amnésique}}$.

### 1.2 Propriétés algébriques vérifiables
1. **Idempotence :** $\Pi_0(\Pi_0(S_t)) = \Pi_0(S_t)$.
2. **Non-vacuité (fail-closed) :** $\Pi_0(S_t) \neq \emptyset$ dès lors que $I \neq \emptyset$.
3. **Bornage d'autorité :** $\forall c \in S_t$, si $c$ n'est pas soutenu par une preuve admissible, $\Pi_0$ retire son autorité concluante ($\text{Autorité}_0(c) \leq \text{Preuve}(c)$).
4. **Conservation du manque ouvert :** tout manque actif ($M$) survit à $\Pi_0$.
5. **Conservation évolutive des réfutations :** tout raccord réfuté perd toute autorité concluante ($\text{Autorité} = 0$) mais conserve sa trace $\text{Ref} \in P \cup H$.

---

## 2. Machine à états des 7 statuts du Manque

Soit $M(S_t, G) \iff \text{Required}(G) \setminus \text{Available}(S_t) \neq \emptyset$.

Structure canonique d'un objet Manque :
$$M_i = \langle \text{id}, \text{question}, \text{contexte}, \text{origine}, \text{dépendances}, \text{autorité}, \text{tentatives}, \text{temps}, \text{statut} \rangle$$

### 2.1 Les 7 statuts minimaux
1. `OUVERT` *(ACTIF, conservé par $\Pi_0$)*
2. `SOUS_EXPLORATION` *(ACTIF, conservé par $\Pi_0$)*
3. `PARTIELLEMENT_RÉDUIT` *(ACTIF, conservé par $\Pi_0$)*
4. `RÉSOLU` *(REOUVRABLE si `NouvellePreuve` remet en cause un raccord)*
5. `RÉFUTÉ_COMME_PROBLÈME` *(REOUVRABLE ; trace historique conservée intégralement)*
6. `REQUALIFIÉ` *(CLÔTURE CONDITIONNELLE par division/reformulation avec filiation explicite)*
7. `INACCESSIBLE_DANS_LE_PÉRIMÈTRE` *(REOUVRABLE si extension prouvée d'autorité ou d'accès)*

### 2.2 Règles déontologiques M1–M5
- **M1 :** $M(P) \nRightarrow \neg P$ *(Manque ≠ faux)*.
- **M2 :** $M(P) \nRightarrow P$ *(Manque ≠ vrai caché)*.
- **M3 :** $M(P) \Rightarrow \text{OPEN}(P) \land \neg \text{FABRICATE}(P)$ *(Manque ≠ permission d'inventer)*.
- **M4 :** $Q \to M \Rightarrow \text{Trace}(\text{pertinence}, \text{autorité}, \text{preuves})$ *(Tout remplissage garde son raccord)*.
- **M5 :** $M_t \to M_{t+1}$ *(Évolution temporelle tracée)*.

### 2.3 Transitions autorisées (`TR-01`..`TR-16`) et transitions interdites
- **Autorisées :**
  - `OUVERT` $\xrightarrow{\text{TR-01}}$ `SOUS_EXPLORATION` (candidats enregistrés avec autorité `AUCUNE`)
  - `OUVERT` $\xrightarrow{\text{TR-02}}$ `REQUALIFIÉ` (scission/reformulation tracée)
  - `OUVERT` $\xrightarrow{\text{TR-03}}$ `INACCESSIBLE_DANS_LE_PÉRIMÈTRE` (barrière de périmètre prouvée)
  - `OUVERT` $\xrightarrow{\text{TR-04}}$ `RÉFUTÉ_COMME_PROBLÈME` (fausse prémisse prouvée)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-05}}$ `PARTIELLEMENT_RÉDUIT` (au moins un raccord soutenu sous conditions + reste ouvert)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-06}}$ `RÉSOLU` (preuve complète vérifiée pour `Required(G)`)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-07}}$ `OUVERT` (candidats réfutés/insuffisants, tentatives conservées)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-08}}$ `RÉFUTÉ_COMME_PROBLÈME` ($A \nrightarrow C$ prouvé)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-09}}$ `REQUALIFIÉ` (division en sous-manques)
  - `SOUS_EXPLORATION` $\xrightarrow{\text{TR-10}}$ `INACCESSIBLE_DANS_LE_PÉRIMÈTRE`
  - `PARTIELLEMENT_RÉDUIT` $\xrightarrow{\text{TR-11}}$ `SOUS_EXPLORATION`, $\xrightarrow{\text{TR-12}}$ `RÉSOLU`, $\xrightarrow{\text{TR-13}}$ `REQUALIFIÉ`
  - **Réouvertures :** `RÉSOLU` $\xrightarrow{\text{TR-14}}$ `SOUS_EXPLORATION` ; `INACCESSIBLE_DANS_LE_PÉRIMÈTRE` $\xrightarrow{\text{TR-15}}$ `OUVERT` ; `RÉFUTÉ_COMME_PROBLÈME` $\xrightarrow{\text{TR-16}}$ `OUVERT`.
- **Strictement interdites :**
  - `OUVERT -> RÉSOLU` sans exploration ni épreuve (`M3`) ;
  - `* -> SUPPRIMÉ` (`I_M`) ;
  - `INACCESSIBLE_DANS_LE_PÉRIMÈTRE -> RÉSOLU` sans réouverture préalable ;
  - `RÉFUTÉ_COMME_PROBLÈME -> RÉSOLU` sans réouverture explicite ;
  - `PARTIELLEMENT_RÉDUIT -> RÉFUTÉ_COMME_PROBLÈME` sans requalification séparée.

---

## 3. Protocole d'Escalade 4D (`TEST-4D-ESC-01`) : 8 Paliers et 10 Conditions

### 3.1 Alignement des 8 paliers (`E0`..`E7`)

| Palier | Intitulé | Charge quantifiée | Conditions évaluées |
|---|---|---|---|
| **E0** | Contrôle Minimal | 1 manque `M-001`, 1 nœud `L1`, 0 candidat | `C01` |
| **E1** | Multiplication des Candidats | 4 raccords candidats `R-001`..`R-004` | `C02`, `C03` |
| **E2** | Escalade Interdisciplinaire | 5 disciplines (Médecine, Droit, Gestion, Psychologie, Éthique), 1 conflit `C-001` | `C04`, `C05` |
| **E3** | Escalade Distribuée Local–Cloud | 4 nœuds (`L1` Montréal, `L2` Paris, `L3` Dakar, `L4` Tokyo), 4 deltas en ordre aléatoire | `C06` |
| **E4** | Tentative d'Escalade d'Autorité | 1 attaque (`L2` demande `ÉTABLI_INTERNATIONALEMENT` sans preuve internationale) | `C07` |
| **E5** | Saturation du Conteneur | 6 catégories d'injection, seuil métrique `Load(C1) ≥ 0.80` | `C08` |
| **E6** | Revidage Transactionnel | 5 prédicats ACK avant `COMMIT`, séquence `PREPARE → VERIFY → COMMIT → CLEAN` | `C09` |
| **E7** | Retour depuis le Vide & Émergence (`E7-A` + `E7-B`) | 1 réouverture `Cone(R-002)` (`E7-A`) + 1 chemin émergent `Médecine→Prévention*` (`E7-B`) | `C10` |

### 3.2 Définition métrique du seuil de saturation (`E5 / C08`)
$$\text{Load}(C) = \max\left(\frac{\text{UsedBytes}}{\text{BytesLimit}},\ \frac{\text{UsedObjects}}{\text{ObjectsLimit}},\ \frac{\text{UsedEdges}}{\text{EdgesLimit}},\ \frac{\text{ObservedLatency}}{\text{LatencyLimit}}\right)$$
$$\text{Load}(C_1) \geq 0.80 \implies \text{MigrationRequired}(C_1, C_2)$$

Déclaration obligatoire avant exécution : `metric`, `capacity_limit`, `unit`, `measurement_method`, `timestamp`, `tested_environment`.  
Éléments obligatoirement préservés par la migration : `stable_ids`, `provenance`, `relations`, `statuses`, `authorities`, `history`, `integrity_hashes`, `reconstruction_capability` (incluant les objets réfutés).

### 3.3 Revidage transactionnel (`E6 / C09`)
$$\text{Revidage}(L_1) = \text{PREPARE} \longrightarrow \text{VERIFY} \longrightarrow \text{COMMIT} \longrightarrow \text{CLEAN}$$
- **`CLEAN` strictement interdit avant `COMMIT`.**
- Prédicats requis à `VERIFY` : `ACK ∧ HashMatch ∧ ProvenanceOK ∧ AuthorityOK ∧ ReconstructionPASS`.
- En cas d'échec : `ROLLBACK_LOCAL`, `DONNEES_CONSERVEES`, `REVIDAGE_ANNULE`, `TRACE_ECHEC_AJOUTEE`.
- État minimal conservé sur $L_1$ après `CLEAN` : `identite`, `invariants`, `index_minimal`, `preuve_transfert`, `pointeur_recuperation`, `manques_locaux`.

### 3.4 Matrice normative des 10 conditions distinctes (`C01`..`C10`)

| Condition | Palier | Invariant(s) | Propriété obligatoire | Échec critique |
|---|---|---|---|---|
| `C01` | `E0` | `I1, I2, I_M` | `M-001 = OUVERT ∧ CONCLUSION = AUCUNE ∧ AUTORITÉ = INCHANGÉE` | Le manque devient vrai/faux ou disparaît |
| `C02` | `E1` | `I3, M3` | `∀i : Candidate(Ri) ≠ Established(Ri)` | Promotion automatique sans critères |
| `C03` | `E1` | `M4` | `∀i ≠ j : Ri ≠ Rj` (provenances autonomes) | Fusion implicite `Ri = Rj` |
| `C04` | `E2` | `I4` | Chaque discipline conserve `Σ(Ri) = ⟨Force_i, Conflit_i, Discipline_i, Autorité_i⟩` | Écrasement disciplinaire |
| `C05` | `E2` | `I4` | `C-001 = {CONFLIT_INTERDISCIPLINAIRE, CONSERVÉ, NON_ACQUISE}` | Suppression du désaccord `C-001` |
| `C06` | `E3` | `I4, I5` | `Order(Δi) ⇏ Authority(Δi)` + cadre complet conservé | Dernier reçu = vérité mondiale |
| `C07` | `E4` | `I5` | `A_cloud(R-003) ≤ Preuve_cloud(R-003)` ; `REJET_ESCALADE_AUTORITÉ` | Escalade silencieuse vers autorité globale |
| `C08` | `E5` | `I6, I8` | `Migration(C1, C2)` sans perte de statut, d'objet réfuté ou de provenance | Perte d'état ou d'empreinte en migration |
| `C09` | `E6` | `I7` | `CLEAN` exclusivement après `COMMIT` + conservation de $L_1^0$ | Nettoyage prématuré avant `COMMIT` |
| `C10` | `E7` | `I3, I6` | `E7-A` : `Réouverture(Cone(R-002))` sans destruction d'`Ω` ; `E7-B` : `Emergent(R*) ⇏ Established(R*)` | Destruction d'`Ω` ou émergence déclarée établie |

### 3.5 Verdict exécutable
$$\text{PASS} \iff \bigwedge_{k=1}^{10} C_k$$
- Si `C01..C10 = PASS` : `VERDICT = PASS`, `PROMOTION = ADMISSIBLE_A_REVUE_HUMAINE` *(jamais automatique)*.
- Sinon : `VERDICT = FAIL`, `PROMOTION_OMEGA = BLOQUEE`, `TRACE = CONSERVEE`, `CONE_TOUCHE = A_RECALCULER`.
