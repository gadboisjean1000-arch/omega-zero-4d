from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .models import (
    AuthorityLevel,
    CloudOmega,
    Manque,
    ManqueStatus,
    Raccord,
    RaccordStatus,
    canonical_sha256,
)
from .projection import Pi0Projector


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


@dataclass
class GRPOGuardrailTrace:
    """Chaîne GF5 : Reward(x) → Candidate(x) → Épreuves(x) → Status(x)."""

    candidate_id: str
    reward_raw: float
    reward_bounded: float
    gf1_outlier_blocked: bool
    advantage: float
    gf2_admitted: bool
    proof_verified: bool
    proof_scope: str
    final_status: str
    authority_level: str
    human_review_required: bool
    trace_sha256: str = ""

    def __post_init__(self) -> None:
        if not self.trace_sha256:
            self.trace_sha256 = canonical_sha256(
                {
                    "candidate_id": self.candidate_id,
                    "reward_raw": self.reward_raw,
                    "reward_bounded": self.reward_bounded,
                    "gf1_outlier_blocked": self.gf1_outlier_blocked,
                    "advantage": round(self.advantage, 8),
                    "gf2_admitted": self.gf2_admitted,
                    "proof_verified": self.proof_verified,
                    "proof_scope": self.proof_scope,
                    "final_status": self.final_status,
                    "authority_level": self.authority_level,
                }
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "candidate_id": self.candidate_id,
            "reward_raw": self.reward_raw,
            "reward_bounded": self.reward_bounded,
            "gf1_outlier_blocked": self.gf1_outlier_blocked,
            "advantage": self.advantage,
            "gf2_admitted": self.gf2_admitted,
            "proof_verified": self.proof_verified,
            "proof_scope": self.proof_scope,
            "final_status": self.final_status,
            "authority_level": self.authority_level,
            "human_review_required": self.human_review_required,
            "trace_sha256": self.trace_sha256,
        }


@dataclass
class GRPOGuardrailReport:
    """Résultat complet de l'intégration GRPO ↔ Ω-ZERO avec garde-fous GF1–GF5."""

    query: str
    r_max: float
    advantage_threshold_tau: float
    explorations: list[CandidateExploration]
    admitted_raccords: list[Raccord]
    gf1_blocked_ids: list[str]
    gf2_filtered_ids: list[str]
    gf3_pi0_preserved: bool
    gf3_pi0_non_empty: bool
    gf4_human_review_required: bool
    promotion: str
    traces: list[GRPOGuardrailTrace] = field(default_factory=list)
    hook: str = "AnalysisCandidate"
    verdict_final: str = "OUVERT"

    def to_dict(self) -> dict[str, Any]:
        return {
            "hook": self.hook,
            "verdict_final": self.verdict_final,
            "query": self.query,
            "r_max": self.r_max,
            "advantage_threshold_tau": self.advantage_threshold_tau,
            "admitted_count": len(self.admitted_raccords),
            "gf1_blocked_ids": list(self.gf1_blocked_ids),
            "gf2_filtered_ids": list(self.gf2_filtered_ids),
            "gf3_pi0_preserved": self.gf3_pi0_preserved,
            "gf3_pi0_non_empty": self.gf3_pi0_non_empty,
            "gf4_human_review_required": self.gf4_human_review_required,
            "promotion": self.promotion,
            "traces": [t.to_dict() for t in self.traces],
        }


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

    @staticmethod
    def explore_with_guardrails(
        query: str,
        hypotheses: list[tuple[str, str, float]],
        *,
        r_max: float = 1.0,
        advantage_threshold_tau: float = 0.0,
        origin_node: str = "GRPO_EXPLORER",
        proof_checker: Callable[[str], tuple[bool, str]] | None = None,
    ) -> GRPOGuardrailReport:
        """Exécute le pipeline GRPO ↔ Ω-ZERO avec les 5 garde-fous GF1–GF5.

        - GF1 : borne R(x) <= r_max (bloque/signale les récompenses aberrantes ou non finies)
        - GF2 : filtre d'admission candidat A_i >= tau appliqué UNIQUEMENT côté Supela (sans casser
                le centrage ∑A_i = 0 du gradient GRPO)
        - GF3 : vérifie que la projection Π₀(S_t) sur l'état gouverné conserve {I, P, M, A, H}
        - GF4 : maintient validation humaine obligatoire (ADMISSIBLE_A_REVUE_HUMAINE, jamais auto-ÉTABLI)
        - GF5 : produit la trace complète Reward(x) → Candidate(x) → Épreuves(x) → Status(x)
        """
        if not hypotheses:
            raise ValueError("La liste d'hypothèses ne peut pas être vide.")
        if r_max <= 0 or not math.isfinite(r_max):
            raise ValueError("r_max doit être fini et strictement positif (GF1).")

        # GF1 : contrôle et bornage des récompenses avant calcul d'avantage
        bounded_rewards: list[float] = []
        gf1_blocked: list[str] = []
        for cid, _, raw_score in hypotheses:
            if not math.isfinite(raw_score) or raw_score > r_max:
                gf1_blocked.append(cid)
                bounded_rewards.append(r_max if math.isfinite(raw_score) else 0.0)
            else:
                bounded_rewards.append(raw_score)

        # Normalisation de groupe complète sur les scores bornés (conserve ∑A_i = 0)
        advantages = SupelaGRPOBridge.compute_group_advantages(bounded_rewards)

        explorations: list[CandidateExploration] = []
        admitted_raccords: list[Raccord] = []
        gf2_filtered: list[str] = []
        traces: list[GRPOGuardrailTrace] = []

        omega = CloudOmega()
        omega.authorities["GRPO_GATE"] = "BARRIERE_SUPELA"
        omega.manques[query] = Manque(
            id=query,
            question=f"Exploration GRPO bornée pour {query}",
            contexte="Pipeline GRPO <-> Omega-ZERO (GF1-GF5)",
            origine=origin_node,
            dependances=["GRPO_EXPLORER", "OMEGA_PI0"],
            autorite="AUCUNE",
            temps="t_grpo",
            statut=ManqueStatus.SOUS_EXPLORATION,
            tentatives=[cid for cid, _, _ in hypotheses],
        )

        any_proof_verified = False
        for (cid, hyp_text, raw_score), b_score, adv in zip(hypotheses, bounded_rewards, advantages):
            gf1_outlier = cid in gf1_blocked
            gf2_admitted = (not gf1_outlier) and (adv >= advantage_threshold_tau)

            verified = False
            scope = ""
            if gf2_admitted and proof_checker is not None:
                verified, scope = proof_checker(cid)
            if verified:
                any_proof_verified = True

            explorations.append(
                CandidateExploration(
                    id=cid,
                    query=query,
                    hypothesis=hyp_text,
                    heuristic_reward=raw_score,
                    advantage=adv,
                    proof_verified=verified,
                    proof_scope=scope,
                )
            )

            if gf2_admitted:
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
                    provenance=(
                        f"grpo_gf1_gf5:raw={raw_score:.3f},bounded={b_score:.3f},adv={adv:.3f}"
                    ),
                )
                raccord.enforce_authority_bound()
                admitted_raccords.append(raccord)
                omega.raccords[cid] = raccord
                final_status = RaccordStatus.CANDIDAT.value
            else:
                gf2_filtered.append(cid)
                final_status = "REJETE_GF1_ABERRANT" if gf1_outlier else "FILTRE_GF2_SOUS_SEUIL"

            traces.append(
                GRPOGuardrailTrace(
                    candidate_id=cid,
                    reward_raw=raw_score,
                    reward_bounded=b_score,
                    gf1_outlier_blocked=gf1_outlier,
                    advantage=adv,
                    gf2_admitted=gf2_admitted,
                    proof_verified=verified,
                    proof_scope=scope or "NON_PROUVE_EXPLORATION_SEULE",
                    final_status=final_status,
                    authority_level=AuthorityLevel.AUCUNE.name,
                    human_review_required=True,
                )
            )

        # GF3 : vérification d'invariants via Π₀ sur l'état gouverné CloudOmega (jamais sur Δθ)
        projector = Pi0Projector()
        zero_state = projector.project(omega)
        gf3_idempotent = projector.verify_idempotence(omega)
        gf3_non_empty = zero_state.is_non_empty()
        gf3_manque_kept = query in zero_state.manques
        gf3_no_auto_authority = all(r.authority_level == AuthorityLevel.AUCUNE for r in admitted_raccords)
        gf3_preserved = gf3_idempotent and gf3_non_empty and gf3_manque_kept and gf3_no_auto_authority

        # GF4 : promotion humaine requise
        promotion = (
            "ADMISSIBLE_A_REVUE_HUMAINE"
            if (gf3_preserved and len(admitted_raccords) > 0 and any_proof_verified)
            else "OUVERT_EN_ATTENTE_EPREUVE"
        )

        return GRPOGuardrailReport(
            query=query,
            r_max=r_max,
            advantage_threshold_tau=advantage_threshold_tau,
            explorations=explorations,
            admitted_raccords=admitted_raccords,
            gf1_blocked_ids=gf1_blocked,
            gf2_filtered_ids=gf2_filtered,
            gf3_pi0_preserved=gf3_preserved,
            gf3_pi0_non_empty=gf3_non_empty,
            gf4_human_review_required=True,
            promotion=promotion,
            traces=traces,
        )

