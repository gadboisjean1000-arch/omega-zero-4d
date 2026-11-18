from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from omega_zero import (
    HUMAN_NORMATIVE_AUTHORITY,
    REPORTED_M365_ARTIFACTS,
    ContradictionBlocksRatificationError,
    DossierStatus,
    LedgerTamperError,
    ObservedOutcome,
    PathBoundaryError,
    SupelaAuthorityError,
    SupelaRuntime,
    UnauthorizedCommandError,
    run_supela_runtime_complete_cycle_demo,
)

ROOT_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PATH = ROOT_DIR / "schemas" / "supela-state.schema.json"


def _load_state_schema() -> dict:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(schema)
    return schema


def test_supela_state_schema_valid_and_complete_cycle(tmp_path: Path) -> None:
    schema = _load_state_schema()
    validator = Draft202012Validator(schema)

    report = run_supela_runtime_complete_cycle_demo(ROOT_DIR, work_dir=tmp_path)
    assert all(report["invariants_verified"].values())
    assert report["executed_at_utc"].endswith("Z")
    assert len(report["report_sha256"]) == 64
    assert report["ed25519_attestation"]["verified"] is True
    assert report["reported_m365_artifacts"] == REPORTED_M365_ARTIFACTS
    assert (
        report["reported_m365_artifacts"]["supela-local-bridge-v0.1.zip"]["sha256"]
        == "650337274c316f1cf76f47be5489eec592fa6bcfbdb5fbc614809cf8c2085710"
    )
    assert (
        report["reported_m365_artifacts"]["supela-runtime-v0.2.zip"]["sha256"]
        == "b5fab177db18288ed78a60a9cd8e84dd866034e0557c0f1c95ed9c06cdebab83"
    )

    validator.validate(report["ratified_snapshot"])
    validator.validate(report["final_reopened_state"])


def test_execution_pass_and_fail_observed_in_scope_without_universal_refutation(
    tmp_path: Path,
) -> None:
    rt = SupelaRuntime(repository_root=ROOT_DIR, state_dir=tmp_path)
    rt.create_concept("DOS-EXEC-01", "Affirmation testée localement", "scope/local")
    rt.register_code("DOS-EXEC-01", "ART-01", "schemas/supela-state.schema.json")

    state_fail = rt.execute("DOS-EXEC-01", "probe_fail")
    assert state_fail["status"] == DossierStatus.EXECUTED.value
    assert (
        state_fail["executions"][0]["observed_outcome"]
        == ObservedOutcome.OBSERVED_FAIL_IN_SCOPE.value
    )
    # Le runtime conserve l'échec dans son périmètre sans basculer automatiquement en réfutation générale
    assert state_fail["contradictions"] == []

    state_pass = rt.execute("DOS-EXEC-01", "probe_pass")
    assert (
        state_pass["executions"][1]["observed_outcome"]
        == ObservedOutcome.OBSERVED_PASS_IN_SCOPE.value
    )


def test_block_paths_outside_repo_and_unauthorized_commands(tmp_path: Path) -> None:
    rt = SupelaRuntime(repository_root=ROOT_DIR, state_dir=tmp_path)
    rt.create_concept("DOS-SEC-01", "Sécurité L0", "scope/security")

    with pytest.raises(PathBoundaryError):
        rt.register_code("DOS-SEC-01", "ART-OUTSIDE", "../outside_file.txt")

    rt.register_code("DOS-SEC-01", "ART-IN", "schemas/supela-state.schema.json")
    with pytest.raises(UnauthorizedCommandError):
        rt.execute("DOS-SEC-01", "rm_rf_unlisted_command")


def test_ledger_tamper_detection(tmp_path: Path) -> None:
    rt = SupelaRuntime(repository_root=ROOT_DIR, state_dir=tmp_path)
    rt.create_concept("DOS-LEDGER-01", "Intégrité registre", "scope/ledger")
    rt.register_code("DOS-LEDGER-01", "ART-01", "schemas/supela-state.schema.json")

    check_ok = rt.verify_ledger()
    assert check_ok["valid"] is True
    assert check_ok["entry_count"] == 2

    # Falsification d'une ligne du registre JSONL
    ledger_file = tmp_path / "ledger.jsonl"
    lines = ledger_file.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["event_type"] = "TAMPERED_EVENT"
    lines[0] = json.dumps(tampered, sort_keys=True)
    ledger_file.write_text("\n".join(lines) + "\n", encoding="utf-8")

    check_bad = rt.verify_ledger()
    assert check_bad["valid"] is False
    assert "entry_hash" in str(check_bad["error"])

    with pytest.raises(LedgerTamperError):
        rt.execute("DOS-LEDGER-01", "probe_pass")


def test_contradiction_blocks_ratification_and_revision_increments_generation(
    tmp_path: Path,
) -> None:
    schema = _load_state_schema()
    validator = Draft202012Validator(schema)
    rt = SupelaRuntime(repository_root=ROOT_DIR, state_dir=tmp_path)

    rt.create_concept("DOS-CONTR-01", "Hypothèse initiale", "scope/rev")
    rt.register_code("DOS-CONTR-01", "ART-G1", "schemas/supela-state.schema.json")
    rt.execute("DOS-CONTR-01", "probe_fail")
    rt.collect_evidence("DOS-CONTR-01")
    st_eval = rt.evaluate("DOS-CONTR-01")

    assert st_eval["status"] == DossierStatus.CONTRADICTOIRE.value
    assert len(st_eval["contradictions"]) == 1
    assert st_eval["contradictions"][0]["status"] == "OPEN"
    g1_hash = st_eval["state_hash"]

    with pytest.raises(ContradictionBlocksRatificationError):
        rt.submit_ratification("DOS-CONTR-01")

    st_rev = rt.request_revision(
        "DOS-CONTR-01",
        reason="Révision explicite suite à la contradiction de génération 1",
    )
    assert st_rev["generation"] == 2
    assert len(st_rev["previous_generations"]) == 1
    assert st_rev["previous_generations"][0]["generation"] == 1
    assert st_rev["previous_generations"][0]["state_hash"] == g1_hash
    # L'ancienne contradiction et l'ancien artefact sont conservés sans suppression
    assert len(st_rev["artifacts"]) == 1
    assert st_rev["contradictions"][0]["status"] == "SUPERSEDED_BY_REVISION"
    assert st_rev["contradictions"][0]["resolved_in_generation"] == 2
    validator.validate(st_rev)


def test_refusal_of_ai_ratification_and_reopen_for_all_three_decisions(
    tmp_path: Path,
) -> None:
    schema = _load_state_schema()
    validator = Draft202012Validator(schema)
    rt = SupelaRuntime(repository_root=ROOT_DIR, state_dir=tmp_path)

    for idx, decision in enumerate(("ACCEPT", "REFUSE", "ADJOURN"), start=1):
        did = f"DOS-NORM-{idx:02d}"
        rt.create_concept(did, f"Concept normatif {decision}", "scope/normative")
        rt.register_code(did, f"ART-{idx}", "schemas/supela-state.schema.json")
        rt.execute(did, "probe_pass")
        rt.collect_evidence(did)
        rt.evaluate(did)
        rt.submit_ratification(did)

        # Toute ratification par l'IA ou un acteur autre que Jean-François Gadbois est refusée
        for forbidden_actor in ("AI", "M365 Copilot", "Antigravity", "claude-opus"):
            with pytest.raises(SupelaAuthorityError):
                rt.ratify(did, forbidden_actor, decision, "Tentative non autorisée")

        ratified = rt.ratify(
            did,
            HUMAN_NORMATIVE_AUTHORITY,
            decision,
            f"Décision souveraine {decision}",
        )
        assert ratified["normative_decision"]["actor"] == HUMAN_NORMATIVE_AUTHORITY
        assert ratified["normative_decision"]["decision"] == decision
        validator.validate(ratified)

        history_len_before = len(ratified["history"])
        reopened = rt.reopen(
            did,
            reason=f"Réouverture motivée après {decision}",
            actor=HUMAN_NORMATIVE_AUTHORITY,
        )
        assert reopened["status"] == DossierStatus.REOPENED.value
        assert len(reopened["history"]) == history_len_before + 1
        assert reopened["normative_decision"]["decision"] == decision
        validator.validate(reopened)


def test_all_11_supela_mcp_tools_over_jsonrpc_stdio(tmp_path: Path) -> None:
    sd = str(tmp_path)
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "supela_create_concept",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "statement": "Test MCP complet L1-L7",
                    "scope": "mcp/test",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {
                "name": "supela_register_code",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "artifact_id": "ART-MCP-1",
                    "relative_path": "schemas/supela-state.schema.json",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "supela_execute",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "command_key": "probe_fail",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {
                "name": "supela_collect_evidence",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 5,
            "method": "tools/call",
            "params": {
                "name": "supela_evaluate",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 6,
            "method": "tools/call",
            "params": {
                "name": "supela_request_revision",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "reason": "Passage en G2 après échec probe_fail",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 7,
            "method": "tools/call",
            "params": {
                "name": "supela_register_code",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "artifact_id": "ART-MCP-2",
                    "relative_path": "schemas/supela-state.schema.json",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 8,
            "method": "tools/call",
            "params": {
                "name": "supela_execute",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "command_key": "probe_pass",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 9,
            "method": "tools/call",
            "params": {
                "name": "supela_collect_evidence",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 10,
            "method": "tools/call",
            "params": {
                "name": "supela_evaluate",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 11,
            "method": "tools/call",
            "params": {
                "name": "supela_submit_ratification",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 12,
            "method": "tools/call",
            "params": {
                "name": "supela_ratify",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "actor": HUMAN_NORMATIVE_AUTHORITY,
                    "decision": "ACCEPT",
                    "rationale": "Validation MCP",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 13,
            "method": "tools/call",
            "params": {
                "name": "supela_reopen",
                "arguments": {
                    "dossier_id": "DOS-MCP-V02",
                    "reason": "Réouverture test MCP",
                    "state_dir": sd,
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 14,
            "method": "tools/call",
            "params": {
                "name": "supela_get_state",
                "arguments": {"dossier_id": "DOS-MCP-V02", "state_dir": sd},
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 15,
            "method": "tools/call",
            "params": {
                "name": "supela_verify_ledger",
                "arguments": {"state_dir": sd},
            },
        },
    ]
    payload = "\n".join(json.dumps(r) for r in requests) + "\n"
    proc = subprocess.run(
        [sys.executable, "-m", "omega_zero.mcp_server"],
        cwd=ROOT_DIR,
        input=payload,
        text=True,
        capture_output=True,
        timeout=30,
        check=True,
    )
    responses = {
        json.loads(line)["id"]: json.loads(line)
        for line in proc.stdout.splitlines()
        if line.strip()
    }
    assert len(responses) == 15
    assert all(not r["result"]["isError"] for r in responses.values())

    state_out = json.loads(responses[14]["result"]["content"][0]["text"])
    assert state_out["generation"] == 2
    assert state_out["status"] == "REOPENED"
    assert state_out["normative_decision"]["actor"] == HUMAN_NORMATIVE_AUTHORITY

    ledger_out = json.loads(responses[15]["result"]["content"][0]["text"])
    assert ledger_out["valid"] is True
    assert ledger_out["entry_count"] >= 10
