from __future__ import annotations

import itertools

from hypothesis import given, settings
from hypothesis import strategies as st

from omega_zero import (
    AuthorityLevel,
    CloudOmega,
    Manque,
    ManqueStatus,
    OmegaZeroEngine,
    Pi0Projector,
    Raccord,
    RaccordStatus,
    SupelaGRPOBridge,
)


def test_e3_exhaustive_all_24_permutations_preserve_authority_and_provenance() -> None:
    """Prouve exhaustivement sur les 4! = 24 permutations que Order(Δi) ⇏ Authority(Δi)."""
    reference_authorities = None
    reference_log_by_delta = None

    for perm in itertools.permutations(["L1", "L2", "L3", "L4"]):
        engine = OmegaZeroEngine()
        nodes = {
            "L1": engine.register_local_node("L1", "Montréal", "Québec-Canada", "AUTORITE_LOCALE_L1"),
            "L2": engine.register_local_node("L2", "Paris", "France-UE", "AUTORITE_LOCALE_L2"),
            "L3": engine.register_local_node("L3", "Dakar", "Sénégal-UEMOA", "AUTORITE_LOCALE_L3"),
            "L4": engine.register_local_node("L4", "Tokyo", "Japon", "AUTORITE_LOCALE_L4"),
        }
        deltas = {
            "L1": engine.build_delta(nodes["L1"], "Δ-L1", "t1", {"raccords": [{"id": "R-002", "label": "Collectif", "status": "CANDIDAT"}]}),
            "L2": engine.build_delta(nodes["L2"], "Δ-L2", "t2", {"raccords": [{"id": "R-002", "label": "Collectif L2", "status": "CANDIDAT"}]}, contradictions=["C-001"]),
            "L3": engine.build_delta(nodes["L3"], "Δ-L3", "t3", {"raccords": [{"id": "R-004", "label": "Interdit", "status": "CANDIDAT"}]}),
            "L4": engine.build_delta(nodes["L4"], "Δ-L4", "t4", {"raccords": [{"id": "R-003", "label": "Revue", "status": "CANDIDAT"}]}),
        }

        for nid in perm:
            engine.merge_delta(deltas[nid])

        by_delta = {
            m["delta_id"]: (m["node_id"], m["jurisdiction"], m["authority_scope"], tuple(m["contradictions"]))
            for m in engine.cloud.merge_log
        }
        if reference_log_by_delta is None:
            reference_log_by_delta = by_delta
            reference_authorities = dict(engine.cloud.authorities)
        else:
            assert by_delta == reference_log_by_delta
            assert dict(engine.cloud.authorities) == reference_authorities


@settings(max_examples=50)
@given(
    raccord_specs=st.lists(
        st.tuples(
            st.sampled_from([
                RaccordStatus.CANDIDAT,
                RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
                RaccordStatus.REFUTE,
                RaccordStatus.INCONNU,
                RaccordStatus.ETABLI,
            ]),
            st.sampled_from(list(AuthorityLevel)),
            st.sampled_from(list(AuthorityLevel)),
        ),
        min_size=1,
        max_size=12,
    ),
    manque_statuses=st.lists(st.sampled_from(list(ManqueStatus)), min_size=1, max_size=8),
)
def test_hypothesis_pi0_idempotence_and_authority_bounds(
    raccord_specs: list[tuple[RaccordStatus, AuthorityLevel, AuthorityLevel]],
    manque_statuses: list[ManqueStatus],
) -> None:
    omega = CloudOmega()
    omega.authorities["DISC:DROIT"] = "DROIT"

    for idx, (status, claimed_auth, ev_level) in enumerate(raccord_specs):
        omega.raccords[f"R-{idx}"] = Raccord(
            id=f"R-{idx}",
            label=f"Raccord {idx}",
            source="A",
            target="B",
            origin_node="L1",
            status=status,
            authority_level=claimed_auth,
            evidence_level=ev_level,
            provenance=f"L1:t{idx}",
        )

    for idx, mstat in enumerate(manque_statuses):
        omega.manques[f"M-{idx}"] = Manque(
            id=f"M-{idx}",
            question=f"Q-{idx}",
            contexte="fuzz",
            origine="S0",
            dependances=["D1"],
            autorite="AUCUNE",
            temps=f"t{idx}",
            statut=mstat,
        )

    proj = Pi0Projector()
    z1 = proj.project(omega)
    z2 = proj.project(z1)

    assert z1.is_non_empty()
    assert z1.canonical_hash() == z2.canonical_hash()

    # Aucun raccord réfuté ne garde d'autorité concluante
    for r_ref in z1.refutations.values():
        assert r_ref["authority"] == AuthorityLevel.AUCUNE.name

    # Toute preuve conservée respecte Autorité <= Preuve
    for pval in z1.proofs.values():
        assert AuthorityLevel[pval["authority"]] <= AuthorityLevel[pval["evidence"]]

    # Tout manque non RÉSOLU survit à Π₀
    for idx, mstat in enumerate(manque_statuses):
        if mstat != ManqueStatus.RESOLU:
            assert f"M-{idx}" in z1.manques


@settings(max_examples=40)
@given(
    theta=st.lists(st.floats(min_value=-3.0, max_value=3.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=6),
    rewards=st.lists(st.floats(min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False), min_size=3, max_size=6),
)
def test_hypothesis_grpo_zero_loss_property(theta: list[float], rewards: list[float]) -> None:
    k = min(len(theta), len(rewards))
    t = theta[:k]
    r = rewards[:k]
    analysis = SupelaGRPOBridge.analyze_zero_loss_nonzero_grad(t, r)
    assert abs(analysis.scalar_loss) < 1e-10
    for g_a, g_fd in zip(analysis.analytical_grad, analysis.finite_diff_grad):
        assert abs(g_a - g_fd) < 1e-4
