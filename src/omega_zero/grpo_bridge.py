from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass

from .models import AuthorityLevel, Raccord, RaccordStatus


@dataclass
class CandidateExploration:
    """Sortie brute d'une génération comparative (type GRPO) avant épreuve Supela."""

    id: str
    query: str
    hypothesis: str
    heuristic_reward: float
    advantage: float = 0.0
    proof_verified: bool = False
    proof_scope: str = ""


@dataclass
class GRPOStepAnalysis:
    """Analyse mathématique d'un pas GRPO à μ=1, β=0 montrant L=0 et ∇L ≠ 0."""

    rewards: list[float]
    advantages: list[float]
    scalar_loss: float
    analytical_grad: list[float]
    finite_diff_grad: list[float]
    grad_norm: float


class SupelaGRPOBridge:
    """Pont méthodologique GRPO → Supela : Explorer librement sans accorder d'autorité par le score.

    Invariant fondamental :
        Reward(H) ≠ Proof(H)
        argmax_H Reward(H) ⇏ H = VRAI
        Valeur observable L = 0 ⇏ ∇L = 0 (effet non nul)
    """

    @staticmethod
    def compute_group_advantages(rewards: list[float], eps: float = 1e-8) -> list[float]:
        if not rewards:
            raise ValueError("Le groupe de récompenses ne peut pas être vide.")
        mean_r = sum(rewards) / len(rewards)
        var_r = sum((r - mean_r) ** 2 for r in rewards) / len(rewards)
        std_r = math.sqrt(var_r)
        if std_r < eps:
            return [0.0 for _ in rewards]
        return [(r - mean_r) / (std_r + eps) for r in rewards]

    @staticmethod
    def analyze_zero_loss_nonzero_grad(
        theta: list[float],
        rewards: list[float],
        clip_eps: float = 0.2,
    ) -> GRPOStepAnalysis:
        """Démontre sur une politique softmax 1-pas (μ=1, β=0) que L=0.0 mais ∇_θ L ≠ 0."""
        if len(theta) != len(rewards):
            raise ValueError("len(theta) doit égaler len(rewards) pour la politique softmax jouet.")

        def softmax(logits: list[float]) -> list[float]:
            m = max(logits)
            exps = [math.exp(x - m) for x in logits]
            s = sum(exps)
            return [e / s for e in exps]

        advantages = SupelaGRPOBridge.compute_group_advantages(rewards)
        old_probs = softmax(theta)

        def loss_fn(cur_theta: list[float]) -> float:
            cur_probs = softmax(cur_theta)
            terms = []
            for p_cur, p_old, adv in zip(cur_probs, old_probs, advantages):
                ratio = p_cur / p_old
                clipped = max(1.0 - clip_eps, min(1.0 + clip_eps, ratio))
                terms.append(min(ratio * adv, clipped * adv))
            return -sum(terms) / len(terms)

        scalar_loss = loss_fn(theta)

        # À θ = θ_old : ratio = 1, donc ∇_θ(p_cur / p_old) = ∇_θ log(p_cur)
        # Pour softmax(θ)_i : ∂log(p_i)/∂θ_j = δ_{ij} - p_j
        k = len(theta)
        analytical_grad = [0.0] * k
        for i, adv in enumerate(advantages):
            for j in range(k):
                d_log_p_ij = (1.0 if i == j else 0.0) - old_probs[j]
                analytical_grad[j] += (-1.0 / k) * adv * d_log_p_ij

        # Vérification par différences finies centrées
        h = 1e-6
        finite_diff_grad = []
        for j in range(k):
            tp = list(theta)
            tm = list(theta)
            tp[j] += h
            tm[j] -= h
            finite_diff_grad.append((loss_fn(tp) - loss_fn(tm)) / (2.0 * h))

        grad_norm = math.sqrt(sum(g * g for g in analytical_grad))
        return GRPOStepAnalysis(
            rewards=list(rewards),
            advantages=advantages,
            scalar_loss=scalar_loss,
            analytical_grad=analytical_grad,
            finite_diff_grad=finite_diff_grad,
            grad_norm=grad_norm,
        )

    @staticmethod
    def explore_and_emit_candidates(
        query: str,
        hypotheses: list[tuple[str, str, float]],
        origin_node: str = "GRPO_EXPLORER",
        proof_checker: Callable[[str], tuple[bool, str]] | None = None,
    ) -> tuple[list[CandidateExploration], list[Raccord]]:
        """Produit des candidats Supela sans jamais convertir un score heuristique en vérité."""
        rewards = [score for _, _, score in hypotheses]
        advantages = SupelaGRPOBridge.compute_group_advantages(rewards)

        explorations: list[CandidateExploration] = []
        raccords: list[Raccord] = []
        for (cid, hyp_text, score), adv in zip(hypotheses, advantages):
            verified = False
            scope = ""
            if proof_checker is not None:
                verified, scope = proof_checker(cid)

            explorations.append(
                CandidateExploration(
                    id=cid,
                    query=query,
                    hypothesis=hyp_text,
                    heuristic_reward=score,
                    advantage=adv,
                    proof_verified=verified,
                    proof_scope=scope,
                )
            )

            # Barrière Supela : même le meilleur score reste CANDIDAT sans autorité tant qu'aucune preuve indépendante ne passe
            raccord = Raccord(
                id=cid,
                label=hyp_text,
                source=query,
                target=f"Hypothesis:{cid}",
                origin_node=origin_node,
                status=RaccordStatus.CANDIDAT,
                authority_level=AuthorityLevel.AUCUNE,
                evidence_level=(
                    AuthorityLevel.LOCALE_CONDITIONNELLE if verified else AuthorityLevel.AUCUNE
                ),
                scope=scope or "NON_PROUVE_EXPLORATION_SEULE",
                validation_required=True,
                provenance=f"grpo_exploration:reward={score:.3f},advantage={adv:.3f}",
            )
            raccords.append(raccord)

        return explorations, raccords
