from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from omega_zero import (
    AuthorityLevel,
    RaccordStatus,
    SupelaGRPOBridge,
    run_integrated_network_pipeline,
    run_network_doctor,
    verify_vr_compliance,
)

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_grpo_gf1_to_gf5_guardrails_preserve_centering_and_pi0() -> None:
    report = SupelaGRPOBridge.explore_with_guardrails(
        "M-GRPO-GF-01",
        [
            ("H-NAN", "Score non fini", float("nan")),
            ("H-OUTLIER", "Score aberrant hors borne r_max", 50.0),
            ("H-PROOF", "Piste borne et prouvee localement", 0.9),
            ("H-LOW", "Piste sous le seuil d'admission", 0.1),
        ],
        r_max=1.0,
        advantage_threshold_tau=0.0,
        proof_checker=lambda cid: (cid == "H-PROOF", "TEST_LOCAL_VALIDE" if cid == "H-PROOF" else ""),
    )

    # GF1 bloque NaN et > r_max sans contaminer la suite
    assert report.gf1_blocked_ids == ["H-NAN", "H-OUTLIER"]
    # GF2 conserve le centrage ∑A_i = 0 côté groupe tout en filtrant l'admission
    assert abs(sum(e.advantage for e in report.explorations)) < 1e-6
    assert "H-LOW" in report.gf2_filtered_ids

    # GF3 & GF4 : Π₀ préservé, jamais d'auto-promotion ÉTABLI
    assert report.gf3_pi0_preserved is True
    assert report.gf3_pi0_non_empty is True
    assert report.gf4_human_review_required is True
    assert report.promotion == "ADMISSIBLE_A_REVUE_HUMAINE"
    assert len(report.admitted_raccords) >= 1
    for r in report.admitted_raccords:
        assert r.status == RaccordStatus.CANDIDAT
        assert r.authority_level == AuthorityLevel.AUCUNE
        assert r.validation_required is True

    # GF5 : chaque trace a son empreinte canonique SHA-256
    assert len(report.traces) == 4
    assert all(len(t.trace_sha256) == 64 for t in report.traces)
    status_by_id = {t.candidate_id: t.final_status for t in report.traces}
    assert status_by_id["H-OUTLIER"] == "REJETE_GF1_ABERRANT"
    assert status_by_id["H-LOW"] == "FILTRE_GF2_SOUS_SEUIL"
    assert status_by_id["H-PROOF"] == "CANDIDAT"


def test_vr_compliance_passes_20_of_20() -> None:
    res = verify_vr_compliance(ROOT_DIR)
    assert res["schema"] == "vr-structura-compliance/1"
    assert res["total_count"] == 20
    assert res["passed_count"] == 20
    assert res["compliance_percent"] == 100.0
    assert res["all_passed"] is True
    assert len(res["seal_sha256"]) == 64


def test_network_doctor_offline_verifies_all_tools_and_mcp() -> None:
    res = run_network_doctor(ROOT_DIR, online=False)
    assert res["schema"] == "omega-network-doctor/1"
    assert res["a12"]["ok"] is True
    assert res["vr_compliance"]["all_passed"] is True
    assert res["mcp_stdio_probe"]["ok"] is True
    assert res["mcp_stdio_probe"]["tool_count"] >= 9
    assert res["operational"] is (res["tools"]["opa"] is not None)
    assert res["rust_guard_kernel"]["crate_present"] is True
    assert res["rust_guard_kernel"]["ipc_protocol"] == "SUP-IPC-01"
    if res["rust_guard_kernel"]["status"] == "OPERATIONAL":
        assert res["rust_guard_kernel"]["ipc_probe_ok"] is True
        assert res["rust_guard_kernel"]["eval_verdict"] == "ADMISSIBLE_A_REVUE_HUMAINE"
    assert res["supela_k3_bridge"]["repo"] == "gadboisjean1000-arch/Supela-K3-Omega"


def test_integrated_network_pipeline_end_to_end() -> None:
    res = run_integrated_network_pipeline(ROOT_DIR, query="M-PYTEST-BUS-01")
    assert res["schema"] == "omega-network-pipeline/1"
    assert res["pi0"]["idempotent"] is True
    assert res["pi0"]["non_empty"] is True
    assert "M-PYTEST-BUS-01" in res["pi0"]["manques_preserved"]
    assert res["guard_kernel"]["c1_roundtrip_verified"] is True
    assert len(res["guard_kernel"]["sup_ici_01_records"]) == 2
    assert res["harness"]["verdict"] == "PASS"
    assert res["worm"]["chain_valid"] is True
    assert res["ed25519_verified"] is True
    if res["opa_allow_human_review"] is not None:
        assert res["opa_allow_human_review"] is True


def test_mcp_server_stdio_subprocess_roundtrip() -> None:
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {"protocolVersion": "2024-11-05", "clientInfo": {"name": "pytest"}, "capabilities": {}},
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "ping", "params": {}},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "omega_pi0_project",
                "arguments": {
                    "manque_id": "M-MCP-TEST",
                    "raccords": [{"id": "R-TEST", "label": "Test raccord"}],
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "guard_kernel_compress",
                "arguments": {
                    "object_id": "OBJ-MCP-01",
                    "content": "Données test Guard-Kernel via MCP",
                    "author": "pytest",
                    "origin": "mcp_test",
                    "target_generation": "G1",
                    "compression_level": "C1",
                    "reason": "Test MCP C1",
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {"name": "omega_verify_vr_compliance", "arguments": {}},
        },
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "resources/read",
            "params": {"uri": "omega://constitution/guard-kernel"},
        },
        {"jsonrpc": "2.0", "id": 8, "method": "unknown/method", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {"name": "nonexistent_tool", "arguments": {}},
        },
    ]
    payload = "\n".join(json.dumps(r) for r in requests) + "\n{bad json\n"
    proc = subprocess.run(
        [sys.executable, "-m", "omega_zero.mcp_server"],
        cwd=ROOT_DIR,
        input=payload,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    # 9 requêtes avec id + 1 erreur JSON invalide (la notification n'emet pas de reponse)
    assert len(responses) == 10
    by_id = {r["id"]: r for r in responses if r.get("id") is not None}

    assert by_id[1]["result"]["serverInfo"]["name"] == "omega-zero-mcp"
    assert by_id[2]["result"] == {}
    tool_names = {t["name"] for t in by_id[3]["result"]["tools"]}
    assert len(tool_names) >= 11
    assert "omega_pcep_prepare" in tool_names

    pi0_out = json.loads(by_id[4]["result"]["content"][0]["text"])
    assert pi0_out["idempotent"] is True
    assert "M-MCP-TEST" in pi0_out["preserved_manques"]

    gk_out = json.loads(by_id[5]["result"]["content"][0]["text"])
    assert gk_out["transition"]["compression_level"] == "C1"
    assert gk_out["transition"]["semantic_loss_passed"] is True

    vr_out = json.loads(by_id[6]["result"]["content"][0]["text"])
    assert vr_out["all_passed"] is True

    res_out = by_id[7]["result"]["contents"][0]["text"]
    assert "SUP-ICI-01" in res_out

    assert by_id[8]["error"]["code"] == -32601
    assert by_id[9]["result"]["isError"] is True
    assert any(r.get("error", {}).get("code") == -32700 for r in responses)
