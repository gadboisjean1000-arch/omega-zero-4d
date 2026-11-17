from __future__ import annotations

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator

from omega_zero.mcp_server import TOOLS_SPEC, call_tool
from omega_zero.network_bus import main as network_bus_main
from omega_zero.network_bus import run_pcep_prepare
from omega_zero.pcep import (
    CalculatedAuthorityAgent,
    ClaimNode,
    ClaimStatus,
    EvolutionaryCodeStep,
    PCEPEngine,
    ReferentialTransport,
    ReferentialVerdict,
    SignatureStatus,
    build_pcep_network_envelope,
)

ROOT_DIR = Path(__file__).resolve().parents[1]


def test_pcep_envelope_ready_for_signature_and_schema_valid() -> None:
    envelope = build_pcep_network_envelope()
    schema = json.loads((ROOT_DIR / "schemas" / "supela_pcep_network_1.schema.json").read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(envelope)

    sig_env = envelope["signature_envelope"]
    assert sig_env["signature_status"] == SignatureStatus.EN_ATTENTE_SIGNATURE.value
    assert sig_env["ready_for_signature"] is True
    assert sig_env["signature"] is None
    assert len(sig_env["canonical_payload_sha256"]) == 64
    assert len(envelope["open_proofs_registry"]) >= 8
    assert all(item["status"] == "A_PROUVER" and item["promoted"] is False for item in envelope["open_proofs_registry"])


def test_pcep_auto_revocation_forbids_direct_contradicted_to_valid() -> None:
    engine = PCEPEngine()
    engine.register_claim(
        ClaimNode(
            claim_id="C-1",
            statement="Propriété locale",
            referential="R_LOCAL",
            sources=["src/omega_zero/pcep.py"],
            status=ClaimStatus.VALID,
        )
    )
    engine.transition_claim(
        "C-1",
        ClaimStatus.CONTRADICTED,
        reason="Contre-exemple trouvé",
        counter_evidence_ref="ADV-01",
    )
    with pytest.raises(ValueError, match="interdite"):
        engine.transition_claim("C-1", ClaimStatus.VALID, reason="Saut illégal")


def test_pcep_referential_transport_fail_closed_without_proof() -> None:
    blocked = ReferentialTransport(
        claim_id="C-1",
        source_referential="R1",
        target_referential="R2",
        conditions=["Invariant préservé"],
        transport_proof_verified=False,
    )
    assert blocked.transport_allowed is False
    assert blocked.target_verdict == ReferentialVerdict.UNKNOWN

    allowed = ReferentialTransport(
        claim_id="C-1",
        source_referential="R1",
        target_referential="R2",
        conditions=["Invariant préservé"],
        transport_proof_verified=True,
    )
    assert allowed.transport_allowed is True
    assert allowed.target_verdict == ReferentialVerdict.TRUE


def test_pcep_agent_authority_strictly_bounded_by_verified_proof() -> None:
    agent = CalculatedAuthorityAgent(
        agent_id="AGENT-01",
        reasoning_capacity=4,
        verified_proof_level=1,
        requested_authority=4,
    )
    assert agent.action_authority == 1
    assert agent.bounded_ok is True


def test_pcep_evolution_step_requires_proof_and_trace() -> None:
    with pytest.raises(ValueError):
        EvolutionaryCodeStep(
            step_id="S-1",
            previous_hash="a" * 64,
            transformation="t",
            trace="tr",
            scope="R_LOCAL",
            proof_refs=[],
            counter_evidence=[],
        )


def test_pcep_dependency_cone_impact_order() -> None:
    engine = PCEPEngine()
    engine.register_claim(ClaimNode("A", "root", "R1", ["s1"], status=ClaimStatus.VALID))
    engine.register_claim(ClaimNode("B", "child", "R1", ["s1"], dependencies=["A"], status=ClaimStatus.VALID))
    engine.register_claim(ClaimNode("C", "grandchild", "R1", ["s1"], dependencies=["B"], status=ClaimStatus.VALID))
    cone = engine.compute_dependency_cone("A")
    assert cone["impacted_claims"] == ["B", "C"]
    assert cone["reevaluation_order"] == ["B", "C"]


def test_pcep_mcp_tool_and_network_bus_cli(tmp_path: Path) -> None:
    tool_names = {t["name"] for t in TOOLS_SPEC}
    assert "omega_pcep_prepare" in tool_names

    mcp_res = call_tool("omega_pcep_prepare", {})
    assert mcp_res["signature_envelope"]["signature_status"] == "EN_ATTENTE_SIGNATURE"

    out_file = tmp_path / "pcep_ready.json"
    bus_res = run_pcep_prepare(ROOT_DIR, out_path=out_file)
    assert out_file.exists()
    assert bus_res["signature_envelope"]["ready_for_signature"] is True
    assert bus_res["signature_envelope"]["signature"] is None

    rc = network_bus_main(["pcep-prepare"])
    assert rc == 0
