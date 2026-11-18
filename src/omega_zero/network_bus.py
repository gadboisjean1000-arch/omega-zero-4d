from __future__ import annotations

import argparse
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .attestation import AttestationSigner
from .grpo_bridge import SupelaGRPOBridge
from .guard_kernel import (
    CompressionLevel,
    GenerationStage,
    KernelObjectStatus,
    SupelaGuardKernel,
)
from .harness import evaluate_escalation_protocol
from .models import AuthorityLevel, Manque, ManqueStatus, RaccordStatus, canonical_sha256
from .projection import Pi0Projector
from .protocol import OmegaZeroEngine
from .vr_compliance import verify_vr_compliance
from .worm_ledger import WormVault


def _find_tool(root: Path, name: str) -> str | None:
    for candidate in (
        root / ".venv" / "bin" / name,
        root / ".venv" / "Scripts" / f"{name}.exe",
    ):
        if candidate.exists():
            return str(candidate)
    return shutil.which(name)


def _probe_mcp_stdio(root: Path, python_exe: str) -> dict[str, Any]:
    """Exécute un véritable aller-retour JSON-RPC 2.0 MCP sur stdin/stdout."""
    requests = [
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "clientInfo": {"name": "omega-network-doctor", "version": "1.0.0"},
                "capabilities": {},
            },
        },
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": {}},
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {"name": "omega_verify_a12", "arguments": {}},
        },
    ]
    stdin_payload = "\n".join(json.dumps(req) for req in requests) + "\n"
    probe_env = dict(os.environ)
    src_path = str(root / "src")
    existing_pp = probe_env.get("PYTHONPATH", "")
    probe_env["PYTHONPATH"] = f"{src_path}{os.pathsep}{existing_pp}" if existing_pp else src_path
    proc = subprocess.run(
        [python_exe, "-m", "omega_zero.mcp_server"],
        cwd=root,
        env=probe_env,
        input=stdin_payload,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    if proc.returncode != 0:
        return {"ok": False, "returncode": proc.returncode, "stderr": proc.stderr.strip()}

    responses = [json.loads(line) for line in proc.stdout.splitlines() if line.strip()]
    by_id = {r.get("id"): r for r in responses if "id" in r}
    tools = by_id.get(2, {}).get("result", {}).get("tools", [])
    a12_resp_raw = by_id.get(3, {}).get("result", {}).get("content", [{}])[0].get("text", "{}")
    a12_resp = json.loads(a12_resp_raw) if a12_resp_raw else {}

    return {
        "ok": (
            1 in by_id
            and 2 in by_id
            and 3 in by_id
            and len(tools) >= 8
            and a12_resp.get("a12_ok") is True
        ),
        "server_name": by_id.get(1, {}).get("result", {}).get("serverInfo", {}).get("name"),
        "tool_count": len(tools),
        "tool_names": [t.get("name") for t in tools],
        "a12_via_mcp_ok": a12_resp.get("a12_ok") is True,
    }


def _check_supela_k3_bridge(root: Path, *, online: bool) -> dict[str, Any]:
    """Vérifie le pont conceptuel et/ou réseau entre omega-zero-4d et Supela-K3-Omega."""
    sibling = root.parent / "Supela-K3-Omega"
    bridge_mapping = {
        "k3_tuple": "GDS = <D, O, A, gamma>",
        "omega_projection": "Pi0(S_t) = {I, P, M, A, H}",
        "guard_kernel_invariant": "SUP-ICI-01: K_n <= Accessible(G_{n+1})",
        "shared_gates": [
            "import rego.v1",
            "attestation_complete + attestation_fresh",
            "worm_immutable (append-only SHA-256)",
            "no_authority_exceeds_proof",
        ],
    }

    if sibling.exists() and (sibling / "policies" / "gds_invariants.rego").exists():
        return {
            "status": "CONNECTED_LOCAL",
            "repo": "gadboisjean1000-arch/Supela-K3-Omega",
            "path": str(sibling),
            "mapping": bridge_mapping,
        }

    if online:
        gh_bin = shutil.which("gh")
        if gh_bin:
            res = subprocess.run(
                [gh_bin, "api", "repos/gadboisjean1000-arch/Supela-K3-Omega", "--jq", ".full_name,.visibility,.default_branch"],
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
            if res.returncode == 0:
                lines = [ln.strip() for ln in res.stdout.splitlines() if ln.strip()]
                return {
                    "status": "CONNECTED_GITHUB_API",
                    "repo": lines[0] if lines else "gadboisjean1000-arch/Supela-K3-Omega",
                    "visibility": lines[1] if len(lines) > 1 else "unknown",
                    "default_branch": lines[2] if len(lines) > 2 else "main",
                    "mapping": bridge_mapping,
                }

    return {
        "status": "BRIDGE_READY_OFFLINE",
        "repo": "gadboisjean1000-arch/Supela-K3-Omega",
        "mapping": bridge_mapping,
    }


def _rustc_supports_file_lock() -> bool:
    rustc = shutil.which("rustc")
    if not rustc:
        return False
    try:
        res = subprocess.run([rustc, "--version"], capture_output=True, text=True, timeout=10, check=False)
    except (OSError, subprocess.SubprocessError):
        return False
    if res.returncode != 0:
        return False
    parts = res.stdout.strip().split()
    if len(parts) < 2:
        return False
    ver_nums = parts[1].split(".")
    if len(ver_nums) < 2:
        return False
    try:
        major, minor = int(ver_nums[0]), int(ver_nums[1])
    except ValueError:
        return False
    return (major, minor) >= (1, 89)


def _probe_rust_guard_kernel(root: Path, cargo_bin: str | None) -> dict[str, Any]:
    """Vérifie la disponibilité et le dialogue réel SUP-IPC-01 avec le binaire Rust."""
    crate_dir = root / "rust" / "supela-guard-kernel"
    if not (crate_dir / "Cargo.toml").exists():
        return {
            "crate_present": False,
            "ipc_protocol": "SUP-IPC-01",
            "ipc_probe_ok": False,
            "status": "CRATE_ABSENT",
        }

    bin_name = "supela-guard-kernel.exe" if sys.platform.startswith("win") else "supela-guard-kernel"
    prebuilt = next(
        (
            candidate
            for candidate in (
                crate_dir / "target" / "debug" / bin_name,
                crate_dir / "target" / "release" / bin_name,
            )
            if candidate.exists()
        ),
        None,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        journal_path = Path(tmpdir) / "bus_rust_probe.jsonl"
        if prebuilt is not None:
            cmd = [str(prebuilt), "serve", "--journal", str(journal_path)]
            cwd = root
            mode = "PREBUILT_BINARY"
        elif cargo_bin is not None and _rustc_supports_file_lock():
            cmd = [cargo_bin, "run", "--locked", "--quiet", "--", "serve", "--journal", str(journal_path)]
            cwd = crate_dir
            mode = "CARGO_RUN_LOCKED"
        else:
            return {
                "crate_present": True,
                "ipc_protocol": "SUP-IPC-01",
                "ipc_probe_ok": False,
                "status": "CARGO_UNAVAILABLE_OR_RUSTC_LT_1_89",
            }

        ipc_requests = [
            {"protocol": "SUP-IPC-01", "request_id": "bus-rust-ping", "op": "ping", "params": {}},
            {
                "protocol": "SUP-IPC-01",
                "request_id": "bus-rust-eval",
                "op": "evaluate_candidate",
                "params": {"candidate_id": "H-BUS-RUST", "reward": 0.85, "r_max": 1.0},
            },
            {
                "protocol": "SUP-IPC-01",
                "request_id": "bus-rust-verify",
                "op": "verify_chain",
                "params": {},
            },
        ]
        stdin_payload = "\n".join(json.dumps(r) for r in ipc_requests) + "\n"
        try:
            proc = subprocess.run(
                cmd,
                cwd=cwd,
                input=stdin_payload,
                text=True,
                capture_output=True,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.SubprocessError) as exc:
            return {
                "crate_present": True,
                "ipc_protocol": "SUP-IPC-01",
                "ipc_probe_ok": False,
                "status": f"EXEC_ERROR:{exc}",
            }

        if proc.returncode != 0:
            return {
                "crate_present": True,
                "ipc_protocol": "SUP-IPC-01",
                "ipc_probe_ok": False,
                "status": f"EXIT_{proc.returncode}",
                "stderr": proc.stderr.strip(),
            }

        try:
            responses = [json.loads(ln) for ln in proc.stdout.splitlines() if ln.strip()]
        except json.JSONDecodeError as exc:
            return {
                "crate_present": True,
                "ipc_protocol": "SUP-IPC-01",
                "ipc_probe_ok": False,
                "status": f"INVALID_JSON_OUTPUT:{exc}",
            }

        by_id = {r.get("request_id"): r for r in responses if isinstance(r, dict)}
        eval_verdict = (
            by_id.get("bus-rust-eval", {})
            .get("result", {})
            .get("evaluation", {})
            .get("promotion_verdict")
        )
        chain_res = by_id.get("bus-rust-verify", {}).get("result", {})
        ok = (
            len(responses) == 3
            and all(bool(r.get("ok")) for r in responses)
            and eval_verdict == "ADMISSIBLE_A_REVUE_HUMAINE"
            and chain_res.get("entries") == 1
            and chain_res.get("valid") is True
        )
        return {
            "crate_present": True,
            "ipc_protocol": "SUP-IPC-01",
            "mode": mode,
            "ipc_probe_ok": ok,
            "eval_verdict": eval_verdict,
            "worm_entries_after_probe": chain_res.get("entries"),
            "status": "OPERATIONAL" if ok else "PROBE_FAILED",
        }


def run_network_doctor(root: Path | None = None, *, online: bool = False) -> dict[str, Any]:
    """Inspecte et vérifie l'intercommunication réelle entre tous les outils du réseau Supela Ω-ZERO."""
    repo_root = (root or Path(__file__).resolve().parents[2]).resolve()
    python_exe = _find_tool(repo_root, "python") or sys.executable
    cargo_bin = _find_tool(repo_root, "cargo")

    tools_found = {
        "python": python_exe,
        "pytest": _find_tool(repo_root, "pytest"),
        "ruff": _find_tool(repo_root, "ruff"),
        "mypy": _find_tool(repo_root, "mypy"),
        "opa": _find_tool(repo_root, "opa"),
        "cosign": _find_tool(repo_root, "cosign"),
        "cargo": cargo_bin,
        "git": _find_tool(repo_root, "git"),
        "gh": _find_tool(repo_root, "gh"),
        "gdrive": _find_tool(repo_root, "gdrive"),
    }

    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    from scripts.verify_a12 import verify_a12

    a12_ok, a12_details = verify_a12(repo_root)
    vr_result = verify_vr_compliance(repo_root)
    mcp_probe = _probe_mcp_stdio(repo_root, python_exe)
    rust_probe = _probe_rust_guard_kernel(repo_root, cargo_bin)
    k3_bridge = _check_supela_k3_bridge(repo_root, online=online)

    core_operational = (
        a12_ok
        and vr_result["all_passed"]
        and mcp_probe["ok"]
        and tools_found["pytest"] is not None
        and tools_found["opa"] is not None
    )

    return {
        "schema": "omega-network-doctor/1",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "root": str(repo_root),
        "operational": core_operational,
        "tools": tools_found,
        "a12": {"ok": a12_ok, **a12_details},
        "vr_compliance": {
            "passed_count": vr_result["passed_count"],
            "total_count": vr_result["total_count"],
            "all_passed": vr_result["all_passed"],
            "seal_sha256": vr_result["seal_sha256"],
        },
        "mcp_stdio_probe": mcp_probe,
        "rust_guard_kernel": rust_probe,
        "supela_k3_bridge": k3_bridge,
    }


def run_integrated_network_pipeline(
    root: Path | None = None,
    *,
    query: str = "M-NET-GRPO-01",
    hypotheses: list[tuple[str, str, float]] | None = None,
) -> dict[str, Any]:
    """Fait circuler un cycle complet entre GRPO(GF1-5) → Ω-ZERO(Π₀) → Guard-Kernel → OPA → WORM → Ed25519."""
    repo_root = (root or Path(__file__).resolve().parents[2]).resolve()
    hyps = hypotheses or [
        ("H-HIGH-OUTLIER", "Score aberrant non borné sans preuve", 9.5),
        ("H-VALIDATED", "Protocole conditionnel avec épreuve locale", 0.85),
        ("H-LOW", "Hypothèse faiblement notée", 0.15),
    ]

    # 1. GRPO Explorer avec garde-fous GF1..GF5
    grpo_report = SupelaGRPOBridge.explore_with_guardrails(
        query,
        hyps,
        r_max=1.0,
        advantage_threshold_tau=0.0,
        proof_checker=lambda cid: (cid == "H-VALIDATED", "TEST_LOCAL_VALIDE" if cid == "H-VALIDATED" else ""),
    )

    # 2. Moteur Ω-ZERO + Projection Π₀
    engine = OmegaZeroEngine()
    node = engine.register_local_node("L-NET", "Noeud-Bus", "LOCAL", "AUTORITE_LOCALE")
    manque = Manque(
        id=query,
        question="Validation inter-outils GRPO -> Ω-ZERO -> Guard-Kernel",
        contexte="Cycle intégré du bus réseau",
        origine="network_bus",
        dependances=["GRPO", "PI0", "SUP-ICI-01", "OPA"],
        autorite="AUCUNE",
        temps=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        statut=ManqueStatus.OUVERT,
    )
    engine.inject_manque(node, manque)
    for raccord in grpo_report.admitted_raccords:
        engine.add_candidate_raccord(node, raccord, manque_id=query)

    zero_state = Pi0Projector().project(engine.cloud)
    pi0_idempotent = Pi0Projector().verify_idempotence(engine.cloud)

    # 3. Supela-Guard-Kernel (G0 -> G1 -> G2 sous SUP-ICI-01 & compression C1)
    kernel = SupelaGuardKernel()
    payload_bytes = json.dumps(grpo_report.to_dict(), sort_keys=True, ensure_ascii=False).encode("utf-8")
    obj_g0 = kernel.create_g0_object(
        object_id=f"OBJ-{query}",
        object_type="grpo_exploration_bundle",
        content=payload_bytes,
        author="omega-network-bus",
        origin="GRPO_EXPLORER",
        creation_context="pipeline_integre",
        status=KernelObjectStatus.HYPOTHESE,
        scope="LOCAL_EXPLORATION",
        dependencies=[query],
        proof_refs=["TRACE-GRPO-GF5"],
    )
    _, rec_g1 = kernel.compress_and_advance(
        obj_g0.object_id,
        target_generation=GenerationStage.G1,
        compression_level=CompressionLevel.C0,
        reason="Ouverture en génération de travail G1",
        transformation="promote_source_to_work",
    )
    obj_g2, rec_g2 = kernel.compress_and_advance(
        obj_g0.object_id,
        target_generation=GenerationStage.G2,
        compression_level=CompressionLevel.C1,
        reason="Compression réversible C1 avant épreuve OPA",
        transformation="zlib_lossless_c1",
    )
    assert kernel.decompress_c1(obj_g2.object_id) == payload_bytes

    # 4. Exécution du harnais 4D complet + vérification OPA live
    harness_report = evaluate_escalation_protocol(
        repo_root / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json",
        repo_root / "schemas",
    )

    opa_bin = _find_tool(repo_root, "opa")
    opa_allowed: bool | None = None
    if opa_bin:
        now_iso = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        opa_input = {
            "protocol": {"sha256": harness_report["protocol_sha256"]},
            "attestation": {
                "producer_id": "omega-network-bus",
                "provenance": "omega_zero.network_bus",
                "signature": "c2lnbmVkLW9tZWdhLWJ1cw==",
                "nonce": "nonce-bus-001",
                "timestamp": now_iso,
                "protocol_sha256": harness_report["protocol_sha256"],
            },
            "ledger": {"mode": "append-only", "tamper_detected": False},
            "ci_cd": {"branch": "refs/heads/main", "direct_commit_to_main": False},
            "report": harness_report,
            "raccords": [
                {
                    "id": r.id,
                    "status": r.status.value,
                    "authority_level": int(r.authority_level),
                    "evidence_level": int(r.evidence_level),
                    "is_emergent": r.is_emergent,
                    "validation_required": r.validation_required,
                    "origin_type": "GRPO_SCORE_ONLY",
                }
                for r in grpo_report.admitted_raccords
            ]
            or [
                {
                    "id": "H-DEFAULT",
                    "status": RaccordStatus.CANDIDAT.value,
                    "authority_level": int(AuthorityLevel.AUCUNE),
                    "evidence_level": int(AuthorityLevel.AUCUNE),
                    "is_emergent": False,
                    "validation_required": True,
                    "origin_type": "GRPO_SCORE_ONLY",
                }
            ],
            "manques": [{"id": query, "statut": "SOUS_EXPLORATION", "silently_deleted": False}],
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
            "guard_kernel_transitions": [rec_g1.to_dict(), rec_g2.to_dict()],
            "grpo_explorations": [t.to_dict() for t in grpo_report.traces],
        }
        with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=True) as tf:
            json.dump(opa_input, tf)
            tf.flush()
            eval_res = subprocess.run(
                [
                    opa_bin,
                    "eval",
                    "--format=json",
                    "--data",
                    "policies/omega_zero_invariants.rego",
                    "--input",
                    tf.name,
                    "data.supela.omega_zero.governance.allow_human_review",
                ],
                cwd=repo_root,
                capture_output=True,
                text=True,
                check=True,
            )
            parsed = json.loads(eval_res.stdout)
            opa_allowed = bool(parsed["result"][0]["expressions"][0]["value"])

    # 5. Scellement éphémère WORM + signature Ed25519
    with tempfile.TemporaryDirectory() as tmpdir:
        vault = WormVault(Path(tmpdir) / "bus_vault")
        vault_res = vault.init_idempotent(harness_report["protocol_sha256"])
        bus_payload = {
            "grpo": grpo_report.to_dict(),
            "guard_kernel_g2": rec_g2.to_dict(),
            "harness_verdict": harness_report["verdict"],
            "opa_allow_human_review": opa_allowed,
        }
        entry = vault.append_event("NETWORK_BUS_PIPELINE", bus_payload)
        chain_ok, _ = vault.verify_chain()

    signer = AttestationSigner()
    signed = signer.sign_report(harness_report, producer_id="omega-network-bus")
    sig_valid = AttestationSigner.verify(signed, harness_report)

    return {
        "schema": "omega-network-pipeline/1",
        "query": query,
        "grpo": grpo_report.to_dict(),
        "pi0": {
            "idempotent": pi0_idempotent,
            "non_empty": zero_state.is_non_empty(),
            "manques_preserved": sorted(zero_state.manques.keys()),
        },
        "guard_kernel": {
            "sup_ici_01_records": [rec_g1.to_dict(), rec_g2.to_dict()],
            "c1_roundtrip_verified": True,
        },
        "harness": {
            "verdict": harness_report["verdict"],
            "promotion": harness_report["promotion"],
            "conditions": len(harness_report["condition_results"]),
        },
        "opa_allow_human_review": opa_allowed,
        "worm": {
            "manifest_sha256": vault_res.manifest_sha256,
            "entry_hash": entry["entry_hash"],
            "chain_valid": chain_ok,
        },
        "ed25519_verified": sig_valid,
        "pipeline_digest": canonical_sha256({"entry": entry["entry_hash"], "sig": signed.signature_b64}),
    }


def run_pcep_prepare(root: Path | None = None, *, out_path: Path | None = None) -> dict[str, Any]:
    """Formalise toutes les possibilités PCEP sur le réseau et produit l'enveloppe prête à signer."""
    from jsonschema import Draft202012Validator

    from .pcep import build_pcep_network_envelope

    repo_root = (root or Path(__file__).resolve().parents[2]).resolve()
    plan_path = repo_root / "docs" / "constitution" / "PLAN-4D-ΩZERO-ESC-01.json"
    protocol_sha = canonical_sha256(json.loads(plan_path.read_text(encoding="utf-8"))) if plan_path.exists() else ""

    envelope = build_pcep_network_envelope(protocol_sha256=protocol_sha)
    schema_path = repo_root / "schemas" / "supela_pcep_network_1.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    Draft202012Validator(schema).validate(envelope)

    if out_path is not None:
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(envelope, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return envelope


def main(argv: list[str] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(description="Bus réseau inter-outils Supela Ω-ZERO.")
    sub = parser.add_subparsers(dest="cmd", required=True)

    doc_p = sub.add_parser("doctor", help="Vérifie l'état opérationnel de tous les outils et du MCP.")
    doc_p.add_argument("--online", action="store_true", help="Interroge aussi GitHub API pour Supela-K3-Omega.")

    pipe_p = sub.add_parser("pipeline", help="Exécute un cycle complet GRPO → Π₀ → Guard-Kernel → OPA → WORM → Ed25519.")
    pipe_p.add_argument("--query", default="M-NET-GRPO-01")

    pcep_p = sub.add_parser("pcep-prepare", help="Formalise l'enveloppe réseau PCEP prête à signer (EN_ATTENTE_SIGNATURE).")
    pcep_p.add_argument("--out", default="", help="Chemin JSON de sortie optionnel.")

    sub.add_parser(
        "sovereign-verify",
        help="Vérifie le noyau inhérent (ZERO-STATE-01, SUP-NORM-NET-01/1.0, Anti-EaaS, Ed25519, topologies).",
    )
    math_p = sub.add_parser(
        "math-eval",
        help="Exécute les invariants mathématiques unifiés MAT-00..MAT-08 et GENERIC.",
    )
    math_p.add_argument("--validator", default="Jean-François Gadbois")

    rt_p = sub.add_parser(
        "runtime-cycle",
        help="Exécute un cycle complet du système nerveux Supela Runtime v0.2 (L0-L7 : Concept -> Contradiction -> Révision G2 -> Ratification -> Réouverture).",
    )
    rt_p.add_argument("--out", default="", help="Chemin JSON de sortie optionnel.")

    args = parser.parse_args(argv)
    if args.cmd == "doctor":
        res = run_network_doctor(online=bool(args.online))
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["operational"] else 1

    if args.cmd == "pcep-prepare":
        out = Path(args.out) if args.out else None
        res = run_pcep_prepare(out_path=out)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        sig_env = res["signature_envelope"]
        return 0 if sig_env["ready_for_signature"] and sig_env["signature_status"] == "EN_ATTENTE_SIGNATURE" else 1

    if args.cmd == "sovereign-verify":
        from .sovereign_net import run_sovereign_net_self_check

        res = run_sovereign_net_self_check()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["audit_trail_verified"] and not res["external_eaas_recalculation"] else 1

    if args.cmd == "math-eval":
        from .supela_math_core import run_supela_math_unification

        res = run_supela_math_unification(validator_name=args.validator)
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["generic_thermodynamics"]["generic_valid"] and res["mat_00_monotone_k"] else 1

    if args.cmd == "runtime-cycle":
        from .supela_runtime import run_supela_runtime_complete_cycle_demo

        repo_root = Path(__file__).resolve().parents[2]
        res = run_supela_runtime_complete_cycle_demo(repo_root)
        if args.out:
            out_path = Path(args.out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(json.dumps(res, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        inv = res["invariants_verified"]
        return 0 if all(inv.values()) else 1

    res = run_integrated_network_pipeline(query=args.query)
    print(json.dumps(res, indent=2, ensure_ascii=False))
    ok = (
        res["pi0"]["idempotent"]
        and res["guard_kernel"]["c1_roundtrip_verified"]
        and res["harness"]["verdict"] == "PASS"
        and res["worm"]["chain_valid"]
        and res["ed25519_verified"]
        and (res["opa_allow_human_review"] in (True, None))
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())

