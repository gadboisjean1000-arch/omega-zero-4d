from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .grpo_bridge import SupelaGRPOBridge
from .guard_kernel import (
    CompressionLevel,
    GenerationStage,
    KernelObjectStatus,
    SupelaGuardKernel,
)
from .harness import evaluate_escalation_protocol
from .models import (
    AuthorityLevel,
    CloudOmega,
    Manque,
    ManqueStatus,
    Raccord,
    RaccordStatus,
)
from .projection import ManqueStateMachine, Pi0Projector
from .vr_compliance import verify_vr_compliance

ROOT_DIR = Path(__file__).resolve().parents[2]
PROTOCOL_VERSION = "2024-11-05"
SERVER_INFO = {"name": "omega-zero-mcp", "version": "1.2.0"}


TOOLS_SPEC: list[dict[str, Any]] = [
    {
        "name": "omega_pi0_project",
        "description": "Exécute la projection Π₀(S_t) = {I, P, M, A, H} et vérifie idempotence et bornage d'autorité.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "manque_id": {"type": "string"},
                "raccords": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "label": {"type": "string"},
                            "status": {"type": "string"},
                            "authority_level": {"type": "integer"},
                            "evidence_level": {"type": "integer"},
                        },
                        "required": ["id", "label"],
                    },
                },
            },
            "required": ["manque_id"],
        },
    },
    {
        "name": "omega_manque_transition",
        "description": "Exécute une transition vérifiée de ManqueStateMachine selon M1–M5 et TR-01..TR-16.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "manque_id": {"type": "string"},
                "from_status": {"type": "string"},
                "to_status": {"type": "string"},
                "reason": {"type": "string"},
                "actor": {"type": "string"},
                "timestamp": {"type": "string"},
                "evidence_ref": {"type": "string"},
                "children_ids": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["manque_id", "from_status", "to_status", "reason", "actor", "timestamp"],
        },
    },
    {
        "name": "omega_grpo_explore",
        "description": "Exécute le pont GRPO ↔ Ω-ZERO avec garde-fous GF1–GF5 sans jamais convertir un score en vérité.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "r_max": {"type": "number"},
                "advantage_threshold_tau": {"type": "number"},
                "hypotheses": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "hypothesis": {"type": "string"},
                            "reward": {"type": "number"},
                            "proof_verified": {"type": "boolean"},
                        },
                        "required": ["id", "hypothesis", "reward"],
                    },
                },
            },
            "required": ["query", "hypotheses"],
        },
    },
    {
        "name": "guard_kernel_compress",
        "description": "Exécute Supela-Guard-Kernel (SUP-ICI-01, C0/C1/C2, test de perte de sens) sur un objet G0.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "object_id": {"type": "string"},
                "content": {"type": "string"},
                "author": {"type": "string"},
                "origin": {"type": "string"},
                "target_generation": {"type": "string", "enum": ["G1", "G4"]},
                "compression_level": {"type": "string", "enum": ["C0", "C1", "C2"]},
                "reason": {"type": "string"},
            },
            "required": ["object_id", "content", "author", "origin", "compression_level", "reason"],
        },
    },
    {
        "name": "omega_run_harness",
        "description": "Exécute le protocole d'escalade 4D TEST-4D-ESC-01 (E0..E7, C01..C10).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "omega_verify_a12",
        "description": "Vérifie la Règle A12 anti-orphelins et la cohérence croisée JSON/Rego/Markdown.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "omega_verify_vr_compliance",
        "description": "Exécute l'audit déterministe VR Structura Supela (VR-01..VR-20).",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "omega_network_pipeline",
        "description": "Exécute le cycle complet GRPO → Π₀ → Guard-Kernel → OPA → WORM → Ed25519.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
        },
    },
    {
        "name": "omega_network_doctor",
        "description": "Diagnostique l'intercommunication réelle des outils (pytest, ruff, mypy, opa, cosign, A12, VR-01..VR-20, MCP stdio, pont K3).",
        "inputSchema": {
            "type": "object",
            "properties": {"online": {"type": "boolean"}},
        },
    },
]

RESOURCES_SPEC: list[dict[str, str]] = [
    {
        "uri": "omega://constitution/index",
        "name": "INDEX_CONSTITUTION.md",
        "description": "Index constitutionnel complet du dépôt omega-zero-4d.",
        "mimeType": "text/markdown",
    },
    {
        "uri": "omega://constitution/registry",
        "name": "supela-article-registry-1.json",
        "description": "Registre des 6 articles IA en 5 branches (Hook: AnalysisCandidate, Verdict: OUVERT).",
        "mimeType": "application/json",
    },
    {
        "uri": "omega://constitution/guard-kernel",
        "name": "SUPELA_GUARD_KERNEL.md",
        "description": "Spécification exécutable Supela-Guard-Kernel (SUP-ICI-01, C0/C1/C2, G0..G5).",
        "mimeType": "text/markdown",
    },
]


def _tool_omega_pi0_project(args: dict[str, Any]) -> dict[str, Any]:
    omega = CloudOmega()
    omega.authorities["MCP_GATE"] = "OMEGA_ZERO"
    mid = str(args["manque_id"])
    omega.manques[mid] = Manque(
        id=mid,
        question=f"Manque {mid}",
        contexte="MCP invocation",
        origine="omega_zero.mcp_server",
        dependances=["PI0"],
        autorite="AUCUNE",
        temps="t_mcp",
        statut=ManqueStatus.OUVERT,
    )
    for item in args.get("raccords", []):
        rid = str(item["id"])
        omega.raccords[rid] = Raccord(
            id=rid,
            label=str(item["label"]),
            source=mid,
            target=f"Target:{rid}",
            origin_node="MCP",
            status=RaccordStatus(item.get("status", "CANDIDAT")),
            authority_level=AuthorityLevel(int(item.get("authority_level", 0))),
            evidence_level=AuthorityLevel(int(item.get("evidence_level", 0))),
        )
    proj = Pi0Projector()
    zero = proj.project(omega)
    return {
        "idempotent": proj.verify_idempotence(omega),
        "non_empty": zero.is_non_empty(),
        "canonical_hash": zero.canonical_hash(),
        "preserved_manques": sorted(zero.manques.keys()),
        "proofs": zero.proofs,
        "refutations": zero.refutations,
        "dropped_provisional": zero.dropped_provisional,
    }


def _tool_omega_manque_transition(args: dict[str, Any]) -> dict[str, Any]:
    m = Manque(
        id=str(args["manque_id"]),
        question="Transition via MCP",
        contexte="MCP",
        origine="MCP",
        dependances=["MCP"],
        autorite="AUCUNE",
        temps=str(args["timestamp"]),
        statut=ManqueStatus(str(args["from_status"])),
        tentatives=["init"] if args.get("evidence_ref") else [],
    )
    guard_id = ManqueStateMachine.transition(
        m,
        ManqueStatus(str(args["to_status"])),
        reason=str(args["reason"]),
        actor=str(args["actor"]),
        timestamp=str(args["timestamp"]),
        evidence_ref=args.get("evidence_ref"),
        children_ids=args.get("children_ids"),
    )
    return {"guard_id": guard_id, "manque": m.to_dict()}


def _tool_omega_grpo_explore(args: dict[str, Any]) -> dict[str, Any]:
    hyps_raw = args["hypotheses"]
    hyps = [(str(h["id"]), str(h["hypothesis"]), float(h["reward"])) for h in hyps_raw]
    verified_ids = {str(h["id"]) for h in hyps_raw if h.get("proof_verified")}
    report = SupelaGRPOBridge.explore_with_guardrails(
        str(args["query"]),
        hyps,
        r_max=float(args.get("r_max", 1.0)),
        advantage_threshold_tau=float(args.get("advantage_threshold_tau", 0.0)),
        proof_checker=lambda cid: (cid in verified_ids, "LOCAL_VERIFIED" if cid in verified_ids else ""),
    )
    return report.to_dict()


def _tool_guard_kernel_compress(args: dict[str, Any]) -> dict[str, Any]:
    kernel = SupelaGuardKernel()
    obj = kernel.create_g0_object(
        object_id=str(args["object_id"]),
        object_type="mcp_artifact",
        content=str(args["content"]).encode("utf-8"),
        author=str(args["author"]),
        origin=str(args["origin"]),
        creation_context="mcp_tool_call",
    )
    target = GenerationStage(str(args.get("target_generation", "G1")))
    level = CompressionLevel(str(args["compression_level"]))
    if target == GenerationStage.G4:
        kernel.compress_and_advance(
            obj.object_id,
            target_generation=GenerationStage.G1,
            compression_level=CompressionLevel.C0,
            reason="Passage G0->G1 avant G2",
            transformation="step_g1",
        )
        kernel.compress_and_advance(
            obj.object_id,
            target_generation=GenerationStage.G2,
            compression_level=CompressionLevel.C0,
            reason="Passage G1->G2 avant G4",
            transformation="step_g2",
        )
    after, record = kernel.compress_and_advance(
        obj.object_id,
        target_generation=target,
        compression_level=level,
        reason=str(args["reason"]),
        transformation=f"mcp_{level.value}",
        new_status=KernelObjectStatus.NON_RECLAME if target == GenerationStage.G4 else None,
    )
    return {"object": after.to_dict(), "transition": record.to_dict()}


def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    if name == "omega_pi0_project":
        return _tool_omega_pi0_project(arguments)
    if name == "omega_manque_transition":
        return _tool_omega_manque_transition(arguments)
    if name == "omega_grpo_explore":
        return _tool_omega_grpo_explore(arguments)
    if name == "guard_kernel_compress":
        return _tool_guard_kernel_compress(arguments)
    if name == "omega_run_harness":
        return evaluate_escalation_protocol(
            ROOT_DIR / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json",
            ROOT_DIR / "schemas",
        )
    if name == "omega_verify_a12":
        if str(ROOT_DIR) not in sys.path:
            sys.path.insert(0, str(ROOT_DIR))
        from scripts.verify_a12 import verify_a12

        ok, details = verify_a12(ROOT_DIR)
        return {"a12_ok": ok, **details}
    if name == "omega_verify_vr_compliance":
        return verify_vr_compliance(ROOT_DIR)
    if name == "omega_network_pipeline":
        from .network_bus import run_integrated_network_pipeline

        return run_integrated_network_pipeline(ROOT_DIR, query=str(arguments.get("query", "M-MCP-01")))
    if name == "omega_network_doctor":
        from .network_bus import run_network_doctor

        return run_network_doctor(ROOT_DIR, online=bool(arguments.get("online", False)))
    raise KeyError(f"Outil MCP inconnu : {name}")


def read_resource(uri: str) -> dict[str, str]:
    mapping = {
        "omega://constitution/index": ("docs/constitution/INDEX_CONSTITUTION.md", "text/markdown"),
        "omega://constitution/registry": ("docs/constitution/supela-article-registry-1.json", "application/json"),
        "omega://constitution/guard-kernel": ("docs/constitution/SUPELA_GUARD_KERNEL.md", "text/markdown"),
    }
    if uri not in mapping:
        raise KeyError(f"Ressource MCP inconnue : {uri}")
    rel, mime = mapping[uri]
    return {
        "uri": uri,
        "mimeType": mime,
        "text": (ROOT_DIR / rel).read_text(encoding="utf-8"),
    }


def handle_jsonrpc_request(req: dict[str, Any]) -> dict[str, Any] | None:
    method = req.get("method")
    req_id = req.get("id")
    params = req.get("params") or {}

    # Notifications sans id
    if req_id is None:
        return None

    try:
        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": PROTOCOL_VERSION,
                    "capabilities": {"tools": {}, "resources": {}},
                    "serverInfo": SERVER_INFO,
                },
            }
        if method == "ping":
            return {"jsonrpc": "2.0", "id": req_id, "result": {}}
        if method == "tools/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": TOOLS_SPEC}}
        if method == "tools/call":
            tool_name = str(params.get("name", ""))
            tool_args = params.get("arguments") or {}
            output = call_tool(tool_name, tool_args)
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [
                        {"type": "text", "text": json.dumps(output, ensure_ascii=False)}
                    ],
                    "isError": False,
                },
            }
        if method == "resources/list":
            return {"jsonrpc": "2.0", "id": req_id, "result": {"resources": RESOURCES_SPEC}}
        if method == "resources/read":
            uri = str(params.get("uri", ""))
            return {"jsonrpc": "2.0", "id": req_id, "result": {"contents": [read_resource(uri)]}}

        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {"code": -32601, "message": f"Method not found: {method}"},
        }
    except (ValueError, KeyError, TypeError, LookupError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "result": {
                "content": [{"type": "text", "text": json.dumps({"error": str(exc)}, ensure_ascii=False)}],
                "isError": True,
            },
        }


def main() -> int:
    for line in sys.stdin:
        raw = line.strip()
        if not raw:
            continue
        try:
            req = json.loads(raw)
        except json.JSONDecodeError as exc:
            err = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": f"Parse error: {exc}"},
            }
            sys.stdout.write(json.dumps(err, ensure_ascii=False) + "\n")
            sys.stdout.flush()
            continue

        resp = handle_jsonrpc_request(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
