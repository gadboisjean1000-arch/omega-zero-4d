"""Supela Ω-ZERO · Local–Cloud–4D executable engine and test harness."""

from .attestation import AttestationSigner, SignedAttestation
from .grpo_bridge import CandidateExploration, SupelaGRPOBridge
from .models import (
    AuthorityLevel,
    CloudOmega,
    Conflict4D,
    Container,
    Delta4D,
    DisciplineAssessment,
    LoadMetricDeclaration,
    LocalMinimalState,
    LocalNode,
    Manque,
    ManqueStatus,
    MergeOutcome,
    Raccord,
    RaccordStatus,
    RevidageStage,
    ZeroState,
)
from .projection import ManqueStateMachine, Pi0Projector, TransitionError
from .protocol import (
    OmegaZeroEngine,
    RevidageFailure,
    SaturationWithoutDeclarationError,
)
from .worm_ledger import VaultRunResult, WormTamperError, WormVault

__all__ = [
    "AttestationSigner",
    "AuthorityLevel",
    "CandidateExploration",
    "CloudOmega",
    "Conflict4D",
    "Container",
    "Delta4D",
    "DisciplineAssessment",
    "LoadMetricDeclaration",
    "LocalMinimalState",
    "LocalNode",
    "Manque",
    "ManqueStateMachine",
    "ManqueStatus",
    "MergeOutcome",
    "OmegaZeroEngine",
    "Pi0Projector",
    "Raccord",
    "RaccordStatus",
    "RevidageFailure",
    "RevidageStage",
    "SaturationWithoutDeclarationError",
    "SignedAttestation",
    "SupelaGRPOBridge",
    "TransitionError",
    "VaultRunResult",
    "WormTamperError",
    "WormVault",
    "ZeroState",
]
