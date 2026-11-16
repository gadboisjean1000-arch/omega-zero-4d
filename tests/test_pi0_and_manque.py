from __future__ import annotations

import pytest

from omega_zero import (
    AuthorityLevel,
    CloudOmega,
    Manque,
    ManqueStateMachine,
    ManqueStatus,
    Pi0Projector,
    Raccord,
    RaccordStatus,
    TransitionError,
)


def _sample_manque(status: ManqueStatus = ManqueStatus.OUVERT) -> Manque:
    return Manque(
        id="M-TEST-01",
        question="Peut-on valider ce transfert ?",
        contexte="Test unitaire",
        origine="S_0",
        dependances=["D1", "D2"],
        autorite="AUCUNE",
        temps="t0",
        statut=status,
    )


def test_all_7_manque_statuses_and_valid_lifecycle_with_reopening() -> None:
    assert len(ManqueStatus) == 7
    m = _sample_manque()

    guard1 = ManqueStateMachine.transition(
        m,
        ManqueStatus.SOUS_EXPLORATION,
        reason="Lancement exploration",
        actor="L1",
        timestamp="t1",
        evidence_ref="R-001",
    )
    assert guard1 == "TR-01"

    guard2 = ManqueStateMachine.transition(
        m,
        ManqueStatus.PARTIELLEMENT_REDUIT,
        reason="R-002 soutenu sous conditions",
        actor="CLOUD",
        timestamp="t2",
        evidence_ref="PREUVE-R002",
    )
    assert guard2 == "TR-05"

    guard3 = ManqueStateMachine.transition(
        m,
        ManqueStatus.RESOLU,
        reason="Tous les aspects prouvés",
        actor="CLOUD",
        timestamp="t3",
        evidence_ref="PREUVE-COMPLETE",
    )
    assert guard3 == "TR-12"

    # Réouverture suite à NouvellePreuve (E7-A / TR-14)
    guard4 = ManqueStateMachine.transition(
        m,
        ManqueStatus.SOUS_EXPLORATION,
        reason="NouvellePreuve contredit un cas limite",
        actor="L1",
        timestamp="t4",
        evidence_ref="NOUVELLE-PREUVE-01",
    )
    assert guard4 == "TR-14"
    assert len(m.transition_log) == 4


def test_inaccessible_and_refuted_reopening_paths() -> None:
    m_inacc = _sample_manque()
    ManqueStateMachine.transition(
        m_inacc,
        ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE,
        reason="Donnée classifiée hors périmètre",
        actor="L1",
        timestamp="t1",
        evidence_ref="BARRIERE-ACCES",
    )
    ManqueStateMachine.transition(
        m_inacc,
        ManqueStatus.OUVERT,
        reason="Accès étendu légalement",
        actor="ADMIN",
        timestamp="t2",
        evidence_ref="MANDAT-ETENDU",
    )
    assert m_inacc.statut == ManqueStatus.OUVERT

    m_ref = _sample_manque()
    ManqueStateMachine.transition(
        m_ref,
        ManqueStatus.REFUTE_COMME_PROBLEME,
        reason="Fausse prémisse prouvée",
        actor="L2",
        timestamp="t1",
        evidence_ref="CONTRE-EXEMPLE",
    )
    assert m_ref.statut == ManqueStatus.REFUTE_COMME_PROBLEME


def test_forbidden_manque_transitions_raise_error() -> None:
    # M3 : OUVERT -> RÉSOLU direct interdit
    m1 = _sample_manque(ManqueStatus.OUVERT)
    with pytest.raises(TransitionError):
        ManqueStateMachine.transition(
            m1,
            ManqueStatus.RESOLU,
            reason="Promotion directe sans exploration",
            actor="BUG",
            timestamp="t1",
            evidence_ref="FAKE",
        )

    # INACCESSIBLE -> RÉSOLU direct interdit
    m2 = _sample_manque(ManqueStatus.INACCESSIBLE_DANS_LE_PERIMETRE)
    with pytest.raises(TransitionError):
        ManqueStateMachine.transition(
            m2,
            ManqueStatus.RESOLU,
            reason="Court-circuit",
            actor="BUG",
            timestamp="t1",
            evidence_ref="FAKE",
        )

    # RÉFUTÉ_COMME_PROBLÈME -> RÉSOLU direct interdit
    m3 = _sample_manque(ManqueStatus.REFUTE_COMME_PROBLEME)
    with pytest.raises(TransitionError):
        ManqueStateMachine.transition(
            m3,
            ManqueStatus.RESOLU,
            reason="Court-circuit",
            actor="BUG",
            timestamp="t1",
            evidence_ref="FAKE",
        )

    # REQUALIFIÉ sans sous-manques enfants interdit
    m4 = _sample_manque(ManqueStatus.OUVERT)
    with pytest.raises(TransitionError):
        ManqueStateMachine.transition(
            m4,
            ManqueStatus.REQUALIFIE,
            reason="Scission sans enfants",
            actor="L1",
            timestamp="t1",
        )


def test_pi0_projection_idempotence_non_empty_and_authority_bounding() -> None:
    omega = CloudOmega()
    omega.authorities["O_P"] = "Psychologie"
    omega.manques["M1"] = _sample_manque(ManqueStatus.PARTIELLEMENT_REDUIT)
    omega.manques["M_DONE"] = _sample_manque(ManqueStatus.RESOLU)

    # Candidat non soutenu mais revendiquant faussement une autorité : Π₀ doit le retirer
    omega.raccords["R_UNPROVEN"] = Raccord(
        id="R_UNPROVEN",
        label="Candidat sans preuve",
        source="A",
        target="B",
        origin_node="L1",
        status=RaccordStatus.CANDIDAT,
        authority_level=AuthorityLevel.INTERNATIONALE_ETABLIE,
        evidence_level=AuthorityLevel.AUCUNE,
    )
    # Raccord réfuté : doit être conservé en refutations avec autorité AUCUNE
    omega.raccords["R_REFUTED"] = Raccord(
        id="R_REFUTED",
        label="Faux raccord",
        source="A",
        target="B",
        origin_node="L1",
        status=RaccordStatus.REFUTE,
        authority_level=AuthorityLevel.AUCUNE,
        evidence_level=AuthorityLevel.AUCUNE,
        refutation_reason="Contredit par expérience",
        provenance="L1:t1",
    )
    # Raccord soutenu sous conditions avec autorité > preuve : Π₀ borne l'autorité à preuve
    omega.raccords["R_COND"] = Raccord(
        id="R_COND",
        label="Soutenu localement",
        source="A",
        target="B",
        origin_node="L1",
        status=RaccordStatus.SUPPORTE_SOUS_CONDITIONS,
        authority_level=AuthorityLevel.INTERNATIONALE_ETABLIE,
        evidence_level=AuthorityLevel.LOCALE_CONDITIONNELLE,
        conditions=["Local uniquement"],
    )
    omega.history.append({"kind": "PROVISIONAL_DRAFT", "text": "brouillon jetable"})
    omega.history.append({"kind": "VERIFIED_EVENT", "text": "trace permanente"})

    proj = Pi0Projector()
    z1 = proj.project(omega)
    z2 = proj.project(z1)

    assert z1.is_non_empty()
    assert z1.canonical_hash() == z2.canonical_hash()
    assert proj.verify_idempotence(omega)
    assert "M1" in z1.manques
    assert "M_DONE" not in z1.manques
    assert "R_REFUTED" in z1.refutations
    assert z1.refutations["R_REFUTED"]["authority"] == "AUCUNE"
    assert "R_UNPROVEN:CANDIDAT" in z1.dropped_provisional
    assert z1.proofs["R_COND"]["authority"] == "LOCALE_CONDITIONNELLE"
    assert all(h["kind"] != "PROVISIONAL_DRAFT" for h in z1.history)
