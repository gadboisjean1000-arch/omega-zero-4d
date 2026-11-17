from __future__ import annotations

from omega_zero.mcp_server import TOOLS_SPEC, call_tool
from omega_zero.network_bus import main as network_bus_main
from omega_zero.supela_math_core import (
    BoundedAuthorityEvaluation,
    GenericThermodynamicStep,
    ProofLatticeLevel,
    SupelaStateTuple,
    ThreeDimensionalSeparation,
    run_supela_math_unification,
)


def test_mat00_monotonicity_and_reset_c() -> None:
    s0 = SupelaStateTuple(provenance=["p0"], evidence=["e0"], contradictions=["c0"], knowledge_register=frozenset({"K0"}))
    s1 = s0.advance({"K1"}, new_provenance="p1")
    assert s0.knowledge_register.issubset(s1.knowledge_register)
    s2 = s1.reset_contradictions_only_in_c()
    assert s2.contradictions == []
    assert s1.knowledge_register == s2.knowledge_register


def test_mat01_mat04_mat06_and_generic_thermodynamics() -> None:
    auth = BoundedAuthorityEvaluation("OBJ", ProofLatticeLevel.G1_OBSERVE, requested_authority=4, improvement_score=1.0)
    assert auth.granted_authority == 1
    assert auth.authority_bounded_ok is True
    assert auth.auto_authorized_by_improvement is False

    hlp = ThreeDimensionalSeparation("h_sha", "local_ctx", "p_sha")
    assert hlp.dimensions_distinct is True

    generic = GenericThermodynamicStep(
        grad_e=(2.0, 0.0),
        grad_s=(0.0, 1.0),
        l_matrix=((0.0, 0.0), (0.0, 0.0)),
        m_matrix=((0.0, 0.0), (0.0, 0.5)),
    )
    res = generic.verify_invariants()
    assert res["generic_valid"] is True
    assert res["energy_conserved"] is True
    assert res["entropy_non_decreasing"] is True


def test_supela_math_unification_mcp_and_cli() -> None:
    report = run_supela_math_unification(validator_name="Jean-François Gadbois")
    assert report["human_test_validation"]["validator"] == "Jean-François Gadbois"
    assert report["human_test_validation"]["universal_claim"] is False
    assert report["mat_00_monotone_k"] is True
    assert report["mat_01_authority_bounded"] is True
    assert report["mat_04_hlp_distinct"] is True
    assert report["mat_06_improvement_not_authorization"] is True
    assert report["mat_07_loss_zero_grad_nonzero"] is True
    assert report["generic_thermodynamics"]["generic_valid"] is True

    assert "omega_math_supela_eval" in {t["name"] for t in TOOLS_SPEC}
    mcp_res = call_tool("omega_math_supela_eval", {"validator_name": "Jean-François Gadbois"})
    assert mcp_res["generic_thermodynamics"]["generic_valid"] is True

    assert network_bus_main(["math-eval", "--validator", "Jean-François Gadbois"]) == 0
