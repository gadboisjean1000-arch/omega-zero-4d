# Mécanique Physique Irréversible (GENERIC) × Mathématiques Supela (`MAT-00`..`MAT-08`)

> **Horodatage canonique :** `2026-11-17T17:28:33Z` (`2026-11-17T09:28:33-08:00`)  
> **Statut épistémique :** `CANDIDAT` (correspondances structurelles explorées sous `Analogie ≠ Isomorphisme prouvé` ; comblements universitaires sourcés).  
> **Auteur souverain :** Jean-François Gadbois  
> **Références internes :** [`REGISTRE_FORMULES_SUPELA.md`](REGISTRE_FORMULES_SUPELA.md), [`BANC_MULTI_MOTEURS_SUPELA.md`](BANC_MULTI_MOTEURS_SUPELA.md), [`SUPELA_GUARD_KERNEL.md`](SUPELA_GUARD_KERNEL.md).

---

## 1. Rectification Factuelle (`TRACE-06`)

- **Médaille Fields & Transport Optimal :** **Cédric Villani** a reçu la médaille Fields en **2010** (transport optimal et amortissement Landau). Les lauréats **2022** sont Hugo Duminil-Copin, June Huh, James Maynard et Maryna Viazovska.

---

## 2. Projection $\Pi_0(S_t) = \{I, P, M, A, H\}$ appliquée à GENERIC

Dans le formalisme **GENERIC** (*General Equation for the Non-Equilibrium Reversible-Irreversible Coupling*) :

$$\dot{z} = L(z)\frac{\delta E}{\delta z} + M(z)\frac{\delta S}{\delta z}, \qquad L(z)\frac{\delta S}{\delta z} = 0, \qquad M(z)\frac{\delta E}{\delta z} = 0$$

| Composante $\Pi_0$ | Mécanique Irréversible | Manque $M(S_t, G)$ détecté | Comblement Mathématique Universitaire |
|---|---|---|---|
| **$I$ (Invariants)** | $\dot{E}=0$, $\dot{S}\ge 0$, $M\succeq 0$ | Réponse linéaire $M(z)$ insuffisante pour plasticité / chimie / rupture | **Cadre d'Évolution de Mielke (Legendre–Fenchel)** : potentiel convexe de dissipation $\Psi(z,\dot{z})$ et dual $\Psi^*(z,\xi)$ via l'inégalité Énergie–Dissipation (EDI). |
| **$P$ (Preuves)** | Identité de Jacobi pour $\{A,B\}_L$, $M\succeq 0$ | Convergence vers l'équilibre hors métrique plate | **Transport Optimal $(P_2, W_2)$** (Otto, Lott–Sturm–Villani) : convexité géodésique ($\lambda$-displacement convexity) et inégalités Log-Sobolev (LSI) $\implies$ décroissance exponentielle de $D_{\mathrm{KL}}(\rho_t \| \rho_{\mathrm{eq}})$. |
| **$M$ (Manques)** | Singularités, chocs, systèmes ouverts | Chocs hyperboliques & mécanique quantique ouverte absents | **1. EDP hyperboliques (Lax / Kružkov)** : sélection entropique $\partial_t \eta(u) + \nabla\cdot q(u) \le 0$.<br>**2. Quantique ouvert (GKSL / Lindblad)** : semigroupe CPTP non inversible $\dot{\rho} = -\frac{i}{\hbar}[H,\rho] + \sum_k \gamma_k (L_k\rho L_k^\dagger - \frac{1}{2}\{L_k^\dagger L_k,\rho\})$. |
| **$A$ (Autorités)** | Validité d'un intégrateur discret | Euler explicite brise $L\frac{\delta S}{\delta z}=0$ | **Intégrateurs géométriques & Gradients discrets** (Gonzalez / McLaren–Quispel / FEEC) préservant exactement $L_{\mathrm{disc}}\bar{\nabla}S=0$ et $M_{\mathrm{disc}}\bar{\nabla}E=0$. |
| **$H$ (Histoire)** | $M$ non inversible | Perte du micro-état | **Monotonie $K_t \subseteq K_{t+1}$ (`MAT-00-MONOTONIE-K`) & Compression `C2` (`SUP-ICI-01`)** : `C2` (`reversible = false`) conserve le noyau de continuité dans un journal WORM append-only. |

---

## 3. Treillis Probatoire $G_0 \prec G_1 \prec G_2 \prec G_3 \prec G_4$ (`MAT-01-TREILLIS`)

1. **$G_0$ (Heuristique)** : *Stosszahlansatz* (chaos moléculaire de Boltzmann).
2. **$G_1$ (Formel)** : Théorème $H$ formel ($\frac{\mathrm{d}}{\mathrm{d}t}\int f\ln f \le 0$).
3. **$G_2$ (Solutions faibles)** : Solutions renormalisées de **DiPerna–Lions (1989)** pour Boltzmann.
4. **$G_3$ (Temps court)** : Limite de Boltzmann–Grad rigoureuse de **Lanford (1975)**.
5. **$G_4$ (Temps long)** : Prolongement au-delà du temps de collision (**Deng–Hani–Ma, 2024**) et décroissance des corrélations pour le billard de Sinaï (**Chernov–Dolgopyat**).

> **Loi `Authority(G) ≤ Proof(G)` :** Un solveur numérique minimisant un résidu (`L(θ_old)=0, ∇L≠0`, `MAT-07`) ne prouve ni l'unicité ni l'admissibilité entropique de Kružkov. Soumis au [`SupelaMultiEngineBench`](../../src/omega_zero/multi_engine_bench.py), tout écart aux invariants $\dot{E}=0$ ou $\dot{S}\ge 0$ produit `DIVERGENCE_CONSERVEE` ou `SUPELA_EN_DÉFAUT`.

---

## 4. Manques Ouverts & Limites d'Exécution (`M3`)

- **`MAT-00-ZERO-INT` & `MAT-03-RESET-STAR` :** Maintenus `INCONNU` / `LATENT` (aucune équivalence fabriquée avec $L\nabla S=0$ ou $M\nabla E=0$).
- **Synchronisation `C:\` / `D:\` :** Non exécutable depuis la VM Linux cloud ; exécuter localement sous Windows `scripts/collect_local_encyclopedie.ps1` et `git pull` dans le dépôt cible.
- **Dépôt ORCID :** Non exécutable sans jeton/API ORCID connecté dans l'environnement ; métadonnées prêtes pour dépôt manuel ou via Zenodo/GitHub Release.
