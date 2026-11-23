"""Banc d'épreuve : validation du sas Agent Ready Supela (0$ PMU)."""

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from omega_zero.supela_agent_ready_engine import (
    AgentPolicyViolation,
    SupelaAgentRuntime,
    ToolSpec,
    ToolVerificationProof,
    build_default_runtime,
)


def _make_runtime() -> SupelaAgentRuntime:
    runtime = SupelaAgentRuntime()

    def local_hasher(args: dict[str, Any]) -> dict[str, Any]:
        data = str(args.get("data", "")).encode("utf-8")
        return {"digest": hashlib.sha256(data).hexdigest()}

    runtime.register_tool(
        ToolSpec(
            name="local_sha256",
            allowed_scopes=("research", "audit"),
            handler=local_hasher,
        )
    )
    return runtime


def test_nominal_agent_execution_admitted() -> None:
    runtime = _make_runtime()
    state, out = runtime.execute_agent_call(
        tool_name="local_sha256",
        arguments={"data": "supela-agent-test"},
        active_scope="research",
    )
    assert state == (1, 1, 1, 1)
    assert "digest" in out
    assert len(runtime.audit_worm_log) == 1
    assert runtime.audit_worm_log[0].allowed is True
    assert runtime.verify_worm_chain() is True


def test_scope_violation_contracts_to_pi0() -> None:
    runtime = _make_runtime()
    state, out = runtime.execute_agent_call(
        tool_name="local_sha256",
        arguments={"data": "malicious_payload"},
        active_scope="unauthorized_public_net",
    )
    assert state == (0, 0, 0, 0)
    assert "DENY_SCOPE" in out["error"]
    assert runtime.audit_worm_log[-1].allowed is False
    assert runtime.verify_worm_chain() is True


def test_unknown_tool_rejection() -> None:
    runtime = _make_runtime()
    state, out = runtime.execute_agent_call(
        tool_name="execute_system_rm",
        arguments={"path": "/"},
        active_scope="audit",
    )
    assert state == (0, 0, 0, 0)
    assert "DENY_UNKNOWN_TOOL" in out["error"]
    assert runtime.audit_worm_log[-1].allowed is False
    assert runtime.verify_worm_chain() is True


def test_invalid_or_nan_arguments_fail_closed() -> None:
    runtime = _make_runtime()
    state_nan, out_nan = runtime.execute_agent_call(
        tool_name="local_sha256",
        arguments={"value": float("nan")},
        active_scope="research",
    )
    assert state_nan == (0, 0, 0, 0)
    assert "DENY_INVALID_ARGS" in out_nan["error"]

    state_list, out_list = runtime.execute_agent_call(
        tool_name="local_sha256",
        arguments=["not-a-dict"],
        active_scope="research",
    )
    assert state_list == (0, 0, 0, 0)
    assert "DENY_INVALID_ARGS" in out_list["error"]
    assert runtime.verify_worm_chain() is True


def test_duplicate_tool_registration_forbidden() -> None:
    runtime = _make_runtime()
    with pytest.raises(AgentPolicyViolation):
        runtime.register_tool(
            ToolSpec(
                name="local_sha256",
                allowed_scopes=("research",),
                handler=lambda args: args,
            )
        )


def test_handler_crash_contracts_to_pi0() -> None:
    runtime = SupelaAgentRuntime()

    def failing_tool(_args: dict[str, Any]) -> dict[str, Any]:
        raise RuntimeError("boom")

    runtime.register_tool(
        ToolSpec(
            name="broken_tool",
            allowed_scopes=("audit",),
            handler=failing_tool,
        )
    )
    state, out = runtime.execute_agent_call(
        tool_name="broken_tool",
        arguments={"probe": True},
        active_scope="audit",
    )
    assert state == (0, 0, 0, 0)
    assert "RESET_PI0" in out["error"]
    assert runtime.audit_worm_log[-1].allowed is False
    assert runtime.verify_worm_chain() is True


def test_build_default_runtime_tools() -> None:
    runtime = build_default_runtime()
    state_hash, out_hash = runtime.execute_agent_call(
        tool_name="local_sha256",
        arguments={"data": "omega-zero"},
        active_scope="verify",
    )
    assert state_hash == (1, 1, 1, 1)
    assert out_hash["digest"] == hashlib.sha256(b"omega-zero").hexdigest()

    # pi0_check sur objet vide ou hors-schéma doit contracter honnêtement à (0, 0, 0, 0)
    for invalid_payload in ({}, {"b": 2, "a": 1}, {"invariants": ["I1"], "force_reset": True}):
        state_bad, out_bad = runtime.execute_agent_call(
            tool_name="pi0_check",
            arguments=invalid_payload,
            active_scope="audit",
        )
        assert state_bad == (0, 0, 0, 0)
        assert "CONTRACT_PI0" in out_bad["error"]
        assert runtime.audit_worm_log[-1].allowed is False

    # pi0_check sur état Supela non vide vérifie la double projection et purge les clés provisoires
    state_ok, out_ok = runtime.execute_agent_call(
        tool_name="pi0_check",
        arguments={
            "invariants": ["I1"],
            "proofs": {"P1": {"verified": True}},
            "history": [{"kind": "PROVISIONAL_DRAFT"}, {"kind": "VERIFIED"}],
            "provisional_extra": ["drop-me"],
        },
        active_scope="audit",
    )
    assert state_ok == (1, 1, 1, 1)
    assert out_ok["idempotent"] is True
    assert out_ok["non_empty"] is True
    assert out_ok["projected_sha256"] == out_ok["second_projection_sha256"]
    assert out_ok["dropped_keys"] == ["provisional_extra"]
    assert runtime.verify_worm_chain() is True


def test_injectable_clock_produces_deterministic_proof_hashes() -> None:
    fixed_ns = 1_700_000_000_000_000_000
    rt_a = SupelaAgentRuntime(clock_ns=lambda: fixed_ns)
    rt_b = SupelaAgentRuntime(clock_ns=lambda: fixed_ns)
    for rt in (rt_a, rt_b):
        rt.register_tool(
            ToolSpec(
                name="echo",
                allowed_scopes=("audit",),
                handler=lambda args: {"echo": args.get("v", "")},
            )
        )

    rec_a = rt_a.execute_agent_call_with_proof("echo", {"v": "supela"}, "audit")
    rec_b = rt_b.execute_agent_call_with_proof("echo", {"v": "supela"}, "audit")
    assert rec_a.proof.proof_hash == rec_b.proof.proof_hash
    assert rec_a.proof.timestamp_ns == fixed_ns


def test_incremental_o1_worm_link_detects_tampering() -> None:
    runtime = build_default_runtime()
    rec1 = runtime.execute_agent_call_with_proof("local_sha256", {"data": "one"}, "verify")
    assert rec1.worm_link_verified is True

    # Altération externe de la queue du journal
    tampered = ToolVerificationProof(
        tool_name=rec1.proof.tool_name,
        arguments_hash=rec1.proof.arguments_hash,
        allowed=rec1.proof.allowed,
        state=rec1.proof.state,
        timestamp_ns=rec1.proof.timestamp_ns,
        prev_proof_hash=rec1.proof.prev_proof_hash,
        proof_hash="f" * 64,
    )
    runtime.audit_worm_log[-1] = tampered

    rec2 = runtime.execute_agent_call_with_proof("local_sha256", {"data": "two"}, "verify")
    assert rec2.worm_link_verified is False
    assert runtime.verify_worm_chain() is False
