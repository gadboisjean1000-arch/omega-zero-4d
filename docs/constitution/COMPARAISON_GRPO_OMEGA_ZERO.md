# Comparaison Mathématique Corrigée : GRPO vs Supela Ω-ZERO

> **Statut :** Document corrigé et aligné avec [`SCHEMA_GRPO_SUPELA.md`](SCHEMA_GRPO_SUPELA.md), [`src/omega_zero/grpo_bridge.py`](../../src/omega_zero/grpo_bridge.py) et [`policies/omega_zero_invariants.rego`](../../policies/omega_zero_invariants.rego).

---

## 1. Formalisation de la Non-Équivalence

| Concept | GRPO | Supela Ω-ZERO |
|---|---|---|
| **Nature** | Algorithme d'optimisation relative de politique | Cadre de gouvernance architecturale 4D |
| **Espace** | Paramètres $\theta \in \mathbb{R}^d$ | États gouvernés $S_t$ (Local / Cloud / Vide / Manque) |
| **Unité d'analyse** | Politique $\pi_\theta(y_i \mid q)$ sur un groupe de réponses | Objets `Manque`, `Raccord`, `Conflict4D`, `ZeroState` |
| **Objectif** | Maximiser l'avantage relatif régularisé par KL | Conserver les invariants `{I, P, M, A, H}`, borner l'autorité $\le$ preuve |

**Théorème :** $\text{GRPO} \neq \Omega\text{-ZERO}$.

1. **GRPO** met à jour $\theta$ via l'objectif tronqué sur le ratio de vraisemblance et la divergence KL active :
   $$\hat{A}_i = \frac{r_i - \mu_r}{\sigma_r + \varepsilon}, \qquad \rho_i(\theta) = \frac{\pi_\theta(y_i \mid q)}{\pi_{\theta_{\text{old}}}(y_i \mid q)}$$
   $$J_{\text{GRPO}}(\theta) = \frac{1}{G}\sum_{i=1}^G \min\bigl(\rho_i(\theta)\hat{A}_i,\ \operatorname{clip}(\rho_i(\theta), 1-\varepsilon, 1+\varepsilon)\hat{A}_i\bigr) - \beta\, D_{\text{KL}}(\pi_\theta \| \pi_{\text{ref}})$$
2. **Ω-ZERO** projette l'état système vers le zéro opérationnel fail-closed :
   $$\Pi_0(S_t) = \{I, P, M, A, H\} \neq \emptyset, \qquad \Pi_0(\Pi_0(S_t)) = \Pi_0(S_t)$$
3. Aucune bijection naturelle ne relie $\theta$ aux invariants $I$ ni à $\Pi_0(S_t)$ : l'optimisation de politique ne certifie donc jamais une vérité normative.

---

## 2. Pipeline GRPO ↔ Ω-ZERO Intégré (Garde-Fous `GF1`–`GF5` Corrigés)

| Garde-Fou | Condition corrigée | Implémentation réelle |
|---|---|---|
| **GF1** | $r_i \in \mathbb{R}$ fini et $r_i \le R_{\max}$ | [`SupelaGRPOBridge.explore_with_guardrails`](../../src/omega_zero/grpo_bridge.py) bloque/signale les récompenses aberrantes |
| **GF2** | $\hat{A}_i \ge \tau$ (seuil $\tau \neq \theta$) appliqué **côté admission Supela uniquement** | Préserve le centrage $\sum \hat{A}_i = 0$ pour le gradient GRPO tout en filtrant l'admission |
| **GF3** | $\Pi_0(S_t)$ sur l'état gouverné `CloudOmega` conserve `{I, P, M, A, H}` et `Autorité(c) ≤ Preuve(c)` | Corrigé : $\Pi_0$ s'applique à l'état système $S_t$ et aux raccords émis, jamais à $\Delta\theta$ directement |
| **GF4** | Admission humaine requise (`validation_required = True`, `ADMISSIBLE_A_REVUE_HUMAINE`) | Verrou Rego [`grpo_barrier_respected`](../../policies/omega_zero_invariants.rego#L131-L138) |
| **GF5** | Chaîne complète `Reward(x) → Candidate(x) → Épreuves(x) → Status(x)` | Dataclass [`GRPOGuardrailTrace`](../../src/omega_zero/grpo_bridge.py) avec SHA-256 canonique |

---

## 3. Limites du Signal de Récompense

$$\text{Reward}(x) \longrightarrow \text{Candidate}(x) \longrightarrow \text{Épreuves}(x) \longrightarrow \text{Status}(x)$$

- **Ordinalité relative uniquement :** $R(x) > R(y)$ indique une préférence heuristique sur un groupe, jamais une preuve.
- **Jamais de raccourci :** $\text{Reward}(x) \nrightarrow \text{Vérité}(x)$ et $\text{Reward}(x) \nrightarrow \text{Status}(x)$ sans épreuve indépendante.

---

## 4. Jonction Propre et État Vérifié dans `omega-zero-4d`

> **Correction factuelle par rapport aux notes antérieures :** l'exécution réelle de `PLAN-4D-ΩZERO-ESC-01` dans `omega-zero-4d` porte sur les 8 paliers `E0..E7` et les 10 conditions `C01..C10` (l'émergence correspond à `C10` / sous-test `E7-B`, et non à un identifiant `C10-EMERG`). Les artefacts sont intégrés au dépôt, exécutés via [`HARNAIS_TEST_ESCALADE_4D.py`](HARNAIS_TEST_ESCALADE_4D.py), `pytest` et `opa test`, et vérifiés par [`verify_a12.py`](../../scripts/verify_a12.py).

```
GRPO explore (θ, π_θ, A_i) ──► GF1 (R ≤ R_max) ──► GF2 (A_i ≥ τ → Candidate)
                                                           │
                                                           ▼
Décision humaine (GF4) ◄── Status(x) ◄── Épreuves(x) ◄── GF3 Π₀(S_t) & GF5 Trace
```
