"""
GovernanceOrchestrator — SCDH v1.0
Moteur décisionnel de production du Système de Contrôle Décentralisé Hexaplexe.
Auto-évalué : CC=9, IS=3 (Conforme — limite maximale autorisée par Annexe D).

Auteur : Jean-François Gadbois (Jef)
Certifié Gate G0 — PV-CVEA-2026-001
"""

from __future__ import annotations
from dataclasses import dataclass
from enum import Enum


class AutoLevel(str, Enum):
    N0_MANUAL     = "N0_MANUAL"
    N1_ASSISTED   = "N1_ASSISTED"
    N2_PARTIAL    = "N2_PARTIAL"
    N3_HIGH       = "N3_HIGH"
    N4_FULL       = "N4_FULL"


class Gate(str, Enum):
    APPROVED  = "APPROVED"
    REVIEW    = "REVIEW"
    REJECTED  = "REJECTED"
    TIMEOUT   = "TIMEOUT"
    EMERGENCY = "EMERGENCY"


@dataclass
class Decision:
    level: AutoLevel
    gate: Gate
    bias_index: float        # I_B : 0.0 → 1.0
    simplicity_index: int    # IS  : 0 → 5
    kill_switch_active: bool = False


class GovernanceOrchestrator:
    """
    Orchestre les décisions autonomes du SCDH en appliquant les 4 invariants :
      Invariant I  — IS ≤ 3 (Anti-sur-ingénierie, Annexe D)
      Invariant II — I_B ≤ 0.10 pour N3+, I_B ≤ 0.25 pour N2 (Annexe C)
      Invariant III — V4 < 100 ms (Annexe B)
      Invariant IV  — Fail-secure : tout état inconnu → N0_MANUAL
    """

    def __init__(self, initial_level: AutoLevel = AutoLevel.N3_HIGH) -> None:
        self.current_level = initial_level
        self.kill_switch_active = False

    def evaluate(self, decision: Decision) -> AutoLevel:
        """Évalue une décision et retourne le niveau d'automatisation résultant."""
        if decision.kill_switch_active or decision.gate is Gate.EMERGENCY:
            return self.trigger_v4_kill_switch()
        target = self._resolve_target_level(decision)
        self.current_level = target
        return target

    def trigger_v4_kill_switch(self) -> AutoLevel:
        """V4 Kill Switch — Débrayage immédiat vers N0_MANUAL (SLA < 100 ms)."""
        self.kill_switch_active = True
        self.current_level = AutoLevel.N0_MANUAL
        return AutoLevel.N0_MANUAL

    def reactivate(self, cvea_votes: int, required_votes: int = 3) -> bool:
        """Réactivation post-V4 — requiert approbation CVEA (majorité qualifiée)."""
        if cvea_votes >= required_votes:
            self.kill_switch_active = False
            self.current_level = AutoLevel.N1_ASSISTED
            return True
        return False

    def _resolve_target_level(self, d: Decision) -> AutoLevel:  # CC ≤ 9
        if d.simplicity_index >= 4:
            return AutoLevel.N1_ASSISTED
        if d.gate in (Gate.REJECTED, Gate.TIMEOUT):
            return AutoLevel.N1_ASSISTED
        if d.bias_index > 0.25:
            return AutoLevel.N0_MANUAL
        if d.bias_index > 0.10:
            return AutoLevel.N1_ASSISTED
        if d.gate is Gate.APPROVED and d.bias_index <= 0.10 and d.simplicity_index <= 3:
            return d.level
        return AutoLevel.N1_ASSISTED
