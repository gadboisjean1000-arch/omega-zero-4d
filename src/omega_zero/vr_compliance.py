from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .models import canonical_sha256

VR_GOVERNANCE_LABELS: tuple[str, ...] = (
    "VR-BUG",
    "VR-FEATURE",
    "VR-DOCS",
    "VR-STRUCTURE",
    "VR-GOVERNANCE",
)


@dataclass
class VRRuleResult:
    rule_id: str
    title: str
    passed: bool
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "title": self.title,
            "passed": self.passed,
            "evidence": self.evidence,
        }


def _check_a12_clean(root: Path) -> tuple[bool, dict[str, list[str]]]:
    root_str = str(root)
    if root_str not in sys.path:
        sys.path.insert(0, root_str)
    from scripts.verify_a12 import verify_a12

    return verify_a12(root)


def verify_vr_compliance(root: Path | None = None) -> dict[str, Any]:
    """Vérifie de façon déterministe la conformité VR-01..VR-20 sur le dépôt réel."""
    repo_root = (root or Path(__file__).resolve().parents[2]).resolve()

    def exists(rel: str) -> bool:
        return (repo_root / rel).exists()

    def json_valid(rel: str) -> bool:
        fp = repo_root / rel
        if not fp.exists():
            return False
        try:
            json.loads(fp.read_text(encoding="utf-8"))
            return True
        except (OSError, json.JSONDecodeError, UnicodeDecodeError):
            return False

    a12_ok, a12_details = _check_a12_clean(repo_root)

    git_wf_path = repo_root / ".agents" / "rules" / "git-workflow.md"
    git_wf_text = git_wf_path.read_text(encoding="utf-8") if git_wf_path.exists() else ""
    labels_present = all(lbl in git_wf_text for lbl in VR_GOVERNANCE_LABELS)

    rego_path = repo_root / "policies" / "omega_zero_invariants.rego"
    rego_text = rego_path.read_text(encoding="utf-8") if rego_path.exists() else ""

    mcp_path = repo_root / ".agents" / "mcp_config.json"
    mcp_ok = False
    if mcp_path.exists():
        try:
            mcp_data = json.loads(mcp_path.read_text(encoding="utf-8"))
            mcp_ok = "mcpServers" in mcp_data and "omega-zero-mcp" in mcp_data["mcpServers"]
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError):
            mcp_ok = False

    env_path = repo_root / ".agents" / "environment.json"
    env_ok = False
    if env_path.exists():
        try:
            env_data = json.loads(env_path.read_text(encoding="utf-8"))
            env_ok = isinstance(env_data.get("install"), str) and bool(env_data["install"].strip())
        except (OSError, json.JSONDecodeError, UnicodeDecodeError, TypeError, AttributeError):
            env_ok = False

    checks: list[VRRuleResult] = [
        VRRuleResult("VR-01", "Constitution racine GEMINI.md présente", exists("GEMINI.md"), "GEMINI.md"),
        VRRuleResult(
            "VR-02",
            "Règles qualité code présentes",
            exists(".agents/rules/code-quality.md"),
            ".agents/rules/code-quality.md",
        ),
        VRRuleResult(
            "VR-03",
            "Règles workflow Git et labels VR présentes",
            exists(".agents/rules/git-workflow.md") and labels_present,
            "labels VR-BUG..VR-GOVERNANCE",
        ),
        VRRuleResult(
            "VR-04",
            "Contexte projet unifié présent",
            exists(".agents/rules/project-context.md"),
            ".agents/rules/project-context.md",
        ),
        VRRuleResult(
            "VR-05",
            "Opérateur Π₀ et machine à états du Manque",
            exists("src/omega_zero/projection.py") and json_valid("docs/constitution/DEFINITION_P0_PROJECTION.json"),
            "projection.py + DEFINITION_P0_PROJECTION.json",
        ),
        VRRuleResult(
            "VR-06",
            "Moteur Local–Cloud–4D et protocoles",
            exists("src/omega_zero/protocol.py") and json_valid("docs/constitution/PLAN-4D-ΩZERO-ESC-01.json"),
            "protocol.py + PLAN-4D-ΩZERO-ESC-01.json",
        ),
        VRRuleResult(
            "VR-07",
            "Harnais d'escalade 4D et rapport exécutable",
            exists("src/omega_zero/harness.py") and exists("docs/constitution/HARNAIS_TEST_ESCALADE_4D.py"),
            "harness.py + HARNAIS_TEST_ESCALADE_4D.py",
        ),
        VRRuleResult(
            "VR-08",
            "Schémas JSON Draft 2020-12 complets",
            all(
                json_valid(s)
                for s in (
                    "schemas/projection_pi0.schema.json",
                    "schemas/manque_statut.schema.json",
                    "schemas/exemple_cycle_p0.schema.json",
                    "schemas/plan_4d_omega_zero_esc_01.schema.json",
                    "schemas/execution_report.schema.json",
                    "schemas/supela_article_registry_1.schema.json",
                    "schemas/supela_encyclopedie_1.schema.json",
                    "schemas/supela_contradictions_1.schema.json",
                    "schemas/supela_guard_kernel_1.schema.json",
                )
            ),
            "9 schémas Draft 2020-12 valides",
        ),
        VRRuleResult(
            "VR-09",
            "Barrière OPA Rego v1 (invariants & Guard-Kernel)",
            "import rego.v1" in rego_text and "coherence_satisfied" in rego_text and "sup_ici_01_satisfied" in rego_text,
            "policies/omega_zero_invariants.rego",
        ),
        VRRuleResult(
            "VR-10",
            "Coffre-fort WORM logique append-only SHA-256",
            exists("src/omega_zero/worm_ledger.py") and exists("runtime/init_omega_vault.ps1"),
            "worm_ledger.py + init_omega_vault.ps1",
        ),
        VRRuleResult(
            "VR-11",
            "Attestation cryptographique Ed25519",
            exists("src/omega_zero/attestation.py"),
            "src/omega_zero/attestation.py",
        ),
        VRRuleResult(
            "VR-12",
            "Configuration d'environnement cloud reproductible",
            env_ok,
            ".agents/environment.json",
        ),
        VRRuleResult(
            "VR-13",
            "Pont GRPO ↔ Ω-ZERO (GF1–GF5)",
            exists("src/omega_zero/grpo_bridge.py") and exists("docs/constitution/COMPARAISON_GRPO_OMEGA_ZERO.md"),
            "grpo_bridge.py + COMPARAISON_GRPO_OMEGA_ZERO.md",
        ),
        VRRuleResult(
            "VR-14",
            "Supela-Guard-Kernel (SUP-ICI-01, C0/C1/C2, G0..G5)",
            exists("src/omega_zero/guard_kernel.py") and exists("docs/constitution/SUPELA_GUARD_KERNEL.md"),
            "guard_kernel.py + SUPELA_GUARD_KERNEL.md",
        ),
        VRRuleResult(
            "VR-15",
            "Registre candidat supela-article-registry/1 verrouillé",
            json_valid("docs/constitution/supela-article-registry-1.json"),
            "supela-article-registry-1.json",
        ),
        VRRuleResult(
            "VR-16",
            "Règle A12 anti-orphelins & cohérence croisée",
            a12_ok and not a12_details["orphans"] and not a12_details["broken_links"] and not a12_details["drift"],
            json.dumps(a12_details, ensure_ascii=False),
        ),
        VRRuleResult(
            "VR-17",
            "Bus réseau inter-outils & passerelle MCP stdio",
            mcp_ok and exists("src/omega_zero/network_bus.py") and exists("src/omega_zero/mcp_server.py"),
            "mcp_config.json + network_bus.py + mcp_server.py",
        ),
        VRRuleResult(
            "VR-18",
            "Document officiel scellé VR Structura Supela",
            exists("docs/constitution/VR_STRUCTURA_OFFICIAL_SEALED.md"),
            "docs/constitution/VR_STRUCTURA_OFFICIAL_SEALED.md",
        ),
        VRRuleResult(
            "VR-19",
            "Workflow GitHub Actions CI & triage gouvernance VR-19/VR-20",
            exists(".github/workflows/omega-zero-ci.yml") and exists(".github/workflows/vr-governance-triage.yml"),
            "omega-zero-ci.yml + vr-governance-triage.yml",
        ),
        VRRuleResult(
            "VR-20",
            "Vérificateur continu déterministe exécutable",
            exists("scripts/vr_compliance_check.py") and exists("src/omega_zero/vr_compliance.py"),
            "scripts/vr_compliance_check.py",
        ),
    ]

    passed_count = sum(1 for c in checks if c.passed)
    total_count = len(checks)
    all_passed = passed_count == total_count
    payload_for_hash = [c.to_dict() for c in checks]
    seal_sha256 = canonical_sha256(payload_for_hash)

    return {
        "schema": "vr-structura-compliance/1",
        "root": str(repo_root),
        "passed_count": passed_count,
        "total_count": total_count,
        "compliance_percent": round((passed_count / total_count) * 100.0, 2),
        "all_passed": all_passed,
        "seal_sha256": seal_sha256,
        "checks": payload_for_hash,
    }
