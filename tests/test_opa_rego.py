from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import pytest

from omega_zero.harness import evaluate_escalation_protocol

ROOT_DIR = Path(__file__).resolve().parents[1]
OPA_CANDIDATE = ROOT_DIR / ".venv" / "bin" / "opa"
OPA_BIN = str(OPA_CANDIDATE) if OPA_CANDIDATE.exists() else shutil.which("opa")


@pytest.mark.skipif(OPA_BIN is None, reason="OPA CLI non installé")
def test_opa_fmt_check_and_16_rego_refutation_tests() -> None:
    fmt = subprocess.run(
        [OPA_BIN, "fmt", "--diff", "policies/", "tests/rego/"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    assert fmt.stdout.strip() == ""

    subprocess.run(
        [OPA_BIN, "check", "--strict", "policies/", "tests/rego/"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )

    res = subprocess.run(
        [OPA_BIN, "test", "policies/", "tests/rego/", "-v"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    assert "PASS: 16/16" in res.stdout


@pytest.mark.skipif(OPA_BIN is None, reason="OPA CLI non installé")
def test_opa_evaluates_live_harness_report_to_allow_human_review(tmp_path: Path) -> None:
    report = evaluate_escalation_protocol(
        ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json",
        ROOT_DIR / "schemas",
    )
    now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
    opa_input = {
        "protocol": {"sha256": report["protocol_sha256"]},
        "attestation": {
            "producer_id": "omega-harness-pytest",
            "provenance": "HARNAIS_TEST_ESCALADE_4D.py",
            "signature": "c2lnYXR1cmU=",
            "nonce": "nonce-live-01",
            "timestamp": now_iso,
            "protocol_sha256": report["protocol_sha256"],
        },
        "ledger": {"mode": "append-only", "tamper_detected": False},
        "ci_cd": {"branch": "refs/heads/main", "direct_commit_to_main": False},
        "report": report,
        "raccords": [
            {
                "id": "R-002",
                "status": "SUPPORTE_SOUS_CONDITIONS",
                "authority_level": 2,
                "evidence_level": 2,
                "is_emergent": False,
                "validation_required": False,
                "origin_type": "PROOF_TESTED",
            },
            {
                "id": "R-EMERGENT-MED-PREV",
                "status": "CANDIDAT",
                "authority_level": 0,
                "evidence_level": 0,
                "is_emergent": True,
                "validation_required": True,
                "origin_type": "COMPOSITION",
            },
        ],
        "manques": [{"id": "M-001", "statut": "SOUS_EXPLORATION", "silently_deleted": False}],
        "manque_transitions": [{"from": "OUVERT", "to": "SOUS_EXPLORATION"}],
        "revidage_tx": {
            "clean_executed_before_commit": False,
            "stage_sequence": ["PREPARE", "VERIFY", "COMMIT", "CLEAN"],
            "verify_predicates": {
                "ACK": True,
                "HashMatch": True,
                "ProvenanceOK": True,
                "AuthorityOK": True,
                "ReconstructionPASS": True,
            },
        },
    }
    input_file = tmp_path / "opa_live_input.json"
    input_file.write_text(json.dumps(opa_input), encoding="utf-8")

    eval_res = subprocess.run(
        [
            OPA_BIN,
            "eval",
            "--format=json",
            "--data",
            "policies/omega_zero_invariants.rego",
            "--input",
            str(input_file),
            "data.supela.omega_zero.governance.allow_human_review",
        ],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        check=True,
    )
    parsed = json.loads(eval_res.stdout)
    assert parsed["result"][0]["expressions"][0]["value"] is True
