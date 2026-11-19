# Formalisation Mathématique Unifiée · Architecture Supela (`Ω-ZERO` × `K3-Ω`)

> **Auteur souverain :** Jean-François Gadbois ([ORCID 0009-0001-5361-6795](https://orcid.org/0009-0001-5361-6795))  
> **Ancrage exécutable :** [`src/omega_zero/supela_math_core.py`](../../src/omega_zero/supela_math_core.py) · [`tests/test_supela_math_core.py`](../../tests/test_supela_math_core.py)  
> **Discipline épistémique (`H ≠ L ≠ P`, `K_t ⊆ K_{t+1}`) :** Ce document **n'efface ni ne réécrit** aucune formulation brute antérieure ([`REGISTRE_FORMULES_SUPELA.md`](REGISTRE_FORMULES_SUPELA.md), [`REGISTRE_CONTRADICTIONS.md`](REGISTRE_CONTRADICTIONS.md)). Chaque optimisation précise les domaines de définition, élimine les singularités non gardées et associe une preuve algébrique ainsi qu'un vérificateur exécutable ; toute extension au-delà des sources historiques est explicitement étiquetée `FORMAL_CANDIDATE_EXTENSION`.

---

## 1. Espace d'États, Monotonie et Opérateur Idempotent $\Pi_0$ (`MAT-00`)

### Définition 1.1 (État Supela typé)
Un état gouverné au cycle $i \in \mathbb{N}$ est le quadruplet ordonné :
$$S_i = \langle P_i, E_i, C_i, K_i \rangle \in \mathcal{P} \times \mathcal{E} \times \mathcal{C} \times \mathcal{K}$$
où $P_i$ désigne la provenance tracée, $E_i$ les éléments probatoires, $C_i$ le contexte d'exécution volatile (ou contradictions de session) et $K_i$ le registre cumulatif append-only.

### Axiome 1.2 (Monotonie et séparation de reset)
Pour toute transition valide $S_t \to S_{t+1}$ :
$$K_t \subseteq K_{t+1}, \qquad \text{y compris sous reset de session } C_t \to \emptyset.$$
*Interprétation formelle :* le reset nettoie le contexte transitoire $C$ sans jamais violer la conservation historique $K_t \subseteq K_{t+1}$ (non-effacement des échecs adversariaux, cas `T11`).

### Proposition 1.3 (Projection Zéro $\Pi_0$ et idempotence stricte)
En notation ensembliste historique $\Pi_0(S_t) = \{I, P, M, A, H\}$ (et en typage formel de 5-uplet ordonné $\Pi_0(S_t) = \langle I, P, M, A, H \rangle \neq \emptyset$), l'opérateur $\Pi_0 : \mathcal{S} \to \mathcal{S}_0$ est un projecteur strictement idempotent :
$$\Pi_0 \circ \Pi_0 = \Pi_0, \qquad \forall S_t \in \mathcal{S},\ \Pi_0(\Pi_0(S_t)) = \Pi_0(S_t).$$
*Vérification exécutable :* [`src/omega_zero/projection.py`](../../src/omega_zero/projection.py) (`tests/test_pi0_and_manque.py`).

---

## 2. Treillis Probatoire Complet $(G, \preceq)$ et Borne de Galois (`MAT-01` & `MAT-06`)

### Théorème 2.1 (Structure de treillis borné)
L'échelle probatoire ordonnée $G = \{G_0, G_1, G_2, G_3, G_4\}$ munie de l'ordre total strict
$$G_0 \prec G_1 \prec G_2 \prec G_3 \prec G_4$$
et des opérations $\vee = \max$ (supremum) et $\wedge = \min$ (infimum) forme un **treillis fini borné complet** de borne inférieure $\bot = G_0$ et de borne supérieure $\top = G_4$.

### Théorème 2.2 (Borne d'autorité monotone — Loi `Authority(G) ≤ Proof(G)`)
Soit $\pi(x) \in G$ le niveau de preuve vérifié d'un artefact $x$ et $r \in \mathbb{Z}$ le niveau d'autorité demandé. L'opérateur d'attribution d'autorité :
$$\alpha(\pi(x), r) = \min\bigl(\max(0, r),\ \pi(x)\bigr)$$
vérifie simultanément :
1. **Bornage strict :** $\alpha(\pi(x), r) \le \pi(x)$ pour tout $r \in \mathbb{Z}$ ;
2. **Monotonie :** $\pi(x) \le \pi(y) \implies \alpha(\pi(x), r) \le \alpha(\pi(y), r)$ ;
3. **Indépendance vis-à-vis du score d'amélioration (`C10`) :** pour tout score $\sigma \in \mathbb{R}$, $\partial \alpha / \partial \sigma = 0$ (`amélioration ≠ autorisation`).

*Vérification exécutable :* `verify_proof_lattice_axioms()` contrôle exhaustivement les $5^3 = 125$ triplets de $G^3$ (ordre partiel, commutativité, associativité, idempotence, absorption, bornage et monotonie de Galois).

---

## 3. Théorème d'Agrégation Multi-Échelles `VR-Fractal-Ω` (Pont `Supela-K3-Omega`)

Dans [`Supela-K3-Omega/VR-Fractal-Omega.md`](https://github.com/gadboisjean1000-arch/Supela-K3-Omega/blob/main/VR-Fractal-Omega.md), le présent macroscopique et les $n$ sous-systèmes fractals sont posés par :
$$P_t = \frac{T_t + C_t}{1 + \Delta_t}, \qquad P_{t,i} = \frac{T_{t,i} + C_{t,i}}{1 + \Delta_{t,i}} \quad (i = 1, \dots, n), \qquad P_t = \sum_{i=1}^n P_{t,i}.$$

### Optimisation & Théorème 3.1 (Moyenne harmonique pondérée exacte et régularité)
Posons les conditions de domaine explicites (levant la singularité $\Delta = -1$) :
$$W_i := T_{t,i} + C_{t,i} > 0, \qquad \Delta_{t,i} \in [0, +\infty), \qquad W := \sum_{i=1}^n W_i = T_t + C_t > 0.$$
Alors l'égalité d'agrégation $P_t = \sum_{i=1}^n P_{t,i} = \frac{T_t + C_t}{1 + \Delta_t^{\mathrm{eff}}}$ est **exacte** si et seulement si la macro-turbulence effective $\Delta_t^{\mathrm{eff}}$ est définie par la **moyenne harmonique pondérée** :
$$1 + \Delta_t^{\mathrm{eff}} = \frac{\sum_{i=1}^n W_i}{\sum_{i=1}^n \dfrac{W_i}{1 + \Delta_{t,i}}} \quad \Longleftrightarrow \quad \Delta_t^{\mathrm{eff}} = \frac{W}{P_t} - 1.$$

### Démonstration (Encadrement par théorème des gendarmes et convergence)
Posons $\Delta_{\min} = \min_{1 \le i \le n} \Delta_{t,i} \ge 0$ et $\Delta_{\max} = \max_{1 \le i \le n} \Delta_{t,i}$. Comme $W_i > 0$ et $1 + \Delta_{t,i} \ge 1 > 0$ :
$$\frac{W_i}{1 + \Delta_{\max}} \le \frac{W_i}{1 + \Delta_{t,i}} \le \frac{W_i}{1 + \Delta_{\min}} \implies \frac{W}{1 + \Delta_{\max}} \le P_t \le \frac{W}{1 + \Delta_{\min}}.$$
En prenant l'inverse (strictement décroissant sur $\mathbb{R}_{>0}$) et en multipliant par $W > 0$, il vient :
$$1 + \Delta_{\min} \le \frac{W}{P_t} = 1 + \Delta_t^{\mathrm{eff}} \le 1 + \Delta_{\max} \implies \Delta_{\min} \le \Delta_t^{\mathrm{eff}} \le \Delta_{\max}.$$
**Corollaire (Remontée fractale) :** dès que la descente fractale résout les micro-turbulences ($\Delta_{\max} \to 0^+$), on obtient nécessairement $\Delta_t^{\mathrm{eff}} \to 0^+$ et $P_t \to \sum_{i=1}^n (T_{t,i} + C_{t,i}) = T_t + C_t$. De plus, $\frac{\partial P_t}{\partial \Delta_{t,i}} = -\frac{W_i}{(1 + \Delta_{t,i})^2} < 0$ garantit la monotonie stricte de toute réduction locale de turbulence. $\blacksquare$

*Vérification exécutable :* `FractalScaleAggregation` dans [`src/omega_zero/supela_math_core.py`](../../src/omega_zero/supela_math_core.py).

---

## 4. Mécanique Irréversible `GENERIC` en Dimension $n \ge 2$ (`MECANIQUE_IRREVERSIBLE_GENERIC_SUPELA.md`)

L'équation d'évolution couplée réversible-irréversible s'écrit en dimension finie $n \ge 2$ :
$$\dot{z} = L(z)\nabla E(z) + M(z)\nabla S(z)$$
soumise aux **7 conditions structurelles simultanées** :
1. **Antisymétrie de Poisson :** $L^\top = -L$ ;
2. **Symétrie d'Onsager–Casimir :** $M^\top = M$ ;
3. **Semi-définie positivité globale :** $M \succeq 0$ ($\forall v \in \mathbb{R}^n,\ v^\top M v \ge 0$), vérifiée mécaniquement par **décomposition de Cholesky à pivotage diagonal complet** (critère nécessaire et suffisant sur matrices singulières ou de plein rang — Higham, Ch. 10), et non par simple test sur le seul vecteur $\nabla S$ ;
4. **Dégénérescence réversible :** $L \nabla S = 0$ ;
5. **Dégénérescence dissipative :** $M \nabla E = 0$ ;
6. **Premier principe (conservation exacte d'énergie) :**
   $$\dot{E} = \langle \nabla E, L\nabla E \rangle + \langle \nabla E, M\nabla S \rangle = 0 + \langle M\nabla E, \nabla S \rangle = 0 ;$$
7. **Second principe (croissance d'entropie) :**
   $$\dot{S} = \langle \nabla S, L\nabla E \rangle + \langle \nabla S, M\nabla S \rangle = -\langle L\nabla S, \nabla E \rangle + \langle \nabla S, M\nabla S \rangle = \langle \nabla S, M\nabla S \rangle \ge 0.$$

### Système canonique couplé non-trivial 3D (Oscillateur amorti + bain thermique)
Pour $z = (q, p, s)$, $E(z) = \frac{1}{2}(q^2 + p^2) + T_0 s$ ($T_0 > 0$), $S(z) = s$ et friction $\gamma > 0$ :
$$L = \begin{pmatrix} 0 & 1 & 0 \\ -1 & 0 & 0 \\ 0 & 0 & 0 \end{pmatrix} \neq 0, \qquad M = \frac{\gamma}{T_0} v v^\top = \gamma \begin{pmatrix} 0 & 0 & 0 \\ 0 & T_0 & -p \\ 0 & -p & p^2/T_0 \end{pmatrix} \succeq 0 \quad \text{avec } v = \begin{pmatrix} 0 \\ T_0 \\ -p \end{pmatrix}.$$
Ce système vérifie l'identité de Jacobi ($L$ constante), $L \neq 0$, $M \neq 0$, $M \succeq 0$, $L\nabla S = 0$, $M\nabla E = 0$, $\dot{E} = 0$ identiquement et $\dot{S} = \gamma p^2 / T_0 > 0$ strictement.

*Vérification exécutable :* `GenericThermodynamicStep.canonical_3d_damped_oscillator()` + réfutations de matrices indéfinies dans `tests/test_supela_math_core.py`.

---

## 5. Normalisation Rationnelle Exacte de `SGG_v2` sans Effacement (`MAT-08-PATTERNS-LAS`)

Dans le *Corpus Unifié v3.0*, la formule brute est :
$$\mathrm{SGG}_{\mathrm{raw}}(A, V, \text{É}, T, M) = \frac{1}{4}A + \frac{3}{10}V + \frac{3}{10}\text{É} + \frac{3}{20}T + \frac{1}{5}M, \qquad \sum_{k=1}^5 w_k = \frac{6}{5} = 1{,}20.$$
Conformément à `CONTR-Z0-TENSION` et `H ≠ L ≠ P`, cette pondération brute est **conservée intacte**. Sa projection canonique sur le simplexe $\Delta^4 = \{w' \in \mathbb{R}_{\ge 0}^5 : \sum w'_k = 1\}$ est définie en arithmétique rationnelle exacte (`fractions.Fraction`) par :
$$\mathrm{SGG}_{\mathrm{norm}} = \frac{5}{6}\mathrm{SGG}_{\mathrm{raw}} = \frac{5}{24}A + \frac{1}{4}V + \frac{1}{4}\text{É} + \frac{1}{8}T + \frac{1}{6}M, \qquad \sum_{k=1}^5 w'_k = 1.$$
**Propriété :** comme $\frac{5}{6} > 0$, l'application $\mathrm{SGG}_{\mathrm{raw}} \mapsto \mathrm{SGG}_{\mathrm{norm}}$ est un **isomorphisme d'ordre strict** sur $[0,1]^5$ et garantit $\mathrm{SGG}_{\mathrm{norm}} \in [0, 1]$.

*Vérification exécutable :* `SGGv2Metric` dans [`src/omega_zero/supela_math_core.py`](../../src/omega_zero/supela_math_core.py).

---

## 6. Extension Formelle Candidate pour `TZI` (`MAT-00-ZERO-INT`) et Vitalité `VR-22` (`MAT-03`)

> **Statut épistémique :** `FORMAL_CANDIDATE_EXTENSION` — cette modélisation ne ferme pas artificiellement `CONTR-Z0-TENSION` et laisse intacte la séparation historique entre Branche A (TZI semi-formel) et Branche B (*Corpus v3.0*, $\mathbb{V} \neq Z_0$).

1. **Espace métrique pointé $(S, d, Z_0)$ & Contraction de Banach :** en remplaçant la norme $\|\Delta S\|$ (qui exige une structure vectorielle normée) par une distance générale $d : S \times S \to \mathbb{R}_{\ge 0}$, un opérateur de reset contractant $R : S \to S$ vérifiant $R(Z_0) = Z_0$ et $d(R(x), Z_0) \le \kappa\, d(x, Z_0)$ ($\kappa \in ]0, 1[$) garantit le retour sous le seuil critique $\theta_{\mathrm{crit}} > 0$ en au plus :
   $$k^* = \begin{cases} 0 & \text{si } d(S_0, Z_0) < \theta_{\mathrm{crit}}, \\ \left\lfloor \dfrac{\ln(\theta_{\mathrm{crit}} / d(S_0, Z_0))}{\ln \kappa} \right\rfloor + 1 & \text{sinon.} \end{cases}$$
2. **Séparation $\mathbb{V}$ vs $Z_0$ :** dans une lecture catégorique candidate, le Vide ontologique $\mathbb{V}$ correspond au substrat initial non initialisé, tandis que Xero ($\mathbb{X} = Z_0$) correspond au point de base opérationnel d'un espace pointé doté de la rétraction idempotente $\Pi_0 : \mathcal{S} \to \mathcal{S}_0$ préservant $K_t \subseteq K_{t+1}$.
3. **Garde de vitalité `VR-22` (`MAT-03-RESET-STAR`) :** pour $V_e = \frac{\mathrm{Valeur}}{\mathrm{Complexité}} \ge 1{,}0$, le domaine est explicitement restreint à $\mathrm{Valeur} \ge 0$ et $\mathrm{Complexité} > 0$.

---

## 7. Contre-Exemple Analytique GRPO (`MAT-07`) & Invariance d'Ordre `Merge*` (`MAT-05`)

1. **Découplage perte / gradient GRPO :** sur la politique softmax à $\mu = 1, \beta = 0$, au point $\theta = \theta_{\mathrm{old}}$ le ratio de vraisemblance vaut $\rho_i(\theta_{\mathrm{old}}) = 1$ et $\sum_{i=1}^G \hat{A}_i = 0$, d'où $L_{\mathrm{GRPO}}(\theta_{\mathrm{old}}) = 0$, alors que le gradient analytique $\frac{\partial L}{\partial \theta_j} = -\frac{1}{G}\sum_{i=1}^G \hat{A}_i(\delta_{ij} - p_j) \neq 0$ (vérifié à $< 10^{-7}$ par différences finies centrées dans `SupelaGRPOBridge.analyze_zero_loss_nonzero_grad` et désormais appelé directement par `run_supela_math_unification()`).
2. **Invariance d'ordre `Merge*` (généralisation à $S_n$ pour tout $n \ge 1$) :** lorsque la fusion de deltas compatibles opère comme un demi-treillis commutatif associatif idempotent augmenté d'un état absorbant conservé $\bot_{\mathrm{conflit}}$ (cas `C-001`), le résultat est invariant sous l'ensemble du groupe symétrique $S_n$ ($n!$ permutations), généralisant la vérification exhaustive des $4! = 24$ permutations (`E3`, `tests/test_properties_hypothesis.py`).

---

## 8. Tableau de Traçabilité Preuve vs Limites Ouvertes (`M3`)

| Domaine mathématique | Statut exécutable local | Borne ouverte conservée (`A_PROUVER`) |
|---|---|---|
| `MAT-00` ($\Pi_0$, $K_t \subseteq K_{t+1}$, $C \to \emptyset$) | ✅ Prouvé (`pytest` + `Hypothesis`) | `OPEN-02:Theoreme_du_Vide_General_A_PROUVER` |
| `MAT-01` (Treillis $G_0..G_4$, 125 triplets, Galois) | ✅ Prouvé (`verify_proof_lattice_axioms`) | `OPEN-01:Validite_Universelle_A_PROUVER` |
| `VR-Fractal-Ω` (Moyenne harmonique pondérée & gendarmes) | ✅ Prouvé (`FractalScaleAggregation`) | Convergence sur graphes dynamiques ouverts |
| `GENERIC n-D` ($L^\top=-L, M^\top=M\succeq 0, \dot{E}=0, \dot{S}\ge 0$) | ✅ Prouvé (`GenericThermodynamicStep`, 2D & 3D) | Extension EDP/Kružkov/GKSL en dimension infinie |
| `MAT-08` (`SGG_v2` brut $6/5$ + simplexe exact $5/6$) | ✅ Prouvé (`SGGv2Metric`, `Fraction`) | Calibration empirique terrain |
| `MAT-07` (`L=0 \land \nabla L \neq 0` analytique + DF) | ✅ Prouvé (`SupelaGRPOBridge`) | Garantie hors distribution sur politiques profondes |
| `MAT-00-ZERO-INT` (`MetricResetContraction` Banach) | 🟡 Modèle formel candidat vérifié | `CONTR-Z0-TENSION` conservée ouverte |
