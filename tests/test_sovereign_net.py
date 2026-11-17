from __future__ import annotations

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from omega_zero.mcp_server import TOOLS_SPEC, call_tool
from omega_zero.network_bus import main as network_bus_main
from omega_zero.sovereign_net import (
    EMPTY_SHA,
    TRANSPORT_PROFILES,
    HistoryEntry,
    SovereignSearchQuery,
    SupelaInherentCore,
    run_sovereign_net_self_check,
)


def test_inherent_core_zero_state_and_unknown_command_rejection() -> None:
    core = SupelaInherentCore()
    assert core.state_hash == EMPTY_SHA
    assert core.audit_trail() is True

    code, _ = core.evaluate_command("commande_fantome")
    assert code == 1
    assert core.state_hash == EMPTY_SHA

    core.register_command("ping_local", lambda c: f"ack:{c}")
    code_ok, _ = core.evaluate_command("ping_local")
    assert code_ok == 2
    assert core.state_hash != EMPTY_SHA
    assert core.audit_trail() is True

    # Reset explicite au vide absolu
    code_rst, _ = core.evaluate_command(" ")
    assert code_rst == 0
    assert core.state_hash == EMPTY_SHA
    assert core.audit_trail() is True


def test_inherent_core_network_frame_and_audit_trail_tamper_detection() -> None:
    core = SupelaInherentCore()
    steps = ["n=4k", "n=2(2k)", "pair(n)"]
    sig = EMPTY_SHA
    for step in steps:
        sig = core._hash(sig + step)

    code_ok, _ = core.verify_network_frame({"calcul_declare": "LINEAR-DIV-v1", "steps": steps, "signature": sig})
    assert code_ok == 0
    assert core.audit_trail() is True

    # Saut logique bloqué
    code_jump, _ = core.verify_network_frame(
        {"calcul_declare": "LINEAR-DIV-v1", "steps": ["n=4k", "pair(n)"], "signature": sig}
    )
    assert code_jump == 1

    # Altération détectée par audit_trail()
    core.history[-1] = HistoryEntry(action="NET_ADMIT:LINEAR-DIV-v1", payload=sig, state_hash="0" * 64)
    assert core.audit_trail() is False


def test_sovereign_search_query_hardening_and_ed25519() -> None:
    with pytest.raises(ValueError, match="type"):
        SovereignSearchQuery(query="box_noire", workspace="monitoring", signature_b64="abc", type_param_present=True)

    with pytest.raises(ValueError, match="caractères non conformes"):
        SovereignSearchQuery(query="Box+noire", workspace="monitoring", signature_b64="abc")

    with pytest.raises(ValueError, match="non autorisé"):
        SovereignSearchQuery(query="box_noire", workspace="saas_cloud", signature_b64="abc")

    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    sq = SovereignSearchQuery.sign_new("box_noire", "monitoring", priv)
    assert sq.verify_integrity(pub) is True

    other_pub = Ed25519PrivateKey.generate().public_key()
    assert sq.verify_integrity(other_pub) is False


def test_transport_profiles_and_mcp_cli_integration() -> None:
    assert len(TRANSPORT_PROFILES) == 7
    vectors = {p.vector.value for p in TRANSPORT_PROFILES}
    assert {"TOR_ONION_V3", "I2P_GARLIC", "MIXNET_SPHINX", "AIR_GAP_DIODE", "SIMPLEX_BLIND_DEAD_DROP"} <= vectors

    report = run_sovereign_net_self_check()
    assert report["audit_trail_verified"] is True
    assert report["external_eaas_recalculation"] is False
    assert report["external_saas_telemetry"] is False

    assert "omega_sovereign_net_verify" in {t["name"] for t in TOOLS_SPEC}
    mcp_res = call_tool("omega_sovereign_net_verify", {})
    assert mcp_res["audit_trail_verified"] is True

    assert network_bus_main(["sovereign-verify"]) == 0
