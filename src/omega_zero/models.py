from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Any


def canonical_sha256(data: Any) -> str:
    """Compute deterministic SHA-256 hex digest of a JSON-serializable object."""
    encoded = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class ManqueStatus(str, Enum):
    """Les 7 statuts minimaux canoniques d'un objet Manque."""

    OUVERT = "OUVERT"
    SOUS_EXPLORATION = "SOUS_EXPLORATION"
    PARTIELLEMENT_REDUIT = "PARTIELLEMENT_RÉDUIT"
    RESOLU = "RÉSOLU"
    REFUTE_COMME_PROBLEME = "RÉFUTÉ_COMME_PROBLÈME"
    REQUALIFIE = "REQUALIFIÉ"
    INACCESSIBLE_DANS_LE_PERIMETRE = "INACCESSIBLE_DANS_LE_PÉRIMÈTRE"


class AuthorityLevel(IntEnum):
    """Échelle ordonnée permettant d'enforcer Autorité(C) <= Preuve(C)."""

    AUCUNE = 0
    LOCALE_CONDITIONNELLE = 1
    COLLECTIVE_CONDITIONNELLE = 2
    INTERDISCIPLINAIRE_QUALIFIEE = 3
    INTERNATIONALE_ETABLIE = 4


class RaccordStatus(str, Enum):
    CANDIDAT = "CANDIDAT"
    SUPPORTE_SOUS_CONDITIONS = "SUPPORTE_SOUS_CONDITIONS"
    REFUTE = "REFUTE"
    INCONNU = "INCONNU"
    ETABLI = "ETABLI"


class MergeOutcome(str, Enum):
    ACCEPTE = "ACCEPTÉ"
    PARTIEL = "PARTIEL"
    CONTESTE = "CONTESTÉ"
    ISOLE = "ISOLÉ"
    REFUSE = "REFUSÉ"


class RevidageStage(str, Enum):
    INIT = "INIT"
    PREPARE = "PREPARE"
    VERIFY = "VERIFY"
    COMMIT = "COMMIT"
    CLEAN = "CLEAN"
    ROLLED_BACK = "ROLLED_BACK"


CORE_INVARIANTS: tuple[str, ...] = (
    "I1:verite_verifiable",
    "I2:tracabilite",
    "I3:refutabilite",
    "I4:coherence",
    "I5:conservation_preuve",
    "I_M:conservation_manque_ouvert",
)


@dataclass
class Manque:
    """Objet Manque 4D avec traçabilité temporelle et machine à états."""

    id: str
    question: str
    contexte: str
    origine: str
    dependances: list[str]
    autorite: str
    temps: str
    statut: ManqueStatus = ManqueStatus.OUVERT
    tentatives: list[str] = field(default_factory=list)
    parent_id: str | None = None
    children_ids: list[str] = field(default_factory=list)
    scope: str = "LOCAL"
    transition_log: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "question": self.question,
            "contexte": self.contexte,
            "origine": self.origine,
            "dependances": list(self.dependances),
            "autorite": self.autorite,
            "tentatives": list(self.tentatives),
            "temps": self.temps,
            "statut": self.statut.value,
            "parent_id": self.parent_id,
            "children_ids": list(self.children_ids),
            "scope": self.scope,
            "transition_log": list(self.transition_log),
        }


@dataclass
class Raccord:
    """Raccord candidat, soutenu, réfuté ou émergent."""

    id: str
    label: str
    source: str
    target: str
    origin_node: str
    status: RaccordStatus = RaccordStatus.CANDIDAT
    authority_level: AuthorityLevel = AuthorityLevel.AUCUNE
    evidence_level: AuthorityLevel = AuthorityLevel.AUCUNE
    scope: str = "LOCAL"
    disciplines: list[str] = field(default_factory=list)
    conditions: list[str] = field(default_factory=list)
    is_emergent: bool = False
    composed_from: list[str] = field(default_factory=list)
    validation_required: bool = True
    provenance: str = ""
    refutation_reason: str | None = None
    version: int = 1
    active: bool = True

    def enforce_authority_bound(self) -> None:
        self.authority_level = min(self.authority_level, self.evidence_level)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "source": self.source,
            "target": self.target,
            "origin_node": self.origin_node,
            "status": self.status.value,
            "authority_level": self.authority_level.name,
            "evidence_level": self.evidence_level.name,
            "scope": self.scope,
            "disciplines": list(self.disciplines),
            "conditions": list(self.conditions),
            "is_emergent": self.is_emergent,
            "composed_from": list(self.composed_from),
            "validation_required": self.validation_required,
            "provenance": self.provenance,
            "refutation_reason": self.refutation_reason,
            "version": self.version,
            "active": self.active,
        }


@dataclass
class DisciplineAssessment:
    """Σ(Ri) = ⟨Force_i, Conflit_i, Discipline_i, Autorité_i⟩."""

    discipline: str
    raccord_id: str
    force: str
    conflit: str
    autorite: str
    conclusion_partielle: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "discipline": self.discipline,
            "raccord_id": self.raccord_id,
            "force": self.force,
            "conflit": self.conflit,
            "autorite": self.autorite,
            "conclusion_partielle": self.conclusion_partielle,
        }


@dataclass
class Conflict4D:
    """Objet 4D représentant un désaccord interdisciplinaire ou inter-nœuds conservé."""

    id: str
    raccord_id: str
    disciplines: list[str]
    type: str = "CONFLIT_INTERDISCIPLINAIRE"
    status: str = "CONSERVÉ"
    resolution: str = "NON_ACQUISE"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "type": self.type,
            "raccord_id": self.raccord_id,
            "disciplines": list(self.disciplines),
            "status": self.status,
            "resolution": self.resolution,
            "notes": self.notes,
        }


@dataclass
class Delta4D:
    """Delta 4D produit par un nœud local L_i : Δ_i(t_a, t_b) = L_i(t_b) ⊖ L_i(t_a)."""

    delta_id: str
    node_id: str
    jurisdiction: str
    timestamp: str
    authority_scope: str
    parent_hash: str
    payload: dict[str, Any]
    dependencies: list[str] = field(default_factory=list)
    contradictions: list[str] = field(default_factory=list)
    requested_cloud_status: str | None = None
    international_proof_attached: bool = False
    recoverable: bool = True
    complete: bool = True
    integrity_hash: str = ""

    def __post_init__(self) -> None:
        if not self.integrity_hash:
            self.integrity_hash = self.compute_hash()

    def compute_hash(self) -> str:
        return canonical_sha256(
            {
                "delta_id": self.delta_id,
                "node_id": self.node_id,
                "jurisdiction": self.jurisdiction,
                "timestamp": self.timestamp,
                "authority_scope": self.authority_scope,
                "parent_hash": self.parent_hash,
                "payload": self.payload,
                "dependencies": self.dependencies,
                "contradictions": self.contradictions,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "delta_id": self.delta_id,
            "node_id": self.node_id,
            "jurisdiction": self.jurisdiction,
            "timestamp": self.timestamp,
            "authority_scope": self.authority_scope,
            "parent_hash": self.parent_hash,
            "payload": self.payload,
            "dependencies": list(self.dependencies),
            "contradictions": list(self.contradictions),
            "requested_cloud_status": self.requested_cloud_status,
            "international_proof_attached": self.international_proof_attached,
            "integrity_hash": self.integrity_hash,
        }


@dataclass
class LocalMinimalState:
    """L_i^0 : état zéro minimal conservé après revidage transactionnel."""

    identite: str
    invariants: list[str]
    autorites: list[str]
    index_minimal: dict[str, str]
    preuve_transfert: str
    pointeur_recuperation: str
    manques_locaux: list[str]

    def is_non_amnesic(self) -> bool:
        return bool(
            self.identite
            and len(self.invariants) >= 6
            and self.preuve_transfert
            and self.pointeur_recuperation
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "identite": self.identite,
            "invariants": list(self.invariants),
            "autorites": list(self.autorites),
            "index_minimal": dict(self.index_minimal),
            "preuve_transfert": self.preuve_transfert,
            "pointeur_recuperation": self.pointeur_recuperation,
            "manques_locaux": list(self.manques_locaux),
        }


@dataclass
class LocalNode:
    """L_i(t) = ⟨D_i, R_i, P_i, C_i, U_i, A_i, H_i⟩_t."""

    node_id: str
    location: str
    jurisdiction: str
    D_observations: list[dict[str, Any]] = field(default_factory=list)
    R_raccords: dict[str, Raccord] = field(default_factory=dict)
    P_preuves: dict[str, dict[str, Any]] = field(default_factory=dict)
    C_conflicts: dict[str, Conflict4D] = field(default_factory=dict)
    U_manques: dict[str, Manque] = field(default_factory=dict)
    A_autorites: list[str] = field(default_factory=list)
    H_history: list[dict[str, Any]] = field(default_factory=list)
    revidage_stage: RevidageStage = RevidageStage.INIT
    frozen_delta: Delta4D | None = None
    commit_tx_id: str | None = None
    minimal_state: LocalMinimalState | None = None

    def snapshot_hash(self) -> str:
        return canonical_sha256(
            {
                "node_id": self.node_id,
                "D": self.D_observations,
                "R": {k: v.to_dict() for k, v in sorted(self.R_raccords.items())},
                "P": self.P_preuves,
                "C": {k: v.to_dict() for k, v in sorted(self.C_conflicts.items())},
                "U": {k: v.to_dict() for k, v in sorted(self.U_manques.items())},
                "A": self.A_autorites,
            }
        )


@dataclass
class LoadMetricDeclaration:
    """Les 6 paramètres obligatoires déclarés avant l'évaluation du seuil de saturation."""

    metric: str
    capacity_limit: dict[str, float | int]
    unit: str
    measurement_method: str
    timestamp: str
    tested_environment: str

    def is_complete(self) -> bool:
        required_keys = {"bytes_limit", "objects_limit", "edges_limit", "latency_limit_ms"}
        return (
            bool(self.metric)
            and required_keys.issubset(self.capacity_limit.keys())
            and all(float(self.capacity_limit[k]) > 0 for k in required_keys)
            and bool(self.unit)
            and bool(self.measurement_method)
            and bool(self.timestamp)
            and bool(self.tested_environment)
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "metric": self.metric,
            "capacity_limit": dict(self.capacity_limit),
            "unit": self.unit,
            "measurement_method": self.measurement_method,
            "timestamp": self.timestamp,
            "tested_environment": self.tested_environment,
        }


@dataclass
class Container:
    """Conteneur 4D mesurable selon Load(C) et migrable sans perte d'invariants."""

    container_id: str
    bytes_limit: int
    objects_limit: int
    edges_limit: int
    latency_limit_ms: float
    observed_latency_ms: float = 10.0
    objects: dict[str, dict[str, Any]] = field(default_factory=dict)
    edges: list[dict[str, Any]] = field(default_factory=list)
    integrity_hashes: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    metric_declaration: LoadMetricDeclaration | None = None

    def used_bytes(self) -> int:
        serialized = json.dumps(
            {"objects": self.objects, "edges": self.edges},
            sort_keys=True,
            ensure_ascii=False,
        )
        return len(serialized.encode("utf-8"))

    def compute_load(self) -> dict[str, float]:
        used_b = self.used_bytes()
        used_o = len(self.objects)
        used_e = len(self.edges)
        ratios = {
            "bytes_ratio": used_b / self.bytes_limit,
            "objects_ratio": used_o / self.objects_limit,
            "edges_ratio": used_e / self.edges_limit,
            "latency_ratio": self.observed_latency_ms / self.latency_limit_ms,
        }
        ratios["load"] = max(ratios.values())
        return ratios

    def add_object(self, obj_id: str, payload: dict[str, Any]) -> None:
        self.objects[obj_id] = payload
        self.integrity_hashes[obj_id] = canonical_sha256(payload)
        self.history.append({"event": "ADD_OBJECT", "id": obj_id, "hash": self.integrity_hashes[obj_id]})

    def add_edge(self, src: str, dst: str, label: str, provenance: str) -> None:
        edge = {"src": src, "dst": dst, "label": label, "provenance": provenance}
        self.edges.append(edge)
        self.history.append({"event": "ADD_EDGE", "edge": edge})

    def can_reconstruct(self) -> bool:
        for obj_id, payload in self.objects.items():
            if self.integrity_hashes.get(obj_id) != canonical_sha256(payload):
                return False
        return len(self.objects) > 0 and len(self.history) >= len(self.objects)


@dataclass
class ZeroState:
    """0_t = {I, P, M, A, H} produit par Π₀(S_t)."""

    invariants: tuple[str, ...]
    proofs: dict[str, dict[str, Any]]
    refutations: dict[str, dict[str, Any]]
    manques: dict[str, Manque]
    authorities: dict[str, str]
    history: list[dict[str, Any]]
    dropped_provisional: list[str] = field(default_factory=list)

    def canonical_hash(self) -> str:
        return canonical_sha256(
            {
                "I": list(self.invariants),
                "P": self.proofs,
                "Ref": self.refutations,
                "M": {k: v.to_dict() for k, v in sorted(self.manques.items())},
                "A": self.authorities,
                "H": self.history,
            }
        )

    def is_non_empty(self) -> bool:
        return len(self.invariants) >= 6


@dataclass
class CloudOmega:
    """Représentation Cloud gouvernée de Ω_t (Hébergement ≠ Propriété)."""

    nodes_registered: dict[str, dict[str, Any]] = field(default_factory=dict)
    deltas_received: list[Delta4D] = field(default_factory=list)
    raccords: dict[str, Raccord] = field(default_factory=dict)
    assessments: list[DisciplineAssessment] = field(default_factory=list)
    conflicts: dict[str, Conflict4D] = field(default_factory=dict)
    manques: dict[str, Manque] = field(default_factory=dict)
    proofs: dict[str, dict[str, Any]] = field(default_factory=dict)
    authorities: dict[str, str] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)
    rejected_escalations: list[dict[str, Any]] = field(default_factory=list)
    merge_log: list[dict[str, Any]] = field(default_factory=list)
    committed_transfers: dict[str, dict[str, Any]] = field(default_factory=dict)
    destroyed: bool = False
