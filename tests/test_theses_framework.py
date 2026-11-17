"""Tests complets du framework autonome des 6 thèses Supela (ORCID 0009-0001-5361-6795)."""

from __future__ import annotations

import json
from pathlib import Path

from omega_zero.attestation import AttestationSigner, SignedAttestation
from omega_zero.supela_math_core import ProofLatticeLevel
from omega_zero.theses import (
    ALL_THESIS_MODULES,
    ORCID_ID,
    ThesisStatus,
    thesis_architecture_3niveaux,
    thesis_dependance_souveraine,
    thesis_fase_one,
    thesis_invariant_axe01,
    thesis_luc_promise,
    thesis_verification_distrib,
)
from scripts.deposit_theses import deposit_all_theses


def test_all_six_theses_default_controle() -> None:
    assert len(ALL_THESIS_MODULES) == 6
    for mod in ALL_THESIS_MODULES:
        res = mod.verify()
        assert res.statut == ThesisStatus.CONTROLE
        assert res.orcid == ORCID_ID
        assert res.timestamp_utc.endswith("+00:00") or res.timestamp_utc.endswith("Z")
        assert len(res.cross_references) == 5


def test_all_six_theses_absent_when_none() -> None:
    for mod in ALL_THESIS_MODULES:
        res = mod.verify(None)
        assert res.statut == ThesisStatus.ABSENT


def test_thesis_1_indetermine_on_missing_question() -> None:
    incomplete = thesis_invariant_axe01.FiveQuestionsFrame(
        origine="S0",
        dependances="K_t",
        maintien="revidage",
        perte="",
        remplacement="preuve",
    )
    res = thesis_invariant_axe01.verify(incomplete)
    assert res.statut == ThesisStatus.INDETERMINE
    assert "perte" in res.details["missing"]


def test_thesis_2_indetermine_on_grey_zone() -> None:
    grey = (
        thesis_luc_promise.LucidityStatement(
            statement_id="STMT-GREY",
            visibility=thesis_luc_promise.EpistemicVisibility.ZONE_GRISE,
        ),
    )
    res = thesis_luc_promise.verify(grey)
    assert res.statut == ThesisStatus.INDETERMINE
    assert res.details["violations_count"] == 1


def test_thesis_3_indetermine_on_low_rank_or_claimed_independence() -> None:
    low_rank = thesis_fase_one.FaseOneCoupling(
        toi_actor="A",
        nous_collective="B",
        written_trace_id="TR-1",
        trace_rank=5,
        claimed_independence=True,
    )
    res = thesis_fase_one.verify(low_rank)
    assert res.statut == ThesisStatus.INDETERMINE


def test_thesis_4_indetermine_on_consensus_elevation_without_proof() -> None:
    probe = thesis_verification_distrib.DistributedConsensusProbe(
        validators_agreeing=100,
        total_validators=100,
        base_proof_level=ProofLatticeLevel.G1_OBSERVE,
        claimed_elevated_level=ProofLatticeLevel.G3_REPRODUIT_CROISE,
        has_reproducible_proof=False,
    )
    res = thesis_verification_distrib.verify(probe)
    assert res.statut == ThesisStatus.INDETERMINE


def test_thesis_5_indetermine_on_empty_omissions() -> None:
    arch = thesis_architecture_3niveaux.ThreeLevelArchitecture(
        n1_facts=("F1",),
        n2_decisions=("D1",),
        n3_omissions=(),
    )
    res = thesis_architecture_3niveaux.verify(arch)
    assert res.statut == ThesisStatus.INDETERMINE


def test_thesis_6_indetermine_on_external_validation_dependency() -> None:
    model = thesis_dependance_souveraine.SovereignDependencyModel(
        question_r00="De quoi dépends-tu ?",
        declared_dependencies=("dep1",),
        invalidators=thesis_dependance_souveraine.SEVEN_INVALIDATORS,
        transitions_count=25,
        requires_external_validation=True,
    )
    res = thesis_dependance_souveraine.verify(model)
    assert res.statut == ThesisStatus.INDETERMINE


def test_deposit_all_theses_end_to_end(tmp_path: Path) -> None:
    manifest = deposit_all_theses(tmp_path)
    assert manifest["orcid"] == ORCID_ID
    assert manifest["thesis_count"] == 6
    assert manifest["all_controle"] is True

    for item in manifest["theses"]:
        pdf_bytes = (tmp_path / item["pdf_file"]).read_bytes()
        assert pdf_bytes.startswith(b"%PDF-1.4")
        assert pdf_bytes.rstrip().endswith(b"%%EOF")
        meta = json.loads((tmp_path / item["metadata_file"]).read_text(encoding="utf-8"))
        assert meta["orcid"] == ORCID_ID
        assert meta["statut"] == "CONTROLE"
        assert meta["pdf_sha256"] == item["pdf_sha256"]

    assert (tmp_path / "citation_network.json").exists()
    assert (tmp_path / "theses_orcid_0009.bib").exists()
    orcid_bundle = json.loads((tmp_path / "orcid_works_v3.json").read_text(encoding="utf-8"))
    assert len(orcid_bundle["works"]) == 6
    assert orcid_bundle["remote_push_executed"] is False

    att = SignedAttestation(**manifest["attestation_ed25519"])
    manifest_core = {k: v for k, v in manifest.items() if k != "attestation_ed25519"}
    assert AttestationSigner.verify(att, manifest_core) is True
