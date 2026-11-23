"""Banc d'épreuve : validation du sas Agent Ready Supela (0$ PMU)."""

from __future__ import annotations

import hashlib
from typing import Any

import pytest

from omega_zero.supela_agent_ready_engine import (
    AgentPolicyViolation,
    SupelaAgentRuntime,
    ToolSpec,
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

    state_pi0, out_pi0 = runtime.execute_agent_call(
        tool_name="pi0_check",
        arguments={"b": 2, "a": 1},
        active_scope="audit",
    )
    assert state_pi0 == (1, 1, 1, 1)
    assert out_pi0["idempotent"] is True
    assert runtime.verify_worm_chain() is True
