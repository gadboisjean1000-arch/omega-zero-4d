from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any

from .models import canonical_sha256


class ClaimStatus(StrEnum):
    VALID = "VALID"
    CONTRADICTED = "CONTRADICTED"
    REOPEN = "REOPEN"
    REVALIDATE = "REVALIDATE"
    UNKNOWN = "UNKNOWN"
    A_PROUVER = "A_PROUVER"


class ReferentialVerdict(StrEnum):
    TRUE = "TRUE"
    UNKNOWN = "UNKNOWN"
    CONTRADICTORY = "CONTRADICTORY"


class SignatureStatus(StrEnum):
    EN_ATTENTE_SIGNATURE = "EN_ATTENTE_SIGNATURE"
    SIGNEE = "SIGNEE"


ALLOWED_REVOCATION_TRANSITIONS: dict[ClaimStatus, set[ClaimStatus]] = {
    ClaimStatus.VALID: {ClaimStatus.CONTRADICTED, ClaimStatus.REOPEN},
    ClaimStatus.CONTRADICTED: {ClaimStatus.REOPEN},
    ClaimStatus.REOPEN: {ClaimStatus.REVALIDATE, ClaimStatus.CONTRADICTED},
    ClaimStatus.REVALIDATE: {ClaimStatus.VALID, ClaimStatus.CONTRADICTED, ClaimStatus.REOPEN},
}


@dataclass(frozen=True)
class ProvenanceRecord:
    timestamp: str
    action: str
    actor: str
    state_hash: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "actor": self.actor,
            "state_hash": self.state_hash,
        }


@dataclass
class ClaimNode:
    """Objet autonome d'encyclopédie exécutable (Familles F2, F5, F9)."""

    claim_id: str
    statement: str
    referential: str
    sources: list[str]
    proofs: list[str] = field(default_factory=list)
    counter_evidence: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    status: ClaimStatus = ClaimStatus.UNKNOWN
    history: list[ProvenanceRecord] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.sources:
            raise ValueError(f"Claim {self.claim_id}: au moins une source est requise.")
        if not self.history:
            ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            digest = canonical_sha256(
                {
                    "claim_id": self.claim_id,
                    "statement": self.statement,
                    "referential": self.referential,
                    "sources": self.sources,
                }
            )
            self.history.append(
                ProvenanceRecord(
                    timestamp=ts,
                    action="INIT_CLAIM",
                    actor="pcep_engine",
                    state_hash=digest,
                )
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "statement": self.statement,
            "referential": self.referential,
            "sources": list(self.sources),
            "proofs": list(self.proofs),
            "counter_evidence": list(self.counter_evidence),
            "dependencies": list(self.dependencies),
            "status": self.status.value,
            "history": [h.to_dict() for h in self.history],
        }


@dataclass(frozen=True)
class ReferentialEvaluation:
    """Évaluation contextualisée à un référentiel R (Famille F4)."""

    claim_id: str
    referential: str
    verdict: ReferentialVerdict
    proof_present: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "referential": self.referential,
            "verdict": self.verdict.value,
            "proof_present": self.proof_present,
        }


@dataclass(frozen=True)
class ReferentialTransport:
    """Transport formel R1 -> R2 (fail-closed sans preuve de transport)."""

    claim_id: str
    source_referential: str
    target_referential: str
    conditions: list[str]
    transport_proof_verified: bool

    @property
    def transport_allowed(self) -> bool:
        return bool(self.conditions) and self.transport_proof_verified

    @property
    def target_verdict(self) -> ReferentialVerdict:
        return ReferentialVerdict.TRUE if self.transport_allowed else ReferentialVerdict.UNKNOWN

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "source_referential": self.source_referential,
            "target_referential": self.target_referential,
            "conditions": list(self.conditions),
            "transport_proof_verified": self.transport_proof_verified,
            "transport_allowed": self.transport_allowed,
            "target_verdict": self.target_verdict.value,
        }


@dataclass(frozen=True)
class AutoRevocationTransition:
    """Transition d'auto-révocation VALID -> CONTRADICTED -> REOPEN -> REVALIDATE (Famille F1)."""

    claim_id: str
    from_status: ClaimStatus
    to_status: ClaimStatus
    reason: str
    contradiction_preserved: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "claim_id": self.claim_id,
            "from_status": self.from_status.value,
            "to_status": self.to_status.value,
            "reason": self.reason,
            "contradiction_preserved": self.contradiction_preserved,
        }


@dataclass(frozen=True)
class CalculatedAuthorityAgent:
    """Agent IA à autorité calculée : capacité != autorité d'action (Famille F7)."""

    agent_id: str
    reasoning_capacity: int
    verified_proof_level: int
    requested_authority: int | None = None

    def __post_init__(self) -> None:
        for val in (self.reasoning_capacity, self.verified_proof_level):
            if not (0 <= val <= 4):
                raise ValueError("Les niveaux doivent être compris entre 0 et 4.")

    @property
    def action_authority(self) -> int:
        if self.requested_authority is None:
            return self.verified_proof_level
        return min(self.requested_authority, self.verified_proof_level)

    @property
    def bounded_ok(self) -> bool:
        return self.action_authority <= self.verified_proof_level

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "reasoning_capacity": self.reasoning_capacity,
            "verified_proof_level": self.verified_proof_level,
            "action_authority": self.action_authority,
            "bounded_ok": self.bounded_ok,
        }


@dataclass(frozen=True)
class SelfRefutingProbe:
    """Sonde adversariale auto-réfutable : FAIL informatif conservé (Famille F8)."""

    probe_id: str
    target_claim_id: str
    outcome: str
    fail_informative_preserved: bool
    counter_evidence_ref: str

    def __post_init__(self) -> None:
        if self.outcome not in {"PASS", "FAIL_INFORMATIF"}:
            raise ValueError("outcome doit être 'PASS' ou 'FAIL_INFORMATIF'.")

    def to_dict(self) -> dict[str, Any]:
        return {
            "probe_id": self.probe_id,
            "target_claim_id": self.target_claim_id,
            "outcome": self.outcome,
            "fail_informative_preserved": self.fail_informative_preserved,
            "counter_evidence_ref": self.counter_evidence_ref,
        }


@dataclass(frozen=True)
class EvolutionaryCodeStep:
    """Code_{t+1} = Transformation(Code_t) + Trace + Portée + Preuve + Contre-preuve (Familles F2, F3)."""

    step_id: str
    previous_hash: str
    transformation: str
    trace: str
    scope: str
    proof_refs: list[str]
    counter_evidence: list[str]
    generation_stage: str = "G2"

    def __post_init__(self) -> None:
        if not self.proof_refs:
            raise ValueError(f"EvolutionaryCodeStep {self.step_id}: au moins une preuve est requise.")
        if not self.trace or not self.scope:
            raise ValueError(f"EvolutionaryCodeStep {self.step_id}: trace et scope requis.")

    @property
    def next_hash(self) -> str:
        return canonical_sha256(
            {
                "step_id": self.step_id,
                "previous_hash": self.previous_hash,
                "transformation": self.transformation,
                "trace": self.trace,
                "scope": self.scope,
                "proof_refs": self.proof_refs,
                "counter_evidence": self.counter_evidence,
                "generation_stage": self.generation_stage,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "step_id": self.step_id,
            "previous_hash": self.previous_hash,
            "next_hash": self.next_hash,
            "transformation": self.transformation,
            "trace": self.trace,
            "scope": self.scope,
            "proof_refs": list(self.proof_refs),
            "counter_evidence": list(self.counter_evidence),
            "generation_stage": self.generation_stage,
        }


DEFAULT_OPEN_PROOFS: list[dict[str, Any]] = [
    {
        "id": "OPEN-01",
        "title": "Validité universelle de Supela sur tout système arbitraire",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Les tests locaux couvrent un périmètre fini, non universel.",
    },
    {
        "id": "OPEN-02",
        "title": "Théorème du Vide / stabilisation absolue vers Ω₀",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Formalisation existante, démonstration mathématique générale ouverte.",
    },
    {
        "id": "OPEN-03",
        "title": "Terminaison générale d'un calcul Supela arbitraire",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Aucune preuve générale de terminaison pour toute entrée.",
    },
    {
        "id": "OPEN-04",
        "title": "Transport général du VRAI entre référentiels R1 -> R2",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Requiert des conditions de transport démontrées au cas par cas.",
    },
    {
        "id": "OPEN-05",
        "title": "Compression intergénérationnelle sans perte de sens pour toute classe",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Vérifiée en C1 réversible; cas général C2 irréversible borné.",
    },
    {
        "id": "OPEN-06",
        "title": "Exhaustivité absolue du cône de dépendance et de la provenance hors journal",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Un journal prouve ce qu'il contient, non l'absence d'événements externes.",
    },
    {
        "id": "OPEN-07",
        "title": "Gold Signature et certification institutionnelle externe universelle",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Spécification interne en attente d'accréditation externe indépendante.",
    },
    {
        "id": "OPEN-08",
        "title": "Doctrine 0$ PMU universelle et souveraineté matérielle complète",
        "status": "A_PROUVER",
        "promoted": False,
        "reason": "Coût nul != dépendance nulle; TPM matériel optionnel absent en CI.",
    },
]


class PCEPEngine:
    """Moteur unifié Proof-Carrying Evolutionary Programming (9 familles + enveloppe à signer)."""

    def __init__(self) -> None:
        self.claims: dict[str, ClaimNode] = {}
        self.revocation_transitions: list[AutoRevocationTransition] = []

    def register_claim(self, claim: ClaimNode) -> None:
        self.claims[claim.claim_id] = claim

    def transition_claim(
        self,
        claim_id: str,
        to_status: ClaimStatus,
        *,
        reason: str,
        actor: str = "pcep_engine",
        counter_evidence_ref: str | None = None,
    ) -> AutoRevocationTransition:
        claim = self.claims[claim_id]
        from_status = claim.status
        allowed = ALLOWED_REVOCATION_TRANSITIONS.get(from_status, set())
        if to_status not in allowed:
            raise ValueError(
                f"Transition auto-révocable interdite: {from_status.value} -> {to_status.value}"
            )
        if counter_evidence_ref and counter_evidence_ref not in claim.counter_evidence:
            claim.counter_evidence.append(counter_evidence_ref)
        claim.status = to_status
        ts = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
        prev_hash = claim.history[-1].state_hash
        new_hash = canonical_sha256(
            {
                "prev_hash": prev_hash,
                "from": from_status.value,
                "to": to_status.value,
                "reason": reason,
                "counter_evidence": claim.counter_evidence,
            }
        )
        claim.history.append(
            ProvenanceRecord(
                timestamp=ts,
                action=f"TRANSITION:{from_status.value}->{to_status.value}",
                actor=actor,
                state_hash=new_hash,
            )
        )
        tx = AutoRevocationTransition(
            claim_id=claim_id,
            from_status=from_status,
            to_status=to_status,
            reason=reason,
            contradiction_preserved=bool(claim.counter_evidence),
        )
        self.revocation_transitions.append(tx)
        return tx

    def compute_dependency_cone(self, root_claim_id: str) -> dict[str, Any]:
        """Calcul par cône de dépendance (Famille F6) : ordre BFS des dépendants impactés."""
        if root_claim_id not in self.claims:
            raise KeyError(f"Claim inconnu: {root_claim_id}")
        reverse_adj: dict[str, list[str]] = {cid: [] for cid in self.claims}
        for cid, node in self.claims.items():
            for dep in node.dependencies:
                if dep in reverse_adj:
                    reverse_adj[dep].append(cid)

        visited: set[str] = {root_claim_id}
        order: list[str] = []
        queue: deque[str] = deque([root_claim_id])
        while queue:
            cur = queue.popleft()
            for child in sorted(reverse_adj.get(cur, [])):
                if child not in visited:
                    visited.add(child)
                    order.append(child)
                    queue.append(child)

        return {
            "root_claim_id": root_claim_id,
            "impacted_claims": sorted(order),
            "reevaluation_order": order,
        }


def build_pcep_network_envelope(
    *,
    protocol_sha256: str = "",
    sign_commands: list[str] | None = None,
) -> dict[str, Any]:
    """Construit l'enveloppe réseau PCEP complète : toutes les possibilités formalisées, prête à signer."""
    engine = PCEPEngine()

    c_pi0 = ClaimNode(
        claim_id="CLAIM-PI0-LOCAL",
        statement="L'opérateur Π₀ est idempotent et préserve les 5 composantes sur le périmètre local.",
        referential="R_LOCAL_PYTHON_311",
        sources=["src/omega_zero/projection.py", "tests/test_pi0_and_manque.py"],
        proofs=["pytest:test_pi0_and_manque", "hypothesis:24_permutations"],
        counter_evidence=[],
        dependencies=[],
        status=ClaimStatus.VALID,
    )
    c_gk = ClaimNode(
        claim_id="CLAIM-GK-SUP-ICI-01",
        statement="SupelaGuardKernel préserve K_n ⊆ Accessible(G_{n+1}) en C0/C1.",
        referential="R_LOCAL_PYTHON_RUST",
        sources=["src/omega_zero/guard_kernel.py", "rust/supela-guard-kernel/src/kernel.rs"],
        proofs=["pytest:test_guard_kernel", "cargo_test:26_tests"],
        counter_evidence=[],
        dependencies=["CLAIM-PI0-LOCAL"],
        status=ClaimStatus.VALID,
    )
    c_grpo = ClaimNode(
        claim_id="CLAIM-GRPO-BRIDGE",
        statement="Le pont GRPO GF1..GF5 isole les scores aberrants sans promouvoir en vérité.",
        referential="R_LOCAL_PYTHON_311",
        sources=["src/omega_zero/grpo_bridge.py", "tests/test_second_domain_example.py"],
        proofs=["pytest:test_grpo_guardrails", "opa:grpo_guardrails_satisfied"],
        counter_evidence=[],
        dependencies=["CLAIM-PI0-LOCAL"],
        status=ClaimStatus.VALID,
    )
    c_auto = ClaimNode(
        claim_id="CLAIM-AUTO-REVOCATION-DEMO",
        statement="Une contradiction adversariale déclenche la révocation sans effacer l'historique.",
        referential="R_LOCAL_PYTHON_311",
        sources=["src/omega_zero/pcep.py"],
        proofs=["pytest:test_pcep"],
        counter_evidence=[],
        dependencies=["CLAIM-GK-SUP-ICI-01"],
        status=ClaimStatus.VALID,
    )

    for c in (c_pi0, c_gk, c_grpo, c_auto):
        engine.register_claim(c)

    # Démonstration exécutable F1 + F5 : VALID -> CONTRADICTED -> REOPEN -> REVALIDATE
    engine.transition_claim(
        "CLAIM-AUTO-REVOCATION-DEMO",
        ClaimStatus.CONTRADICTED,
        reason="Sonde adversariale PROBE-ADV-01 : contre-exemple borné détecté",
        counter_evidence_ref="PROBE-ADV-01:FAIL_INFORMATIF",
    )
    engine.transition_claim(
        "CLAIM-AUTO-REVOCATION-DEMO",
        ClaimStatus.REOPEN,
        reason="Réouverture explicite du cône pour réexamen sous preuve",
    )
    engine.transition_claim(
        "CLAIM-AUTO-REVOCATION-DEMO",
        ClaimStatus.REVALIDATE,
        reason="Réévaluation bornée au référentiel local avec contre-preuve conservée",
    )

    referential_evaluations = [
        ReferentialEvaluation(
            claim_id="CLAIM-PI0-LOCAL",
            referential="R_LOCAL_PYTHON_311",
            verdict=ReferentialVerdict.TRUE,
            proof_present=True,
        ).to_dict(),
        ReferentialEvaluation(
            claim_id="CLAIM-PI0-LOCAL",
            referential="R_UNIVERSAL_UNBOUNDED",
            verdict=ReferentialVerdict.UNKNOWN,
            proof_present=False,
        ).to_dict(),
        ReferentialEvaluation(
            claim_id="CLAIM-AUTO-REVOCATION-DEMO",
            referential="R_LOCAL_PYTHON_311",
            verdict=ReferentialVerdict.CONTRADICTORY,
            proof_present=True,
        ).to_dict(),
    ]

    referential_transports = [
        ReferentialTransport(
            claim_id="CLAIM-PI0-LOCAL",
            source_referential="R_LOCAL_PYTHON_311",
            target_referential="R_UNIVERSAL_UNBOUNDED",
            conditions=["Démontrer invariance sur domaine infini non borné"],
            transport_proof_verified=False,
        ).to_dict(),
        ReferentialTransport(
            claim_id="CLAIM-GK-SUP-ICI-01",
            source_referential="R_LOCAL_PYTHON_RUST",
            target_referential="R_LOCAL_MCP_BUS",
            conditions=["Parité JSON-RPC 2.0 + SUP-IPC-01 vérifiée par doctor"],
            transport_proof_verified=True,
        ).to_dict(),
    ]

    dependency_cone = engine.compute_dependency_cone("CLAIM-PI0-LOCAL")

    agent_authorities = [
        CalculatedAuthorityAgent(
            agent_id="AGENT-EXPLORER-GRPO",
            reasoning_capacity=4,
            verified_proof_level=1,
            requested_authority=4,
        ).to_dict(),
        CalculatedAuthorityAgent(
            agent_id="AGENT-GUARD-KERNEL",
            reasoning_capacity=3,
            verified_proof_level=2,
            requested_authority=2,
        ).to_dict(),
    ]

    self_refuting_probes = [
        SelfRefutingProbe(
            probe_id="PROBE-ADV-01",
            target_claim_id="CLAIM-AUTO-REVOCATION-DEMO",
            outcome="FAIL_INFORMATIF",
            fail_informative_preserved=True,
            counter_evidence_ref="PROBE-ADV-01:FAIL_INFORMATIF",
        ).to_dict(),
        SelfRefutingProbe(
            probe_id="PROBE-ADV-02",
            target_claim_id="CLAIM-PI0-LOCAL",
            outcome="PASS",
            fail_informative_preserved=True,
            counter_evidence_ref="",
        ).to_dict(),
    ]

    genesis_hash = protocol_sha256 if len(protocol_sha256) == 64 else canonical_sha256({"genesis": "SUPELA-PCEP-0"})
    step_1 = EvolutionaryCodeStep(
        step_id="EVOL-STEP-01",
        previous_hash=genesis_hash,
        transformation="formalize_pcep_9_families_network_bus",
        trace="omega_zero.pcep.build_pcep_network_envelope",
        scope="R_LOCAL_PYTHON_RUST_MCP",
        proof_refs=["pytest:test_pcep", "opa:pcep_invariants_satisfied", "a12:verify_a12"],
        counter_evidence=["OPEN-01..OPEN-08:A_PROUVER", "PROBE-ADV-01:FAIL_INFORMATIF"],
        generation_stage="G2",
    )

    core_payload: dict[str, Any] = {
        "schema": "supela-pcep-network/1",
        "generated_at_utc": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "claims": [c.to_dict() for c in engine.claims.values()],
        "referential_evaluations": referential_evaluations,
        "referential_transports": referential_transports,
        "dependency_cone": dependency_cone,
        "auto_revocation_transitions": [tx.to_dict() for tx in engine.revocation_transitions],
        "agent_authorities": agent_authorities,
        "self_refuting_probes": self_refuting_probes,
        "evolution_steps": [step_1.to_dict()],
        "open_proofs_registry": DEFAULT_OPEN_PROOFS,
    }

    payload_digest = canonical_sha256(core_payload)
    commands = sign_commands or [
        "cosign sign-blob --key cosign.key --yes --bundle reports/PCEP-NETWORK-SIGN-READY.json.bundle reports/PCEP-NETWORK-SIGN-READY.json",
        "gh pr review --approve <PR_NUMBER>",
    ]

    core_payload["signature_envelope"] = {
        "signature_status": SignatureStatus.EN_ATTENTE_SIGNATURE.value,
        "ready_for_signature": True,
        "canonical_payload_sha256": payload_digest,
        "signature": None,
        "required_signer_role": "AUTORITE_HUMAINE_CTO_CTA",
        "sign_commands": commands,
    }
    return core_payload
