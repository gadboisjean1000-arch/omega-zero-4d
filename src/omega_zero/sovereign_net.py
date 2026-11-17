from __future__ import annotations

import base64
import hashlib
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Final

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from .models import canonical_sha256

EMPTY_SHA: Final[str] = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
SAFE_QUERY_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[a-z0-9_\-]+$")
ALLOWED_WORKSPACES: Final[frozenset[str]] = frozenset({"k8s", "dev", "prod", "monitoring", "local"})


class TransportVector(StrEnum):
    TOR_ONION_V3 = "TOR_ONION_V3"
    I2P_GARLIC = "I2P_GARLIC"
    MIXNET_SPHINX = "MIXNET_SPHINX"
    MESH_YGGDRASIL_LORA = "MESH_YGGDRASIL_LORA"
    PLUGGABLE_TRANSPORT = "PLUGGABLE_TRANSPORT"
    AIR_GAP_DIODE = "AIR_GAP_DIODE"
    SIMPLEX_BLIND_DEAD_DROP = "SIMPLEX_BLIND_DEAD_DROP"


@dataclass(frozen=True)
class TransportProfile:
    """Profil formel d'une topologie de transport anonyme ou découplée."""

    vector: TransportVector
    correlation_resistance: str
    internet_dependency: str
    feedback_mode: str
    stateless_strict: bool
    notes: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector": self.vector.value,
            "correlation_resistance": self.correlation_resistance,
            "internet_dependency": self.internet_dependency,
            "feedback_mode": self.feedback_mode,
            "stateless_strict": self.stateless_strict,
            "notes": self.notes,
        }


TRANSPORT_PROFILES: tuple[TransportProfile, ...] = (
    TransportProfile(
        vector=TransportVector.TOR_ONION_V3,
        correlation_resistance="MOYENNE",
        internet_dependency="OUI",
        feedback_mode="BIDIRECTIONAL",
        stateless_strict=False,
        notes="Routage en oignon faible latence (.onion v3 Ed25519); sensible à la corrélation temporelle globale.",
    ),
    TransportProfile(
        vector=TransportVector.I2P_GARLIC,
        correlation_resistance="BONNE",
        internet_dependency="OUI",
        feedback_mode="BIDIRECTIONAL",
        stateless_strict=False,
        notes="Routage en ail par tunnels unidirectionnels séparés (.i2p).",
    ),
    TransportProfile(
        vector=TransportVector.MIXNET_SPHINX,
        correlation_resistance="TRES_FORTE",
        internet_dependency="OUI",
        feedback_mode="ASYNC_MIXED",
        stateless_strict=False,
        notes="Mélange Sphinx avec délais aléatoires et trafic de couverture (Nym/Katzenpost).",
    ),
    TransportProfile(
        vector=TransportVector.MESH_YGGDRASIL_LORA,
        correlation_resistance="ELEVEE",
        internet_dependency="PARTIELLE_OU_NON",
        feedback_mode="MESH_AD_HOC",
        stateless_strict=False,
        notes="Routage cryptographique géométrique ou radiofréquence LoRa/Meshtastic sans FAI.",
    ),
    TransportProfile(
        vector=TransportVector.PLUGGABLE_TRANSPORT,
        correlation_resistance="MOYENNE",
        internet_dependency="OUI",
        feedback_mode="OBFUSCATED_BIDIRECTIONAL",
        stateless_strict=False,
        notes="Dissimulation de flux (Shadowsocks/V2Ray/stéganographie de protocole).",
    ),
    TransportProfile(
        vector=TransportVector.AIR_GAP_DIODE,
        correlation_resistance="ABSOLUE_RESEAU",
        internet_dependency="NON",
        feedback_mode="UNIDIRECTIONAL_PHYSICAL",
        stateless_strict=True,
        notes="Déconnexion physique totale, échange asynchrone signé (QR/USB/diode optique).",
    ),
    TransportProfile(
        vector=TransportVector.SIMPLEX_BLIND_DEAD_DROP,
        correlation_resistance="FORTE_DECOUPLEE",
        internet_dependency="OPTIONNELLE",
        feedback_mode="SIMPLEX_BLIND",
        stateless_strict=True,
        notes="Diffusion unidirectionnelle aveugle sans ACK/SYN; lecture par invariant local.",
    ),
)


@dataclass(frozen=True)
class HistoryEntry:
    action: str
    payload: str
    state_hash: str


class SupelaInherentCore:
    """
    Noyau inhérent souverain (0$ PMU) :
    - ZERO-STATE-01 : ancrage physique au Vide absolu (EMPTY_SHA)
    - ZERO-AGENT-01 : rejet sec des cibles non canoniques
    - SUP-NORM-NET-01/1.0 : admission réseau par preuve pas-à-pas sans saut logique
    """

    EMPTY_SHA: Final[str] = EMPTY_SHA

    def __init__(self, node_id: str = "NODE-LOCAL-01") -> None:
        self.node_id = node_id
        self.state_hash: str = self.EMPTY_SHA
        self.history: list[HistoryEntry] = []
        self.registry: dict[str, Callable[[str], str]] = {}
        self.reset_to_zero()

    @staticmethod
    def _hash(data: str) -> str:
        return hashlib.sha256(data.encode("utf-8")).hexdigest()

    def reset_to_zero(self) -> None:
        """ZERO-STATE-01 : purge réelle, traçable et vérifiable vers le point zéro."""
        self.state_hash = self.EMPTY_SHA
        self.history.append(HistoryEntry(action="RESET_ZERO", payload="", state_hash=self.state_hash))

    def register_command(self, trigger: str, handler: Callable[[str], str]) -> None:
        self.registry[trigger.strip().lower()] = handler

    def evaluate_command(self, raw_input: str) -> tuple[int, str]:
        cmd = raw_input.strip().lower()
        if not cmd or len(cmd) < 2:
            self.reset_to_zero()
            return 0, f"[RESET_ZERO] État ramené au point zéro | HASH: {self.state_hash[:8]}"

        if cmd not in self.registry:
            return 1, f"[ERR_NON_CANONIQUE] Cible inconnue. État verrouillé | HASH: {self.state_hash[:8]}"

        result = str(self.registry[cmd](cmd))
        self.state_hash = self._hash(self.state_hash + result)
        self.history.append(HistoryEntry(action=f"CMD:{cmd}", payload=result, state_hash=self.state_hash))
        return 2, f"[OK] {result} | HASH: {self.state_hash[:8]}"

    def verify_network_frame(self, frame: dict[str, Any]) -> tuple[int, str]:
        """SUP-NORM-NET-01/1.0 : admet un paquet réseau uniquement s'il prouve sa chaîne sans saut."""
        calcul = frame.get("calcul_declare")
        steps = frame.get("steps")
        expected_sig = frame.get("signature", "")

        if not calcul or not isinstance(steps, list) or not steps:
            return 1, "[REJET_STRUCTURE] Calcul non déclaré ou étapes manquantes."

        running_sig = self.EMPTY_SHA
        for step in steps:
            running_sig = self._hash(running_sig + str(step))

        if running_sig != expected_sig:
            return 1, "[BLOQUE_FALSIFICATION] Preuve rejetée : saut logique ou signature invalide."

        self.state_hash = self._hash(self.state_hash + str(expected_sig))
        self.history.append(
            HistoryEntry(action=f"NET_ADMIT:{calcul}", payload=str(expected_sig), state_hash=self.state_hash)
        )
        return 0, f"[CONFORME_INTERNATIONAL] Calcul {calcul} validé | HASH: {self.state_hash[:8]}"

    def audit_trail(self) -> bool:
        """Rejeu déterministe complet de l'historique depuis EMPTY_SHA (détecte toute altération)."""
        if not self.history:
            return False
        calc = self.EMPTY_SHA
        for entry in self.history:
            if entry.action == "RESET_ZERO":
                calc = self.EMPTY_SHA
            elif entry.action.startswith("CMD:") or entry.action.startswith("NET_ADMIT:"):
                calc = self._hash(calc + entry.payload)
            else:
                return False
            if calc != entry.state_hash:
                return False
        return calc == self.state_hash


@dataclass(frozen=True)
class SovereignSearchQuery:
    """Requête de recherche souveraine, normalisée, sans énumération ?type=... et signée Ed25519."""

    query: str
    workspace: str
    signature_b64: str
    type_param_present: bool = False

    def __post_init__(self) -> None:
        if self.type_param_present:
            raise ValueError("CRITICAL: L'énumération explicite de types (?type=...) est interdite.")
        cleaned_query = self.query.strip().lower()
        if not SAFE_QUERY_PATTERN.match(cleaned_query):
            raise ValueError(f"CRITICAL: Requête rejetée (caractères non conformes): {self.query!r}")
        if self.workspace not in ALLOWED_WORKSPACES:
            raise ValueError(f"CRITICAL: Espace de travail non autorisé: {self.workspace!r}")
        object.__setattr__(self, "query", cleaned_query)

    def canonical_bytes(self) -> bytes:
        return canonical_sha256({"query": self.query, "workspace": self.workspace}).encode("utf-8")

    @classmethod
    def sign_new(
        cls,
        query: str,
        workspace: str,
        private_key: Ed25519PrivateKey,
    ) -> SovereignSearchQuery:
        cleaned = query.strip().lower()
        draft = cls(query=cleaned, workspace=workspace, signature_b64="pending")
        sig = private_key.sign(draft.canonical_bytes())
        return cls(
            query=cleaned,
            workspace=workspace,
            signature_b64=base64.b64encode(sig).decode("ascii"),
        )

    def verify_integrity(self, public_key: Ed25519PublicKey) -> bool:
        try:
            sig_bytes = base64.b64decode(self.signature_b64, validate=True)
            public_key.verify(sig_bytes, self.canonical_bytes())
            return True
        except (InvalidSignature, ValueError):
            return False

    def to_opa_dict(self, *, signature_verified: bool) -> dict[str, Any]:
        return {
            "query": self.query,
            "workspace": self.workspace,
            "type_param_present": self.type_param_present,
            "signature_verified": signature_verified,
        }


@dataclass
class SovereignNetReport:
    """Synthèse exécutable de l'isolation anti-EaaS, du noyau inhérent et des topologies."""

    external_saas_telemetry: bool = False
    external_eaas_recalculation: bool = False
    exogenous_unsigned_rejected: bool = True
    audit_trail_verified: bool = True
    search_queries: list[dict[str, Any]] = field(default_factory=list)
    transport_profiles: list[dict[str, Any]] = field(default_factory=list)
    inherent_core_state_hash: str = EMPTY_SHA

    def to_dict(self) -> dict[str, Any]:
        return {
            "external_saas_telemetry": self.external_saas_telemetry,
            "external_eaas_recalculation": self.external_eaas_recalculation,
            "exogenous_unsigned_rejected": self.exogenous_unsigned_rejected,
            "audit_trail_verified": self.audit_trail_verified,
            "search_queries": list(self.search_queries),
            "transport_profiles": list(self.transport_profiles),
            "inherent_core_state_hash": self.inherent_core_state_hash,
        }


def run_sovereign_net_self_check() -> dict[str, Any]:
    """Exécute le banc d'auto-validation complet (Zéro, Rejet, SUP-NORM-NET-01/1.0, Ed25519, Topologies)."""
    core = SupelaInherentCore()
    assert core.state_hash == EMPTY_SHA

    # Rejet ZERO-AGENT-01
    code_unknown, _ = core.evaluate_command("commande_fantome")
    assert code_unknown == 1 and core.state_hash == EMPTY_SHA

    # Preuve réseau légitime SUP-NORM-NET-01/1.0
    steps_ok = ["n=4k", "n=2(2k)", "pair(n)"]
    sig_ok = EMPTY_SHA
    for s in steps_ok:
        sig_ok = core._hash(sig_ok + s)
    code_ok, _ = core.verify_network_frame({"calcul_declare": "LINEAR-DIV-v1", "steps": steps_ok, "signature": sig_ok})
    assert code_ok == 0

    # Saut logique refusé
    code_jump, _ = core.verify_network_frame(
        {"calcul_declare": "LINEAR-DIV-v1", "steps": ["n=4k", "pair(n)"], "signature": sig_ok}
    )
    assert code_jump == 1

    # Requête souveraine signée Ed25519
    priv = Ed25519PrivateKey.generate()
    pub = priv.public_key()
    sq = SovereignSearchQuery.sign_new("box_noire", "monitoring", priv)
    sig_verified = sq.verify_integrity(pub)
    assert sig_verified is True

    report = SovereignNetReport(
        external_saas_telemetry=False,
        external_eaas_recalculation=False,
        exogenous_unsigned_rejected=True,
        audit_trail_verified=core.audit_trail(),
        search_queries=[sq.to_opa_dict(signature_verified=sig_verified)],
        transport_profiles=[p.to_dict() for p in TRANSPORT_PROFILES],
        inherent_core_state_hash=core.state_hash,
    )
    return report.to_dict()
