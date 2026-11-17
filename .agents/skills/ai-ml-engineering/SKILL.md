---
name: ai-ml-engineering
description: Ingénierie IA/RL (GRPO, évaluation, garde-fous GF1-GF5) avec séparation stricte entre signal de récompense heuristique, preuve et vérité normative.
---
# Skill `ai-ml-engineering`

1. Appliquer la règle **GRPO ≠ Ω-ZERO** : un avantage $\hat{A}_i$ ou une récompense $R(y_i, q)$ reste une heuristique d'exploration, jamais une preuve (`Score ≠ Preuve ≠ Vérité`).
2. Implémenter les 5 garde-fous via `SupelaGRPOBridge.explore_with_guardrails` :
   - **GF1** : borner $R \le R_{\max}$ et rejeter les valeurs non finies ;
   - **GF2** : appliquer le seuil $\tau$ uniquement à l'admission candidat afin de préserver $\sum \hat{A}_i = 0$ ;
   - **GF3** : vérifier $\Pi_0(S_t)$ sur l'état `CloudOmega` (jamais sur $\Delta\theta$ directement) ;
   - **GF4** : exiger la revue humaine (`ADMISSIBLE_A_REVUE_HUMAINE`) ;
   - **GF5** : tracer `Reward → Candidate → Épreuves → Status` avec empreinte SHA-256.
3. Respecter l'état épistémique de `supela-article-registry-1.json` (`Hook: AnalysisCandidate`, `verdict_final: OUVERT`).
