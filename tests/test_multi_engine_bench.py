from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

from omega_zero import (
    BenchOutcome,
    BenchVerdict,
    EngineRecordStatus,
    EngineResult,
    EngineRunRecord,
    MultiEngineBenchError,
    SupelaMultiEngineBench,
    TruthLevel,
)
from omega_zero.mcp_server import call_tool

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "schemas" / "supela_multi_engine_bench_1.schema.json"


def _validate_against_schema(payload: dict[str, object]) -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    jsonschema.validate(instance=payload, schema=schema)


def test_three_engines_saying_true_without_proof_never_constitutes_proof() -> None:
    records = [
        EngineRunRecord(
            objet="OBJ-VOTE-01",
            moteur="Copilot",
            version="2026.11",
            referentiel="learn.microsoft.com",
            premisses=("P1",),
            methode="heuristique_web",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
        ),
        EngineRunRecord(
            objet="OBJ-VOTE-01",
            moteur="IA_X",
            version="1.0",
            referentiel="corpus_generique",
            premisses=("P1",),
            methode="generation_llm",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
        ),
        EngineRunRecord(
            objet="OBJ-VOTE-01",
            moteur="Supela",
            version="omega-zero-4d",
            referentiel="SUPELA-SPEC",
            premisses=("P1",),
            methode="projection_pi0",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
        ),
    ]
    report = SupelaMultiEngineBench.evaluate(records)
    assert report.vote_interdit is True
    assert report.convergence_n_est_pas_preuve is True
    assert report.outcome == BenchOutcome.CONVERGENCE
    assert report.verdict_banc == BenchVerdict.CONVERGENCE_SANS_PREUVE
    assert report.statut_verite == TruthLevel.NON_ETABLI
    assert report.promotion_autorisee is False
    assert report.supela_en_defaut is False
    assert len(report.report_sha256) == 64
    _validate_against_schema(report.to_dict())


def test_divergence_is_preserved_as_bench_data() -> None:
    records = [
        EngineRunRecord(
            objet="OBJ-DIV-01",
            moteur="Copilot",
            version="2026.11",
            referentiel="M365-Learn",
            premisses=("WorkIQ",),
            methode="search_rag",
            resultat=EngineResult.VRAI,
            preuve_fournie="Citation Learn §1.4",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
        ),
        EngineRunRecord(
            objet="OBJ-DIV-01",
            moteur="Formel_Math",
            version="z3-local",
            referentiel="SUP-PROV-TRACE-01",
            premisses=("WorkIQ",),
            methode="verification_formelle",
            resultat=EngineResult.INDETERMINE,
            preuve_fournie="Divergence UI web vs Teams non documentée",
            preuve_verifiee=True,
            contradictions=("UI web ne respecte pas la politique Allow web search",),
            statut=EngineRecordStatus.INDETERMINE,
        ),
    ]
    report = SupelaMultiEngineBench.evaluate(records)
    assert report.outcome == BenchOutcome.DIVERGENCE
    assert report.verdict_banc == BenchVerdict.DIVERGENCE_CONSERVEE
    assert report.promotion_autorisee is False
    assert len(report.contradictions_consolidees) >= 2
    _validate_against_schema(report.to_dict())


def test_supela_en_defaut_when_supela_contradicts_verified_proof() -> None:
    records = [
        EngineRunRecord(
            objet="OBJ-SYMMETRY-01",
            moteur="Formel_Math",
            version="lean4-local",
            referentiel="Axiome-TZI",
            premisses=("A1", "A2"),
            methode="preuve_formelle",
            resultat=EngineResult.FAUX,
            preuve_fournie="Contre-exemple constructif x=0",
            preuve_verifiee=True,
            statut=EngineRecordStatus.REFUTE,
        ),
        EngineRunRecord(
            objet="OBJ-SYMMETRY-01",
            moteur="Supela",
            version="k3-omega",
            referentiel="SUPELA-SPEC",
            premisses=("A1", "A2"),
            methode="heuristique_locale",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
        ),
    ]
    report = SupelaMultiEngineBench.evaluate(records)
    assert report.supela_en_defaut is True
    assert report.verdict_banc == BenchVerdict.SUPELA_EN_DEFAUT
    assert report.promotion_autorisee is False
    assert any("SUPELA_EN_DÉFAUT" in c for c in report.contradictions_consolidees)
    _validate_against_schema(report.to_dict())


def test_supela_en_defaut_on_unproven_auto_promotion_attempt() -> None:
    records = [
        EngineRunRecord(
            objet="OBJ-SELF-JUDGE-01",
            moteur="Copilot",
            version="2026.11",
            referentiel="R1",
            premisses=("P1",),
            methode="rag",
            resultat=EngineResult.INDETERMINE,
            preuve_fournie="",
            statut=EngineRecordStatus.INDETERMINE,
        ),
        EngineRunRecord(
            objet="OBJ-SELF-JUDGE-01",
            moteur="Supela",
            version="k3-omega",
            referentiel="R1",
            premisses=("P1",),
            methode="auto_arbitrage",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.CANDIDAT,
            auto_promotion_tentee=True,
        ),
    ]
    report = SupelaMultiEngineBench.evaluate(records)
    assert report.supela_en_defaut is True
    assert report.verdict_banc == BenchVerdict.SUPELA_EN_DEFAUT
    assert report.promotion_autorisee is False
    _validate_against_schema(report.to_dict())


def test_fail_closed_validation_and_mcp_tool() -> None:
    with pytest.raises(MultiEngineBenchError):
        EngineRunRecord(
            objet="OBJ-ERR",
            moteur="Supela",
            version="1.0",
            referentiel="R",
            premisses=(),
            methode="test",
            resultat=EngineResult.VRAI,
            preuve_fournie="",
            preuve_verifiee=False,
            statut=EngineRecordStatus.PROUVE,
        )

    mcp_res = call_tool(
        "omega_multi_engine_bench",
        {
            "runs": [
                {
                    "objet": "OBJ-MCP-01",
                    "moteur": "Copilot",
                    "version": "2026.11",
                    "referentiel": "REF-1",
                    "premisses": ["P1"],
                    "methode": "rag",
                    "resultat": "VRAI",
                    "preuve_fournie": "sha256:abc",
                    "preuve_verifiee": True,
                    "statut": "PROUVE",
                },
                {
                    "objet": "OBJ-MCP-01",
                    "moteur": "Supela",
                    "version": "4d",
                    "referentiel": "REF-1",
                    "premisses": ["P1"],
                    "methode": "pi0",
                    "resultat": "VRAI",
                    "preuve_fournie": "sha256:def",
                    "preuve_verifiee": True,
                    "statut": "PROUVE",
                },
            ]
        },
    )
    assert mcp_res["verdict_banc"] == "CONVERGENCE_ETAYEE_A_RATIFIER"
    assert mcp_res["promotion_autorisee"] is True
    assert mcp_res["ratification_humaine_requise"] is True
    _validate_against_schema(mcp_res)
