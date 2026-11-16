# Schéma GRPO pour Supela · `Exploration ≠ Autorité` (`Score ≠ Preuve ≠ Vérité`)

## 1. Chaîne causale de GRPO vs Barrière épistémique Supela

Dans GRPO (*Group Relative Policy Optimization*), pour une requête $q$ :
$$q \longrightarrow \{o_1, \dots, o_G\} \longrightarrow \{r_1, \dots, r_G\} \longrightarrow \{\hat{A}_1, \dots, \hat{A}_G\} \longrightarrow \nabla_\theta L \longrightarrow \theta'$$
avec avantage relatif au groupe :
$$\hat{A}_i = \frac{r_i - \mu_r}{\sigma_r + \varepsilon}$$

Dans Supela, la récompense heuristique $r_i$ aide à **explorer** l'espace des hypothèses, mais ne crée **aucune** autorité concluante :
$$\text{Reward}(H) \neq \text{Proof}(H) \qquad \arg\max_H \text{Reward}(H) \nRightarrow H = \text{VRAI}$$

## 2. Architecture Supela-GRPO en 5 étages

```
[Manque M ouvert]
        │
        ▼
(1) EXPLORATION COMPARATIVE (GRPO)
    q -> {H_1, ..., H_G} + scores {r_1, ..., r_G} + avantages {A_1, ..., A_G}
    ⚠ Autorité émise = AUCUNE ; Statut émis = CANDIDAT
        │
        ▼
(2) TRAÇABILITÉ & PROVENANCE (M4 / I2)
    Chaque H_i devient un Raccord candidat tracé (origine, score, avantage)
        │
        ▼
(3) ÉPREUVE INDÉPENDANTE (Verrou de preuve Supela)
    Tests disciplinaires, réfutation, preuve reproductible, conflits conservés
        │
        ├── Échec / réfutation ──► STATUT = REFUTE, Autorité = AUCUNE, Trace ∈ Ref
        ├── Soutien borné ───────► STATUT = SUPPORTE_SOUS_CONDITIONS, Autorité ≤ Preuve
        └── Manque persistant ───► STATUT = INCONNU, Manque conservé dans Π₀(S_t)
```

## 3. Preuve analytique : perte nulle ($\mu=1, \beta=0$) mais gradient non nul

Lorsque `num_iterations = 1` ($\mu = 1$) et `beta = 0.0` (aucun terme KL) :
- Avant la mise à jour, $\pi_\theta = \pi_{\theta_{\text{old}}}$, donc le ratio de probabilités vaut exactement :
  $$\rho_i(\theta_{\text{old}}) = \frac{\pi_\theta(o_i \mid q)}{\pi_{\theta_{\text{old}}}(o_i \mid q)} = 1$$
- Les avantages étant centrés sur le groupe ($\sum_{i=1}^G \hat{A}_i = 0$), la valeur scalaire de la perte vaut :
  $$L(\theta_{\text{old}}) = -\frac{1}{G} \sum_{i=1}^G \rho_i(\theta_{\text{old}}) \hat{A}_i = -\frac{1}{G}\sum_{i=1}^G \hat{A}_i = 0$$
- **Pourtant, le gradient ne s'annule pas**, car la dérivée de $\rho_i(\theta)$ évaluée en $\theta = \theta_{\text{old}}$ vaut :
  $$\left.\nabla_\theta \rho_i(\theta)\right|_{\theta=\theta_{\text{old}}} = \frac{\nabla_\theta \pi_\theta(o_i \mid q)}{\pi_{\theta_{\text{old}}}(o_i \mid q)} = \nabla_\theta \log \pi_\theta(o_i \mid q)$$
  d'où :
  $$\left.\nabla_\theta L(\theta)\right|_{\theta=\theta_{\text{old}}} = -\frac{1}{G} \sum_{i=1}^G \hat{A}_i \nabla_\theta \log \pi_\theta(o_i \mid q) \neq 0$$
  dès lors que $\sigma_r > 0$ et que les $\nabla_\theta \log \pi_\theta(o_i \mid q)$ diffèrent entre réponses.

Implémentation vérifiée numériquement (analytique + différences finies) dans [`grpo_bridge.py`](../../src/omega_zero/grpo_bridge.py).
