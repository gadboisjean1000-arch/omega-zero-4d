"""Moteur Agent Ready Supela K3-Omega (0$ PMU).
Orchestration d'outils, garde fail-closed et journal d'audit WORM chaîné SHA-256.

Auteur canonique : Jean-François Gadbois
Doctrine : 0$ PMU | Déterminisme absolu | Zéro dépendance captive
"""

from __future__ import annotations

import hashlib
import json
import threading
import time
import uuid
from collections.abc import Callable
from copy import deepcopy
from dataclasses import dataclass
from typing import Any, NamedTuple

GENESIS_HASH: str = "0" * 64
_PI0_CORE_KEYS: tuple[str, ...] = (
    "invariants",
    "proofs",
    "refutations",
    "manques",
    "authorities",
    "history",
)
_PI0_LIST_KEYS: frozenset[str] = frozenset({"invariants", "history"})
_PI0_DICT_KEYS: frozenset[str] = frozenset({"proofs", "refutations", "manques", "authorities"})


class ToolVerificationProof(NamedTuple):
    tool_name: str
    arguments_hash: str
    allowed: bool
    state: tuple[int, int, int, int]
    timestamp_ns: int
    prev_proof_hash: str = GENESIS_HASH
    proof_hash: str = ""


class AgentCallReceipt(NamedTuple):
    state: tuple[int, int, int, int]
    result: dict[str, Any]
    proof: ToolVerificationProof
    worm_link_verified: bool
    chain_length: int


class AgentPolicyViolation(Exception):
    """Refus immédiat par le Policy Enforcement Point (PEP)."""


@dataclass(frozen=True)
class ToolSpec:
    name: str
    allowed_scopes: tuple[str, ...]
    handler: Callable[[dict[str, Any]], dict[str, Any]]


class SupelaAgentRuntime:
    """Noyau d'exécution agentique sécurisé local (100 % stdlib)."""

    def __init__(
        self,
        node_id: str = "node:local-agent",
        *,
        clock_ns: Callable[[], int] = time.time_ns,
    ) -> None:
        self.node_id = node_id
        self.instance_id: str = uuid.uuid4().hex[:16]
        self._clock_ns = clock_ns
        self.tools_registry: dict[str, ToolSpec] = {}
        self.audit_worm_log: list[ToolVerificationProof] = []
        self._last_proof_hash: str = GENESIS_HASH
        self._worm_chain_valid: bool = True
        self._lock = threading.Lock()

    def register_tool(self, spec: ToolSpec) -> None:
        if not isinstance(spec.name, str) or not spec.name.strip():
            raise AgentPolicyViolation("Nom d'outil invalide ou vide.")
        if (
            not isinstance(spec.allowed_scopes, tuple)
            or not spec.allowed_scopes
            or any(not isinstance(scope, str) or not scope.strip() for scope in spec.allowed_scopes)
        ):
            raise AgentPolicyViolation(f"Périmètres autorisés invalides pour l'outil '{spec.name}'.")
        if not callable(spec.handler):
            raise AgentPolicyViolation(f"Handler non appelable pour l'outil '{spec.name}'.")
        with self._lock:
            if spec.name in self.tools_registry:
                raise AgentPolicyViolation(
                    f"Outil '{spec.name}' déjà homologué : écrasement interdit (ANTI_SHADOW)."
                )
            self.tools_registry[spec.name] = spec

    @staticmethod
    def _canonical_json(payload: Any) -> bytes:
        return json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")

    @classmethod
    def _hash_args(cls, args: dict[str, Any]) -> str:
        return hashlib.sha256(cls._canonical_json(args)).hexdigest()

    @classmethod
    def _compute_proof_hash(
        cls,
        prev_proof_hash: str,
        tool_name: str,
        arguments_hash: str,
        allowed: bool,
        state: tuple[int, int, int, int],
        timestamp_ns: int,
    ) -> str:
        envelope = {
            "prev_proof_hash": prev_proof_hash,
            "tool_name": tool_name,
            "arguments_hash": arguments_hash,
            "allowed": allowed,
            "state": list(state),
            "timestamp_ns": timestamp_ns,
        }
        return hashlib.sha256(cls._canonical_json(envelope)).hexdigest()

    def _append_proof(
        self,
        tool_name: str,
        arguments_hash: str,
        allowed: bool,
        state: tuple[int, int, int, int],
        timestamp_ns: int,
    ) -> tuple[ToolVerificationProof, bool, int]:
        actual_prev = self.audit_worm_log[-1].proof_hash if self.audit_worm_log else GENESIS_HASH
        link_ok = (actual_prev == self._last_proof_hash) and self._worm_chain_valid
        proof_hash = self._compute_proof_hash(
            prev_proof_hash=actual_prev,
            tool_name=tool_name,
            arguments_hash=arguments_hash,
            allowed=allowed,
            state=state,
            timestamp_ns=timestamp_ns,
        )
        proof = ToolVerificationProof(
            tool_name=tool_name,
            arguments_hash=arguments_hash,
            allowed=allowed,
            state=state,
            timestamp_ns=timestamp_ns,
            prev_proof_hash=actual_prev,
            proof_hash=proof_hash,
        )
        self.audit_worm_log.append(proof)
        self._last_proof_hash = proof_hash
        self._worm_chain_valid = link_ok
        return (proof, link_ok, len(self.audit_worm_log))

    def verify_worm_chain(self) -> bool:
        """Vérifie l'intégrité complète de la chaîne SHA-256 WORM depuis GENESIS_HASH."""
        with self._lock:
            expected_prev = GENESIS_HASH
            for proof in self.audit_worm_log:
                if proof.prev_proof_hash != expected_prev:
                    return False
                expected_hash = self._compute_proof_hash(
                    prev_proof_hash=proof.prev_proof_hash,
                    tool_name=proof.tool_name,
                    arguments_hash=proof.arguments_hash,
                    allowed=proof.allowed,
                    state=proof.state,
                    timestamp_ns=proof.timestamp_ns,
                )
                if proof.proof_hash != expected_hash:
                    return False
                expected_prev = proof.proof_hash
            return expected_prev == self._last_proof_hash and self._worm_chain_valid

    def execute_agent_call_with_proof(
        self,
        tool_name: str,
        arguments: Any,
        active_scope: str,
    ) -> AgentCallReceipt:
        """Sas L0-L7 atomique retournant le reçu cryptographique WORM sous verrou."""
        with self._lock:
            now_ns = self._clock_ns()
            safe_tool_name = tool_name if isinstance(tool_name, str) else repr(tool_name)
            if (
                not isinstance(tool_name, str)
                or not tool_name.strip()
                or not isinstance(active_scope, str)
                or not active_scope.strip()
                or not isinstance(arguments, dict)
            ):
                fallback_hash = hashlib.sha256(repr(arguments).encode("utf-8")).hexdigest()
                proof, link_ok, chain_len = self._append_proof(
                    safe_tool_name, fallback_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": "Arguments ou paramètres invalides (DENY_INVALID_ARGS)"},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )

            try:
                raw_args_bytes = self._canonical_json(arguments)
                args_hash = hashlib.sha256(raw_args_bytes).hexdigest()
                safe_args_obj = json.loads(raw_args_bytes.decode("utf-8"))
                if not isinstance(safe_args_obj, dict):
                    raise TypeError("Les arguments doivent former un objet JSON.")
                safe_args: dict[str, Any] = safe_args_obj
            except (TypeError, ValueError):
                fallback_hash = hashlib.sha256(repr(arguments).encode("utf-8")).hexdigest()
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, fallback_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": "Arguments ou paramètres invalides (DENY_INVALID_ARGS)"},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )

            # Invariant 1 : L'outil doit être formellement déclaré
            if tool_name not in self.tools_registry:
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, args_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": f"Outil '{tool_name}' non homologué (DENY_UNKNOWN_TOOL)"},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )

            spec = self.tools_registry[tool_name]

            # Invariant 2 : Étanchéité de périmètre (Scope Containment)
            if active_scope not in spec.allowed_scopes:
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, args_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": f"Périmètre '{active_scope}' illégitime pour {tool_name} (DENY_SCOPE)"},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )

            # Invariant 3 : Exécution confinée et vérification de retour
            try:
                raw_result = spec.handler(safe_args)
                if not isinstance(raw_result, dict):
                    raise TypeError("Retour d'outil non conforme")
                result_bytes = self._canonical_json(raw_result)
                verified_obj = json.loads(result_bytes.decode("utf-8"))
                if not isinstance(verified_obj, dict):
                    raise TypeError("Retour d'outil non conforme")
                verified_result: dict[str, Any] = verified_obj
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, args_hash, True, (1, 1, 1, 1), now_ns
                )
                return AgentCallReceipt(
                    state=(1, 1, 1, 1),
                    result=verified_result,
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )
            except AgentPolicyViolation as exc:
                err_msg = str(exc)
                if "CONTRACT_PI0" not in err_msg:
                    err_msg = f"{err_msg} (CONTRACT_PI0)"
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, args_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": err_msg},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )
            except Exception as exc:  # noqa: BLE001 — Fail-closed Π₀ sur tout crash d'outil externe
                # Tout crash d'outil externe contracte au point zéro Pi_0
                proof, link_ok, chain_len = self._append_proof(
                    tool_name, args_hash, False, (0, 0, 0, 0), now_ns
                )
                return AgentCallReceipt(
                    state=(0, 0, 0, 0),
                    result={"error": f"Échec d'exécution mécanique : {exc} (RESET_PI0)"},
                    proof=proof,
                    worm_link_verified=link_ok,
                    chain_length=chain_len,
                )

    def execute_agent_call(
        self,
        tool_name: str,
        arguments: Any,
        active_scope: str,
    ) -> tuple[tuple[int, int, int, int], dict[str, Any]]:
        """Sas de contrôle L0-L7 fail-closed avant toute exécution mécanique."""
        receipt = self.execute_agent_call_with_proof(tool_name, arguments, active_scope)
        return (receipt.state, receipt.result)


def _tool_local_sha256(args: dict[str, Any]) -> dict[str, Any]:
    data = str(args.get("data", "")).encode("utf-8")
    return {"digest": hashlib.sha256(data).hexdigest()}


def _project_pi0_state(raw: dict[str, Any]) -> dict[str, Any]:
    """Projette un état sur ses champs canoniques Π₀ en purgeant les brouillons provisoires."""
    projected: dict[str, Any] = {}
    for key in _PI0_CORE_KEYS:
        if key not in raw:
            projected[key] = [] if key in _PI0_LIST_KEYS else {}
            continue
        val = raw[key]
        if key in _PI0_LIST_KEYS:
            if not isinstance(val, list):
                raise AgentPolicyViolation(f"Champ Π₀ '{key}' invalide : liste attendue (CONTRACT_PI0)")
            if key == "history":
                projected[key] = [
                    deepcopy(entry)
                    for entry in val
                    if not (isinstance(entry, dict) and entry.get("kind") == "PROVISIONAL_DRAFT")
                ]
            else:
                projected[key] = deepcopy(val)
        elif key in _PI0_DICT_KEYS:
            if not isinstance(val, dict):
                raise AgentPolicyViolation(f"Champ Π₀ '{key}' invalide : objet attendu (CONTRACT_PI0)")
            projected[key] = deepcopy(val)
    return projected


def _tool_pi0_check(args: dict[str, Any]) -> dict[str, Any]:
    """Vérifie réellement la double projection Π₀(Π₀(S)) = Π₀(S) et la non-vacuité."""
    if args.get("force_reset") is True:
        raise AgentPolicyViolation("Contraction forcée au vide Π₀ (CONTRACT_PI0)")
    z1 = _project_pi0_state(args)
    z2 = _project_pi0_state(z1)
    non_empty = any(bool(z1[key]) for key in _PI0_CORE_KEYS)
    h1 = hashlib.sha256(SupelaAgentRuntime._canonical_json(z1)).hexdigest()
    h2 = hashlib.sha256(SupelaAgentRuntime._canonical_json(z2)).hexdigest()
    if not non_empty or h1 != h2:
        raise AgentPolicyViolation(
            "Contraction au vide Π₀ : état sans invariant ou preuve vérifiable (CONTRACT_PI0)"
        )
    return {
        "projected_sha256": h1,
        "second_projection_sha256": h2,
        "idempotent": True,
        "non_empty": True,
        "dropped_keys": sorted(set(args.keys()) - set(_PI0_CORE_KEYS)),
    }


def build_default_runtime(node_id: str = "node:cloudrun-supela") -> SupelaAgentRuntime:
    """Construit un runtime local déterministe doté des outils stdlib canoniques."""
    runtime = SupelaAgentRuntime(node_id=node_id)
    runtime.register_tool(
        ToolSpec(
            name="local_sha256",
            allowed_scopes=("research", "audit", "verify"),
            handler=_tool_local_sha256,
        )
    )
    runtime.register_tool(
        ToolSpec(
            name="pi0_check",
            allowed_scopes=("audit", "verify"),
            handler=_tool_pi0_check,
        )
    )
    return runtime
