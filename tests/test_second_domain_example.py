from __future__ import annotations

import pytest

from omega_zero import AuthorityLevel, RaccordStatus, SupelaGRPOBridge
from omega_zero.scenarios import run_second_domain_hydrology_example


def test_second_domain_hydrology_scenario_end_to_end() -> None:
    result = run_second_domain_hydrology_example()
    assert result["example_id"] == "EX-P0-02"
    assert result["conflict_preserved"] is True
    assert result["merge_outcome"] == "ISOLÉ"
    assert result["rejected_escalations"] == 1
    assert result["pi0_idempotent"] is True
    assert result["pi0_non_empty"] is True
    assert "M-HYDRO-01b" in result["pi0_preserved_manques"]
    assert "M-HYDRO-SAT" in result["pi0_preserved_manques"]
    assert "M-HYDRO-SEUIL-FIXE" in result["pi0_preserved_manques"]
    assert "RH-01" in result["pi0_preserved_refutations"]
    assert "RH-02" in result["pi0_preserved_proofs"]
    assert result["reopen_info"]["omega_destroyed"] is False
    assert "RH-02" in result["reopen_info"]["cone_reopened"]


def test_grpo_zero_loss_still_has_nonzero_exact_gradient() -> None:
    # À μ=1, β=0 : θ = θ_old => ratio = 1 => somme des avantages centrés = 0 => L = 0.0
    theta = [0.2, -0.5, 0.9, -0.1]
    rewards = [1.0, 0.0, 0.8, 0.2]

    analysis = SupelaGRPOBridge.analyze_zero_loss_nonzero_grad(theta, rewards)

    # Valeur scalaire observée de la perte = 0 (aux erreurs numériques flottantes près)
    assert abs(analysis.scalar_loss) < 1e-12
    # Moyenne des avantages = 0
    assert abs(sum(analysis.advantages)) < 1e-7
    # Gradient strictement non nul et identique aux différences finies
    assert analysis.grad_norm > 0.05
    for g_ana, g_fd in zip(analysis.analytical_grad, analysis.finite_diff_grad):
        assert g_ana == pytest.approx(g_fd, abs=1e-6)


def test_supela_grpo_bridge_enforces_score_neq_proof_neq_truth() -> None:
    explorations, raccords = SupelaGRPOBridge.explore_and_emit_candidates(
        query="M-HYDRO-01b",
        hypotheses=[
            ("H1", "Évacuation automatique immédiate (score heuristique très élevé)", 0.99),
            ("H2", "Validation municipale + contrôle zones vulnérables", 0.72),
            ("H3", "Statu quo sans alerte", 0.05),
        ],
        proof_checker=lambda cid: (cid == "H2", "TEST_LOCAL_VALIDE" if cid == "H2" else ""),
    )

    assert len(explorations) == 3
    # Le candidat avec le plus haut score heuristique (H1=0.99) reste CANDIDAT sans autorité !
    h1 = next(r for r in raccords if r.id == "H1")
    assert h1.status == RaccordStatus.CANDIDAT
    assert h1.authority_level == AuthorityLevel.AUCUNE
    assert h1.evidence_level == AuthorityLevel.AUCUNE
    assert h1.validation_required is True

    # Même H2 vérifié localement n'est pas promu automatiquement en ÉTABLI par le score seul
    h2 = next(r for r in raccords if r.id == "H2")
    assert h2.status == RaccordStatus.CANDIDAT
    assert h2.authority_level == AuthorityLevel.AUCUNE
    assert h2.evidence_level == AuthorityLevel.LOCALE_CONDITIONNELLE
