from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

from omega_zero.guard_kernel import (
    AccessibilityMode,
    CompressionFailureError,
    CompressionLevel,
    G5Decision,
    GenerationStage,
    GuardKernelError,
    KernelObjectStatus,
    SemanticResidue,
    SupelaGuardKernel,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
GK_SCHEMA = json.loads((ROOT_DIR / "schemas" / "supela_guard_kernel_1.schema.json").read_text(encoding="utf-8"))


def test_g0_requires_identity_author_origin_and_non_empty_content() -> None:
    kernel = SupelaGuardKernel()
    with pytest.raises(GuardKernelError):
        kernel.create_g0_object(
            object_id="",
            object_type="note",
            content=b"abc",
            author="jean",
            origin="local",
            creation_context="test",
        )
    with pytest.raises(GuardKernelError):
        kernel.create_g0_object(
            object_id="OBJ-EMPTY",
            object_type="note",
            content=b"",
            author="jean",
            origin="local",
            creation_context="test",
        )


def test_c0_and_c1_zlib_lossless_roundtrip_and_schema_validation() -> None:
    kernel = SupelaGuardKernel()
    payload = b"Contenu normatif Supela Omega-ZERO avec preuves et limites reproductibles." * 4
    kernel.create_g0_object(
        object_id="OBJ-C1-01",
        object_type="dossier_epistemique",
        content=payload,
        author="jean",
        origin="omega-zero-4d",
        creation_context="test_c1",
        dependencies=["PI0", "SUP-ICI-01"],
        proof_refs=["TRACE-01"],
    )
    _, rec_g1 = kernel.compress_and_advance(
        "OBJ-C1-01",
        target_generation=GenerationStage.G1,
        compression_level=CompressionLevel.C0,
        reason="Entree en generation de travail",
        transformation="promote_g0_to_g1",
    )
    obj_g2, rec_g2 = kernel.compress_and_advance(
        "OBJ-C1-01",
        target_generation=GenerationStage.G2,
        compression_level=CompressionLevel.C1,
        reason="Compression reversible C1 avant validation",
        transformation="zlib_level9",
    )

    Draft202012Validator(GK_SCHEMA).validate(rec_g1.to_dict())
    Draft202012Validator(GK_SCHEMA).validate(rec_g2.to_dict())
    assert rec_g2.reversible is True
    assert obj_g2.accessibility_mode == AccessibilityMode.RECONSTRUCTIBLE
    assert kernel.decompress_c1("OBJ-C1-01") == payload


def test_c2_semantic_residue_non_reclaimed_and_never_full_copy() -> None:
    kernel = SupelaGuardKernel()
    kernel.create_g0_object(
        object_id="OBJ-C2-01",
        object_type="exploration_note",
        content=b"Texte complet d'une piste non encore reclamee",
        author="jean",
        origin="grpo_bridge",
        creation_context="cycle_test",
        dependencies=["M-001"],
        contradictions=["CONTRA-01"],
    )
    kernel.compress_and_advance(
        "OBJ-C2-01",
        target_generation=GenerationStage.G1,
        compression_level=CompressionLevel.C0,
        reason="Passage G1",
        transformation="g0_to_g1",
    )
    kernel.compress_and_advance(
        "OBJ-C2-01",
        target_generation=GenerationStage.G2,
        compression_level=CompressionLevel.C0,
        reason="Passage G2",
        transformation="g1_to_g2",
    )

    # Interdit : presenter C2 comme copie complete
    with pytest.raises(CompressionFailureError):
        kernel.compress_and_advance(
            "OBJ-C2-01",
            target_generation=GenerationStage.G4,
            compression_level=CompressionLevel.C2,
            reason="Compactage C2",
            transformation="g2_to_g4_c2",
            claim_full_copy=True,
        )

    # Interdit : heriter silencieusement d'une autorite
    with pytest.raises(GuardKernelError):
        kernel.compress_and_advance(
            "OBJ-C2-01",
            target_generation=GenerationStage.G4,
            compression_level=CompressionLevel.C2,
            reason="Compactage C2",
            transformation="g2_to_g4_c2",
            inherit_authority_silently=True,
        )

    obj_g4, rec_g4 = kernel.compress_and_advance(
        "OBJ-C2-01",
        target_generation=GenerationStage.G4,
        compression_level=CompressionLevel.C2,
        reason="Sortie provisoire vers NON-RECLAME",
        transformation="extract_semantic_residue",
    )
    Draft202012Validator(GK_SCHEMA).validate(rec_g4.to_dict())
    assert obj_g4.status == KernelObjectStatus.NON_RECLAME
    assert obj_g4.accessibility_mode == AccessibilityMode.REFERENTIAL
    assert rec_g4.reversible is False
    assert obj_g4.residue is not None
    assert obj_g4.residue.contradictions == ["CONTRA-01"]

    # Le schema Draft 2020-12 rejette une fiche C2 déclarée reversible=True
    invalid_c2 = dict(rec_g4.to_dict())
    invalid_c2["reversible"] = True
    with pytest.raises(ValidationError):
        Draft202012Validator(GK_SCHEMA).validate(invalid_c2)


def test_hypothese_promotion_rules_and_semantic_loss_detection() -> None:
    kernel = SupelaGuardKernel()
    obj = kernel.create_g0_object(
        object_id="OBJ-HYP-01",
        object_type="hypothese",
        content=b"Hypothese candidate",
        author="jean",
        origin="local_node",
        creation_context="test_hyp",
        status=KernelObjectStatus.HYPOTHESE,
        dependencies=["DEP-1"],
        proof_refs=["PROOF-INIT"],
        contradictions=["C-ACTIVE"],
    )

    # Sans preuve nouvelle, HYPOTHESE -> FAIT est interdit par compression
    with pytest.raises(GuardKernelError):
        kernel.compress_and_advance(
            "OBJ-HYP-01",
            target_generation=GenerationStage.G1,
            compression_level=CompressionLevel.C0,
            reason="Tentative promotion sans preuve",
            transformation="illegal_promote",
            new_status=KernelObjectStatus.FAIT,
        )

    # Test de perte de sens : effacement de provenance, contradiction ou preuve -> COMPRESSION-FAIL
    bad_residue = SemanticResidue(
        identity={"id": obj.object_id, "type": obj.object_type},
        provenance={"author": obj.author, "origin": ""},
        original_hash=obj.original_hash,
        status=KernelObjectStatus.FAIT.value,
        scope=obj.scope,
        dependencies=[],
        transformation="compress",
        reason="motif",
        reopening_conditions=[],
        location="",
        proof_refs=[],
        contradictions=[],
    )
    loss = SupelaGuardKernel.run_semantic_loss_test(obj, bad_residue, reversible=False)
    assert loss.passed is False
    assert loss.verdict == "COMPRESSION-FAIL"
    assert "q2_origin" in loss.missing_answers
    assert "q4_status" in loss.missing_answers
    assert "q6_contradictions_preserved" in loss.missing_answers
    assert "q8_proofs_preserved" in loss.missing_answers

    # Avec nouvelle preuve explicite, la promotion vers FAIT est permise
    promoted, rec = kernel.compress_and_advance(
        "OBJ-HYP-01",
        target_generation=GenerationStage.G1,
        compression_level=CompressionLevel.C0,
        reason="Preuve reproductible ajoutee",
        transformation="promote_with_proof",
        new_status=KernelObjectStatus.FAIT,
        added_proofs=["PROOF-EXPER-02"],
    )
    assert promoted.status == KernelObjectStatus.FAIT
    assert rec.semantic_loss_passed is True


def test_reclaim_from_g4_and_last_passage_g5_preserves_rejection_register() -> None:
    kernel = SupelaGuardKernel()
    kernel.create_g0_object(
        object_id="OBJ-LIFE-01",
        object_type="artefact",
        content=b"Cycle complet G0..G5",
        author="jean",
        origin="omega-zero-4d",
        creation_context="lifecycle",
        dependencies=["D1"],
    )
    kernel.compress_and_advance(
        "OBJ-LIFE-01",
        target_generation=GenerationStage.G1,
        compression_level=CompressionLevel.C0,
        reason="G1",
        transformation="step1",
    )
    kernel.compress_and_advance(
        "OBJ-LIFE-01",
        target_generation=GenerationStage.G2,
        compression_level=CompressionLevel.C0,
        reason="G2",
        transformation="step2",
    )
    kernel.compress_and_advance(
        "OBJ-LIFE-01",
        target_generation=GenerationStage.G4,
        compression_level=CompressionLevel.C2,
        reason="En G4 avant reclamation",
        transformation="step4",
    )

    reclaimed, rec_reclaim = kernel.reclaim_from_g4(
        "OBJ-LIFE-01",
        target_generation=GenerationStage.G2,
        trigger_reason="Nouvelle dependance critique",
    )
    assert reclaimed.generation == GenerationStage.G2
    assert reclaimed.status == KernelObjectStatus.RECLAME
    Draft202012Validator(GK_SCHEMA).validate(rec_reclaim.to_dict())

    # G5 direct depuis G2 est interdit (doit repasser par G4)
    with pytest.raises(GuardKernelError):
        kernel.last_passage_g5(
            "OBJ-LIFE-01",
            decision=G5Decision.REJET_JUSTIFIE,
            dependencies_checked=True,
            reason="Hors G4",
            human_ratified=True,
        )

    kernel.compress_and_advance(
        "OBJ-LIFE-01",
        target_generation=GenerationStage.G4,
        compression_level=CompressionLevel.C2,
        reason="Retour en G4",
        transformation="g2_to_g4",
    )

    with pytest.raises(GuardKernelError):
        kernel.last_passage_g5(
            "OBJ-LIFE-01",
            decision=G5Decision.REJET_JUSTIFIE,
            dependencies_checked=False,
            reason="Dependances non verifiees",
            human_ratified=True,
        )

    with pytest.raises(GuardKernelError):
        kernel.last_passage_g5(
            "OBJ-LIFE-01",
            decision=G5Decision.REJET_JUSTIFIE,
            dependencies_checked=True,
            reason="Sans validation humaine",
            human_ratified=False,
        )

    final_obj, rec_g5 = kernel.last_passage_g5(
        "OBJ-LIFE-01",
        decision=G5Decision.REJET_JUSTIFIE,
        dependencies_checked=True,
        reason="Rejet justifie apres audit des dependances",
        human_ratified=True,
    )
    Draft202012Validator(GK_SCHEMA).validate(rec_g5.to_dict())
    assert final_obj.generation == GenerationStage.G5
    assert rec_g5.authority == "RATIFIED_HUMAN"
    assert len(kernel.rejection_registry) == 1
    assert kernel.rejection_registry[0]["historical_existence_preserved"] is True
    assert kernel.rejection_registry[0]["object_id"] == "OBJ-LIFE-01"
