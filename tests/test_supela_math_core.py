from __future__ import annotations

from fractions import Fraction

import pytest

from omega_zero.mcp_server import TOOLS_SPEC, call_tool
from omega_zero.network_bus import main as network_bus_main
from omega_zero.supela_math_core import (
    BoundedAuthorityEvaluation,
    CanonicalHLPSeparation,
    FractalScaleAggregation,
    GenericThermodynamicStep,
    MetricResetContraction,
    ProofLatticeLevel,
    SGGv2Metric,
    SupelaStateTuple,
    ThreeDimensionalSeparation,
    VR22VitalityEvaluator,
    run_supela_math_unification,
    verify_proof_lattice_axioms,
)


def test_mat00_monotonicity_and_reset_c() -> None:
    s0 = SupelaStateTuple(
        provenance=["p0"],
        evidence=["e0"],
        contradictions=["c0"],
        knowledge_register=frozenset({"K0"}),
    )
    s1 = s0.advance({"K1"}, new_provenance="p1")
    assert s0.knowledge_register.issubset(s1.knowledge_register)
    s2 = s1.reset_contradictions_only_in_c()
    assert s2.contradictions == []
    assert s1.knowledge_register == s2.knowledge_register


def test_mat01_lattice_axioms_mat04_mat06_and_generic_2d_and_3d() -> None:
    lattice = verify_proof_lattice_axioms()
    assert lattice["cardinality"] == 5
    assert lattice["triples_checked"] == 125
    assert lattice["all_axioms_verified"] is True

    auth = BoundedAuthorityEvaluation(
        "OBJ", ProofLatticeLevel.G1_OBSERVE, requested_authority=4, improvement_score=1.0
    )
    assert auth.granted_authority == 1
    assert auth.authority_bounded_ok is True
    assert auth.auto_authorized_by_improvement is False

    hlp = ThreeDimensionalSeparation("h_sha", "local_ctx", "p_sha")
    assert hlp.dimensions_distinct is True
    hlp_canon = CanonicalHLPSeparation("Sens humain", "Texte brut littéral", "Preuve CI vérifiée")
    assert hlp_canon.dimensions_distinct is True

    # Compatibilité 2D préservée
    generic_2d = GenericThermodynamicStep(
        grad_e=(2.0, 0.0),
        grad_s=(0.0, 1.0),
        l_matrix=((0.0, 0.0), (0.0, 0.0)),
        m_matrix=((0.0, 0.0), (0.0, 0.5)),
    )
    res_2d = generic_2d.verify_invariants()
    assert res_2d["generic_valid"] is True
    assert res_2d["m_positive_semidefinite"] is True
    assert res_2d["energy_conserved"] is True
    assert res_2d["entropy_non_decreasing"] is True

    # Nouveau : GENERIC 3D couplé non-trivial (L != 0, M != 0, M >= 0, dE/dt = 0, dS/dt > 0)
    generic_3d = GenericThermodynamicStep.canonical_3d_damped_oscillator(
        q=1.2, p=0.8, temperature=2.0, gamma=0.5
    )
    res_3d = generic_3d.verify_invariants()
    assert res_3d["dimension"] == 3
    assert res_3d["l_non_trivial"] is True
    assert res_3d["m_non_trivial"] is True
    assert res_3d["m_positive_semidefinite"] is True
    assert res_3d["generic_valid"] is True
    assert abs(res_3d["dE_dt"]) < 1e-12
    assert abs(res_3d["dS_dt"] - 0.16) < 1e-12


def test_generic_refutes_indefinite_m_even_when_single_vector_entropy_positive() -> None:
    # M = [[0, 0, 0], [0, 1, 2], [0, 2, 1]] a det(2x2) = -3 < 0 (indéfinie !),
    # même si grad_S^T M grad_S = 1 >= 0 pour grad_S = (0, 0, 1).
    indefinite_step = GenericThermodynamicStep(
        grad_e=(1.0, 0.0, 0.0),
        grad_s=(0.0, 0.0, 1.0),
        l_matrix=((0.0, 0.0, 0.0), (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
        m_matrix=((0.0, 0.0, 0.0), (0.0, 1.0, 2.0), (0.0, 2.0, 1.0)),
    )
    res = indefinite_step.verify_invariants()
    assert res["entropy_non_decreasing"] is True
    assert res["m_positive_semidefinite"] is False
    assert res["generic_valid"] is False

    # Matrice zéro sur diagonale avec hors-diagonale non-nul [[0, 1], [1, 0]] (valeurs propres +-1)
    anti_diag = GenericThermodynamicStep(
        grad_e=(0.0, 0.0),
        grad_s=(1.0, 1.0),
        l_matrix=((0.0, 0.0), (0.0, 0.0)),
        m_matrix=((0.0, 1.0), (1.0, 0.0)),
    )
    assert anti_diag.verify_invariants()["m_positive_semidefinite"] is False


def test_vr_fractal_omega_weighted_harmonic_mean_and_domain_guards() -> None:
    agg = FractalScaleAggregation(
        subsystems=((10.0, 5.0, 0.25), (6.0, 4.0, 0.10), (3.0, 2.0, 0.0))
    )
    res = agg.evaluate()
    assert res["theorem_verified"] is True
    assert res["harmonic_identity_verified"] is True
    assert res["squeeze_bound_verified"] is True
    assert 0.0 <= res["effective_turbulence_delta_eff"] <= 0.25

    # Limite exacte à turbulence nulle
    zero_res = FractalScaleAggregation(subsystems=((4.0, 6.0, 0.0), (2.0, 3.0, 0.0))).evaluate()
    assert zero_res["theorem_verified"] is True
    assert zero_res["macro_state_P_t"] == pytest.approx(15.0)
    assert zero_res["effective_turbulence_delta_eff"] == pytest.approx(0.0)

    # Garde de domaine : refuse Delta = -1 (singularité) ou négatif, et W_i <= 0
    with pytest.raises(ValueError):
        FractalScaleAggregation(subsystems=((5.0, 5.0, -1.0),))
    with pytest.raises(ValueError):
        FractalScaleAggregation(subsystems=((0.0, 0.0, 0.1),))


def test_sgg_v2_exact_rational_simplex_preserves_raw_trace() -> None:
    metric = SGGv2Metric.from_floats(1.0, 1.0, 1.0, 1.0, 1.0)
    res = metric.evaluate()
    assert res["metric_verified"] is True
    assert res["raw_weights_sum_exact"] == "6/5"
    assert res["normalized_weights_sum_exact"] == "1"
    assert res["sgg_raw_exact"] == "6/5"
    assert res["sgg_norm_exact"] == "1"
    assert res["raw_trace_preserved_without_erasure"] is True
    assert SGGv2Metric(
        Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2), Fraction(1, 2)
    ).evaluate()["sgg_norm_exact"] == "1/2"

    with pytest.raises(ValueError):
        SGGv2Metric.from_floats(1.1, 0.5, 0.5, 0.5, 0.5)
    # Constructeur direct Fraction : doit rejeter tout composant hors [0, 1] même si moyenne ∈ [0, 1]
    with pytest.raises(ValueError):
        SGGv2Metric(Fraction(-1), Fraction(1), Fraction(1), Fraction(1), Fraction(1))
    with pytest.raises(ValueError):
        SGGv2Metric(Fraction(3, 2), Fraction(0), Fraction(0), Fraction(0), Fraction(0))


def test_tzi_metric_contraction_and_vr22_vitality_guards() -> None:
    contr = MetricResetContraction(
        initial_distance=8.0, contraction_kappa=0.5, critical_threshold=0.1
    ).verify_convergence()
    assert contr["epistemic_scope"] == "FORMAL_CANDIDATE_EXTENSION"
    assert contr["contraction_verified"] is True
    assert contr["guaranteed_steps_k_star"] == 7
    assert contr["final_distance"] < 0.1

    # Cas limites puissance exacte (arrondi flottant log(0.81)/log(0.9) ≈ 1.9999999999999998)
    exact_pow = MetricResetContraction(
        initial_distance=1.0, contraction_kappa=0.9, critical_threshold=0.81
    ).verify_convergence()
    assert exact_pow["guaranteed_steps_k_star"] == 3
    assert exact_pow["final_distance"] < 0.81
    assert exact_pow["contraction_verified"] is True

    exact_half = MetricResetContraction(
        initial_distance=1.0, contraction_kappa=0.5, critical_threshold=0.25
    ).verify_convergence()
    assert exact_half["guaranteed_steps_k_star"] == 3
    assert exact_half["final_distance"] < 0.25
    assert exact_half["contraction_verified"] is True

    with pytest.raises(ValueError):
        MetricResetContraction(initial_distance=1.0, contraction_kappa=1.0, critical_threshold=0.1)

    v_ok = VR22VitalityEvaluator(value=3.0, complexity=2.0)
    assert v_ok.vitality_ratio == pytest.approx(1.5)
    assert v_ok.vitality_ok is True

    with pytest.raises(ValueError):
        VR22VitalityEvaluator(value=3.0, complexity=0.0)


def test_supela_math_unification_mcp_and_cli() -> None:
    report = run_supela_math_unification(validator_name="Jean-François Gadbois")
    assert report["human_test_validation"]["validator"] == "Jean-François Gadbois"
    assert report["human_test_validation"]["universal_claim"] is False
    assert report["mat_00_monotone_k"] is True
    assert report["mat_00_tzi_metric_contraction"]["contraction_verified"] is True
    assert report["mat_01_authority_bounded"] is True
    assert report["mat_01_lattice_axioms"]["all_axioms_verified"] is True
    assert report["mat_03_vr22_vitality"]["vitality_ok"] is True
    assert report["mat_04_hlp_distinct"] is True
    assert report["mat_06_improvement_not_authorization"] is True
    assert report["mat_07_loss_zero_grad_nonzero"] is True
    assert report["mat_07_grpo_analysis"]["max_finite_diff_error"] < 1e-7
    assert report["mat_08_sgg_v2_simplex"]["metric_verified"] is True
    assert report["vr_fractal_omega_aggregation"]["theorem_verified"] is True
    assert report["generic_thermodynamics"]["generic_valid"] is True
    assert report["generic_thermodynamics"]["m_positive_semidefinite"] is True
    assert report["generic_thermodynamics"]["l_non_trivial"] is True

    assert "omega_math_supela_eval" in {t["name"] for t in TOOLS_SPEC}
    mcp_res = call_tool("omega_math_supela_eval", {"validator_name": "Jean-François Gadbois"})
    assert mcp_res["generic_thermodynamics"]["generic_valid"] is True
    assert mcp_res["vr_fractal_omega_aggregation"]["theorem_verified"] is True

    assert network_bus_main(["math-eval", "--validator", "Jean-François Gadbois"]) == 0
