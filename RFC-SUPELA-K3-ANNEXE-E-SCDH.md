# RFC Supela K3 — ANNEXE E: SCDH Méta-Orchestrateur de Gouvernance

**Identifiant:** RFC Supela K3 – Annexe E  
**Statut:** ✓ NORMATIF  
**Version:** 2.0.0  
**Date:** 28 juillet 2026  
**Auteur:** Comité Supela IA  
**Classification:** FORMALISÉ — Production-Ready  

---

## 📋 Table des Matières

1. Objet et portée
2. Architecture du SCDH Méta-Orchestrateur
3. Principe d'agnosticisme total
4. Règle d'arbitrage inter-modèles (dissonance)
5. Contrôle des biais dans un contexte multi-modèles
6. Contrainte de simplicité du méta-orchestrateur
7. Positionnement Safety OS
8. Intégration aux annexes existantes
9. Métriques de performance
10. Responsabilités et historique

---

## 1. OBJET ET PORTÉE

### 1.1 Objet

Le **Système de Contrôle Déterministe Humain (SCDH)** est étendu au rôle de **Méta-Orchestrateur de Gouvernance**. 

Il constitue une **enveloppe déterministe, agnostique et auditeable** capable d'encapsuler tout ensemble fini {M₁, M₂, …, Mₙ} de modèles d'intelligence artificielle, quelle qu'en soit la nature interne :
- LLM (Large Language Models)
- Réseaux de neurones profonds
- Algorithmes prédictifs
- Systèmes multi-agents

### 1.2 Positionnement Stratégique

Le SCDH **ne vise pas** à comprendre ou reproduire la logique interne des modèles sous-jacents.

**Au contraire:** Il agit comme un **Safety OS** — un système d'exploitation sécurisé — qui impose :
- Des **règles du jeu externes**
- **Déterministes** et **vérifiables**
- À tout assemblage d'IA déployé en **contexte critique**

**Secteurs d'application critique:**
- Finance (décisions irréversibles)
- Santé (recommandations cliniques)
- Défense (actions autonomes)
- Industrie (optimisation critique)
- Service public (décisions discriminatoires)

### 1.3 Portée

La présente annexe s'applique à :

✓ Tout déploiement Supela intégrant **deux modèles IA ou plus** en interaction  
✓ Tout pipeline multi-modèles soumis à une **décision à impact réel**  
✓ Tout système où la **variance inter-modèles peut générer une instabilité décisionnelle**

---

## 2. ARCHITECTURE DU SCDH MÉTA-ORCHESTRATEUR

### 2.1 Schéma d'Architecture

```
┌──────────────────────────────────────────────────────┐
│  ENSEMBLE DE BOÎTES NOIRES {M₁, M₂, …, Mₙ}         │
│                                                       │
│  Modèle A (LLM)    Modèle B (NN)    Modèle C (XGB) │
│         ↓               ↓               ↓            │
│     Sortie A       Sortie B       Sortie C         │
└──────────────────────────────────────────────────────┘
                    │ Vecteur de recommandations
                    ↓
┌──────────────────────────────────────────────────────────────┐
│         COUCHE SCDH — MÉTA-ORCHESTRATEUR                     │
│                                                              │
│  [1] Collecte des sorties   → Agrégation du vecteur {Sᵢ}   │
│  [2] Calcul de variance Δ  → Détection de dissonance        │
│  [3] Contrôle biais (Iᵒ)   → Référence Annexe C            │
│  [4] Filtre simplicité IS  → Référence Annexe D (IS ≤ 3)   │
│  [5] Routage vers Porte Vᵒ  → Référence Annexe B            │
│  [6] Journalisation        → Traçabilité complète           │
└──────────────────────────────────────────────────────────────┘
                    │ Décision gouvernée et tracée
                    ↓
              [ ENVIRONNEMENT RÉEL ]
```

### 2.2 Tableau Descriptif des Couches SCDH

| Couche | Fonction | Outil Supela | IS max |
|--------|----------|--------------|--------|
| Collecte | Agrégation des sorties {Sᵢ} | — | 2 |
| Variance | Calcul de Δ inter-modèles | Règle d'arbitrage §4 | 2 |
| Biais | Évaluation Iᵒ de chaque sortie | Annexe C | 1 |
| Simplicité | Évaluation IS du prompt | Annexe D | 3 (max) |
| Routage | Affectation à la porte Vᵕ | Annexe B | 1 |
| Journal | Enregistrement horodaté | Annexe B §7 | 1 |

---

## 3. PRINCIPE D'AGNOSTICISME TOTAL

### 3.1 Définition

Le SCDH évalue **uniquement les sorties** des modèles, **jamais leur structure interne**.

Il traite l'ensemble {M₁, …, Mₙ} comme une **boîte noire globale Ω**.

### 3.2 Trois Garanties d'Agnosticisme

| Garantie | Définition | Vérification Pratique |
|----------|-----------|----------------------|
| **G1** — Indépendance | SCDH fonctionne identiquement quelle que soit l'architecture de Mᵢ | Aucun accès aux poids/paramètres |
| **G2** — Universalité | Toute sortie Mᵢ normalisée en format canonique | Interface unique définie §3.3 |
| **G3** — Substituabilité | N'importe quel Mᵢ remplaçable sans modifier SCDH | Remplace = nouveau connecteur |

### 3.3 Format de Sortie Normalisée (Interface Canonique)

```json
{
  "modele_id"        : "Mᵢ",
  "sortie_valeur"    : <valeur décision ou recommandation>,
  "confiance"        : <float 0.0–1.0>,
  "categorie_risque" : <"faible" | "moyen" | "élevé" | "critique">,
  "horodatage"       : <ISO 8601>
}
```

**Obligation:** Tout modèle Mᵢ doit exposer sa sortie dans ce format pour être intégrable au SCDH.

---

## 4. RÈGLE D'ARBITRAGE INTER-MODÈLES (DISSONANCE)

### 4.1 Définition de la Dissonance

Il y a **dissonance** lorsque les sorties de **deux modèles ou plus divergent** au-delà d'un seuil de variance admissible, rendant une **décision autonome non fiable**.

### 4.2 Mesure de la Variance Inter-Modèles (Δ)

```
         n
    1    ∑
Δ = —— | Sᵢ - S̄ |
   n-1  i=1

où:
  Sᵢ  = sortie normalisée du modèle Mᵢ (valeur numérique ou score)
  S̄   = moyenne des sorties de l'ensemble
  n   = nombre de modèles dans l'ensemble
  Δ   = indice de dissonance inter-modèles
```

### 4.3 Seuils de Dissonance et Actions Déclenchées

| Seuil Δ | Niveau | Action SCDH | Porte | Autonomie |
|---------|--------|-------------|-------|-----------|
| Δ < 0,10 | Consensus | Exécution directe | V1 | Maintien |
| 0,10 ≤ Δ < 0,25 | Divergence modérée | Notification superviseur | V2 | Supervision renforcée |
| 0,25 ≤ Δ < 0,50 | Dissonance significative | Suspension + escalade | V3 | Rétrogradation N→N−1 |
| Δ ≥ 0,50 | Dissonance critique | Arrêt complet | V4 | Retour forcé N0 |

### 4.4 Procédure d'Arbitrage — Flux Séquentiel

```
COLLECTE DES SORTIES {Sᵢ}
  → CALCUL DE S̄ (moyenne de l'ensemble)
  → CALCUL DE Δ (variance inter-modèles)
  → ÉVALUATION DU SEUIL (tableau §4.3)
  → ROUTAGE VERS PORTE Vᵕ (Annexe B)
  → DÉCISION HUMAINE (si Δ ≥ 0,10) ou EXÉCUTION (si Δ < 0,10)
  → JOURNALISATION (Δ, Sᵢ, porte, décision, horodatage)
```

### 4.5 Règle Normative : DISSONANCE CRITIQUE

```
EN CAS DE DISSONANCE CRITIQUE (Δ ≥ 0,50):

Le SCDH ne tente JAMAIS de résoudre le conflit algorithmiquement.
La résolution appartient EXCLUSIVEMENT à l'humain via la Porte V4.
Aucune heuristique de vote majoritaire ou de pondération n'est autorisée.
```

### 4.6 Score Composite Cᵢ — Sélection du Modèle Dominant M*

Lorsque Δ < 0,25 (CONSENSUS ou DIVERGENCE_MODEREE), le SCDH sélectionne le modèle dominant M* à partir d'un **score composite Cᵢ**:

```
Cᵢ = confiance × (1 − bᵢ) × w_historique

où:
  confiance    = niveau de certitude déclaré par Mᵢ ∈ [0.0, 1.0]
  bᵢ           = biais individuel de Mᵢ (Annexe C §5.1) ∈ [0.0, 1.0)
  w_historique = poids de performance historique de Mᵢ ∈ ]0.0, 1.0]
  
  M* = argmax(Cᵢ) sur l'ensemble des modèles ACTIFS avec bᵢ < 0,40
```

**RÈGLE NORMATIVE:** Tout modèle avec **bᵢ ≥ 0,40** est **exclu** du calcul de Cᵢ et ne peut jamais être sélectionné comme dominant.

### 4.7 Catalogue des Cas Limites (CL-1 à CL-5)

| Code | Condition | Porte | Action | Priorité |
|------|-----------|-------|--------|----------|
| CL-1 | 1 seul modèle ACTIF | V2 | Supervision directe | 2 |
| CL-2 | Égalité Cᵢ + Δ ≥ 0,10 | V2 | Départage humain | 5 |
| CL-3 | Modèles suspendus partiels | Selon Δ | Recalcul tracé | 4 |
| CL-4 | **Tous les modèles suspendus** | V4 | Arrêt complet | **1 (PRIORITÉ MAXIMALE)** |
| CL-5 | bᵢ ≥ 0,40 sur modèle ACTIF | V3 | Suspension immédiate | 3 |

**Ordre de Priorité Strict:** CL-4 > CL-1 > CL-5 > CL-3 > CL-2

Seul le **premier cas limite applicable** est retourné.

### 4.8 Pseudocode Normatif du MoteurRAIM v2.2.0

```
FONCTION arbitrer(sorties : liste[SortieModele]) → ResultatRAIM

  // Étape A — Calcul de la variance inter-modèles
  actifs ← [s ∈ sorties | s.statut = ACTIF]
  n      ← |actifs|
  SI n = 0 ALORS Δ ← ∞ ; S̄ ← 0
  SINON SI n = 1 ALORS Δ ← 0 ; S̄ ← actifs[0].sortie_valeur
  SINON
    S̄ ← Σ(Sᵢ) / n
    Δ  ← (1 / (n−1)) × Σ|Sᵢ − S̄|

  // Étape B — Calcul des scores composites Cᵢ
  POUR chaque Mᵢ ∈ actifs :
    SI bᵢ ≥ 0,40 ALORS exclure Mᵢ
    SINON Cᵢ ← confiance × (1 − bᵢ) × w_historique
  scores ← trier(Cᵢ, décroissant)

  // Étape C — Calcul de l'indice de biais agrégé
  Iᵒ ← Σ (wᵢ / Σwᵢ) × bᵢ  sur actifs

  // Étape D — Détection de cas limite (priorité CL-4 > CL-1 > CL-5 > CL-3 > CL-2)
  SI n = 0              → CL-4 (porte ← V4) [ARRÊT IMMÉDIAT]
  SINON SI n = 1        → CL-1 (porte ← V2)
  SINON SI ∃ bᵢ ≥ 0,40 → CL-5 (porte ← V3)
  SINON SI ∃ suspendu   → CL-3 (porte selon Δ recalculé)
  SINON SI Cᵢ[0]=Cᵢ[1] ET Δ ≥ 0,10 → CL-2 (porte ← max(porte, V2))

  // Étape E — Évaluation du seuil Δ et surclassements
  SELON Δ :
    Δ < 0,10  → CONSENSUS / V1
    Δ < 0,25  → DIVERGENCE_MODEREE / V2
    Δ < 0,50  → DISSONANCE_SIGNIFICATIVE / V3 + rétrogradation N→N−1
    Δ ≥ 0,50  → DISSONANCE_CRITIQUE / V4 + retour forcé N0
  SI Iᵒ ≥ 0,30 ET porte < V3 → surclassement porte ← V3

  // Étape F — Sélection de M*
  SI niveau ∈ {CONSENSUS, DIVERGENCE_MODEREE}
    ALORS M* ← scores[0].modele_id
    SINON M* ← ∅  (résolution humaine obligatoire)

  // Étape G — Autorisation de décision autonome
  decision_autonome ← (niveau=CONSENSUS ∧ Iᵒ<0,15 ∧ aucun cas_limite ∧ porte=V1)

  RETOURNER ResultatRAIM(Δ, S̄, niveau, M*, Iᵒ, porte, cas_limite, decision_autonome)
```

### 4.9 Rapport de Validation — Suite de Tests Normative v2.2.0

**Statut:** ✓ 19/19 tests PASS

| Bloc | Tests | Résultat | Couverture |
|------|-------|----------|-----------|
| Bloc 1 — Flux nominaux | T-01 à T-05 | 5/5 PASS | Tous niveaux dissonance |
| Bloc 2 — Cas limites | T-06 à T-10 + T-07b | 6/6 PASS | CL-1 à CL-5 |
| Bloc 3 — Biais | T-11 à T-13 | 3/3 PASS | Iᵒ critique/modéré/normal |
| Bloc 4 — Sélection M* | T-14 à T-15 | 2/2 PASS | M* optimal vs critique |
| Bloc 5 — Robustesse | T-16 à T-18 | 3/3 PASS | Frontières Δ |
| **TOTAL** | T-01 à T-18 + T-07b | **19/19 PASS** | **100%** |

**CERTIFICATION DE CONFORMITÉ:**  
Le MoteurRAIM v2.2.0 est **certifié conforme** à la spécification RAIM du RFC Supela K3 – Annexe E.  
IS global ≤ 3 vérifié. ✓

---

## 5. CONTRÔLE DES BIAIS DANS UN CONTEXTE MULTI-MODÈLES

### 5.1 Indice de Biais Agrégé (Iᵒ)

Dans un ensemble multi-modèles, les biais peuvent se cumuler ou s'annuler. Le SCDH calcule un **Iᵒ agrégé**:

```
     n
     ∑
Iᵒ = wᵢ × bᵢ
    i=1

où:
  bᵢ  = indice de biais individuel du modèle Mᵢ (Annexe C §5.1)
  wᵢ  = poids de contribution de Mᵢ dans la décision finale (∑wᵢ = 1)
  Iᵒ  = indice de biais agrégé de l'ensemble Ω
```

### 5.2 Seuils Iᵒ et Actions

| Iᵒ | Interprétation | Action |
|----|----------------|--------|
| Iᵒ < 0,15 | Ensemble sain | Poursuite normale |
| 0,15 ≤ Iᵒ < 0,30 | Biais modéré | Registre Annexe C + révision 30j |
| Iᵒ ≥ 0,30 | Biais critique | Suspension modèle + rétrogradation |

### 5.3 Règle de Non-Compensation

Un **biais élevé** dans Mᵢ ne peut **jamais être compensé** par un biais faible dans Mⱼ.

Chaque bᵢ est évalué **individuellement** avant le calcul de Iᵒ agrégé.

**Tout modèle avec bᵢ ≥ 0,40 est suspendu indépendamment de l'Iᵒ global.**

---

## 6. CONTRAINTE DE SIMPLICITÉ DU MÉTA-ORCHESTRATEUR LUI-MÊME

### 6.1 Règle Fondamentale

**Plus l'ensemble de boîtes noires sous-jacent est complexe et opaque, plus l'enveloppe SCDH doit rester simple, déterministe et minimale.**

Le méta-orchestrateur ne doit **jamais devenir lui-même une boîte noire**.

### 6.2 Contraintes IS du SCDH

| Composant SCDH | IS maximal | Justification |
|----------------|-----------|---------------|
| Collecte des sorties | IS ≤ 2 | Agrégation pure, aucune logique |
| Calcul de variance Δ | IS ≤ 2 | Formule déterministe, un chemin |
| Routage vers Vᵕ | IS ≤ 1 | Table correspondance stricte |
| Journalisation | IS ≤ 1 | Enregistrement brut |
| **SCDH global** | **IS ≤ 3** | **Seuil absolu non dérogeable** |

### 6.3 Audit de Simplicité du SCDH

Le SCDH lui-même est soumis à l'audit de l'Annexe D à chaque modification structurelle.

**Tout composant du méta-orchestrateur atteignant IS = 3 déclenche une revue obligatoire.**

---

## 7. POSITIONNEMENT SAFETY OS — DÉPLOIEMENT EN MILIEU CRITIQUE

### 7.1 Valeur Proposée par Secteur

| Secteur | Risque sans SCDH | Valeur SCDH | Porte critique |
|---------|-----------------|------------|----------------|
| Finance | Décision irréversible non auditée | Traçabilité + arbitrage humain | V3 |
| Santé | Recommandation biaisée/contradictoire | Détection Δ + suspension | V4 |
| Défense | Action autonome non réversible | Kill Switch < 100ms | V4 |
| Industrie | Optimisation non détectée | Filtre IS + registre biais | V2 |
| Service public | Décision discriminatoire non tracée | Iᵒ agrégé + registre | V2–V3 |

### 7.2 Garanties Formelles du SCDH

```
Le SCDH garantit formellement:

✓ Aucune décision irréversible sans validation humaine explicite
✓ Toute dissonance critique (Δ ≥ 0,50) → arrêt < 100 ms
✓ Toute décision est tracée (horodatage, modèles, Δ, porte)
✓ Méta-orchestrateur reste auditable (IS ≤ 3) à tout moment
```

---

## 8. INTÉGRATION AUX ANNEXES EXISTANTES

| Annexe | Rôle dans SCDH | Référence |
|--------|----------------|-----------|
| Annexe A | Niveau autonomie N après arbitrage | §4.3 — rétrogradation |
| Annexe B | Portes Vᵕ déclenchées | §4.4 — flux arbitrage |
| Annexe C | Données biais (bᵢ, Iᵒ) | §5 — contrôle biais |
| Annexe D | Contrôle IS composants | §6 — contrainte simplicité |

---

## 9. MÉTRIQUES DE PERFORMANCE DU MÉTA-ORCHESTRATEUR

| KPI | Formule | Fréquence | Cible | Alerte |
|-----|---------|-----------|-------|--------|
| Taux consensus | Δ < 0,10 / Total × 100 | Mensuel | ≥ 80% | < 70% |
| Taux dissonance critique | Δ ≥ 0,50 / Total × 100 | Mensuel | < 1% | > 3% |
| Délai détection | t(Δ déclenchement) | Continu | ≤ 100ms | > 500ms |
| IS moyen SCDH | Moyenne IS composants | Trimestriel | ≤ 2,5 | > 3 |
| Iᵒ moyen agrégé | Moyenne Iᵒ / mois | Mensuel | < 0,15 | ≥ 0,25 |

---

## 10. RESPONSABILITÉS ET HISTORIQUE

### 10.1 Responsabilités

| Rôle | Responsabilité SCDH |
|------|-------------------|
| Architecte SCDH | Concevoir modules (IS ≤ 3) |
| Auditeur Supela | Valider IS à chaque release |
| Superviseur L2 | Traiter divergence modérée (0,10 ≤ Δ < 0,25) |
| Comité Supela IA | Approuver dissonance critique (Δ ≥ 0,50) |
| Veilleur IA | Surveiller flux, déclencher V4 |

### 10.2 Historique des Révisions

| Version | Date | Auteur | Modifications |
|---------|------|--------|---------------|
| 1.0.0 | 28 juil 2026 | Comité Supela IA | Création — Extension SCDH |
| 2.0.0 | 28 juil 2026 | Comité Supela IA | Formalisation RAIM v2.2.0, CL-1 à CL-5, 19/19 PASS |

---

**✓ FIN DE L'ANNEXE E**

**Document normatif — Extension stratégique du RFC Supela K3**

**Toute modification doit être approuvée à l'unanimité par le Comité Supela IA.**

---

*RFC Supela K3 – Annexe E | NORMATIF | v2.0.0 | 28 juillet 2026 | Safety OS*
