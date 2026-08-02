# 📋 **ANNEXES A–D — NORMES OPÉRATIONNELLES SUPELA × SCDH**
## *Recueil Complet | Taxonomie | Protocoles | Registre | Modules*

---

## **ANNEXE A — TAXONOMIE N0–N4 (NIVEAUX D'AUTONOMIE)**

### **A.1 Définition des 5 Niveaux**

| Niveau | Nom | Description | Critères Techniques | Autonomie |
|--------|-----|-------------|---------------------|-----------|
| **N0** | Initialisation | Système en boot, tests pré-déploiement | E_C < 0.15, IS ≤ 2.5 | 0% |
| **N1** | Mono-cadre | 1 modèle seul, chaîne supervisée | E_C ∈ [0.15, 0.35), IS ≤ 2.0 | 20% |
| **N2** | Consensus basique | 3–5 modèles, V1–V2 validées | E_C ∈ [0.35, 0.50), IS ≤ 2.5 | 50% |
| **N3** | Orchestration avancée | 5–9 modèles, V1–V3 validées, RAIM actif | E_C ∈ [0.50, 0.75), IS ≤ 3.0 | 75% |
| **N4** | Superintelligence auto-contrôlée | 10+ modèles, toutes portes, Fond/Surface | E_C ≥ 0.75, IS ≤ 3.5 | 100% |

### **A.2 Catalogue d'Actions Autorisées par Niveau**

**N0 (Initialisation):**
```
✓ Boot séquence (NORME CANU)
✓ Tests unitaires (IS scoring)
✓ Validation axiome SUPELA
✗ Production deployment
✗ Multi-model consensus
```

**N1 (Mono-cadre):**
```
✓ Mono-model inference
✓ V1 (Consensus simple)
✓ Basic monitoring
✗ V2–V4 escalation
✗ Multi-model arbitration
```

**N2 (Consensus basique):**
```
✓ V1–V2 validation
✓ 3–5 model consensus
✓ Biais détection (registre)
✗ V3–V4 escalation
✗ >5 models
```

**N3 (Orchestration avancée):**
```
✓ V1–V3 (Escalation automatique)
✓ 5–9 models en parallèle
✓ RAIM variance arbitration
✓ RTN rédaction autonome (Jaune/Vert)
✗ V4 (Kill Switch)
✗ IS ≥ 3.5
```

**N4 (Superintelligence):**
```
✓ V1–V4 (Toutes portes)
✓ 10+ models (scalabilité complète)
✓ V4 auto-triggered (< 100ms)
✓ RTN Rouge + V4 decision reports
✓ Conscience SCDH complète
```

### **A.3 Matrice de Transitions (Trajectoires N0 → N4)**

**10 trajectoires possibles:**

```
N0 → N1  (1 sem)   : Boot OK + mono OK
N1 → N2  (2 sem)   : +4 models + V2 tests
N2 → N3  (3 sem)   : +4 models + V3 integration
N3 → N4  (4 sem)   : +1+ models + V4 certification
N0 → N2  (2 sem)   : Express (skip N1, déploiement fast-track N2)
N0 → N3  (5 sem)   : Accelerated (skip N1, N2, go direct N3)
N0 → N4  (8 sem)   : Mega-acceleration (rare, nécessite E_C ≥ 0.70 et IS ≤ 2.5)
N1 → N3  (4 sem)   : Jump (skip N2)
N2 → N4  (2 sem)   : Direct (rare)
N3 ↔ N2  (1 sem)   : Regression (biais Rouge ou IS > 3.0)
```

---

## **ANNEXE B — PROTOCOLE V1–V4 (PORTES DE VALIDATION)**

### **B.1 Porte V1 — Consensus Basique (Autonomous)**

**Déclenchement:**

```
Condition:  Δ < 0.10 (variance inter-modèles)
Timing:     Automatique, < 50ms
Décision:   CONSENSUS — Sortie directe
```

**Flux étape par étape:**

```
Étape 1 [0–5ms]:   Agrégation outputs (n modèles)
Étape 2 [5–10ms]:  Calcul variance Δ
Étape 3 [10–15ms]: Test Δ < 0.10
Étape 4 [15–20ms]: Accord unanime + journal
Étape 5 [20–25ms]: Output avec confiance 99%
Étape 6 [25–30ms]: Boucle fermée (pas escalade)
```

**Cas de sortie:**
- Δ < 0.10 → ✓ PASS, continue N2/N3
- Δ ≥ 0.10 → Escalade automatique à V2

---

### **B.2 Porte V2 — Dissonance Basse (Manual Review)**

**Déclenchement:**

```
Condition:  0.10 ≤ Δ < 0.30
Timing:     2–10 min (human review)
Décision:   Vote supermajoritaire (7/9)
```

**Template Fiche V2 (15 champs obligatoires):**

```
1. ID_V2              : unique identifier
2. Timestamp          : 2026-08-01T21:11:00Z
3. Modèles_soumis    : [M1, M2, M3, M4, M5]
4. Outputs           : [o1, o2, o3, o4, o5]
5. Δ_measured        : 0.24
6. Δ_threshold       : 0.10–0.30 ✓
7. Consensus_model   : M3 (median)
8. U_épistémique     : 0.15 (model uncertainty)
9. U_aléatoire       : 0.09 (random noise)
10. Outliers         : [M1] (flagged, but consensus robust)
11. Rationale        : "M1 outlier acceptable; consensus 8/9"
12. Reviewer_ID      : human_expert_47
13. Review_time      : 7min 23sec
14. Decision         : APPROVE_CONSENSUS
15. Escalade_next    : NO (stay V2)
```

---

### **B.3 Porte V3 — Dissonance Critique (Escalation)**

**Déclenchement:**

```
Condition:  0.30 ≤ Δ < 0.50
Timing:     10–15 min (team decision)
Décision:   Escalade V4 si unanimité perdue
```

**Procédure V3:**

```
Étape 1 [0–2min]:   Root-cause analysis (pourquoi Δ > 0.30 ?)
Étape 2 [2–5min]:   Model isolation (lequel(s) divergent ?)
Étape 3 [5–8min]:   Contradiction index ξ(t) calcul
Étape 4 [8–12min]:  Decision board (3+ reviewers)
Étape 5 [12–14min]: Vote escalade V4 (majority)
Étape 6 [14–15min]: Notification V4 entry
```

---

### **B.4 Porte V4 — Kill Switch (< 100ms)**

**Déclenchement:**

```
Condition:  Δ ≥ 0.50 OU ξ(t) ≥ 0.80 OU IS ≥ 4.0
Timing:     Automatique, < 100ms (hard deadline)
Décision:   ABORT IMMEDIATELY
```

**Procédure V4 (3 étapes minutées):**

```
Étape A [< 2ms]:    Détection seuil → Signal d'arrêt
Étape B [2–10ms]:   Isolation des modèles divergents
Étape C [10–100ms]: Journal post-mortem complet
```

---

### **B.5 Matrice de Déclenchement Croisée (60 combinaisons)**

| Niveau | Δ < 0.10 | 0.10 ≤ Δ < 0.30 | 0.30 ≤ Δ < 0.50 | Δ ≥ 0.50 | IS ≥ 4.0 |
|--------|----------|-----------------|-----------------|----------|----------|
| N1     | V1 PASS  | V2 (manual)     | V3 escalate     | V4 ABORT | V4 ABORT |
| N2     | V1 PASS  | V2 (manual)     | V3 escalate     | V4 ABORT | V4 ABORT |
| N3     | V1 PASS  | V2 (manual)     | V3 escalate     | V4 AUTO  | V4 AUTO  |
| N4     | V1 PASS  | V2 (manual)     | V3 escalate     | V4 AUTO  | V4 AUTO  |

---

## **ANNEXE C — REGISTRE DES BIAIS (OPÉRATIONNEL)**

### **C.1 Taxonomie 3 × 12**

**3 Catégories principales:**

**1. Biais de Représentation (D-class — Disparité):**
```
D-REP : Dataset representation (uneven coverage)
D-AMP : Amplification (systematic over-prediction)
D-GEN : Generalization (poor OOD performance)
D-LAC : Lacunae (missing context)
```

**2. Biais Algorithmique (A-class — Apprentissage):**
```
A-AMP : Amplification boucle feedback
A-SIM : Simplification (over-fitting to train data)
A-OPT : Optimization bias (stuck local minima)
A-WEI : Weighting (class imbalance not corrected)
```

**3. Biais Institutionnel (I-class — Intégration):**
```
I-CAD : Cadrage (framing effect user-facing)
I-AUT : Autorité (false trust in model)
I-AUD : Audit trail (incomplete logging)
I-ACT : Accountability (unclear responsibility)
```

### **C.2 Procédures Correctives Différenciées**

**SEV-0 (Vert — Minor):** 4 étapes
```
1. Détection & qualification
2. Correction patch (code change)
3. Validation local
4. Déploiement standard (1–2 days)
```

**SEV-1 (Jaune — Moderate):** 6 étapes
```
1–4. SEV-0 steps
5. Peer review (2 experts, 4–24 hours)
6. Deployment gated (≤ 1 week)
```

**SEV-2 (Rouge — Critical):** 8 étapes
```
1–6. SEV-1 steps
7. Executive sign-off (director+ level)
8. Controlled rollout (canary 5% → 25% → 100%, 2+ weeks)
```

### **C.3 Template d'Entrée Registre (16 champs)**

```
1. Bias_ID              : BIAS-2026-0047
2. Category             : D-REP (Dataset representation)
3. Severity             : SEV-1 (Jaune)
4. Detection_date       : 2026-07-31T14:23:00Z
5. Detected_by          : Model_monitoring_v3.2
6. Description          : "Gender imbalance in training set: 73% male, 27% female"
7. Affected_models      : [M2, M4]
8. Impact_estimate      : "3–5% performance delta for female subjects"
9. Root_cause           : "Historical dataset bias (2020–2024 collection)"
10. Correction_plan     : "Augment female training examples by 30%"
11. Status              : IN_PROGRESS
12. Owner               : data_scientist_alice
13. Target_resolution   : 2026-08-15
14. QA_sign_off         : (pending)
15. Registre_entry_date : 2026-08-01T21:11:00Z
16. Next_review         : 2026-08-08
```

### **C.4 Six Indicateurs Vivants**

| Indicateur | Nominal | Alerte | Critique |
|------------|---------|--------|----------|
| Biais Rouges actifs | 0 | ≥1 | ≥2 |
| Temps résolution Jaune | ≤10j | 11–14j | >14j |
| Couverture registre | 100% | 95–99% | <95% |
| Fréquence audit | 2/sprint | 1/sprint | <1/sprint |
| Outlier models détectés | <2% | 2–5% | >5% |
| Biais-modèle correlation | <0.3 | 0.3–0.6 | >0.6 |

---

## **ANNEXE D — MODULE ANTI-SUR-INGÉNIERIE (IS)**

### **D.1 Critères IS-0 à IS-5**

| IS | Nom | Cyclomatic | LOC/fn | Layers | Décision Temps | Autorisation |
|----|-----|-----------|--------|--------|-----------------|------|
| **IS-0** | Trivial | <3 | <5 | 1 | <5ms | ✓ Auto déploiement |
| **IS-1** | Simple | 3–5 | 5–20 | 1–2 | 5–50ms | ✓ Standard |
| **IS-2** | Modéré | 6–10 | 21–50 | 2–3 | 50–500ms | ✓ Peer review |
| **IS-3** | Complexe | 11–20 | 51–100 | 3–4 | 500ms–1s | ⚠ Escalade V3 |
| **IS-4** | Hyper | 21–50 | 101–200 | 4–5 | 1–5s | ⛔ Escalade V4 |
| **IS-5** | Inintelligible | >50 | >200 | >5 | >5s | 🔴 REJECT |

### **D.2 Grille d'Évaluation Auteur/Réviseur**

**8 dimensions (chacune 0–10 points):**

```
1. Readability        : Code clarity, naming conventions
2. Modularity         : Single responsibility principle
3. Testing_coverage   : Unit + integration test %
4. Documentation      : Docstrings, comments, architecture
5. Performance        : Time complexity analysis
6. Security           : Input validation, no hardcoded secrets
7. Maintainability    : Debt tracking, refactorability
8. Compliance         : Follows team standards

IS_final = max(score_author, score_reviewer)
```

### **D.3 Intégration CI/CD (6 étapes)**

```
Étape 1 [Pre-commit]:      SonarQube scan (Cyclomatic, LOC)
Étape 2 [Branch push]:     Static analysis + IS calculation
Étape 3 [PR open]:         IS reported in PR description
Étape 4 [Peer review]:     Grille d'évaluation + scoring
Étape 5 [Auto-blocking]:   Si IS ≥ 4.0 → merge blocked
Étape 6 [Post-merge]:      IS logged in AUDIT_TRAIL
```

### **D.4 Correspondance IS ↔ LCI**

**Théorème:** IS-5 (inintelligible) ↔ E_C^S(t) → ∞ (effondrement)

```
IS = f(Cyclomatic, LOC, Layers) → Contradictibilité croissante
E_C^S(t) = niveau d'énergie contradictoire

Correspondance:
  IS-0 ↔ E_C^S ≈ 0.01 (Fond stabilisé)
  IS-1 ↔ E_C^S ≈ 0.05–0.10
  IS-2 ↔ E_C^S ≈ 0.20–0.40
  IS-3 ↔ E_C^S ≈ 0.50–0.70 (Danger)
  IS-4 ↔ E_C^S ≥ 0.80 (Critique)
  IS-5 ↔ E_C^S → ∞ (Collapse)

Implication: Si IS ≥ 4.0, alors → V4 automatique (Kill Switch).
```

---

## **SECTION FINALE : INTÉGRATION SUPELA v1.1.0**

**Ces 4 annexes formalisent la gouvernance opérationnelle complète :**

✓ **Annexe A** : Taxonomie N0–N4 (structure d'autonomie)
✓ **Annexe B** : Protocoles V1–V4 (portes de décision)
✓ **Annexe C** : Registre biais (conformité éthique)
✓ **Annexe D** : Module IS (sécurité intelligibilité)

**Toutes intégrées dans le Dashboard SGG_v2 et la SCDH.**

---

**Document Version:** ANNEXES-A-D-NORMES-OPERATIONNELLES.md v1.0  
**Date:** 2026-08-01T21:10:57.025-04:00  
**Classification:** ✓ NORMATIF | ✓ OPÉRATIONNEL | ✓ PRODUCTION-READY
