from __future__ import annotations

from pathlib import Path

import pytest

from omega_zero import (
    Container,
    LoadMetricDeclaration,
    OmegaZeroEngine,
    RevidageFailure,
    RevidageStage,
    SaturationWithoutDeclarationError,
)
from omega_zero.harness import FaultInjection, evaluate_escalation_protocol

ROOT_DIR = Path(__file__).resolve().parents[1]
PROTOCOL_PATH = ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json"
SCHEMA_DIR = ROOT_DIR / "schemas"


def test_escalation_4d_full_positive_execution() -> None:
    report = evaluate_escalation_protocol(PROTOCOL_PATH, SCHEMA_DIR)
    assert report["verdict"] == "PASS"
    assert report["promotion"] == "ADMISSIBLE_A_REVUE_HUMAINE"
    assert report["trace_preserved"] is True
    assert report["cone_to_recalculate"] == []
    assert len(report["palier_results"]) == 8
    assert all(p["status"] == "PASS" for p in report["palier_results"])

    e7 = next(p for p in report["palier_results"] if p["palier_id"] == "E7")
    assert e7["sub_results"] == {"E7-A": "PASS", "E7-B": "PASS"}

    assert len(report["condition_results"]) == 10
    assert {c["condition_id"] for c in report["condition_results"]} == {
        f"C{i:02d}" for i in range(1, 11)
    }
    assert all(c["status"] == "PASS" for c in report["condition_results"])


@pytest.mark.parametrize(
    "fail_cond",
    ["C01", "C02", "C03", "C04", "C05", "C06", "C07", "C08", "C09", "C10"],
)
def test_negative_critical_failures_block_promotion(fail_cond: str) -> None:
    report = evaluate_escalation_protocol(
        PROTOCOL_PATH,
        SCHEMA_DIR,
        fault=FaultInjection(fail_condition=fail_cond),
    )
    assert report["verdict"] == "FAIL"
    assert report["promotion"] == "BLOQUEE"
    assert report["trace_preserved"] is True
    assert any(fail_cond in item for item in report["cone_to_recalculate"])

    target = next(
        c for c in report["condition_results"] if c["condition_id"] == fail_cond
    )
    assert target["status"] == "FAIL"


def test_revidage_rollback_on_verify_failure_and_premature_clean() -> None:
    engine = OmegaZeroEngine()
    node = engine.register_local_node("L1", "Montréal", "Québec", "LOCALE")
    node.D_observations.append({"sample": 42})
    delta = engine.build_delta(node, "D1", "t1", {"raccords": []})

    engine.prepare_revidage(node, delta)
    # Échec sur reconstruction_pass=False => ROLLBACK_LOCAL, données conservées
    ok = engine.verify_revidage(
        node,
        ack=True,
        hash_match=True,
        provenance_ok=True,
        authority_ok=True,
        reconstruction_pass=False,
    )
    assert ok is False
    assert node.revidage_stage == RevidageStage.ROLLED_BACK
    assert len(node.D_observations) == 1

    # Tentative de CLEAN sans COMMIT => exception + données intactes
    engine.prepare_revidage(node, delta)
    with pytest.raises(RevidageFailure):
        engine.clean_revidage(node)
    assert node.revidage_stage == RevidageStage.ROLLED_BACK
    assert len(node.D_observations) == 1


def test_load_saturation_requires_pre_execution_metric_declaration() -> None:
    engine = OmegaZeroEngine()
    c1 = Container("C1", bytes_limit=1000, objects_limit=10, edges_limit=10, latency_limit_ms=50.0)
    c2 = Container("C2", bytes_limit=10000, objects_limit=100, edges_limit=100, latency_limit_ms=50.0)
    c1.add_object("OBJ-1", {"k": "v"})

    with pytest.raises(SaturationWithoutDeclarationError):
        engine.evaluate_saturation_and_migrate(c1, c2)

    c1.metric_declaration = LoadMetricDeclaration(
        metric="max_ratio",
        capacity_limit={
            "bytes_limit": 1000,
            "objects_limit": 10,
            "edges_limit": 10,
            "latency_limit_ms": 50.0,
        },
        unit="bytes/count/ms",
        measurement_method="direct",
        timestamp="2026-11-15T21:00:00Z",
        tested_environment="pytest",
    )
    res = engine.evaluate_saturation_and_migrate(c1, c2)
    assert res["migration_triggered"] is False
