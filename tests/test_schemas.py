from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT_DIR / "schemas"
CONST_DIR = ROOT_DIR / "docs" / "constitution"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.mark.parametrize(
    ("schema_name", "doc_name"),
    [
        ("projection_pi0.schema.json", "DEFINITION_P0_PROJECTION.json"),
        ("manque_statut.schema.json", "STATUT_MANQUE.json"),
        ("exemple_cycle_p0.schema.json", "TEST_P0_EXEMPLE.json"),
        ("exemple_cycle_p0.schema.json", "TEST_P0_EXEMPLE_SEC_DOMAINE.json"),
        ("plan_4d_omega_zero_esc_01.schema.json", "PLAN-4D-ΩZERO-ESC-01.json"),
    ],
)
def test_all_constitutional_documents_validate_draft_2020_12(
    schema_name: str, doc_name: str
) -> None:
    schema = _load(SCHEMA_DIR / schema_name)
    doc = _load(CONST_DIR / doc_name)
    Draft202012Validator.check_schema(schema)
    Draft202012Validator(schema).validate(doc)


def test_plan_has_exact_8_paliers_and_10_unique_conditions() -> None:
    plan = _load(CONST_DIR / "PLAN-4D-ΩZERO-ESC-01.json")
    palier_ids = [p["id"] for p in plan["paliers"]]
    assert palier_ids == ["E0", "E1", "E2", "E3", "E4", "E5", "E6", "E7"]

    assigned_conditions = [cid for p in plan["paliers"] for cid in p["condition_ids"]]
    assert len(assigned_conditions) == 10
    assert set(assigned_conditions) == {f"C{i:02d}" for i in range(1, 11)}

    matrix_pairs = {(row["id"], row["palier"]) for row in plan["matrix_normative"]}
    palier_pairs = {
        (cid, p["id"]) for p in plan["paliers"] for cid in p["condition_ids"]
    }
    assert matrix_pairs == palier_pairs

    e7 = next(p for p in plan["paliers"] if p["id"] == "E7")
    assert {s["id"] for s in e7["sub_tests"]} == {"E7-A", "E7-B"}


def test_statut_manque_has_all_7_canonical_statuses() -> None:
    doc = _load(CONST_DIR / "STATUT_MANQUE.json")
    codes = {s["code"] for s in doc["statuts"]}
    assert codes == {
        "OUVERT",
        "SOUS_EXPLORATION",
        "PARTIELLEMENT_RÉDUIT",
        "RÉSOLU",
        "RÉFUTÉ_COMME_PROBLÈME",
        "REQUALIFIÉ",
        "INACCESSIBLE_DANS_LE_PÉRIMÈTRE",
    }


def test_negative_truncated_plan_rejected_by_schema() -> None:
    schema = _load(SCHEMA_DIR / "plan_4d_omega_zero_esc_01.schema.json")
    truncated = {
        "schema": "PLAN-4D-ΩZERO-ESC-01/1",
        "title": "Plan tronqué",
        "version": "1.0.0",
        "status": "PROTOCOLE_CORRIGE_READY",
        "palier_count": 8,
        "condition_count": 10,
    }
    with pytest.raises(ValidationError):
        Draft202012Validator(schema).validate(truncated)
